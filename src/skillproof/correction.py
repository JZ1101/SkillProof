"""Generate correction videos based on original video frames."""
import json
import subprocess
import time
import uuid
from pathlib import Path

import requests
from google import genai

from .config import settings

CORRECTIONS_DIR = Path("corrections")
CORRECTIONS_DIR.mkdir(exist_ok=True)
FRAMES_DIR = CORRECTIONS_DIR / "frames"
FRAMES_DIR.mkdir(exist_ok=True)

SKIP_VIDEO_KEYWORDS = [
    "gloves", "goggles", "safety glasses", "ppe", "mask", "dust mask",
    "knee pad", "protective", "eye protection", "ear protection",
    "hard hat", "hi-vis", "ventilat", "power isolated",
    "drop sheet", "trip hazard", "slip hazard", "stable surface",
    "clean area", "tidy", "organised", "organized",
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


def _upload_to_runware(image_path: str) -> str:
    """Upload image to Runware, return the image URL (not UUID)."""
    import base64
    url = "https://api.runware.ai/v1"
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()
    resp = requests.post(url, json=[{
        "taskType": "imageUpload",
        "taskUUID": str(uuid.uuid4()),
        "imageBase64": f"data:image/jpeg;base64,{image_b64}",
    }], headers={"Authorization": f"Bearer {settings.runware_api_key}"}, timeout=30)
    data = resp.json()
    if "data" in data and len(data["data"]) > 0:
        return data["data"][0].get("imageURL")
    return None


def _generate_video_runware(image_url: str, prompt: str) -> str:
    url = "https://api.runware.ai/v1"
    task_uuid = str(uuid.uuid4())
    resp = requests.post(url, json=[{
        "taskType": "videoInference",
        "taskUUID": task_uuid,
        "model": "klingai:5@3",
        "positivePrompt": prompt,
        "duration": 5,
        "width": 1080,
        "height": 1080,
        "frameImages": [{"inputImage": image_url, "frame": "first"}],
        "numberResults": 1,
        "deliveryMethod": "async",
        "outputFormat": "MP4",
    }], headers={"Authorization": f"Bearer {settings.runware_api_key}"}, timeout=30)

    for _ in range(60):
        time.sleep(5)
        poll_resp = requests.post(url, json=[{
            "taskType": "getResponse",
            "taskUUID": task_uuid,
        }], headers={"Authorization": f"Bearer {settings.runware_api_key}"}, timeout=30)
        poll_data = poll_resp.json()
        if "data" in poll_data:
            for item in poll_data["data"]:
                if item.get("taskUUID") == task_uuid and item.get("videoURL"):
                    video_resp = requests.get(item["videoURL"], timeout=60)
                    filename = f"correction_{uuid.uuid4().hex[:8]}.mp4"
                    out_path = CORRECTIONS_DIR / filename
                    out_path.write_bytes(video_resp.content)
                    return str(out_path)
    return None


def _generate_video_script(task_title: str, error: str, explanation: str) -> dict:
    """Generate ONE video prompt with all steps in a single continuous sequence."""
    client = genai.Client(api_key=settings.gemini_api_key)

    prompt = f"""You are a professional trade skills instructor.

A worker failed this criterion during a {task_title} assessment:
ERROR: {error}
CONTEXT: {explanation}

Generate ONE correction video that shows the correct technique as a single continuous 8-second clip.
All steps must happen in sequence within this one video.

Rules:
- Write ONE video_prompt describing the COMPLETE correct sequence from start to finish
- Use time markers: "In seconds 0-3... In seconds 3-6... In seconds 6-8..."
- Each time segment = one step of the correct technique
- Be ultra-specific: tool angles, hand positions, material behavior
- Scene stays the same as the original (we'll use a frame as starting image)
- Static camera, no cuts
- Also write narration_steps that map to the video timeline

CRITICAL PHYSICAL CONSTRAINTS:
- Tiles are rigid 300x300mm ceramic squares. They don't bend or float.
- Adhesive is thick grey paste. It stays where spread.
- Trowel has a handle (grip it there, not the blade)
- Once a tile is placed, it stays placed
- Gravity works normally

Return ONLY valid JSON:
{{
  "frame_ratio": 0.3,
  "video_prompt": "Starting from this workshop scene: In seconds 0-3, a hand grips the wooden trowel handle and presses the 10mm notched edge against wall adhesive at exactly 45 degrees. In seconds 3-6, the hand draws the trowel horizontally left-to-right in one smooth stroke creating even parallel ridges. In seconds 6-8, camera holds on the finished result showing uniform parallel ridges. Static camera, eye level, fluorescent workshop lighting.",
  "narration_steps": [
    "0-3s: Position trowel at 45° angle against the adhesive",
    "3-6s: Draw in straight parallel lines with steady pressure",
    "6-8s: Result: uniform ridges with full coverage"
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
        for criterion in failed:
            corrections.append({
                "category": category,
                "error": criterion,
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
    original_video_path: str = None,
) -> list[dict]:
    corrections = _build_explanation(assessment, task_title)
    if not corrections:
        return []

    results = []

    for i, correction in enumerate(corrections):
        if not _needs_video(correction["error"]):
            results.append({
                "category": correction["category"],
                "error": correction["error"],
                "explanation": correction["explanation"],
                "video_path": None,
                "narration_steps": [],
                "skipped_reason": "Basic safety/PPE requirement — no video needed",
            })
            continue

        try:
            # One cohesive script per error
            script = _generate_video_script(
                task_title, correction["error"], correction["explanation"]
            )
            video_prompt = script.get("video_prompt", "")
            narration_steps = script.get("narration_steps", [])
            video_path = None

            # Generate with Veo
            try:
                veo_client = genai.Client(api_key=settings.gemini_api_key)
                print(f"[Veo] Generating correction {i}: {correction['error'][:60]}...")
                operation = veo_client.models.generate_videos(
                    model="veo-3.0-fast-generate-001",
                    prompt=video_prompt,
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
                    filename = f"correction_{cert_id}_{task_id}_{i}.mp4"
                    out_path = CORRECTIONS_DIR / filename
                    out_path.write_bytes(resp_bytes)
                    video_path = str(out_path)
                    print(f"[Veo] ✓ correction {i} saved: {filename}")
                else:
                    print(f"[Veo] No videos generated. Done={operation.done}, Result={operation.result}")
            except Exception as ve:
                print(f"[Veo] Error: {ve}")
                import traceback; traceback.print_exc()

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
