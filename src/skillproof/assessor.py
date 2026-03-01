import json
from pathlib import Path

from google import genai
from google.genai import types

from .config import settings

RUBRICS_DIR = Path(__file__).resolve().parent.parent.parent / "rubrics"


def _load_rubric(trade: str) -> dict:
    trade_key = trade.lower().replace(" & ", "_").replace(" ", "_")
    mapping = {
        "tiling": "tiling",
        "wall_and_floor_tiling": "tiling",
        "painting": "painting",
        "painting_decorating": "painting",
        "painting_&_decorating": "painting",
    }
    filename = mapping.get(trade_key, trade_key)
    rubric_path = RUBRICS_DIR / f"{filename}.json"
    with open(rubric_path) as f:
        return json.load(f)


def _find_task(rubric: dict, task_id: str) -> dict:
    for task in rubric["tasks"]:
        if task["id"].upper() == task_id.upper():
            return task
    raise ValueError(f"Task {task_id} not found in rubric for {rubric['trade']}")


def _build_prompt(task: dict, rubric: dict) -> str:
    criteria = task["criteria"]
    return f"""You are an NVQ Level 2 assessor for {rubric['trade']}.
Reference standards: {', '.join(rubric['reference_standards'])}

TASK: {task['title']} ({task['id']})
Instructions given to the worker: {task['instruction']}

Assess the submitted video/photo against these criteria:

SAFETY (weight {criteria['safety']['weight']}):
{chr(10).join(f'- {c}' for c in criteria['safety']['checks'])}

TECHNIQUE (weight {criteria['technique']['weight']}):
{chr(10).join(f'- {c}' for c in criteria['technique']['checks'])}

RESULT QUALITY (weight {criteria['result']['weight']}):
{chr(10).join(f'- {c}' for c in criteria['result']['checks'])}

Return ONLY valid JSON with this exact structure:
{{
  "safety": {{
    "score": <0-100>,
    "observations": ["observation1", "observation2"],
    "criteria_met": ["criterion that was met"],
    "criteria_failed": ["criterion that was not met"]
  }},
  "technique": {{
    "score": <0-100>,
    "observations": ["observation1", "observation2"],
    "criteria_met": ["criterion that was met"],
    "criteria_failed": ["criterion that was not met"]
  }},
  "result": {{
    "score": <0-100>,
    "observations": ["observation1", "observation2"],
    "criteria_met": ["criterion that was met"],
    "criteria_failed": ["criterion that was not met"]
  }},
  "feedback": "One paragraph of detailed feedback for the worker"
}}"""


def assess_video(trade: str, task_id: str, video_url: str) -> dict:
    rubric = _load_rubric(trade)
    task = _find_task(rubric, task_id)
    prompt = _build_prompt(task, rubric)

    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[
            types.Content(
                parts=[
                    types.Part.from_uri(file_uri=video_url, mime_type="video/mp4"),
                    types.Part.from_text(text=prompt),
                ]
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )

    return json.loads(response.text)


def assess_file(trade: str, task_id: str, filepath: str) -> dict:
    rubric = _load_rubric(trade)
    task = _find_task(rubric, task_id)
    prompt = _build_prompt(task, rubric)

    client = genai.Client(api_key=settings.gemini_api_key)

    path = Path(filepath)
    suffix = path.suffix.lower()
    mime_map = {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".webm": "video/webm",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }
    mime_type = mime_map.get(suffix, "video/mp4")

    uploaded = client.files.upload(file=path, config={"mime_type": mime_type})

    # Wait for file processing to complete
    import time
    while uploaded.state and uploaded.state.name == "PROCESSING":
        time.sleep(2)
        uploaded = client.files.get(name=uploaded.name)

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[
            types.Content(
                parts=[
                    types.Part.from_uri(file_uri=uploaded.uri, mime_type=mime_type),
                    types.Part.from_text(text=prompt),
                ]
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )

    return json.loads(response.text)
