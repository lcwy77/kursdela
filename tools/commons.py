"""Поиск свободных фото на Wikimedia Commons. Запускается на GitHub (воркфлоу «Фото с Wikimedia Commons»),
потому что из рабочей среды Claude сайт Commons недоступен.

  SEARCH="запрос 1; запрос 2"           → out/cand/<номер запроса>/<nn>.jpg (превью 500 px) и out/cand.json
  PICK="слаг=File:Имя.jpg; слаг2=File:…"  → out/pick/<слаг>.jpg (до 2400 px) и out/pick.json с автором и лицензией

Берём только свободные лицензии: CC0, общественное достояние, CC BY, CC BY-SA.
"""
import json, os, re, time, html, urllib.parse, urllib.request
from pathlib import Path

UA = "KursMediaBot/1.0 (https://kursmedia.com) python-urllib"
API = "https://commons.wikimedia.org/w/api.php"
OUT = Path("out")
FREE = re.compile(r"^(cc0|cc[- ]by|public domain|pd)", re.I)


def get(url, binary=False, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                data = r.read()
                return data if binary else json.loads(data)
        except Exception as e:
            print("  retry", i, url[:120], e, flush=True)
            time.sleep(2 + 3 * i)
    return None


def strip(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).split())


def info(params):
    q = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
         "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Credit|ImageDescription|DateTimeOriginal", **params}
    return get(API + "?" + urllib.parse.urlencode(q))


def rec(p):
    ii = p["imageinfo"][0]
    m = ii.get("extmetadata", {})
    v = lambda k: strip(m.get(k, {}).get("value", ""))
    return {"title": p["title"], "page": ii.get("descriptionurl"), "url": ii["url"], "thumb": ii.get("thumburl"), "w": ii["width"], "h": ii["height"],
            "mime": ii["mime"], "license": v("LicenseShortName"), "license_url": v("LicenseUrl"), "artist": v("Artist"),
            "credit": v("Credit")[:300], "desc": v("ImageDescription")[:400], "date": v("DateTimeOriginal")[:40]}


def search(queries):
    res = {}
    for n, q in enumerate(queries):
        d = info({"generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 20, "iiurlwidth": 500})
        pages = sorted((d or {}).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
        cands = []
        for p in pages:
            if "imageinfo" not in p:
                continue
            r = rec(p)
            if r["mime"] in ("image/jpeg", "image/png", "image/webp") and r["w"] >= 1200 and FREE.search(r["license"]):
                cands.append(r)
            if len(cands) >= 12:
                break
        folder = OUT / "cand" / f"{n:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        for i, r in enumerate(cands):
            b = get(r["thumb"], binary=True) if r["thumb"] else None
            if b:
                (folder / f"{i:02d}.jpg").write_bytes(b)
            r["i"] = i
            time.sleep(0.15)
        res[q] = cands
        print(q, len(cands), flush=True)
    (OUT / "cand.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


def pick(pairs):
    res = {}
    (OUT / "pick").mkdir(parents=True, exist_ok=True)
    for slug, title in pairs:
        d = info({"titles": title, "iiurlwidth": 2400})
        r = rec(next(iter(d["query"]["pages"].values())))
        src = r["thumb"] if r["w"] > 2400 and r["thumb"] else r["url"]
        b = get(src, binary=True) or get(r["url"], binary=True)
        if b:
            (OUT / "pick" / f"{slug}.jpg").write_bytes(b)
        res[slug] = r
        print(slug, r["license"], r["artist"][:60], flush=True)
        time.sleep(0.5)
    (OUT / "pick.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    if os.environ.get("SEARCH", "").strip():
        search([q.strip() for q in os.environ["SEARCH"].split(";") if q.strip()])
    if os.environ.get("PICK", "").strip():
        pick([tuple(x.strip().split("=", 1)) for x in os.environ["PICK"].split(";") if "=" in x])
