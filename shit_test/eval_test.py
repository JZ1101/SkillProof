"""Task 1: Minimal AI assessment test using Gemini 2.5 Pro with a YouTube tiling video."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Load tiling rubric
rubric_path = Path(__file__).resolve().parent.parent / "rubrics" / "tiling.json"
rubric = json.loads(rubric_path.read_text())

# Use Task T4 (Tile a 1m² section) as test — most visually assessable
task = next(t for t in rubric["tasks"] if t["id"] == "T4")

system_prompt = f"""You are an expert NVQ Level 2 Wall and Floor Tiling assessor.
You assess worker-submitted videos against official British Standards.

Reference standards: {json.dumps(rubric['reference_standards'])}

You are assessing: {task['title']}
Task instruction: {task['instruction']}

Assessment criteria:
{json.dumps(task['criteria'], indent=2)}

Scoring rules:
- Score each of safety, technique, result from 0-100
- For each criterion, list which checks passed/failed with specific observations
- Reference the relevant British Standard clause where applicable
- Overall pass requires 70%+ weighted score AND safety >= 60%
- Weights: safety={rubric['scoring']['weights']['safety']}, technique={rubric['scoring']['weights']['technique']}, result={rubric['scoring']['weights']['result']}

Return your assessment as JSON:
{{
  "task_id": "T4",
  "scores": {{
    "safety": {{"score": int, "observations": [str]}},
    "technique": {{"score": int, "observations": [str]}},
    "result": {{"score": int, "observations": [str]}}
  }},
  "weighted_score": float,
  "pass": bool,
  "feedback": "One paragraph of constructive feedback referencing specific standards"
}}
"""

# Test with a YouTube tiling tutorial video
video_url = "https://www.youtube.com/watch?v=qqUE97v_n6g"  # tiling tutorial

print("Sending video to Gemini 2.5 Pro for assessment...")
print(f"Video: {video_url}")
print(f"Task: {task['title']}")
print("-" * 60)

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents=[
        {
            "parts": [
                {"text": system_prompt},
                {"text": f"Assess this tiling video: {video_url}\n\nNote: This is a tutorial/demonstration video. Assess the tiling work shown as if it were a worker's submission."},
            ]
        }
    ],
)

print(response.text)
