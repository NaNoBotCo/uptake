#!/usr/bin/env python3
"""Pull the public-domain pictures from Wikimedia Commons, with a licence sidecar
beside each file. Re-runnable: a picture already on disk is left alone."""
import json, re, pathlib, urllib.parse, urllib.request

UA = "uptake-manual/1.0 (https://github.com/NaNoBotCo/uptake)"
API = "https://commons.wikimedia.org/w/api.php"
OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "img"

WANTED = [
    ("scribe",       "File:Jean Miélot, Brussels.jpg", 1400),
    ("card-catalog", "File:Card Division of the Library of Congress 3c18631u original.jpg", 1600),
    ("mundaneum",    "File:Paul Otlet et son équipe.jpg", 1600),
    ("skep-stone",   "File:Straw Skep on gravestone, Stobo Kirk.JPG", 1400),
    ("skep-line",    "File:1911 Britannica - Bee - Straw skep.png", 492),
]

def strip(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(html or ""))).strip()

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=60).read()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, title, width in WANTED:
        q = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "imageinfo",
            "iiprop": "url|extmetadata|size", "iiurlwidth": width, "titles": title})
        data = json.loads(get(f"{API}?{q}"))
        page = next(iter(data["query"]["pages"].values()))
        ii = page["imageinfo"][0]
        em = ii.get("extmetadata", {})
        src = ii.get("thumburl") or ii["url"]
        ext = ".png" if src.lower().split("?")[0].endswith(".png") else ".jpg"
        img = OUT / f"{slug}{ext}"
        if not img.exists():
            img.write_bytes(get(src))
        meta = {
            "file": img.name,
            "title": strip(em.get("ObjectName", {}).get("value")) or page["title"],
            "commons": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(page["title"].replace(" ", "_")),
            "creator": strip(em.get("Artist", {}).get("value")) or "unknown",
            "date": strip(em.get("DateTimeOriginal", {}).get("value")),
            "licence": strip(em.get("LicenseShortName", {}).get("value")),
            "licence_url": strip(em.get("LicenseUrl", {}).get("value")),
            "source_page_bytes": ii.get("size"),
            "stored_px": [ii.get("thumbwidth", ii.get("width")), ii.get("thumbheight", ii.get("height"))],
            "retrieved": "2026-09-18",
        }
        (OUT / f"{slug}{ext}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
        print(f"{img.name:20} {img.stat().st_size:>9,} B  {meta['licence']}  — {meta['title'][:60]}")

if __name__ == "__main__":
    main()
