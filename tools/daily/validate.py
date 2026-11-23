#!/usr/bin/env python3
"""Check the published site: links resolve, every byline is Devon's, no stray tokens."""
import os
import re
import sys
from urllib.parse import unquote, urlparse

import paths

LINK_RE = re.compile(r"""(?:href|window\.location\.href)\s*=?\s*["']([^"'#]+)["']""")
BYLINE_RE = re.compile(r">\s*(POR\s+[A-ZÁÉÍÓÚÑ0-9 .'’-]{2,40}?)\s*<")
# Pages that were already missing before the daily pipeline existed.
KNOWN_MISSING = {
    "ad.html", "glamour.html", "gq.html", "wired.html", "met-gala.html",
    "premios-oscar.html", "premios-emmy.html", "festival-de-cannes.html",
    "met-gala-2026.html", "globos-de-oro.html", "grammy.html",
    "festivales.html", "golden-globes.html", "premios-grammy.html", "todoslostemas.html",
}
# Links that were already broken before the daily pipeline existed: ali.html
# capitalises every file name, and two landing pages link to "index" with no
# extension. Both pre-date the automation and are left as they are.
KNOWN_BROKEN = {("ali.html", "capitalised"), ("coleccionlucky.html", "index"),
                ("euphoria.html", "index")}


def pre_existing(rel, url):
    if (rel, url) in KNOWN_BROKEN:
        return True
    return rel == "ali.html" and url[:1].isupper() and ("ali.html", "capitalised") in KNOWN_BROKEN


def targets(path):
    text = open(path, encoding="utf-8").read()
    for raw in LINK_RE.findall(text):
        url = raw.strip()
        if not url or urlparse(url).scheme or url.startswith(("//", "mailto:", "tel:", "javascript:")):
            continue
        yield url, text


def main():
    missing, bylines, tokens = [], [], []
    for folder, depth in ((paths.ROOT, 0), (paths.ARTDIR, 1), (os.path.dirname(paths.NEWSLETTER), 1)):
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".html"):
                continue
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, paths.ROOT)
            seen_text = None
            for url, text in targets(path):
                seen_text = text
                resolved = os.path.normpath(os.path.join(folder, unquote(url.lstrip("/"))))
                if url.startswith("/"):
                    resolved = os.path.normpath(os.path.join(paths.ROOT, unquote(url.lstrip("/"))))
                if os.path.basename(resolved).lower() in KNOWN_MISSING:
                    continue
                if not os.path.exists(resolved) and not pre_existing(rel, url):
                    missing.append(f"{rel} -> {url}")
            if seen_text is None:
                seen_text = open(path, encoding="utf-8").read()
            for byline in BYLINE_RE.findall(seen_text):
                if byline.strip().upper() != "POR DEVON":
                    bylines.append(f"{rel}: {byline.strip()}")
            if "{{" in seen_text:
                tokens.append(rel)

    for label, items in (("enlaces internos roto", missing), ("firmas distintas de POR DEVON", bylines),
                         ("plantillas sin rellenar", tokens)):
        print(f"{label}: {len(items)}")
        for item in sorted(set(items))[:20]:
            print("  ", item)
    if missing or bylines or tokens:
        sys.exit(1)
    print("sitio validado")


if __name__ == "__main__":
    main()
