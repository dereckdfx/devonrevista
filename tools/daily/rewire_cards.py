#!/usr/bin/env python3
"""Point every card on the site at Devon's own articles, keeping the markup untouched."""
import html as htmlmod
import json
import os
import re
import sys

import paths

ROOT = paths.ROOT
MANIFEST = json.load(open(paths.MANIFEST, encoding="utf-8"))
BY_SLUG = {a["slug"]: a for a in MANIFEST}

DATE_RE = re.compile(r"^\d{1,2} de (?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre) de \d{4}$")
LINK_RE = re.compile(r"""(?:onclick="window\.location\.href='|href=")((?:\.\./)?(?:articulos/)?[A-Za-z0-9._-]+?(?:\.html)?)(?=['"])""")
# Cards whose story used to live at the site root instead of articulos/.
LEGACY_ROOT = {
    "zapatos-tacon-frances-elegantes-vestidos-faldas-verano-2026.html",
    "zapatos-jelly-tendencia-vestidos-faldas-jeans-verano-2026.html",
    "zapatos-coreanos-elegantes-jeans-faldas-vestidos-verano-2026.html",
    "isabel-allende.html",
    "como-llevar-la-playera-seleccion-mexicana",
    "vogue-ficcion-2026-ganadoras-y-finalistas",
}
# Image hosts that still serve the old magazine's pictures.
LEGACY_HOSTS = ("res.cloudinary.com", "dwgyu36up6iuz.cloudfront.net")
# Artwork Devon made itself, which must survive the swap.
KEEP_IMG = ("Devon_June_2026_N.231",)
IMG_RE = re.compile(r"<img\b[^>]*>", re.S)
# The full-bleed poster at the top of the homepage, whose copy lives outside a card.
HERO_RE = re.compile(
    r'(<a class="vw-poster" id="vw-poster" href=")[^"]*("\s+aria-label=")[^"]*(")'
    r'(.*?<img\b[^>]*\bsrc=")[^"]*(")'
    r'(.*?<span class="vw-tag">)[^<]*(</span>)'
    r'(\s*<p class="vw-headline">)[^<]*(</p>)',
    re.S,
)
ATTR_RE = re.compile(r'\b(src|alt|class)="([^"]*)"')
TAG_RE = re.compile(r"<(p|h1|h2|h3|h4|span|time)\b([^>]*)>((?:(?!</?\1[\s>]).)*?)</\1>", re.S)
SECTION_BREAK = "border-t border-b border-gray-200"

# Which categories each page should prefer, in order.
PAGE_PREFS = {
    "index.html": ["MODA", "RED CARPET", "BELLEZA", "ESTILO DE VIDA", "PASARELAS", "COMPRAS", "HOLLYWOOD", "(RE)DEVON"],
    "moda.html": ["MODA", "PASARELAS", "COMPRAS", "RED CARPET", "BELLEZA", "ESTILO DE VIDA", "(RE)DEVON", "HOLLYWOOD"],
    "pasarelas.html": ["PASARELAS", "MODA", "COMPRAS", "BELLEZA", "RED CARPET", "ESTILO DE VIDA", "(RE)DEVON", "HOLLYWOOD"],
    "belleza.html": ["BELLEZA", "MODA", "PASARELAS", "ESTILO DE VIDA", "RED CARPET", "COMPRAS", "(RE)DEVON", "HOLLYWOOD"],
    "estilodevida.html": ["ESTILO DE VIDA", "HOLLYWOOD", "BELLEZA", "MODA", "COMPRAS", "(RE)DEVON", "RED CARPET", "PASARELAS"],
    "compras.html": ["COMPRAS", "MODA", "BELLEZA", "(RE)DEVON", "PASARELAS", "ESTILO DE VIDA", "RED CARPET", "HOLLYWOOD"],
    "redevon.html": ["(RE)DEVON", "COMPRAS", "MODA", "ESTILO DE VIDA", "PASARELAS", "BELLEZA", "RED CARPET", "HOLLYWOOD"],
    "hollywood.html": ["HOLLYWOOD", "RED CARPET", "ESTILO DE VIDA", "BELLEZA", "MODA", "PASARELAS", "COMPRAS", "(RE)DEVON"],
    "redcarpet.html": ["RED CARPET", "HOLLYWOOD", "MODA", "PASARELAS", "BELLEZA", "ESTILO DE VIDA", "COMPRAS", "(RE)DEVON"],
    "espaciodevon.html": ["ESTILO DE VIDA", "COMPRAS", "MODA", "(RE)DEVON", "BELLEZA", "PASARELAS", "RED CARPET", "HOLLYWOOD"],
    "videos.html": ["HOLLYWOOD", "RED CARPET", "PASARELAS", "MODA", "BELLEZA", "ESTILO DE VIDA", "COMPRAS", "(RE)DEVON"],
    "tendencias.html": ["MODA", "BELLEZA", "PASARELAS", "COMPRAS", "ESTILO DE VIDA", "RED CARPET", "HOLLYWOOD", "(RE)DEVON"],
    "loultimo.html": ["ESTILO DE VIDA", "MODA", "RED CARPET", "BELLEZA", "HOLLYWOOD", "PASARELAS", "COMPRAS", "(RE)DEVON"],
    "members.html": ["RED CARPET", "MODA", "ESTILO DE VIDA", "BELLEZA", "HOLLYWOOD", "PASARELAS", "COMPRAS", "(RE)DEVON"],
}
DEFAULT_PREFS = ["MODA", "BELLEZA", "ESTILO DE VIDA", "RED CARPET", "PASARELAS", "HOLLYWOOD", "COMPRAS", "(RE)DEVON"]


def esc(text):
    return htmlmod.escape(text, quote=True)


def order_for(page):
    prefs = PAGE_PREFS.get(page, DEFAULT_PREFS)
    buckets = {cat: [a for a in MANIFEST if a["cat"] == cat] for cat in prefs}
    ordered = []
    for cat in prefs:
        ordered += buckets[cat]
    return ordered


def rewrite_segment(segment, art):
    """Replace the image, kicker, headline, byline and date inside one card."""
    state = {"img": False, "cat": False, "title": False}

    def img_sub(match):
        tag = match.group(0)
        attrs = dict((m.group(1), m.group(2)) for m in ATTR_RE.finditer(tag))
        src = attrs.get("src", "")
        if state["img"] or not any(h in src for h in LEGACY_HOSTS) or any(k in src for k in KEEP_IMG):
            return tag
        state["img"] = True
        tag = tag.replace(f'src="{attrs["src"]}"', f'src="{esc(art["images"][0]["url"])}"')
        if "alt" in attrs:
            tag = tag.replace(f'alt="{attrs["alt"]}"', f'alt="{esc(art["title"])}"')
        return tag

    segment = IMG_RE.sub(img_sub, segment)

    def tag_sub(match):
        tag, attrs, inner = match.groups()
        classes = (ATTR_RE.search(attrs) and dict(
            (m.group(1), m.group(2)) for m in ATTR_RE.finditer(attrs)).get("class", "")) or ""
        text = re.sub(r"<[^>]+>", "", inner).strip()
        if text.upper().startswith("POR "):
            return f"<{tag}{attrs}>POR DEVON</{tag}>"
        if DATE_RE.match(text):
            return f"<{tag}{attrs}>{art['date']}</{tag}>"
        if (not state["cat"] and tag in ("p", "span") and "uppercase" in classes
                and "tracking" in classes and 0 < len(text) <= 40):
            state["cat"] = True
            return f"<{tag}{attrs}>{esc(art['cat'])}</{tag}>"
        if (not state["title"] and tag in ("h2", "h3", "h4") and "leading" in classes
                and "tracking-wide" not in classes):
            state["title"] = True
            return f"<{tag}{attrs}>{esc(art['title'])}</{tag}>"
        return match.group(0)

    return TAG_RE.sub(tag_sub, segment)


def rewrite_hero(text, art):
    """The homepage poster needs its link, picture, kicker and headline to agree."""
    def sub(match):
        g = match.groups()
        return (g[0] + f"articulos/{art['slug']}.html" + g[1] + esc(art["title"]) + g[2]
                + g[3] + esc(art["images"][0]["url"]) + g[4]
                + g[5] + esc(art["cat"]) + g[6]
                + g[7] + esc(art["title"]) + g[8])

    return HERO_RE.sub(sub, text, count=1)


def is_card(target):
    stripped = target.lstrip("./")
    return stripped.startswith("articulos/") or stripped in LEGACY_ROOT


def process(path, depth):
    page = os.path.basename(path)
    text = open(path, encoding="utf-8").read()
    pool = order_for(page)
    used, assigned = set(), []
    slots = 0
    if HERO_RE.search(text):
        hero = next((a for a in pool if not a["images"][0]["portrait"]), pool[0])
        used.add(hero["slug"])
        text = rewrite_hero(text, hero)
        slots += 1

    matches = [m for m in LINK_RE.finditer(text)
               if is_card(m.group(1)) and 'id="vw-poster"' not in text[max(0, m.start() - 120):m.start()]]
    if not matches:
        open(path, "w", encoding="utf-8").write(text)
        return slots
    for _ in matches:
        pick = next((a for a in pool if a["slug"] not in used), None)
        if pick is None:
            used.clear()
            pick = pool[0]
        used.add(pick["slug"])
        assigned.append(pick)

    out, cursor = [], 0
    for idx, match in enumerate(matches):
        art = assigned[idx]
        out.append(text[cursor:match.start(1)])
        out.append(f"{'../' if depth else ''}articulos/{art['slug']}.html")
        seg_start = match.end(1)
        seg_end = matches[idx + 1].start(1) if idx + 1 < len(matches) else len(text)
        seg_end = min(seg_end, seg_start + 3000)
        segment = text[seg_start:seg_end]
        cut = segment.find(SECTION_BREAK)
        if cut > 0:
            head, tail = segment[:cut], segment[cut:]
        else:
            head, tail = segment, ""
        head = rewrite_segment(head, art)
        out.append(head + tail)
        cursor = seg_end
    out.append(text[cursor:])
    open(path, "w", encoding="utf-8").write("".join(out))
    return slots + len(matches)


def main():
    total = 0
    for name in sorted(os.listdir(ROOT)):
        if name.endswith(".html"):
            total += process(os.path.join(ROOT, name), 0)
    print(f"rewired {total} card slots across root pages")


if __name__ == "__main__":
    main()
