#!/usr/bin/env python3
"""Runs in GitHub Actions. Posts every wood/queue/*.json job to Buffer, then moves it to queue/done/.
Job file: {"spec": "posts/NNN-slug.json", "video": "videos/NNN-slug.mp4", "due": "now" | ISO datetime with offset}
Result of every job is appended to wood/queue/log.txt (committed back by the workflow)."""
import datetime, glob, json, os, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = "https://raw.githubusercontent.com/idobits261/maklida/main/wood/"
os.chdir(HERE)
failed = False
log = open("queue/log.txt", "a")
for path in sorted(glob.glob("queue/*.json")):
    job = json.load(open(path))
    url = RAW + job["video"]
    for _ in range(12):
        try:
            if urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20).status == 200:
                break
        except Exception:
            pass
        time.sleep(10)
    r = subprocess.run([sys.executable, "buffer_post.py", "post", job["spec"], url, job["due"]],
                       capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()[-1500:]
    stamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    log.write(f"[{stamp}] {os.path.basename(path)} due={job['due']} exit={r.returncode}\n{out}\n\n")
    print(out)
    if r.returncode == 0:
        os.rename(path, "queue/done/" + os.path.basename(path))
    else:
        failed = True
log.close()
sys.exit(1 if failed else 0)
