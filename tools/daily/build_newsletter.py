#!/usr/bin/env python3
"""Rebuild the latest newsletter from Devon's own stories."""
import html as htmlmod
import json
import re

import paths

PATH = paths.NEWSLETTER
MANIFEST = json.load(open(paths.MANIFEST, encoding="utf-8"))
TODAY = "26 de octubre de 2026"

LINK_RE = re.compile(r"/articulos/([A-Za-z0-9._-]+)\.html")
IMG_RE = re.compile(r"<img\b[^>]*>")
TITLE_RE = re.compile(r"(<div[^>]*font-family:Georgia[^>]*>)(.*?)(</div>)", re.S)
DEK_RE = re.compile(r"(<div[^>]*Helvetica Neue[^>]*font-size:1[35]px[^>]*>)(.*?)(</div>)", re.S)
DATE_RE = re.compile(r"\d{1,2} de [a-zé]+ de \d{4}")


def esc(text):
    return htmlmod.escape(text, quote=True)


def pick(count):
    """One story per newsletter slot, rotating through the categories."""
    order = ["MODA", "BELLEZA", "ESTILO DE VIDA", "PASARELAS", "HOLLYWOOD",
             "RED CARPET", "COMPRAS", "(RE)DEVON"]
    buckets = {cat: [a for a in MANIFEST if a["cat"] == cat] for cat in order}
    out = []
    while len(out) < count:
        for cat in order:
            if buckets[cat] and len(out) < count:
                out.append(buckets[cat].pop(0))
    return out


def main():
    text = open(PATH, encoding="utf-8").read()
    old = list(dict.fromkeys(LINK_RE.findall(text)))
    new = pick(len(old))
    for before, art in zip(old, new):
        text = text.replace(f"/articulos/{before}.html", f"/articulos/{art['slug']}.html")

    out, cursor = [], 0
    for idx, art in enumerate(new):
        href = f"/articulos/{art['slug']}.html"
        start = text.index(href, cursor)
        end = text.index(f"/articulos/{new[idx + 1]['slug']}.html") if idx + 1 < len(new) else len(text)
        span = text[start:end]
        span = IMG_RE.sub(
            lambda m: re.sub(r'alt="[^"]*"', f'alt="{esc(art["title"])}"',
                             re.sub(r'src="[^"]*"', f'src="{esc(art["images"][0]["url"])}"', m.group(0))),
            span, count=1,
        )
        span = TITLE_RE.sub(lambda m: m.group(1) + esc(art["title"]) + m.group(3), span)
        span = DEK_RE.sub(lambda m: m.group(1) + esc(art["dek"]) + m.group(3), span)
        out.append(text[cursor:start] + span)
        cursor = end
    text = "".join(out) + text[cursor:]

    text = re.sub(r"(<title>Devon México: ).*?(</title>)", lambda m: m.group(1) + esc(new[0]["title"]) + m.group(2), text)
    text = DATE_RE.sub(TODAY, text)
    text = re.sub(r"\d+ historias nuevas hoy", f"{len(new)} historias nuevas hoy", text)
    open(PATH, "w", encoding="utf-8").write(text)
    print(f"newsletter rewired to {len(new)} Devon stories")


if __name__ == "__main__":
    main()
