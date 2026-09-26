"""Build the simulation montage with ffmpeg/ffprobe and Pillow.

Run from any directory: python3 scripts/build_simulation_video.py
"""

import json
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
TASKS = [
    ("Gear Assembly", "Gear Assembly.mp4", 1),
    ("Power Plug Insertion", "Power Plug Insertion.mp4", 1),
    ("USB Insertion", "USB insertion.mp4", 1),
    ("Peg Insertion", "peg insertion.mp4", 1),
    ("Peg Reorientation", "Peg Reorientation.mp4", 1),
    ("Bulb Screwing", "bulb screwing.mp4", 3),
]
FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
font_path = next((p for p in FONT_PATHS if Path(p).exists()), None)
if font_path is None:
    raise RuntimeError("Install Arial or DejaVu Sans to render the task labels.")
font = ImageFont.truetype(font_path, 21)
badge_font = ImageFont.truetype(font_path, 20)
inputs = []
durations = []
for _, filename, speed in TASKS:
    path = ROOT / "TARO videos" / "sim video" / filename
    inputs.extend(["-i", str(path)])
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-of", "json", str(path)
    ]))
    durations.append(float(probe["format"]["duration"]) / speed)
duration = max(durations)

# Keep both original 256 x 256 views intact in each column.
overlay = Image.new("RGBA", (1632, 600))
draw = ImageDraw.Draw(overlay)
for i, (label, _, _) in enumerate(TASKS):
    left = 18 + i * 268
    draw.rounded_rectangle((left, 18, left + 256, 69), radius=9, fill="#ffffff")
    draw.rounded_rectangle((left + 112, 22, left + 144, 25), radius=1, fill="#6b4eff")
    draw.text((left + 128, 47), label, font=font, anchor="mm", fill="#202124")
    # A fine divider separates the two views without covering either one.
    draw.line((left, 332, left + 255, 332), fill="#eeeaff", width=1)
left = 18 + 5 * 268
draw.rounded_rectangle((left + 198, 86, left + 246, 117), radius=8, fill="#6b4eff")
draw.text((left + 222, 102), "×3", font=badge_font, anchor="mm", fill="white")

output = ROOT / "static/images/simulation_experiments.mp4"
with tempfile.TemporaryDirectory() as temp:
    overlay_path = Path(temp) / "labels.png"
    overlay.save(overlay_path)
    filters = []
    for i, (_, _, speed) in enumerate(TASKS):
        filters.append(
            f"[{i}:v]setpts=(PTS-STARTPTS)/{speed},fps=30,setsar=1,"
            f"tpad=stop_mode=clone:stop_duration={duration},trim=duration={duration},"
            f"pad=268:576:6:64:color=0xf7f7fa[v{i}]"
        )
    filters.append(
        "".join(f"[v{i}]" for i in range(6))
        + "hstack=inputs=6,pad=1632:600:12:12:color=0xf7f7fa[montage]"
    )
    filters.append("[montage][6:v]overlay=0:0:format=auto,format=yuv420p[out]")
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", *inputs,
        "-i", str(overlay_path), "-filter_complex", ";".join(filters),
        "-map", "[out]", "-an", "-t", str(duration), "-c:v", "libx264",
        "-preset", "slow", "-crf", "19", "-movflags", "+faststart", str(output)
    ], check=True)
subprocess.run([
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", "1",
    "-i", str(output), "-frames:v", "1", "-q:v", "2", str(output.with_suffix(".jpg"))
], check=True)
print(f"Created {output.name}: {duration:.2f}s, {output.stat().st_size / 1e6:.2f} MB")
