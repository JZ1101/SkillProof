import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from .config import settings


def generate_certificate(
    worker_name: str,
    trade: str,
    score: float,
    task_scores: dict,
    cert_id: str | None = None,
) -> dict:
    cert_id = cert_id or uuid.uuid4().hex[:12].upper()
    issued_at = datetime.now(timezone.utc)

    cert_dir = Path(settings.cert_dir)
    cert_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = cert_dir / f"{cert_id}.pdf"

    verify_url = f"{settings.base_url}/api/verify/{cert_id}"

    _render_pdf(
        path=pdf_path,
        worker_name=worker_name,
        trade=trade,
        score=score,
        task_scores=task_scores,
        cert_id=cert_id,
        issued_at=issued_at,
        verify_url=verify_url,
    )

    return {
        "cert_id": cert_id,
        "pdf_path": str(pdf_path),
        "verify_url": verify_url,
        "issued_at": issued_at.isoformat(),
    }


def _make_qr(url: str) -> BytesIO:
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _render_pdf(
    path: Path,
    worker_name: str,
    trade: str,
    score: float,
    task_scores: dict,
    cert_id: str,
    issued_at: datetime,
    verify_url: str,
) -> None:
    from reportlab.lib.utils import ImageReader

    w, h = A4
    c = canvas.Canvas(str(path), pagesize=A4)

    # Background border
    c.setStrokeColor(HexColor("#1a5276"))
    c.setLineWidth(3)
    c.rect(15 * mm, 15 * mm, w - 30 * mm, h - 30 * mm)

    # Inner border
    c.setStrokeColor(HexColor("#2980b9"))
    c.setLineWidth(1)
    c.rect(18 * mm, 18 * mm, w - 36 * mm, h - 36 * mm)

    # Title
    y = h - 50 * mm
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(HexColor("#1a5276"))
    c.drawCentredString(w / 2, y, "SKILLPROOF")

    y -= 12 * mm
    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(w / 2, y, "AI-Powered Trade Certification")

    # Divider
    y -= 10 * mm
    c.setStrokeColor(HexColor("#2980b9"))
    c.setLineWidth(0.5)
    c.line(40 * mm, y, w - 40 * mm, y)

    # Certificate text
    y -= 15 * mm
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(w / 2, y, "This certifies that")

    y -= 12 * mm
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(HexColor("#1a5276"))
    c.drawCentredString(w / 2, y, worker_name)

    y -= 12 * mm
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(w / 2, y, "has successfully completed the assessment for")

    y -= 12 * mm
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(HexColor("#2980b9"))
    c.drawCentredString(w / 2, y, trade)

    y -= 10 * mm
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(w / 2, y, "NVQ Level 2 Equivalent")

    # Score section
    y -= 18 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(w / 2, y, f"Overall Score: {score:.1f}%")

    y -= 10 * mm
    c.setFont("Helvetica", 10)
    scores_text = (
        f"Safety: {task_scores.get('safety', 0)}%  |  "
        f"Technique: {task_scores.get('technique', 0)}%  |  "
        f"Result: {task_scores.get('result', 0)}%"
    )
    c.drawCentredString(w / 2, y, scores_text)

    # Details
    y -= 18 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(w / 2, y, f"Certificate ID: {cert_id}")

    y -= 8 * mm
    c.drawCentredString(w / 2, y, f"Issued: {issued_at.strftime('%d %B %Y')}")

    # QR code
    qr_buf = _make_qr(verify_url)
    qr_img = ImageReader(qr_buf)
    qr_size = 35 * mm
    c.drawImage(qr_img, (w - qr_size) / 2, 30 * mm, qr_size, qr_size)

    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#888888"))
    c.drawCentredString(w / 2, 25 * mm, "Scan to verify this certificate")

    c.save()
