"""Pre-baked correction video fallbacks.

When real video generation is slow (fal.ai can take 30-60s+), we serve
pre-recorded demo videos for common correction scenarios. These are mapped
by trade + error category keyword matching.

To add a pre-baked video:
1. Place the .mp4 in corrections/prebaked/
2. Add a mapping below with keywords that match the error description
"""
from pathlib import Path

PREBAKED_DIR = Path("corrections/prebaked")

# Each entry: (keywords_list, video_filename, narration_steps)
# Keywords are matched against the error/criterion text (case-insensitive)
PREBAKED_MAP = {
    "tiling": [
        {
            "keywords": ["notched trowel", "45°", "adhesive", "trowel angle", "ridges"],
            "video": "tiling_trowel_technique.mp4",
            "narration": [
                "Hold the notched trowel at approximately 45° to the surface",
                "Apply adhesive in sweeping arcs to create even ridges",
                "Ridges should be consistent height — this ensures full bed contact per BS 5385",
            ],
        },
        {
            "keywords": ["spacer", "spacing", "consistent gap", "spacer gap"],
            "video": "tiling_spacers.mp4",
            "narration": [
                "Insert spacers at every tile corner intersection",
                "Use 2-3mm spacers for wall tiles, 3-5mm for floor tiles (BS 5385:1)",
                "Check alignment with a straight edge after every 3-4 tiles",
            ],
        },
        {
            "keywords": ["level", "lippage", "flat", "spirit level", "uneven"],
            "video": "tiling_levelling.mp4",
            "narration": [
                "Place spirit level across multiple tiles to check flatness",
                "Maximum 1mm lippage between adjacent tiles (BS 8000:11)",
                "Adjust tiles by pressing or adding adhesive while still workable",
            ],
        },
        {
            "keywords": ["grout", "float", "diagonal", "joints", "grouting"],
            "video": "tiling_grouting.mp4",
            "narration": [
                "Hold grout float at 45° and draw diagonally across joints",
                "Never drag parallel to joints — this pulls grout out",
                "Fill all joints, then clean with a damp sponge within 15-30 minutes",
            ],
        },
        {
            "keywords": ["cut", "cutting", "tile cutter", "measurement", "chips"],
            "video": "tiling_cutting.mp4",
            "narration": [
                "Measure gap precisely, allowing for spacer width",
                "Score firmly in a single pass — do not go over the line twice",
                "Snap cleanly and check for chips before fitting",
            ],
        },
        {
            "keywords": ["back-butter", "back butter", "large format", "bed contact", "coverage"],
            "video": "tiling_backbutter.mp4",
            "narration": [
                "For tiles over 300x300mm, apply a thin layer to the tile back as well",
                "This ensures minimum 80% bed contact for walls, 95% for wet areas",
                "Press tile with a slight sliding motion to collapse ridges",
            ],
        },
    ],
    "painting": [
        {
            "keywords": ["cutting in", "cut in", "ceiling line", "brush", "steady"],
            "video": "painting_cutting_in.mp4",
            "narration": [
                "Use an angled 50-63mm cutting-in brush held on its narrow edge",
                "Load brush 1/3 depth, remove excess on kettle edge",
                "Draw steady strokes along the ceiling line — max 1-2mm deviation",
            ],
        },
        {
            "keywords": ["roller", "w pattern", "m pattern", "lap marks", "wet edge"],
            "video": "painting_rolling.mp4",
            "narration": [
                "Load roller evenly — roll back and forth on tray ramp",
                "First pass: W or M pattern to distribute paint",
                "Second pass: even vertical strokes to lay off, maintaining a wet edge",
            ],
        },
        {
            "keywords": ["masking", "tape", "mask", "protection"],
            "video": "painting_masking.mp4",
            "narration": [
                "Apply tape in long continuous strips, pressed firmly to the edge",
                "No gaps between tape sections — paint will bleed through",
                "Remove at 45° angle while paint is still slightly tacky",
            ],
        },
    ],
}


def find_prebaked(trade: str, error_text: str) -> dict | None:
    """Find a pre-baked correction video matching the error description.
    
    Returns dict with video_path, narration_steps or None if no match.
    """
    trade_lower = trade.lower().replace("wall and floor ", "").replace(" & decorating", "")
    entries = PREBAKED_MAP.get(trade_lower, [])
    error_lower = error_text.lower()
    
    for entry in entries:
        if any(kw in error_lower for kw in entry["keywords"]):
            video_path = PREBAKED_DIR / entry["video"]
            if video_path.exists():
                return {
                    "video_path": str(video_path),
                    "narration_steps": entry["narration"],
                    "prebaked": True,
                }
            else:
                # Video file doesn't exist yet — return narration only
                return {
                    "video_path": None,
                    "narration_steps": entry["narration"],
                    "prebaked": True,
                    "video_missing": True,
                }
    return None
