"""Render a video from scene images + narration audio with FFmpeg.

Usage: python3 render.py <run_dir> [--long]

<run_dir> must contain:
  scenes.json   [{"image": "scene01.png", "duration": 3.5}, ...]  (paths relative to run_dir)
  narration.*   one audio file (mp3/wav/m4a)
Writes <run_dir>/final.mp4. Shorts are 1080x1920 (default), --long is 1920x1080.
The last scene is stretched so the video is never shorter than the narration.
Captions (SRT) are uploaded to YouTube separately, so they are not burned in.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FPS = 30
AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".aac")


def audio_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def plan_durations(durations: list[float], audio_len: float) -> list[float]:
    """Stretch the last scene so total video length covers the narration."""
    if not durations:
        raise ValueError("scenes.json has no scenes")
    if any(d <= 0 for d in durations):
        raise ValueError("scene durations must be positive")
    shortfall = audio_len - sum(durations)
    if shortfall > 0:
        durations = durations[:-1] + [durations[-1] + shortfall]
    return durations


def render(run_dir: Path, long_form: bool) -> Path:
    scenes = json.loads((run_dir / "scenes.json").read_text(encoding="utf-8"))
    audio = next((p for p in sorted(run_dir.glob("narration.*")) if p.suffix in AUDIO_EXTS), None)
    if audio is None:
        raise FileNotFoundError(f"no narration audio in {run_dir}")
    w, h = (1920, 1080) if long_form else (1080, 1920)
    durations = plan_durations([float(s["duration"]) for s in scenes], audio_duration(audio))

    inputs, chains = [], []
    for i, (scene, d) in enumerate(zip(scenes, durations)):
        img = run_dir / scene["image"]
        if not img.exists():
            raise FileNotFoundError(img)
        inputs += ["-loop", "1", "-t", f"{d:.3f}", "-i", str(img)]
        chains.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p[v{i}]"
        )
    concat = "".join(f"[v{i}]" for i in range(len(scenes))) + f"concat=n={len(scenes)}:v=1:a=0[vout]"
    out = run_dir / "final.mp4"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs, "-i", str(audio),
           "-filter_complex", ";".join(chains + [concat]),
           "-map", "[vout]", "-map", f"{len(scenes)}:a",
           "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
           "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(render(Path(sys.argv[1]), "--long" in sys.argv))
