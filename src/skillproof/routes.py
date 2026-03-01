import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select

from .assessor import assess_video, assess_file
from .certificate import generate_certificate
from .correction import generate_correction_videos, generate_text_corrections
from .config import settings
from .database import get_session
from .models import User, Certification, TaskResult, Certificate, Organisation, CustomRubric
from .scorer import aggregate
from .upload import save_upload

router = APIRouter(prefix="/api")

RUBRICS_DIR = Path(__file__).resolve().parent.parent.parent / "rubrics"


@router.get("/trades")
def list_trades():
    trades = []
    for rubric_file in sorted(RUBRICS_DIR.glob("*.json")):
        with open(rubric_file) as f:
            rubric = json.load(f)
        trades.append({
            "key": rubric_file.stem,
            "name": rubric["trade"],
            "level": rubric["level"],
            "task_count": len(rubric["tasks"]),
            "pass_threshold": rubric["scoring"]["pass_threshold"],
        })
    return {"trades": trades}


@router.get("/trades/{trade_key}/tasks")
def list_tasks(trade_key: str):
    rubric_path = RUBRICS_DIR / f"{trade_key}.json"
    if not rubric_path.exists():
        raise HTTPException(404, f"Trade '{trade_key}' not found")
    with open(rubric_path) as f:
        rubric = json.load(f)
    tasks = [
        {
            "id": t["id"],
            "title": t["title"],
            "format": t["format"],
            "time_minutes": t["time_minutes"],
            "instruction": t["instruction"],
        }
        for t in rubric["tasks"]
    ]
    return {"trade": rubric["trade"], "tasks": tasks}


@router.post("/users")
def create_user(name: str = Form(...), email: str = Form(...), session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        return {"user_id": existing.id, "name": existing.name, "email": existing.email}
    user = User(name=name, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"user_id": user.id, "name": user.name, "email": user.email}


@router.post("/certifications")
def start_certification(
    user_id: int = Form(...),
    trade: str = Form(...),
    session: Session = Depends(get_session),
):
    cert = Certification(user_id=user_id, trade=trade)
    session.add(cert)
    session.commit()
    session.refresh(cert)
    return {"certification_id": cert.id, "trade": cert.trade, "status": cert.status}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        result = await save_upload(file)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return result


@router.post("/assess")
def assess_task(
    certification_id: int = Form(...),
    task_id: str = Form(...),
    trade: str = Form(...),
    video_url: str = Form(None),
    file_path: str = Form(None),
    session: Session = Depends(get_session),
):
    if not video_url and not file_path:
        raise HTTPException(400, "Provide either video_url or file_path")

    if video_url:
        assessment = assess_video(trade, task_id, video_url)
    else:
        assessment = assess_file(trade, task_id, file_path)

    result = aggregate(assessment)

    task_result = TaskResult(
        certification_id=certification_id,
        task_id=task_id,
        video_url=video_url,
        file_path=file_path,
        assessment_json=json.dumps(assessment),
        safety_score=result["scores"]["safety"],
        technique_score=result["scores"]["technique"],
        result_score=result["scores"]["result"],
        weighted_total=result["weighted_total"],
        passed=result["passed"],
    )
    session.add(task_result)
    session.commit()
    session.refresh(task_result)

    # Get text corrections for failed criteria
    rubric_path = RUBRICS_DIR / f"{trade}.json"
    task_title = task_id
    if rubric_path.exists():
        with open(rubric_path) as f:
            rubric = json.load(f)
        for t in rubric["tasks"]:
            if t["id"].upper() == task_id.upper():
                task_title = t["title"]
                break

    corrections = generate_text_corrections(task_title, assessment)

    return {
        "task_result_id": task_result.id,
        "task_id": task_id,
        **result,
        "assessment": assessment,
        "corrections": corrections,
    }


@router.post("/corrections/generate")
def gen_corrections(
    task_result_id: int = Form(...),
    session: Session = Depends(get_session),
):
    task_result = session.get(TaskResult, task_result_id)
    if not task_result:
        raise HTTPException(404, "Task result not found")

    assessment = json.loads(task_result.assessment_json)
    if assessment.get("skipped"):
        return {"corrections": []}

    # Find task title from rubric
    cert = session.get(Certification, task_result.certification_id)
    rubric_path = RUBRICS_DIR / f"{cert.trade}.json"
    task_title = task_result.task_id
    if rubric_path.exists():
        with open(rubric_path) as f:
            rubric = json.load(f)
        for t in rubric["tasks"]:
            if t["id"].upper() == task_result.task_id.upper():
                task_title = t["title"]
                break

    corrections = generate_correction_videos(
        task_id=task_result.task_id,
        task_title=task_title,
        assessment=assessment,
        cert_id=task_result.certification_id,
        original_video_path=task_result.file_path,
        trade=cert.trade,
    )
    return {"corrections": corrections}


@router.post("/skip")
def skip_task(
    certification_id: int = Form(...),
    task_id: str = Form(...),
    score: float = Form(40),
    session: Session = Depends(get_session),
):
    task_result = TaskResult(
        certification_id=certification_id,
        task_id=task_id,
        video_url=None,
        file_path=None,
        assessment_json=json.dumps({"skipped": True, "default_score": score}),
        safety_score=score,
        technique_score=score,
        result_score=score,
        weighted_total=score,
        passed=score >= 70,
    )
    session.add(task_result)
    session.commit()
    session.refresh(task_result)
    return {"task_result_id": task_result.id, "task_id": task_id, "skipped": True, "score": score}


@router.post("/certificate")
def issue_certificate(
    certification_id: int = Form(...),
    worker_name: str = Form(...),
    session: Session = Depends(get_session),
):
    cert_record = session.get(Certification, certification_id)
    if not cert_record:
        raise HTTPException(404, "Certification not found")

    results = session.exec(
        select(TaskResult).where(TaskResult.certification_id == certification_id)
    ).all()

    if not results:
        raise HTTPException(400, "No task results found for this certification")

    # Allow certificate generation even with failed tasks — shows overall score

    avg_safety = sum(r.safety_score for r in results) / len(results)
    avg_technique = sum(r.technique_score for r in results) / len(results)
    avg_result = sum(r.result_score for r in results) / len(results)
    avg_total = sum(r.weighted_total for r in results) / len(results)

    task_scores = {
        "safety": round(avg_safety, 1),
        "technique": round(avg_technique, 1),
        "result": round(avg_result, 1),
    }

    cert_data = generate_certificate(
        worker_name=worker_name,
        trade=cert_record.trade,
        score=avg_total,
        task_scores=task_scores,
    )

    # Get org name if linked
    org_name = None
    if cert_record.org_id:
        org = session.get(Organisation, cert_record.org_id)
        if org:
            org_name = org.name

    db_cert = Certificate(
        certification_id=certification_id,
        cert_id=cert_data["cert_id"],
        worker_name=worker_name,
        trade=cert_record.trade,
        overall_score=avg_total,
        safety_score=avg_safety,
        technique_score=avg_technique,
        result_score=avg_result,
        org_name=org_name,
        pdf_path=cert_data["pdf_path"],
        verify_url=cert_data["verify_url"],
    )
    session.add(db_cert)

    cert_record.status = "passed"
    session.add(cert_record)
    session.commit()
    session.refresh(db_cert)

    return {
        "cert_id": db_cert.cert_id,
        "worker_name": db_cert.worker_name,
        "trade": db_cert.trade,
        "overall_score": db_cert.overall_score,
        "scores": task_scores,
        "org_name": db_cert.org_name,
        "pdf_path": db_cert.pdf_path,
        "verify_url": db_cert.verify_url,
        "issued_at": db_cert.issued_at.isoformat(),
    }


@router.get("/verify/{cert_id}")
def verify_certificate(cert_id: str, session: Session = Depends(get_session)):
    from fastapi.responses import HTMLResponse
    cert = session.exec(
        select(Certificate).where(Certificate.cert_id == cert_id)
    ).first()
    if not cert:
        raise HTTPException(404, "Certificate not found")
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SkillProof — Certificate Verification</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;margin:0;padding:20px}}
.card{{max-width:480px;margin:0 auto;background:#fff;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,.1)}}
.badge{{display:inline-block;background:#e8f5e9;color:#2e7d32;padding:4px 12px;border-radius:20px;font-weight:700;font-size:14px;margin-bottom:16px}}
h1{{font-size:20px;margin:0 0 4px}}
.trade{{color:#1565c0;font-size:16px;font-weight:600;margin-bottom:16px}}
.scores{{display:flex;gap:12px;margin:12px 0}}
.score-item{{flex:1;text-align:center;padding:8px;background:#f8f9fa;border-radius:8px}}
.score-item .val{{font-size:20px;font-weight:700}}
.score-item .label{{font-size:12px;color:#666}}
.meta{{font-size:13px;color:#888;margin-top:16px}}
.overall{{font-size:28px;font-weight:700;margin:8px 0}}
</style></head><body>
<div class="card">
<span class="badge">✓ Verified Certificate</span>
<h1>{cert.worker_name}</h1>
<p class="trade">{cert.trade}</p>
<p class="overall">{cert.overall_score:.1f}%</p>
<div class="scores">
<div class="score-item"><div class="val">{cert.safety_score:.0f}%</div><div class="label">Safety</div></div>
<div class="score-item"><div class="val">{cert.technique_score:.0f}%</div><div class="label">Technique</div></div>
<div class="score-item"><div class="val">{cert.result_score:.0f}%</div><div class="label">Result</div></div>
</div>
<p class="meta">Certificate ID: {cert.cert_id}<br>Issued: {cert.issued_at.strftime('%d %B %Y')}<br>Powered by SkillProof</p>
</div></body></html>"""
    return HTMLResponse(content=html)


# ---- Organisation / B2B routes ----

@router.post("/orgs")
def create_org(
    name: str = Form(...),
    logo_url: str = Form(None),
    session: Session = Depends(get_session),
):
    import re
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    # Ensure unique slug
    existing = session.exec(select(Organisation).where(Organisation.slug == slug)).first()
    if existing:
        return {"org_id": existing.id, "name": existing.name, "slug": existing.slug}
    org = Organisation(name=name, logo_url=logo_url, slug=slug)
    session.add(org)
    session.commit()
    session.refresh(org)
    return {"org_id": org.id, "name": org.name, "slug": org.slug}


@router.get("/orgs/{slug}")
def get_org(slug: str, session: Session = Depends(get_session)):
    org = session.exec(select(Organisation).where(Organisation.slug == slug)).first()
    if not org:
        raise HTTPException(404, "Organisation not found")
    # Get custom rubrics
    rubrics = session.exec(select(CustomRubric).where(CustomRubric.org_id == org.id)).all()
    return {
        "org_id": org.id,
        "name": org.name,
        "slug": org.slug,
        "logo_url": org.logo_url,
        "rubrics": [
            {"id": r.id, "trade": r.trade, "pass_threshold": r.pass_threshold}
            for r in rubrics
        ],
    }


@router.post("/orgs/{slug}/rubrics")
def save_custom_rubric(
    slug: str,
    trade: str = Form(...),
    rubric_json: str = Form(...),
    pass_threshold: float = Form(70),
    session: Session = Depends(get_session),
):
    org = session.exec(select(Organisation).where(Organisation.slug == slug)).first()
    if not org:
        raise HTTPException(404, "Organisation not found")
    # Validate JSON
    try:
        json.loads(rubric_json)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid rubric JSON")
    # Update existing or create new
    existing = session.exec(
        select(CustomRubric).where(CustomRubric.org_id == org.id, CustomRubric.trade == trade)
    ).first()
    if existing:
        existing.rubric_json = rubric_json
        existing.pass_threshold = pass_threshold
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return {"rubric_id": existing.id, "trade": trade, "updated": True}
    cr = CustomRubric(org_id=org.id, trade=trade, rubric_json=rubric_json, pass_threshold=pass_threshold)
    session.add(cr)
    session.commit()
    session.refresh(cr)
    return {"rubric_id": cr.id, "trade": trade, "updated": False}


@router.get("/orgs/{slug}/rubrics/{trade}")
def get_custom_rubric(slug: str, trade: str, session: Session = Depends(get_session)):
    org = session.exec(select(Organisation).where(Organisation.slug == slug)).first()
    if not org:
        raise HTTPException(404, "Organisation not found")
    cr = session.exec(
        select(CustomRubric).where(CustomRubric.org_id == org.id, CustomRubric.trade == trade)
    ).first()
    if not cr:
        # Return default rubric
        rubric_path = RUBRICS_DIR / f"{trade}.json"
        if not rubric_path.exists():
            raise HTTPException(404, f"Trade '{trade}' not found")
        with open(rubric_path) as f:
            rubric = json.load(f)
        return {"rubric": rubric, "is_default": True, "pass_threshold": rubric["scoring"]["pass_threshold"]}
    return {"rubric": json.loads(cr.rubric_json), "is_default": False, "pass_threshold": cr.pass_threshold}


@router.get("/assess/{slug}/{trade}")
def get_org_assessment_info(slug: str, trade: str, session: Session = Depends(get_session)):
    """Info endpoint for branded assessment links: /assess/abc-recruitment/tiling"""
    org = session.exec(select(Organisation).where(Organisation.slug == slug)).first()
    if not org:
        raise HTTPException(404, "Organisation not found")
    cr = session.exec(
        select(CustomRubric).where(CustomRubric.org_id == org.id, CustomRubric.trade == trade)
    ).first()
    if cr:
        rubric = json.loads(cr.rubric_json)
        threshold = cr.pass_threshold
    else:
        rubric_path = RUBRICS_DIR / f"{trade}.json"
        if not rubric_path.exists():
            raise HTTPException(404, f"Trade '{trade}' not found")
        with open(rubric_path) as f:
            rubric = json.load(f)
        threshold = rubric["scoring"]["pass_threshold"]

    tasks = [
        {"id": t["id"], "title": t["title"], "format": t["format"],
         "time_minutes": t["time_minutes"], "instruction": t["instruction"]}
        for t in rubric["tasks"]
    ]
    return {
        "org": {"name": org.name, "logo_url": org.logo_url, "slug": org.slug},
        "trade": rubric.get("trade", trade),
        "tasks": tasks,
        "pass_threshold": threshold,
    }


@router.get("/orgs/{slug}/submissions")
def get_org_submissions(slug: str, session: Session = Depends(get_session)):
    """Business portal — view all worker submissions for this org."""
    org = session.exec(select(Organisation).where(Organisation.slug == slug)).first()
    if not org:
        raise HTTPException(404, "Organisation not found")
    
    certs = session.exec(
        select(Certification).where(Certification.org_id == org.id).order_by(Certification.created_at.desc())
    ).all()
    
    submissions = []
    for cert in certs:
        user = session.get(User, cert.user_id)
        task_results = session.exec(
            select(TaskResult).where(TaskResult.certification_id == cert.id)
        ).all()
        
        tasks_data = []
        for tr in task_results:
            assessment = json.loads(tr.assessment_json) if tr.assessment_json else {}
            tasks_data.append({
                "task_id": tr.task_id,
                "passed": tr.passed,
                "weighted_total": tr.weighted_total,
                "scores": {
                    "safety": tr.safety_score,
                    "technique": tr.technique_score,
                    "result": tr.result_score,
                },
                "skipped": assessment.get("skipped", False),
                "file_path": tr.file_path,
                "created_at": tr.created_at.isoformat(),
            })
        
        submissions.append({
            "cert_id": cert.id,
            "worker_name": user.name if user else "Unknown",
            "worker_email": user.email if user else "",
            "trade": cert.trade,
            "status": cert.status,
            "created_at": cert.created_at.isoformat(),
            "tasks": tasks_data,
        })
    
    return {"org": {"name": org.name, "slug": org.slug}, "submissions": submissions}
