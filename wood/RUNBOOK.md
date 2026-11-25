# woodshmood — daily run (automatic, no approval)

Lives in the maklida repo under `wood/`. Separate from the Hebrew series: never touch files outside `wood/`
and never post to the maklida Buffer channels (the Buffer connector in Claude is maklida's account — do NOT use it here).

Posting goes through the SECOND Buffer account via `buffer_post.py`. Auth = a Network secret for api.buffer.com in the cloud environment (the proxy adds it); no key in code or env.

## Steps
1. `cd wood`. Read CONTENT.md and STATE.md.
2. Environment: `pip install --break-system-packages numpy pillow` if missing; ffmpeg; DejaVu fonts
   (/usr/share/fonts/truetype/dejavu; else `apt-get install -y fonts-dejavu-core`).
3. Run `python3 buffer_post.py channels`. If it fails with UNAUTHENTICATED (secret missing): still write + render + push today's 3 posts, mark them "pending" in STATE.md,
   and report to Ido in short Hebrew that the key is missing. Stop.
4. First post any posts marked "pending" in STATE.md (oldest first) — they count toward today's 3.
5. Write the remaining new specs (total 3 posts per day) as posts/NNN-slug.json (NNN continues from STATE.md),
   following the series rotation in STATE.md. Validate JSON and re-check every number by hand.
6. Render: `python3 render.py posts/NNN-slug.json out/` then move `out/NNN-slug.mp4` to `videos/`.
   ffprobe: 1080x1920, 12–22 s. Open slide 1 and the densest slide PNG and look at them: no overflowing text,
   nothing outside the frame. Fix and re-render if needed. Don't commit out/.
7. Delete videos/*.mp4 older than 10 days (already published). Update STATE.md. Commit and push to main.
8. Check each URL returns 200: https://raw.githubusercontent.com/idobits261/maklida/main/wood/videos/NNN-slug.mp4
9. Schedule via `python3 buffer_post.py post posts/NNN-slug.json <url> <dueAt>` with today's slots
   (Asia/Jerusalem): 16:00, 21:00, and 02:00 next day (= 9am, 2pm, 7pm US Eastern). Use the correct offset (+02:00 in winter, +03:00 in summer).
   Skip a slot that is already in the past.
10. Log in STATE.md (post ids, series, slots, Buffer result), commit, push.
11. If anything fails: don't half-post silently. Record what failed in STATE.md, push, and report to Ido in short Hebrew.
