#!/usr/bin/env python3
"""Fetch freely licensed, verified images from Wikimedia Commons for the daily build."""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = ("DevonRevistaBot/1.0 (+https://github.com/dereckdfx/devonrevista; stadeereck@gmail.com) python-urllib/3.12")
OK_LICENSES = ("cc0", "public domain", "pd", "cc by", "cc-by", "no restrictions", "attribution")
BAD = re.compile(r"(logo|flag of|\bmap\b|coat of arms|\bicon\b|\.svg|diagram|chart|\bseal\b|screenshot)", re.I)


def _get(url, tries=5):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt < tries - 1:
                time.sleep(8 * (attempt + 1))
                continue
            raise
        except Exception:
            if attempt < tries - 1:
                time.sleep(4)
                continue
            raise


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def search(query, limit=28):
    params = {
        "action": "query", "format": "json", "formatversion": "2",
        "generator": "search", "gsrsearch": f"filetype:bitmap {query}",
        "gsrlimit": str(limit), "gsrnamespace": "6",
        "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": "1600",
    }
    data = _get(API + "?" + urllib.parse.urlencode(params))
    out = []
    for page in data.get("query", {}).get("pages", []):
        info = (page.get("imageinfo") or [{}])[0]
        title = page.get("title", "")
        if BAD.search(title):
            continue
        w, h = info.get("width", 0), info.get("height", 0)
        if w < 800 or h < 700:
            continue
        meta = info.get("extmetadata", {})
        lic_raw = strip_tags(meta.get("LicenseShortName", {}).get("value", ""))
        lic = lic_raw.lower()
        if not (any(lic.startswith(p) for p in OK_LICENSES) or lic.startswith("cc by-sa")):
            continue
        url = info.get("thumburl") or info.get("url")
        if not url:
            continue
        url = url.split("?")[0].replace("https://thumb.wikimedia.org/", "https://upload.wikimedia.org/")
        author = strip_tags(meta.get("Artist", {}).get("value", "")) or "Wikimedia Commons"
        author = re.sub(r"\s+", " ", author)[:48]
        out.append({
            "url": url,
            "credit": f"{author} / Wikimedia Commons ({lic_raw})" if lic_raw else f"{author} / Wikimedia Commons",
            "portrait": h > w,
        })
    return out


def verify(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200 and int(r.headers.get("Content-Length") or 1) > 20000
    except Exception:
        return False


def main():
    queries = json.load(open(sys.argv[1]))
    cache_path = sys.argv[2]
    want = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    for q in queries:
        if len(cache.get(q, [])) >= want:
            continue
        got = list(cache.get(q, []))
        seen = {g["url"] for g in got}
        found = search(q)
        if not found:
            print(f" !  sin resultados para {q}; reintento", flush=True)
            time.sleep(20)
            found = search(q)
        for cand in found:
            if cand["url"] in seen:
                continue
            if verify(cand["url"]):
                got.append(cand)
                seen.add(cand["url"])
                time.sleep(0.15)
            if len(got) >= want:
                break
        cache[q] = got
        print(f"{len(got):>2}  {q}", flush=True)
        json.dump(cache, open(cache_path, "w"), ensure_ascii=False, indent=1)
        time.sleep(1.5)


if __name__ == "__main__":
    main()
