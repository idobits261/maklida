# @woodshmood — content rules

Audience: US/English beginner and weekend woodworkers. Language: English only.
Goal: grow followers and send clicks to the affiliate link (Ted's Woodworking via ClickBank):
https://f.mtr.cool/busqrfcvqk

## Format
Vertical 1080x1920 MP4, 5 slides, ~15–18 s, blueprint style (render.py). Spec = posts/NNN-slug.json.
Slide types: hook (title, sub; draws `parts` if present), list (items [name, price], total, note),
cutlist (items [qty, part, size, length_number]), steps (items, tip), text (label, heading, body, fix), cta.

## Four series (rotate; never two of the same series in a row)
1. **Build for $X • Sell for $Y** (accent #F2A541) — hook+drawing / cost list / cut list / steps / cta.
   A real, simple, rectangular project. `parts` = cuboids in inches [x,y,z] + [w,d,h]; mark one part "hl": true.
2. **Mistake #N** (accent #E4572E) — numbered, N continues from STATE.md. hook (no parts) / text (what goes wrong, why) /
   text (the fix) / steps (3 quick checks) / cta.
3. **1% Know This** (accent #4CC9F0) — one joinery, tool or finishing trick. hook / text / steps / text or list / cta.
4. **5 Projects That Sell for $100+** (accent #7BD389) — once a week (Sunday's first post). hook / list (5 projects with
   typical selling price) / text / list / cta. This one leans hardest into the plans link.

## Accuracy (non-negotiable)
- Every number must be consistent: cut list matches the parts model, materials cover the cut list
  (6 ft fence picket = 72", boards in standard lengths), totals add up.
- Prices = conservative typical US big-box prices; always add "Typical US prices. Varies by area." on cost slides.
- Selling prices = realistic craft-fair / Marketplace ranges. No income promises.
- Safety-correct advice only (push sticks, blade guards, pre-drilling, eye/ear protection when relevant).
- Never claim things about Ted's Woodworking (no "tested", no numbers from their page). CTA only says plans are in the caption link.

## Variety (avoid "repetitive content" flags)
- Never repeat a project, mistake or trick already in STATE.md.
- Vary hook wording; no two hooks in a week with the same pattern.
- Footer CTA: "PLANS → LINK IN CAPTION" until the profile has a link; then "FREE PLANS → LINK IN PROFILE".

## Caption template
<one-line hook rephrased> <emoji> <one line of value>. Save this for the weekend!
#woodworking #diy + 3 topical tags (#woodworkingprojects #sidehustle #beginnerwoodworking …)
🪵 Full woodworking plans → https://f.mtr.cool/busqrfcvqk
Optional `title` field in the spec (≤ 90 chars) for TikTok/YouTube titles.
