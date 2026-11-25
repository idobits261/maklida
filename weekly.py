#!/usr/bin/env python3
"""Weekly omnibus: join wide (16:9) episode files into one long video, no re-encode.
Usage: python3 weekly.py out/week1.mp4 out/s01e01_wide.mp4 out/s01e02_wide.mp4 ...
All inputs must come from render.py --wide (same size, fps and encoder settings)."""
import sys, subprocess, tempfile, os
from pathlib import Path
out, parts = Path(sys.argv[1]), [Path(p).resolve() for p in sys.argv[2:]]
with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
    f.write("\n".join(f"file '{p}'" for p in parts))
tmp = out.with_name(out.stem + ".tmp.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f.name,
                "-c", "copy", "-movflags", "+faststart", str(tmp)], check=True)
os.unlink(f.name); tmp.rename(out); print("ok", out)
