"""Test Veo video generation for correction demos."""
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = """A professional tiler demonstrating correct technique: 
holding a notched trowel at a 45-degree angle, applying adhesive evenly 
to a wall surface with consistent parallel ridges. Close-up view showing 
proper hand position and even pressure. Clean, well-lit workshop setting. 
Instructional video style."""

print("Generating video with Veo 3.1...")
operation = client.models.generate_videos(
    model="veo-3.0-fast-generate-001",
    prompt=prompt,
    config={"number_of_videos": 1, "duration_seconds": 8},
)

# Poll until done
while not operation.done:
    print(f"  Processing... ")
    time.sleep(5)
    operation = client.operations.get(operation)

if operation.result and operation.result.generated_videos:
    video = operation.result.generated_videos[0]
    print(f"Video generated! URI: {video.video.uri}")
    # Download
    resp = client.files.download(file=video.video)
    out = Path(__file__).parent / "demo_correction.mp4"
    out.write_bytes(resp)
    print(f"Saved to {out} ({out.stat().st_size} bytes)")
else:
    print(f"Failed: {operation.error}")
