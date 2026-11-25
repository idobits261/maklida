#!/usr/bin/env python3
"""Render a woodshmood post (JSON spec) into a vertical 1080x1920 MP4 + slide PNGs.

Usage: python3 render.py posts/2026-11-26-a.json out_dir/
Spec keys: id, series, accent, slides[], parts[] (cuboids in inches for the blueprint drawing).
Slide types: hook, list, cutlist, steps, cta.
"""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BG = (14, 34, 58)
GRID = (26, 52, 84)
LINE = (170, 220, 255)
WHITE = (240, 246, 252)
MUTED = (140, 170, 200)
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
HERE = os.path.dirname(os.path.abspath(__file__))


def font(size, bold=True, cond=True):
    for cand in [os.path.join(HERE, "fonts", "Oswald-Bold.ttf" if bold else "Oswald-Regular.ttf")]:
        if os.path.exists(cand):
            return ImageFont.truetype(cand, size)
    name = "DejaVuSans" + ("Condensed" if cond else "") + ("-Bold" if bold else "") + ".ttf"
    return ImageFont.truetype(FONT_DIR + name, size)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def base(spec, idx, total):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 40):
        d.line([(x, 0), (x, H)], fill=GRID if x % 200 else (34, 66, 104), width=1)
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill=GRID if y % 200 else (34, 66, 104), width=1)
    acc = hexrgb(spec.get("accent", "#F2A541"))
    # series bar
    f = font(46)
    t = spec["series"].upper()
    tw = d.textlength(t, font=f)
    d.rounded_rectangle([(W - tw) / 2 - 30, 150, (W + tw) / 2 + 30, 222], 14, fill=acc)
    d.text((W / 2, 186), t, font=f, fill=BG, anchor="mm")
    # footer
    d.text((60, H - 230), "@woodshmood", font=font(34, bold=False), fill=MUTED, anchor="lm")
    d.text((W - 60, H - 230), f"{idx}/{total}", font=font(34, bold=False), fill=MUTED, anchor="rm")
    # title-block frame like a drawing sheet
    d.rectangle([30, 110, W - 30, H - 190], outline=(60, 100, 150), width=3)
    return im, d, acc


def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(d, text, y, size, fill=WHITE, maxw=920, bold=True, gap=1.15):
    f = font(size, bold)
    for line in wrap(d, text, f, maxw):
        d.text((W / 2, y), line, font=f, fill=fill, anchor="mt")
        y += int(size * gap)
    return y


# ---------- isometric blueprint drawing ----------
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))


def iso(p):
    x, y, z = p
    return ((x - y) * C30, (x + y) * S30 - z)


def draw_parts(im, parts, box, acc):
    """parts: [{"p":[x,y,z],"s":[w,d,h]}...] inches. box: (x0,y0,x1,y1) target area."""
    if not parts:
        return
    pts = []
    for pr in parts:
        (x, y, z), (w, dd, h) = pr["p"], pr["s"]
        for cx in (x, x + w):
            for cy in (y, y + dd):
                for cz in (z, z + h):
                    pts.append(iso((cx, cy, cz)))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    bx0, by0, bx1, by1 = box
    sc = min((bx1 - bx0 - 280) / (maxx - minx), (by1 - by0 - 160) / (maxy - miny))
    ox = bx0 + (bx1 - bx0 - (maxx - minx) * sc) / 2 - minx * sc
    oy = by0 + (by1 - by0 - (maxy - miny) * sc) / 2 - miny * sc

    def P(p):
        a, b = iso(p)
        return (ox + a * sc, oy + b * sc)

    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    order = sorted(parts, key=lambda pr: pr["p"][0] + pr["s"][0] / 2 + pr["p"][1] + pr["s"][1] / 2 + pr["p"][2] + pr["s"][2] / 2)
    for pr in order:
        (x, y, z), (w, dd, h) = pr["p"], pr["s"]
        hl = pr.get("hl", False)
        top = [P((x, y, z + h)), P((x + w, y, z + h)), P((x + w, y + dd, z + h)), P((x, y + dd, z + h))]
        fx = [P((x + w, y, z)), P((x + w, y + dd, z)), P((x + w, y + dd, z + h)), P((x + w, y, z + h))]
        fy = [P((x, y + dd, z)), P((x + w, y + dd, z)), P((x + w, y + dd, z + h)), P((x, y + dd, z + h))]
        base_c = acc if hl else (60, 110, 165)
        for poly, k in ((fy, 0.55), (fx, 0.75), (top, 1.0)):
            c = tuple(int(v * k) for v in base_c)
            d.polygon(poly, fill=c + (255,), outline=LINE + (255,))
            d.line(poly + [poly[0]], fill=LINE + (255,), width=3)
    im.paste(layer, (0, 0), layer)
    # overall dimensions
    X = max(p["p"][0] + p["s"][0] for p in parts)
    Y = max(p["p"][1] + p["s"][1] for p in parts)
    Z = max(p["p"][2] + p["s"][2] for p in parts)
    dd = ImageDraw.Draw(im)
    f = font(40)
    off = 10

    def dim(a, b, label, nx, ny):
        a2, b2 = (a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny)
        dd.line([a2, b2], fill=acc, width=3)
        for q in (a2, b2):
            dd.ellipse([q[0] - 6, q[1] - 6, q[0] + 6, q[1] + 6], fill=acc)
        m = ((a2[0] + b2[0]) / 2 + nx * (1.3 if ny == 0 else 0.9), (a2[1] + b2[1]) / 2 + ny * 0.9)
        dd.text(m, label, font=f, fill=acc, anchor="mm")

    def fmt(v):
        whole = int(v)
        frac = v - whole
        fr = {0.25: "¼", 0.5: "½", 0.75: "¾"}.get(round(frac * 4) / 4, "")
        return f'{whole}{fr}"'

    dim(P((0, Y, 0)), P((X, Y, 0)), fmt(X), -40, 46)
    dim(P((X, 0, 0)), P((X, Y, 0)), fmt(Y), 46, 40)
    dim(P((0, Y, 0)), P((0, Y, Z)), fmt(Z), -50, 0)


# ---------- slides ----------
def slide_hook(spec, s, i, n):
    im, d, acc = base(spec, i, n)
    y = text_block(d, s["title"], 300 if spec.get("parts") else 640, 104 if spec.get("parts") else 118)
    if s.get("sub"):
        y = text_block(d, s["sub"], y + 20, 52, fill=acc, bold=False)
    draw_parts(im, spec.get("parts"), (60, y + 20, W - 60, H - 300), acc)
    return im


def slide_list(spec, s, i, n):
    im, d, acc = base(spec, i, n)
    y = text_block(d, s["heading"], 400, 92)
    y += 90
    f, fp = font(56, bold=False), font(58)
    for name, price in s["items"]:
        d.text((90, y), name, font=f, fill=WHITE, anchor="lm")
        d.text((W - 90, y), price, font=fp, fill=acc, anchor="rm")
        d.line([(90, y + 60), (W - 90, y + 60)], fill=(60, 100, 150), width=2)
        y += 140
    if s.get("total"):
        y += 30
        d.rounded_rectangle([90, y - 10, W - 90, y + 110], 18, outline=acc, width=4)
        d.text((W / 2, y + 50), s["total"], font=font(62), fill=acc, anchor="mm")
        y += 170
    if s.get("note"):
        text_block(d, s["note"], y + 20, 44, fill=MUTED, bold=False)
    return im


def slide_cutlist(spec, s, i, n):
    im, d, acc = base(spec, i, n)
    y = text_block(d, s["heading"], 400, 92)
    y += 80
    f, fb = font(52, bold=False), font(54)
    d.text((90, y), "QTY", font=font(36), fill=MUTED, anchor="lm")
    d.text((230, y), "PART", font=font(36), fill=MUTED, anchor="lm")
    d.text((W - 90, y), "SIZE", font=font(36), fill=MUTED, anchor="rm")
    y += 70
    maxlen = max(float(it[3]) for it in s["items"]) if s["items"] and len(s["items"][0]) > 3 else None
    for it in s["items"]:
        qty, part, size = it[0], it[1], it[2]
        d.text((90, y), f"{qty}×", font=fb, fill=acc, anchor="lm")
        d.text((230, y), part, font=f, fill=WHITE, anchor="lm")
        d.text((W - 90, y), size, font=fb, fill=WHITE, anchor="rm")
        if maxlen:
            bw = (W - 320) * float(it[3]) / maxlen
            d.rectangle([230, y + 44, 230 + bw, y + 66], fill=(60, 110, 165), outline=LINE, width=2)
            y += 180
        else:
            y += 100
    if s.get("note"):
        text_block(d, s["note"], y + 20, 44, fill=MUTED, bold=False)
    return im


def slide_steps(spec, s, i, n):
    im, d, acc = base(spec, i, n)
    y = text_block(d, s["heading"], 360, 92)
    y += 70
    f = font(52, bold=False)
    for k, step in enumerate(s["items"], 1):
        d.ellipse([90, y - 6, 160, y + 64], fill=acc)
        d.text((125, y + 29), str(k), font=font(44), fill=BG, anchor="mm")
        lines = wrap(d, step, f, W - 300)
        for j, line in enumerate(lines):
            d.text((200, y + j * 64), line, font=f, fill=WHITE)
        y += max(1, len(lines)) * 64 + 56
    if s.get("tip"):
        y += 20
        lines = wrap(d, "PRO TIP: " + s["tip"], font(46), W - 260)
        hh = len(lines) * 58 + 60
        d.rounded_rectangle([90, y, W - 90, y + hh], 18, outline=acc, width=4)
        for j, line in enumerate(lines):
            d.text((W / 2, y + 30 + j * 58), line, font=font(46), fill=acc, anchor="mt")
    return im


def slide_cta(spec, s, i, n):
    im, d, acc = base(spec, i, n)
    y = text_block(d, s["title"], 560, 110)
    y = text_block(d, s.get("sub", ""), y + 40, 54, fill=MUTED, bold=False)
    y += 80
    d.rounded_rectangle([110, y, W - 110, y + 150], 30, fill=acc)
    d.text((W / 2, y + 75), s.get("button", "FREE PLANS → LINK IN PROFILE"), font=font(54), fill=BG, anchor="mm")
    y += 260
    if s.get("next"):
        text_block(d, s["next"], y, 52, fill=WHITE)
    return im


def slide_text(spec, s, i, n):
    """Big statement: optional label (e.g. MISTAKE #3), heading, body, optional fix box."""
    im, d, acc = base(spec, i, n)
    y = 420
    if s.get("label"):
        d.text((W / 2, y), s["label"].upper(), font=font(60), fill=acc, anchor="mt")
        y += 110
    y = text_block(d, s["heading"], y, 88)
    y = text_block(d, s.get("body", ""), y + 50, 52, fill=WHITE, bold=False, gap=1.3)
    if s.get("fix"):
        y += 60
        lines = wrap(d, "DO THIS: " + s["fix"], font(48), W - 260)
        hh = len(lines) * 60 + 60
        d.rounded_rectangle([90, y, W - 90, y + hh], 18, outline=acc, width=4)
        for j, line in enumerate(lines):
            d.text((W / 2, y + 30 + j * 60), line, font=font(48), fill=acc, anchor="mt")
    return im


KINDS = dict(text=slide_text, hook=slide_hook, list=slide_list, cutlist=slide_cutlist, steps=slide_steps, cta=slide_cta)


def pad_audio(path, dur, seed=0):
    sr = 44100
    t = np.arange(int(sr * dur)) / sr
    rng = np.random.default_rng(seed)
    roots = [110.0, 98.0, 130.81, 87.31]
    sig = np.zeros_like(t)
    seg = dur / len(roots)
    for k, r in enumerate(roots):
        m = (t >= k * seg) & (t < (k + 1) * seg + 0.5)
        env = np.clip(np.minimum((t - k * seg) / 0.6, ((k + 1) * seg + 0.5 - t) / 0.6), 0, 1)
        for mult, a in ((1, .5), (1.5, .3), (2, .25), (2.52, .15)):
            sig += m * env * a * np.sin(2 * np.pi * r * mult * t + rng.random() * 6)
    beat = 60 / 84
    for b in np.arange(0, dur, beat):
        idx = int(b * sr)
        L = int(0.12 * sr)
        tt = np.arange(L) / sr
        hit = np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 28) * 0.9
        sig[idx:idx + L] += hit[: len(sig[idx:idx + L])]
    sig *= np.clip(np.minimum(t / 1.0, (dur - t) / 1.2), 0, 1)
    sig = sig / (np.abs(sig).max() + 1e-9) * 0.35
    data = (sig * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(data.tobytes())


def main(spec_path, out_dir):
    spec = json.load(open(spec_path))
    os.makedirs(out_dir, exist_ok=True)
    n = len(spec["slides"])
    pngs = []
    for i, s in enumerate(spec["slides"], 1):
        im = KINDS[s["type"]](spec, s, i, n)
        p = os.path.join(out_dir, f"{spec['id']}_{i}.png")
        im.save(p)
        pngs.append(p)
    durs = [s.get("dur", 3.2) for s in spec["slides"]]
    fade = 0.35
    total = sum(durs) - fade * (n - 1)
    wav = os.path.join(out_dir, f"{spec['id']}.wav")
    pad_audio(wav, total, seed=abs(hash(spec["id"])) % 1000)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for p, dur in zip(pngs, durs):
        cmd += ["-loop", "1", "-t", str(dur), "-i", p]
    cmd += ["-i", wav]
    fc, prev, off = [], "0:v", 0.0
    for k in range(n):
        fc.append(f"[{k}:v]scale={W}:{H},format=yuv420p,setsar=1[s{k}]")
    prev = "s0"
    for k in range(1, n):
        off += durs[k - 1] - fade
        fc.append(f"[{prev}][s{k}]xfade=transition=slideleft:duration={fade}:offset={off:.2f}[x{k}]")
        prev = f"x{k}"
    mp4 = os.path.join(out_dir, f"{spec['id']}.mp4")
    cmd += ["-filter_complex", ";".join(fc), "-map", f"[{prev}]", "-map", f"{n}:a",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", mp4]
    subprocess.run(cmd, check=True)
    os.remove(wav)
    print(mp4)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
