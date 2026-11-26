# woodshmood — daily run (automatic, no approval)

Lives in the maklida repo under `wood/`. Separate from the Hebrew series: never touch files outside `wood/`
and never post to the maklida Buffer channels (the Buffer connector in Claude is maklida's account — do NOT use it here).

Posting: this run only pushes job files to `wood/queue/`. A GitHub Action (.github/workflows/wood-post.yml) then posts them to the SECOND Buffer account with the repo secret BUFFER_WOOD_KEY and moves each job to `queue/done/`, logging to `queue/log.txt`. The cloud run itself has no Buffer key: never call buffer_post.py here.

## Steps
1. `cd wood`. Read CONTENT.md and STATE.md.
2. Environment: `pip install --break-system-packages numpy pillow` if missing; ffmpeg; DejaVu fonts
   (/usr/share/fonts/truetype/dejavu; else `apt-get install -y fonts-dejavu-core`).
3. Check `queue/log.txt` (last entries) and any job files still left in `queue/` (= failed earlier). Report failures to Ido at the end.
4. First post any posts marked "pending" in STATE.md (oldest first) — they count toward today's 3.
5. Write the remaining new specs (total 3 posts per day) as posts/NNN-slug.json (NNN continues from STATE.md),
   following the series rotation in STATE.md. Validate JSON and re-check every number by hand.
6. Render: `python3 render.py posts/NNN-slug.json out/` then move `out/NNN-slug.mp4` to `videos/`.
   ffprobe: 1080x1920, 12–22 s. Open slide 1 and the densest slide PNG and look at them: no overflowing text,
   nothing outside the frame. Fix and re-render if needed. Don't commit out/.
7. Delete videos/*.mp4 older than 10 days (already published). Update STATE.md. Commit and push to main.
8. Check each URL returns 200: https://raw.githubusercontent.com/idobits261/maklida/main/wood/videos/NNN-slug.mp4
9. For each post write `queue/NNN-slug.json`: {"spec": "posts/NNN-slug.json", "video": "videos/NNN-slug.mp4", "due": "<ISO with offset>"}
   with today's slots (Asia/Jerusalem): 16:00, 21:00, and 02:00 next day (= 9am, 2pm, 7pm US Eastern; +02:00 winter, +03:00 summer).
   Skip a slot already in the past. Commit and push. Wait ~3 minutes, `git pull`, and confirm the jobs moved to `queue/done/`
   and `queue/log.txt` shows exit=0 for each. If not, quote the log error in the report.
10. Log in STATE.md (post ids, series, slots, Buffer result), commit, push.
11. If anything fails: don't half-post silently. Record what failed in STATE.md, push, and report to Ido in short Hebrew.
