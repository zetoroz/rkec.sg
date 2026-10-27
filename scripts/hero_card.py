#!/usr/bin/env python3
"""Render an rkec.sg guide hero as a flat price card (no stock or AI imagery).

Dan rejected generated pictures as "AI slop" (Oct 2026). Where there is no real
job photo, a guide's hero is this card instead: an ink band with the title, a
clay band with the one real price that matters, and up to three line items from
the actual invoice or quote on paper. Same 1600x1073 size as the photo heroes.
Guide pages crop heroes to 26rem tall (about 75px off top and bottom at desktop
width), so content keeps clear of those edges.

  python3 scripts/hero_card.py spec.json assets/projects/g-<slug>.jpg

spec: {"eyebrow","title","num","numlabel","cols":[{"head","big","note"}],"source"}
"""
import json, os, subprocess, sys, tempfile
from html import escape
from pathlib import Path

W, H = 1600, 1073
CHROME = os.environ.get("CHROME_BIN") or str(next(Path.home().glob(
    ".cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell")))


def html(s):
    cols = s.get("cols", [])[:3]
    n = max(len(cols), 1)
    longest = max([len(str(c["big"])) for c in cols] or [1])
    big = min(64, int((W - 2 * 88 - (n - 1) * 36) / n / (0.6 * longest)))
    num = str(s["num"])
    numpx = min(190, int(W * 0.5 / (0.6 * max(len(num), 1))))
    cells = "".join(
        f'<div class="c"><div class="ch">{escape(c.get("head", ""))}</div><div class="cb">{escape(str(c["big"]))}</div>'
        f'<div class="cn">{escape(c.get("note", ""))}</div></div>' for c in cols)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Manrope:wght@500;600;700;800&display=block" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#FCFAF6;font-family:Manrope,sans-serif;color:#15233B;-webkit-font-smoothing:antialiased}}
.wrap{{display:flex;flex-direction:column;height:100%}}
.top{{background:#15233B;color:#F7F4EF;flex:0 0 400px;padding:112px 88px 48px;display:flex;flex-direction:column;justify-content:space-between}}
.eb{{font-size:24px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#E0915F}}
.t{{font-family:Fraunces,serif;font-weight:500;font-size:70px;line-height:1.05;letter-spacing:-.02em;max-width:1400px}}
.mid{{background:#C26A3C;color:#FCFAF6;flex:0 0 250px;padding:0 88px;display:flex;align-items:center;gap:44px}}
.n{{font-size:{numpx}px;font-weight:800;letter-spacing:-.04em;line-height:.9;white-space:nowrap}}
.nl{{font-size:30px;font-weight:600;line-height:1.3;max-width:640px}}
.bot{{flex:1;padding:44px 88px 96px;display:flex;flex-direction:column;justify-content:space-between}}
.cols{{display:grid;grid-template-columns:repeat({n},1fr);gap:36px}}
.c{{border-top:8px solid #15233B;padding-top:18px}}
.ch{{font-size:22px;font-weight:600;color:#5B6472}}
.cb{{font-size:{big}px;font-weight:800;letter-spacing:-.03em;margin-top:6px}}
.cn{{font-size:21px;color:#3a4554;margin-top:6px;line-height:1.35}}
.ft{{display:flex;justify-content:space-between;align-items:flex-end;font-size:20px;color:#7b8494}}
.ft b{{font-family:Fraunces,serif;font-size:28px;color:#15233B;font-weight:600}}
</style></head><body><div class="wrap">
<div class="top"><div class="eb">{escape(s["eyebrow"])}</div><div class="t">{escape(s["title"])}</div></div>
<div class="mid"><div class="n">{escape(num)}</div><div class="nl">{escape(s["numlabel"])}</div></div>
<div class="bot"><div class="cols">{cells}</div><div class="ft"><span>{escape(s.get("source", ""))}</span><b>RK E&amp;C</b></div></div>
</div></body></html>"""


def main():
    spec = json.load(open(sys.argv[1]))
    out = Path(sys.argv[2])
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "card.html"
        page.write_text(html(spec), encoding="utf-8")
        png = Path(d) / "card.png"
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox",
                        "--hide-scrollbars", "--virtual-time-budget=5000", f"--window-size={W},{H}",
                        f"--screenshot={png}", page.as_uri()], capture_output=True)
        from PIL import Image
        Image.open(png).convert("RGB").save(out, "JPEG", quality=88, optimize=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
