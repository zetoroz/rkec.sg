#!/usr/bin/env python3
"""
RK E&C drip publisher.

Reads articles.json and, based on TODAY (Asia/Singapore), makes each article:
  - published (indexable, listed on home + /guides/, in sitemap.xml)   if date <= today
  - hidden    (noindex, shown as "Coming soon", absent from sitemap)   if date >  today

Idempotent. Run at build time (see .github/workflows/pages.yml) so articles
go live automatically on their scheduled date with no manual step.

Usage:  python scripts/publish_due.py          # apply for today
        python scripts/publish_due.py 2026-07-10   # simulate a date (testing)
"""
import json, re, sys
from datetime import datetime, timezone, timedelta, date

ROOT = __file__.rsplit("/scripts/", 1)[0]
SG = timezone(timedelta(hours=8))

def today():
    if len(sys.argv) > 1:
        return date.fromisoformat(sys.argv[1])
    return datetime.now(SG).date()

def read(p):  return open(f"{ROOT}/{p}", encoding="utf-8").read()
def write(p, s): open(f"{ROOT}/{p}", "w", encoding="utf-8").write(s)

ARROW = ('<svg class="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" '
         'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path d="M5 12h14M13 6l6 6-6 6"/></svg>')

def esc(s): return s.replace("&", "&amp;")

def home_card(a):
    return f'''<a href="guides/{a['slug']}/" class="group block rounded-3xl border border-line bg-cream/40 p-8 card-shadow transition-all duration-300 hover:-translate-y-1 hover:border-clay/40 cursor-pointer">
            <span class="text-xs font-semibold uppercase tracking-widest text-clay">{esc(a['category'])}</span>
            <h3 class="mt-4 font-display text-xl font-medium leading-snug">{esc(a['title'])}</h3>
            <p class="mt-3 text-[15px] leading-[1.7] text-muted">{esc(a['desc'])}</p>
            <span class="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-ink group-hover:text-clay transition-colors duration-200">Read guide
              {ARROW}
            </span>
          </a>'''

def guide_card_live(a):
    return f'''<a href="{a['slug']}/" class="group flex flex-col overflow-hidden rounded-3xl border border-line bg-paper card-shadow transition-all duration-300 hover:-translate-y-1 hover:border-clay/40 cursor-pointer">
            <div class="relative overflow-hidden">
              <img src="../assets/projects/{a['hero']}" alt="{esc(a['title'])}" class="h-48 w-full object-cover transition-transform duration-500 group-hover:scale-105" loading="lazy">
            </div>
            <div class="flex flex-1 flex-col p-7">
              <span class="text-xs font-semibold uppercase tracking-widest text-clay">{esc(a['category'])}</span>
              <h2 class="mt-3 font-display text-xl font-medium leading-snug">{esc(a['title'])}</h2>
              <p class="mt-3 text-[15px] leading-[1.7] text-muted">{esc(a['desc'])}</p>
              <span class="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-ink group-hover:text-clay transition-colors duration-200">Read guide
                {ARROW}
              </span>
            </div>
          </a>'''

def guide_card_soon(a):
    return f'''<div class="flex flex-col rounded-3xl border border-line bg-cream/40 p-7 card-shadow opacity-80">
            <span class="text-xs font-semibold uppercase tracking-widest text-clay">{esc(a['category'])}</span>
            <h2 class="mt-3 font-display text-xl font-medium leading-snug">{esc(a['title'])}</h2>
            <p class="mt-3 text-[15px] leading-[1.7] text-muted">{esc(a['desc'])}</p>
            <span class="mt-5 inline-flex items-center gap-1.5 rounded-full bg-ink/5 px-3 py-1 text-xs font-semibold text-muted">Coming soon</span>
          </div>'''

def replace_block(html, start, end, body):
    return re.sub(re.escape(start) + r".*?" + re.escape(end),
                  start + "\n" + body + "\n          " + end, html, flags=re.S)

def main():
    t = today()
    data = json.loads(read("articles.json"))
    arts = data["articles"]
    for a in arts:
        a["_d"] = date.fromisoformat(a["date"])
        a["_pub"] = a["_d"] <= t

    pub = sorted([a for a in arts if a["_pub"]], key=lambda a: a["_d"], reverse=True)
    soon = sorted([a for a in arts if not a["_pub"]], key=lambda a: a["_d"])

    # 1. flip each article's robots flag
    for a in arts:
        p = f"guides/{a['slug']}/index.html"
        try:
            h = read(p)
        except FileNotFoundError:
            print(f"WARN missing {p}"); continue
        content = "index, follow" if a["_pub"] else "noindex"
        nh = re.sub(r'<meta name="robots"[^>]*/?><!--RKEC-FLAG-->',
                    f'<meta name="robots" content="{content}" /><!--RKEC-FLAG-->', h)
        if nh != h:
            write(p, nh)

    # 2. homepage featured cards (3 newest published)
    h = read("index.html")
    home_body = "          " + "\n          ".join(home_card(a) for a in pub[:3])
    h = replace_block(h, "<!--HOME-GUIDES:START-->", "<!--HOME-GUIDES:END-->", home_body)
    write("index.html", h)

    # 3. guides index (published first, then coming-soon)
    g = read("guides/index.html")
    cards = [guide_card_live(a) for a in pub] + [guide_card_soon(a) for a in soon]
    guides_body = "          " + "\n          ".join(cards)
    g = replace_block(g, "<!--GUIDES-LIST:START-->", "<!--GUIDES-LIST:END-->", guides_body)
    write("guides/index.html", g)

    # 4. sitemap.xml
    iso = t.isoformat()
    urls = [("https://rkec.sg/", iso, "weekly", "1.0"),
            ("https://rkec.sg/guides/", iso, "weekly", "0.7")]
    for a in sorted(pub, key=lambda a: a["_d"]):
        urls.append((f"https://rkec.sg/guides/{a['slug']}/", a["date"], "monthly", "0.8"))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lm, cf, pr in urls:
        sm += ["  <url>", f"    <loc>{loc}</loc>", f"    <lastmod>{lm}</lastmod>",
               f"    <changefreq>{cf}</changefreq>", f"    <priority>{pr}</priority>", "  </url>"]
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")

    # 5. llms.txt — keep the Guides section in sync with published articles (GEO)
    try:
        l = read("llms.txt")
        items = "\n".join(
            f"- [{a['title']}](https://rkec.sg/guides/{a['slug']}/): {a['desc']}"
            for a in pub if a["slug"] != "taobao-furniture-assembly-singapore" or True
        )
        def _repl(m): return m.group(1) + items + "\n" + m.group(2)
        l2 = re.sub(r"(## Guides\n)(?:.*?)(\n## Contact)", _repl, l, flags=re.S)
        if l2 != l:
            write("llms.txt", l2)
    except FileNotFoundError:
        pass

    print(f"[publish_due] {t}  live={len(pub)} hidden={len(soon)}")
    for a in pub:  print("  LIVE  ", a["slug"])
    for a in soon: print("  hidden", a["slug"], a["date"])

if __name__ == "__main__":
    main()
