"""Generate correction videos based on original video frames via fal.ai."""
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

import fal_client
import requests
from google import genai

from .config import settings
from .prebaked import find_prebaked

CORRECTIONS_DIR = Path("corrections")
CORRECTIONS_DIR.mkdir(exist_ok=True)
FRAMES_DIR = CORRECTIONS_DIR / "frames"
FRAMES_DIR.mkdir(exist_ok=True)

SKIP_VIDEO_KEYWORDS = [
    "gloves", "goggles", "safety glasses", "ppe", "mask", "dust mask",
    "knee pad", "protective", "eye protection", "ear protection",
    "hard hat", "hi-vis", "ventilat", "power isolated",
    "drop sheet",
]


def _needs_video(criterion: str) -> bool:
    lower = criterion.lower()
    return not any(kw in lower for kw in SKIP_VIDEO_KEYWORDS)


def _extract_frame(video_path: str, timestamp: float = None) -> str:
    path = Path(video_path)
    if not path.exists():
        return None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        duration = float(result.stdout.strip())
    except Exception:
        duration = 10.0
    if timestamp is None:
        timestamp = duration / 2
    frame_path = FRAMES_DIR / f"frame_{uuid.uuid4().hex[:8]}.jpg"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(timestamp), "-i", str(path),
             "-frames:v", "1", "-q:v", "2", str(frame_path)],
            capture_output=True, timeout=10,
        )
        if frame_path.exists() and frame_path.stat().st_size > 0:
            return str(frame_path)
    except Exception:
        pass
    return None


def _generate_video_veo(prompt: str, image_path: str = None) -> str:
    """Generate video using Google Veo via Gemini API."""
    veo_client = genai.Client(api_key=settings.gemini_api_key)
    print(f"[Veo] Generating video: {prompt[:80]}...")
    try:
        operation = veo_client.models.generate_videos(
            model="veo-3.0-fast-generate-001",
            prompt=prompt,
            config={"number_of_videos": 1, "duration_seconds": 8},
        )
        elapsed = 0
        while not operation.done and elapsed < 180:
            time.sleep(5)
            elapsed += 5
            operation = veo_client.operations.get(operation)
        if operation.done and operation.result and operation.result.generated_videos:
            video = operation.result.generated_videos[0]
            resp_bytes = veo_client.files.download(file=video.video)
            filename = f"correction_{uuid.uuid4().hex[:8]}.mp4"
            out_path = CORRECTIONS_DIR / filename
            out_path.write_bytes(resp_bytes)
            print(f"[Veo] ✓ saved: {filename}")
            return str(out_path)
        else:
            print(f"[Veo] No videos generated. Done={operation.done}")
            return None
    except Exception as e:
        print(f"[Veo] Error: {e}")
        import traceback; traceback.print_exc()
        return None


def _generate_video_fal(prompt: str, image_path: str = None) -> str:
    """Generate video using fal.ai. Fallback option."""
    os.environ["FAL_KEY"] = settings.fal_key
    print(f"[fal.ai] Generating video: {prompt[:80]}...")
    try:
        if image_path and Path(image_path).exists():
            image_url = fal_client.upload_file(image_path)
            result = fal_client.subscribe(
                "fal-ai/kling-video/v2/master/image-to-video",
                arguments={"prompt": prompt, "image_url": image_url, "duration": "5", "aspect_ratio": "1:1"},
            )
        else:
            result = fal_client.subscribe(
                "fal-ai/kling-video/v2/master/text-to-video",
                arguments={"prompt": prompt, "duration": "5", "aspect_ratio": "1:1"},
            )
        video_url = result.get("video", {}).get("url")
        if not video_url:
            return None
        resp = requests.get(video_url, timeout=120)
        filename = f"correction_{uuid.uuid4().hex[:8]}.mp4"
        out_path = CORRECTIONS_DIR / filename
        out_path.write_bytes(resp.content)
        print(f"[fal.ai] ✓ saved: {filename} ({len(resp.content)} bytes)")
        return str(out_path)
    except Exception as e:
        print(f"[fal.ai] Error: {e}")
        return None


def _generate_video_script(task_title: str, error: str, explanation: str) -> dict:
    """Generate ONE video prompt with all steps in a single continuous sequence."""
    client = genai.Client(api_key=settings.gemini_api_key)

    prompt = f"""You are a professional NVQ Level 2 trade skills instructor creating a correction demonstration video.

ASSESSMENT CONTEXT:
- Trade: {task_title}
- The worker FAILED this specific criterion: {error}
- Assessor observation: {explanation}

YOUR TASK: Generate a detailed video prompt showing the CORRECT way to perform this specific action.

The video should be a single continuous 8-second instructional clip that demonstrates exactly what the worker should have done differently.

REQUIREMENTS:
- Write ONE detailed video_prompt describing the complete correct technique from start to finish
- Use precise time markers: "In seconds 0-3... In seconds 3-6... In seconds 6-8..."
- Be extremely specific about: tool names, grip positions, angles in degrees, distances in mm, material behavior, body positioning
- Describe the scene: well-lit workshop, clean workbench, professional setting
- Include what the CORRECT result looks like at the end
- Static camera, eye level, no cuts, instructional video style
- Write clear narration_steps explaining what's happening and WHY it matters (reference standards where relevant)

PHYSICAL REALITY CONSTRAINTS (critical for realistic video):
- Tiles are rigid ceramic/porcelain squares (typically 300x300mm or 600x300mm). They do NOT bend, flex, or float.
- Tile adhesive is thick grey/white paste. It holds its shape when combed with a notched trowel.
- Trowels have wooden/plastic handles — grip the handle, NOT the blade.
- Spirit levels are straight metal bars with bubble vials.
- Spacers are small plastic crosses (2-5mm).
- Grout is a fine paste pushed into gaps with a rubber float.
- All materials obey gravity. Nothing floats or hovers.
- Human hands have 5 fingers and hold tools naturally.

Return ONLY valid JSON:
{{
  "video_prompt": "A professional workshop scene with bright overhead lighting. A clean workbench with ceramic wall tiles, a bucket of grey adhesive, and tiling tools neatly arranged. In seconds 0-3, a worker's right hand grips the wooden handle of a 10mm notched trowel and scoops adhesive from the bucket, then presses the flat side against the wall surface spreading a 5mm base layer. In seconds 3-6, the worker rotates the trowel to the notched edge, holds it at exactly 45 degrees to the wall, and draws it horizontally left-to-right in one smooth confident stroke, creating perfectly even parallel ridges in the adhesive. In seconds 6-8, the camera holds steady on the finished result: uniform parallel ridges approximately 10mm apart with no gaps, swirls, or bare patches — meeting BS 5385 full-bed coverage requirements. Static camera, eye level, professional instructional style.",
  "narration_steps": [
    "0-3s: Apply base coat — spread adhesive evenly with the flat side of the trowel to create good contact with the wall surface",
    "3-6s: Comb with notched edge at 45° — draw in straight parallel lines with steady, even pressure to create uniform ridges (BS 5385 requirement)",
    "6-8s: Check the result — ridges should be even, parallel, and consistent with no gaps or swirls, ensuring minimum 80% bed contact for walls"
  ]
}}"""

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[prompt],
        config={"temperature": 0.1, "response_mime_type": "application/json"},
    )
    return json.loads(response.text)


def _build_explanation(assessment: dict, task_title: str) -> list[dict]:
    corrections = []
    for category in ["safety", "technique", "result"]:
        cat_data = assessment.get(category, {})
        failed = cat_data.get("criteria_failed", [])
        observations = cat_data.get("observations", [])
        for item in failed:
            # Support both old format (string) and new format (dict with timestamp)
            if isinstance(item, dict):
                criterion = item.get("criterion", str(item))
                timestamp = item.get("timestamp_seconds", 0)
            else:
                criterion = item
                timestamp = 0
            corrections.append({
                "category": category,
                "error": criterion,
                "timestamp_seconds": timestamp,
                "explanation": next(
                    (o for o in observations if any(
                        word in o.lower() for word in criterion.lower().split()[:3]
                    )),
                    f"This criterion was not met: {criterion}",
                ),
            })
    return corrections


def generate_correction_videos(
    task_id: str, task_title: str, assessment: dict, cert_id: int,
    original_video_path: str = None, trade: str = "",
) -> list[dict]:
    corrections = _build_explanation(assessment, task_title)
    if not corrections:
        return []

    results = []

    # Find first correction that needs a video, generate only that one
    video_generated = False
    for i, correction in enumerate(corrections):
        if not _needs_video(correction["error"]) or video_generated:
            results.append({
                "category": correction["category"],
                "error": correction["error"],
                "explanation": correction["explanation"],
                "video_path": None,
                "narration_steps": [],
                "skipped_reason": "Basic safety/PPE requirement — no video needed" if not _needs_video(correction["error"]) else None,
            })
            continue

        # Try pre-baked fallback first (instant)
        prebaked = find_prebaked(trade, correction["error"])
        if prebaked and prebaked.get("video_path"):
            video_generated = True
            results.append({
                "category": correction["category"],
                "error": correction["error"],
                "explanation": correction["explanation"],
                "video_path": prebaked["video_path"],
                "narration_steps": prebaked["narration_steps"],
                "prebaked": True,
            })
            continue
        elif prebaked and prebaked.get("narration_steps"):
            # No video file yet but we have narration
            video_generated = True
            results.append({
                "category": correction["category"],
                "error": correction["error"],
                "explanation": correction["explanation"],
                "video_path": None,
                "narration_steps": prebaked["narration_steps"],
                "prebaked": True,
            })
            continue

        video_generated = True
        try:
            # Generate script via Gemini
            script = _generate_video_script(
                task_title, correction["error"], correction["explanation"]
            )
            video_prompt = script.get("video_prompt", "")
            narration_steps = script.get("narration_steps", [])

            # Use Veo (Gemini) for video generation
            video_path = _generate_video_veo(video_prompt)

            results.append({
                "category": correction["category"],
                "error": correction["error"],
                "explanation": correction["explanation"],
                "video_path": video_path,
                "narration_steps": narration_steps,
            })
        except Exception as e:
            results.append({
                "category": correction["category"],
                "error": correction["error"],
                "explanation": correction["explanation"],
                "video_path": None,
                "narration_steps": [],
                "video_error": str(e),
            })

    return results


def generate_text_corrections(task_title: str, assessment: dict) -> list[dict]:
    return _build_explanation(assessment, task_title)
