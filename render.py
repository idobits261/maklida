#!/usr/bin/env python3
"""Chat-story renderer: episode JSON -> vertical 1080x1920 mp4.

Usage: python3 render.py episodes/s01e01.json out/s01e01.mp4 [--preview N,N,N]
Each visual state is drawn once as a still (headless Chrome), then all stills are
encoded in one ffmpeg pass; audio (message pops + low pad) is synthesized here.
"""
import json, sys, os, html, math, subprocess, wave, struct, shutil
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright

WIDE = "--wide" in sys.argv   # 16:9 version for regular (non-Shorts) YouTube videos
W, H, FPS = (1920, 1080, 30) if WIDE else (1080, 1920, 30)
META = {}
STEP = 2 / FPS  # one typing step = 2 frames
ROOT = Path(__file__).parent
FONT = ROOT / "fonts"

import base64
def _b64(name):
    return base64.b64encode((FONT / name).read_bytes()).decode()
_FACES = "".join(
    "@font-face{font-family:%s;font-weight:%d;src:url(data:font/woff2;base64,%s) format('woff2')}" % (fam, w, _b64("heebo-%s-%d-normal.woff2" % (sub, w)))
    for fam, sub in (("HeeboHe", "hebrew"), ("HeeboLa", "latin")) for w in (400, 500, 700))
CSS = _FACES + """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;background:#000;font-family:HeeboHe,HeeboLa,'Noto Color Emoji',sans-serif;color:#e7ecef;overflow:hidden}
.phone{position:absolute;left:50px;top:250px;width:1080px;height:1671px;transform-origin:top left;transform:scale(.778);border-radius:44px;overflow:hidden;background:#0c1317;display:flex;flex-direction:column;direction:rtl}
.status{height:74px;display:flex;align-items:center;justify-content:space-between;padding:0 44px;font-size:32px;font-weight:500;color:#dfe5e8;direction:ltr}
.status .r{display:flex;gap:14px;align-items:center}
.bars{display:flex;gap:4px;align-items:flex-end;height:26px}.bars i{width:7px;background:#dfe5e8;border-radius:2px}
.batt{width:52px;height:26px;border:3px solid #dfe5e8;border-radius:7px;padding:2px}.batt i{display:block;height:100%%;width:62%%;background:#dfe5e8;border-radius:3px}
.head{height:150px;background:#1b262d;display:flex;align-items:center;gap:26px;padding:0 34px}
.back{font-size:58px;color:#9fb0b9;line-height:1;margin-top:-6px}
.av{width:96px;height:96px;border-radius:50%%;display:flex;align-items:center;justify-content:center;font-size:48px;font-weight:700;color:#fff}
.who{flex:1}.who b{display:block;font-size:44px;font-weight:500}.who span{font-size:30px;color:#8fa3ad}.who span.t{color:#3fd0a3}
.msgs{flex:1;display:flex;flex-direction:column;justify-content:flex-end;gap:14px;padding:26px 30px 24px;overflow:hidden;
 background:#0c1317}
.b{max-width:80%%;padding:18px 26px 14px;border-radius:26px;font-size:46px;line-height:1.32;position:relative}
.b.them{align-self:flex-start;background:#212e36;border-start-start-radius:6px}
.b.me{align-self:flex-end;background:#0f5a4a;border-start-end-radius:6px}
.b .m{display:block;font-size:25px;color:#9db0b8;margin-top:4px;direction:ltr;text-align:left}
.b.me .m{color:#a9d6c9}.b.me .m:after{content:' ✓✓';color:#63c7f2;font-size:24px}
.b.del{font-style:italic;color:#8fa3ad}.b.del .x{font-style:normal;margin-inline-end:10px;opacity:.8}
.gap{height:26px}
.bar{min-height:126px;display:flex;align-items:flex-end;gap:20px;padding:8px 26px 22px}
.inp{flex:1;min-height:92px;border-radius:46px;background:#1f2b32;padding:19px 36px;font-size:40px;line-height:1.35;color:#7f929c}
.inp.on{color:#e7ecef}.cur{display:inline-block;width:4px;height:44px;background:#14a37f;vertical-align:-8px;margin-inline-start:4px}
.mic{width:92px;height:92px;border-radius:50%%;background:#14a37f;display:flex;align-items:center;justify-content:center}
.mic i{width:0;height:0;border-top:17px solid transparent;border-bottom:17px solid transparent;border-right:28px solid #fff;margin-right:6px}
.card{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;background:#000;direction:rtl;text-align:center}
.card h1{font-size:120px;font-weight:700;letter-spacing:-1px}.card p{font-size:52px;color:#9fb0b9}.card .ln{width:120px;height:6px;background:#14a37f;border-radius:3px}
""".replace("%%","%")
if WIDE:
    CSS += """
html,body{width:1920px;height:1080px;background:radial-gradient(ellipse at 50% 40%,#12211f 0%,#060a0c 60%,#000 100%)}
.phone{left:50%;top:0;height:1500px;border-radius:0;transform-origin:top center;transform:translateX(-50%) scale(.72);box-shadow:0 0 120px rgba(0,0,0,.8)}
.card{background:#000}
.side{position:absolute;top:0;height:1080px;width:571px;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:22px;direction:rtl;text-align:center}
.side.r{right:0}.side.l{left:0}
.side h2{font-size:64px;font-weight:700}.side p{font-size:36px;color:#9fb0b9}.side .ln{width:80px;height:5px;background:#14a37f;border-radius:3px}
.side .brand{font-size:44px;font-weight:500;color:#3fd0a3}
"""


def esc(s):
    return html.escape(s)


def page_html(st):
    if st["kind"] == "card":
        body = f'<div class="card"><h1>{esc(st["title"])}</h1><div class="ln"></div><p>{esc(st["sub"])}</p></div>'
    else:
        rows = []
        for m in st["msgs"]:
            if m.get("gap"):
                rows.append('<div class="gap"></div>')
                continue
            if m.get("deleted"):
                rows.append(f'<div class="b {m["from"]} del"><span class="x">⊘</span>הודעה זו נמחקה<span class="m">{m["t"]}</span></div>')
            else:
                rows.append(f'<div class="b {m["from"]}">{esc(m["text"])}<span class="m">{m["t"]}</span></div>')
        sub = '<span class="t">מקליד/ה…</span>' if st["typing"] else '<span>מחובר/ת</span>'
        draft = st.get("draft")
        inp = f'<div class="inp on">{esc(draft)}<span class="cur"></span></div>' if draft else '<div class="inp">הודעה</div>'
        side = ""
        if WIDE:
            side = (f'<div class="side r"><h2>{esc(META["series"])}</h2><div class="ln"></div><p>פרק {META["episode"]}</p></div>'
                    f'<div class="side l"><div class="brand">מקליד/ה…</div><p>פרק חדש כל יום</p></div>')
        body = side + f'''<div class="phone">
<div class="status"><span>{st["clock"]}</span><span class="r"><span class="bars"><i style="height:9px"></i><i style="height:14px"></i><i style="height:20px"></i><i style="height:26px"></i></span><span class="batt"><i></i></span></span></div>
<div class="head"><span class="back">›</span><div class="av" style="background:{st["color"]}">{esc(st["avatar"])}</div><div class="who"><b>{esc(st["chat"])}</b>{sub}</div></div>
<div class="msgs">{"".join(rows)}</div>
<div class="bar">{inp}<div class="mic"><i></i></div></div></div>'''
    return f'<!doctype html><html lang="he"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'


def read_time(text, hold=None):
    if hold:
        return hold
    return max(1.1, min(2.8, 0.75 + 0.055 * len(text)))


def build_states(ep):
    """Flatten the episode into (state, duration, sound) steps."""
    S = []
    S.append(({"kind": "card", "title": ep["series"], "sub": f'פרק {ep["episode"]}'}, 2.0, None))
    for sc in ep["scenes"]:
        base = dict(kind="chat", chat=sc["chat"], avatar=sc["avatar"], color=sc["color"])
        clock = sc["clock"]
        msgs = []

        def st(typing=False, draft=None):
            return dict(base, clock=clock, typing=typing, draft=draft, msgs=[dict(m) for m in msgs])

        S.append((st(), 0.9, None))
        for ev in sc["events"]:
            if "clock" in ev:
                clock = ev["clock"]
                if msgs:
                    msgs.append({"gap": True})
            if "delete" in ev:
                for m in msgs:
                    if m.get("id") == ev["delete"]:
                        m["deleted"] = True
                S.append((st(), ev.get("hold", 1.6), None))
                continue
            if "typing" in ev:
                S.append((st(typing=True), ev["typing"], None))
                continue
            if "from" not in ev:
                S.append((st(), ev.get("pause", 0.8), None))
                continue
            text = ev["text"]
            if ev["from"] == "them":
                if not ev.get("no_typing"):
                    S.append((st(typing=True), max(0.7, min(1.5, 0.45 + 0.028 * len(text))), None))
                msgs.append({"from": "them", "text": text, "t": clock, "id": ev.get("id")})
                S.append((st(), read_time(text, ev.get("hold")), ev.get("sound", "in")))
            else:
                dur = max(0.6, min(1.9, 0.045 * len(text)))
                steps = max(1, min(len(text), int(dur / STEP)))
                for k in range(1, steps + 1):
                    cut = math.ceil(len(text) * k / steps)
                    S.append((st(draft=text[:cut]), STEP, "key"))
                S.append((st(draft=text), 0.2, None))
                msgs.append({"from": "me", "text": text, "t": clock, "id": ev.get("id")})
                S.append((st(), read_time(text, ev.get("hold")), "out"))
    S.append(({"kind": "card", "title": ep.get("end_card", "הפרק הבא מחר"), "sub": ep["series"]}, 2.6, None))
    return S


def synth_audio(states, path, sr=44100):
    """All sound is synthesized here: message pops, typing clicks, phone buzz, end sting, tension bed."""
    total = sum(d for _, d, _ in states)
    n = int(total * sr) + sr
    t = np.arange(n) / sr
    rng = np.random.default_rng(7)
    a = np.zeros(n)

    def add(at, sig):
        i = int(at * sr)
        if i >= n:
            return
        sig = sig[: n - i]
        a[i:i + len(sig)] += sig

    def tone(f, dur, decay, vol, harm=0.0):
        tt = np.arange(int(dur * sr)) / sr
        s = np.sin(2 * np.pi * f * tt) + harm * np.sin(2 * np.pi * 2 * f * tt)
        return vol * s * np.exp(-tt * decay) * np.minimum(1, tt / 0.004)

    def blip(at, f1, f2, vol):
        L = int(0.16 * sr)
        tt = np.arange(L) / sr
        f = np.linspace(f1, f2, L)
        add(at, vol * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 26))

    def pop_in(at):
        blip(at, 880, 1320, 0.34)
        blip(at + 0.09, 1320, 1760, 0.22)

    def pop_out(at):
        blip(at, 620, 480, 0.2)

    def click(at, vol):
        L = int(0.012 * sr)
        add(at, vol * rng.standard_normal(L) * np.exp(-np.arange(L) / (0.002 * sr)))

    def buzz(at):     # phone vibrating on a table: two bursts
        for k in (0.0, 0.34):
            tt = np.arange(int(0.24 * sr)) / sr
            body = np.sign(np.sin(2 * np.pi * 155 * tt)) * 0.5 + np.sin(2 * np.pi * 78 * tt)
            rattle = 0.15 * rng.standard_normal(len(tt)) * (np.sin(2 * np.pi * 155 * tt) > 0)
            env = np.minimum(1, tt / 0.015) * np.minimum(1, (0.24 - tt) / 0.03)
            add(at + k, 0.17 * (body + rattle) * env)

    def sting(at):    # riser into a low hit with a dissonant tail
        R = int(1.3 * sr)
        tr = np.arange(R) / sr
        riser = 0.10 * rng.standard_normal(R) * (tr / 1.3) ** 3
        riser = np.convolve(riser, np.ones(24) / 24, mode="same")
        add(max(0, at - 1.3), riser)
        tt = np.arange(int(2.8 * sr)) / sr
        f = 46 + 30 * np.exp(-tt * 9)
        boom = 0.55 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 1.6)
        tail = 0.06 * (np.sin(2 * np.pi * 311 * tt) + np.sin(2 * np.pi * 329.6 * tt) + np.sin(2 * np.pi * 466 * tt)) * np.exp(-tt * 1.1)
        add(at, (boom + tail) * np.minimum(1, tt / 0.003))

    # tension bed: low pad + slow heartbeat that gets a little stronger over the episode
    grow = 0.55 + 0.45 * (t / total).clip(0, 1)
    pad = 0.040 * (np.sin(2 * np.pi * 55 * t) + 0.7 * np.sin(2 * np.pi * 82.4 * t + 1.3) + 0.35 * np.sin(2 * np.pi * 110.6 * t)) \
        * (0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t))
    a += pad * grow
    beat = 0.0
    while beat < total - 1:
        g = 0.5 + 0.5 * beat / total
        for off, v in ((0.0, 0.16), (0.27, 0.11)):
            tt = np.arange(int(0.22 * sr)) / sr
            add(beat + off, v * g * np.sin(2 * np.pi * (58 - 60 * tt) * tt) * np.exp(-tt * 20))
        beat += 1.05

    at = 0.0
    for _, d, snd in states:
        if snd == "key":
            click(at, 0.06 + 0.05 * rng.random())
        elif snd == "out":
            pop_out(at)
        elif snd in ("in", "buzz", "sting"):
            pop_in(at)
            if snd == "sting":
                sting(at)
        at += d
    fade = int(0.5 * sr)
    a[:fade] *= np.linspace(0, 1, fade)
    a = a[: int(total * sr)]
    a[-fade:] *= np.linspace(1, 0, fade)
    a = np.tanh(a * 1.15)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767 * 0.95).astype("<i2").tobytes())
    return total


def main():
    args = [a for a in sys.argv[1:] if a != "--wide"]
    src, out = Path(args[0]), Path(args[1])
    preview = None
    if "--preview" in sys.argv:
        preview = [int(x) for x in sys.argv[sys.argv.index("--preview") + 1].split(",")]
    ep = json.loads(src.read_text(encoding="utf-8"))
    META.update(series=ep["series"], episode=ep["episode"])
    states = build_states(ep)
    work = out.parent / (out.stem + "_work")
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    with sync_playwright() as p:
        br = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
        pg = br.new_page(viewport={"width": W, "height": H})
        for i, (st, d, _) in enumerate(states):
            if preview is not None and i not in preview:
                continue
            pg.set_content(page_html(st))
            pg.evaluate("document.fonts.ready")
            pg.screenshot(path=str(work / f"{i:04d}.jpg"), type="jpeg", quality=92)
        br.close()
    if preview is not None:
        print("states:", len(states), "total sec:", round(sum(d for _, d, _ in states), 1))
        return
    lst = work / "list.txt"
    lines = []
    for i, (_, d, _) in enumerate(states):
        frames = max(1, round(d * FPS))
        lines += [f"file '{i:04d}.jpg'", f"duration {frames / FPS:.5f}"]
    lines.append(f"file '{len(states) - 1:04d}.jpg'")
    lst.write_text("\n".join(lines))
    wav = work / "a.wav"
    total = synth_audio([(s, max(1, round(d * FPS)) / FPS, x) for s, d, x in states], wav)
    tmp = out.with_name(out.stem + ".tmp.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(wav),
                    "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                    "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.3f}", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.rename(out)
    print("ok", out, "sec", round(total, 1), "states", len(states))


if __name__ == "__main__":
    main()
