#!/usr/bin/env python3
"""Remove every residual mention of the old magazine from the site's HTML.

The card rewiring only touches the content slots, so brand text that lives in
comments, CSS annotations and tracking parameters survives it. This pass closes
that gap and fails loudly if anything is left behind.
"""
import os
import re
import sys

import paths

SUBS = [
    ("<!-- FOOTER: Diseño estilo Vogue -->", "<!-- FOOTER: Diseño editorial Devon -->"),
    ("<!-- FOOTER: Diseño estilo Devon (Basado en Vogue) -->", "<!-- FOOTER: Diseño editorial Devon -->"),
    ("// Animación colapso del Header (estilo Vogue)", "// Animación colapso del Header (estilo editorial)"),
    ("/* Estilo Botones Opciones (Tipo Vogue) */", "/* Estilo Botones Opciones */"),
    ("/* Vogue World Milano hero (Vogue.mx-style mobile poster + player) */",
     "/* Hero editorial Devon a pantalla completa */"),
    ("<!-- Pestañas Superiores (ocultas: no forman parte del look móvil tipo Vogue) -->",
     "<!-- Pestañas Superiores (ocultas: no forman parte del look móvil) -->"),
    ("<!-- Carrusel Vogue World Milán 2026 -->", "<!-- Carrusel Devon World Milán 2026 -->"),
    ("<!-- Título VOGUE WORLD MILÁN 2026 -->", "<!-- Título DEVON WORLD MILÁN 2026 -->"),
    # One stale page kept the former publisher's name in the footer column that
    # every other page titles "Más de Devon".
    ("<!-- Columna Derecha: CONDÉ NAST MÉXICO -->", "<!-- Columna Derecha: Publicaciones -->"),
    (">CONDÉ NAST MÉXICO</h4>", ">Más de Devon</h4>"),
    # Advertising deep links carry the old magazine's name in their tracking slots.
    ("utm_source=vogue", "utm_source=devon"),
    ("PERLEE--VOGUE_SUPER_BANNER", "PERLEE--DEVON_SUPER_BANNER"),
    ("3RD_PPS-VOGUE-SECTION", "3RD_PPS-DEVON-SECTION"),
]
# Blocks keyed by a unique marker line: everything from the opening tag that
# contains it up to its closing tag is dropped.
DROP_BLOCKS = [
    ("suscripcion.html", "SitioCovers_PRINT_DIGITAL_VG_JUL26", '<div class="relative', "</div>"),
]
BRAND_RE = re.compile(r"vogue|cond[eé]\s*nast|cnevids", re.I)


def drop_block(text, marker, open_tag, close_tag):
    """Remove the element containing `marker`, matching nested tags of its kind."""
    pos = text.index(marker)
    start = text.rindex(open_tag, 0, pos)
    tag_re = re.compile(rf"{re.escape(open_tag[:4])}|{re.escape(close_tag)}")
    depth = 0
    for match in tag_re.finditer(text, start):
        depth += 1 if match.group(0) == open_tag[:4] else -1
        if depth == 0:
            end = match.end()
            break
    else:
        raise SystemExit(f"unbalanced block around {marker}")
    return text[:start].rstrip() + "\n" + text[end:].lstrip("\n")


def main():
    changed = 0
    for name, marker, open_tag, close_tag in DROP_BLOCKS:
        path = os.path.join(paths.ROOT, name)
        text = open(path, encoding="utf-8").read()
        if marker in text:
            open(path, "w", encoding="utf-8").write(drop_block(text, marker, open_tag, close_tag))
            changed += 1

    for root, dirs, files in os.walk(paths.ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "tools", "assets")]
        for name in sorted(files):
            if not name.endswith((".html", ".js", ".md")):
                continue
            path = os.path.join(root, name)
            text = open(path, encoding="utf-8").read()
            fixed = text
            for before, after in SUBS:
                fixed = fixed.replace(before, after)
            if fixed != text:
                open(path, "w", encoding="utf-8").write(fixed)
                changed += 1

    leftovers = []
    for root, dirs, files in os.walk(paths.ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "tools")]
        for name in sorted(files):
            if not name.endswith((".html", ".js", ".json", ".md")):
                continue
            path = os.path.join(root, name)
            for num, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                if BRAND_RE.search(line):
                    leftovers.append(f"{os.path.relpath(path, paths.ROOT)}:{num}")

    print(f"scrubbed {changed} files")
    if leftovers:
        print("leftover brand mentions:", *leftovers[:40], sep="\n  ")
        sys.exit(1)
    print("no brand mentions left")


if __name__ == "__main__":
    main()
