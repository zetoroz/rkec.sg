#!/usr/bin/env python3
"""
Ping IndexNow (Bing, Copilot, Yandex, etc.) with the site's live URLs.
Runs in CI after deploy. Reads the published URLs from sitemap.xml and the
IndexNow key from the <key>.txt file at the site root. No login required.
"""
import re, glob, json, urllib.request

ROOT = __file__.rsplit("/scripts/", 1)[0]
HOST = "rkec.sg"

def main():
    keyfiles = [f for f in glob.glob(f"{ROOT}/*.txt")
                if re.fullmatch(r"[0-9a-f]{32}", f.rsplit("/", 1)[-1][:-4] or "")]
    if not keyfiles:
        print("[indexnow] no key file found; skipping"); return
    key = keyfiles[0].rsplit("/", 1)[-1][:-4]
    sm = open(f"{ROOT}/sitemap.xml", encoding="utf-8").read()
    urls = re.findall(r"<loc>(https://rkec\.sg/[^<]*)</loc>", sm)
    if not urls:
        print("[indexnow] no urls; skipping"); return
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"https://{HOST}/{key}.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"[indexnow] submitted {len(urls)} urls -> HTTP {r.status}")
    except Exception as e:
        print(f"[indexnow] ping failed (non-fatal): {e}")

if __name__ == "__main__":
    main()
