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
# Commons keeps returning the same off-register results for these queries: paintings and
# museum scans instead of interiors, model aircraft instead of catwalks, supplement
# photography instead of cosmetics. They are never usable in a fashion magazine.
OFF_REGISTER = re.compile(
    r"(van[._ ]?gogh|holofernes|\bjudith\b|\boil on canvas\b|\bpainting\b|\bportrait of\b"
    r"|museum[._ ]journal|\bengraving\b|\blithograph\b|\bwoodcut\b"
    r"|google[._ ]art[._ ]project|lossy-page"
    r"|model[._ ](airplane|aircraft|flying|landing)|(airport|former|landing)[._ ]runway"
    r"|letter[._ ]signed|imagined[._ ]by|^thumbnail"
    r"|aloe[._ ]vera|\bdiaper|\bsupply[._ ]food\b"
    r"|mcdonald|burger[._ ]and[._ ]fries|washing[._ ]machine|vending[._ ]machine|cat[._ ]eye"
    r"|exxxotica|miss[._ ]sexy|den[._ ]brna)", re.I)


def off_register(text):
    return bool(BAD.search(text) or OFF_REGISTER.search(urllib.parse.unquote(text)))


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


def clean_author(raw):
    """Commons credits often trail into prose; keep just the name."""
    name = re.sub(r"\s+", " ", strip_tags(raw)).strip("“”\"' ")
    if "(" in name and len(name) > 24:
        name = name.split("(")[0].strip(" ,;-")
    if len(name) > 60:
        name = name[:60].rsplit(" ", 1)[0]
    return name.strip(" ,;-") or "Wikimedia Commons"


STOPWORDS = {"the", "and", "with", "from", "for"}


def stems(text):
    """Lowercased word stems, short enough to survive plurals and hyphenation."""
    return {w[:5] for w in re.split(r"[^a-z]+", urllib.parse.unquote(text).lower())
            if len(w) > 3 and w not in STOPWORDS}


def relevance(title, query):
    """How many words of the query the file's own title actually uses.

    Commons full-text search matches the description page, so a query like
    "eye make-up model" happily returns a ferris wheel named "London Eye". The
    file title is a much better signal of what the photo shows.
    """
    return len(stems(title) & stems(query))


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
        if off_register(title):
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
        author = clean_author(meta.get("Artist", {}).get("value", ""))
        out.append({
            "url": url,
            "credit": f"{author} / Wikimedia Commons ({lic_raw})" if lic_raw else f"{author} / Wikimedia Commons",
            "portrait": h > w,
            "match": relevance(title, query),
        })
    out.sort(key=lambda c: -c["match"])
    return out


def verify(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200 and int(r.headers.get("Content-Length") or 1) > 20000
    except Exception:
        return False


def load_blocklist():
    """Photos rejected on review. Commons keeps returning them, so keep them out."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blocklist.json")
    return set(json.load(open(path, encoding="utf-8"))) if os.path.exists(path) else set()


def main():
    queries = json.load(open(sys.argv[1]))
    cache_path = sys.argv[2]
    want = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    blocked = load_blocklist()
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    for pool, items in cache.items():
        cache[pool] = [i for i in items
                       if i["url"] not in blocked and not off_register(i["url"])]
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
        # Two query words in the file's own title; one only if the pool stays short.
        for floor in (2, 1):
            for cand in found:
                if cand["match"] < floor or cand["url"] in seen or cand["url"] in blocked:
                    continue
                if off_register(cand["url"]):
                    continue
                if verify(cand["url"]):
                    got.append(cand)
                    seen.add(cand["url"])
                    time.sleep(0.15)
                if len(got) >= want:
                    break
            if len(got) >= want:
                break
        cache[q] = got
        print(f"{len(got):>2}  {q}", flush=True)
        json.dump(cache, open(cache_path, "w"), ensure_ascii=False, indent=1)
        time.sleep(1.5)


if __name__ == "__main__":
    main()
