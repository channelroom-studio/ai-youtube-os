"""Machine checks before uploading a video.

Usage: python3 preflight.py <video.mp4> [captions.srt]
Prints one PASS/WARN/FAIL line per check and exits 1 if any FAIL.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SILENT_DB = -60.0        # mean volume below this = effectively no narration
LOUD_PEAK_DB = -0.5      # peak above this = likely clipping
SHORTS_MAX_SEC = 180.0   # YouTube Shorts upper limit
CAPTION_GAP_SEC = 3.0    # captions ending this far from video end = likely truncated


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def volume(path: Path) -> tuple[float, float]:
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    mean = float(re.search(r"mean_volume: (-?[\d.]+|-inf) dB", out).group(1).replace("-inf", "-999"))
    peak = float(re.search(r"max_volume: (-?[\d.]+|-inf) dB", out).group(1).replace("-inf", "-999"))
    return mean, peak


def last_caption_end(srt_text: str) -> float:
    ends = re.findall(r"--> (\d+):(\d+):(\d+)[,.](\d+)", srt_text)
    if not ends:
        return 0.0
    h, m, s, ms = map(int, ends[-1])
    return h * 3600 + m * 60 + s + ms / 1000


def checks(info: dict, mean_db: float | None, peak_db: float | None,
           caption_end: float | None) -> list[tuple[str, str, str]]:
    """Pure decision logic: returns (status, name, detail) rows."""
    rows = []
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    dur = float(info["format"]["duration"])

    if video is None:
        rows.append(("FAIL", "video", "no video stream"))
    else:
        w, h = video["width"], video["height"]
        vertical = h > w
        rows.append(("PASS", "resolution", f"{w}x{h} ({'vertical/Shorts' if vertical else 'horizontal'})"))
        if vertical and dur > SHORTS_MAX_SEC:
            rows.append(("WARN", "duration", f"{dur:.1f}s is over the {SHORTS_MAX_SEC:.0f}s Shorts limit"))
    rows.append(("PASS", "duration", f"{dur:.1f}s"))

    if not has_audio:
        rows.append(("FAIL", "audio", "no audio track"))
    elif mean_db is not None:
        if mean_db < SILENT_DB:
            rows.append(("FAIL", "audio", f"mean {mean_db:.1f} dB, effectively silent"))
        elif peak_db is not None and peak_db > LOUD_PEAK_DB:
            rows.append(("WARN", "audio", f"peak {peak_db:.1f} dB, may clip"))
        else:
            rows.append(("PASS", "audio", f"mean {mean_db:.1f} dB, peak {peak_db:.1f} dB"))

    if caption_end is not None:
        gap = dur - caption_end
        status = "PASS" if abs(gap) <= CAPTION_GAP_SEC else "WARN"
        rows.append((status, "captions", f"last cue ends {caption_end:.1f}s, video {dur:.1f}s"))
    return rows


def main(argv: list[str]) -> int:
    video = Path(argv[1])
    info = probe(video)
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    mean_db, peak_db = volume(video) if has_audio else (None, None)
    cap_end = last_caption_end(Path(argv[2]).read_text(encoding="utf-8")) if len(argv) > 2 else None
    rows = checks(info, mean_db, peak_db, cap_end)
    for status, name, detail in rows:
        print(f"{status:4}  {name:10} {detail}")
    return 1 if any(r[0] == "FAIL" for r in rows) else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv))
