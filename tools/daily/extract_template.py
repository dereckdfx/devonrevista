#!/usr/bin/env python3
"""Turn an existing Devon article into a token template, preserving every bit of markup."""
import os
import re
import sys

import paths

OUT = paths.TEMPLATE


def source():
    """An existing article page to tokenize; they all share one template."""
    if len(sys.argv) > 1:
        return os.path.join(paths.ARTDIR, sys.argv[1])
    return os.path.join(paths.ARTDIR, sorted(os.listdir(paths.ARTDIR))[0])


def main():
    html = open(source(), encoding="utf-8").read()

    # --- head metadata ---
    html = re.sub(r"<title>.*?</title>", "<title>{{TITLE}} | Devon México y Latinoamérica</title>", html, count=1, flags=re.S)
    html = re.sub(r'<meta name="description" content=".*?">',
                  '<meta name="description" content="{{DEK}}">', html, count=1, flags=re.S)
    html = re.sub(r'<meta property="og:title" content=".*?">',
                  '<meta property="og:title" content="{{TITLE}} | Devon México y Latinoamérica">', html, count=1, flags=re.S)
    html = re.sub(r'<meta property="og:description" content=".*?">',
                  '<meta property="og:description" content="{{DEK}}">', html, count=1, flags=re.S)
    html = re.sub(r'<meta property="og:image" content=".*?">',
                  '<meta property="og:image" content="{{HERO}}">', html, count=1, flags=re.S)

    # --- hero ---
    html = re.sub(r'(<section class="w-full border-b border-gray-200 pb-10">.*?<img src=")[^"]*(" alt=")[^"]*(")',
                  r'\1{{HERO}}\2{{TITLE_ATTR}}\3', html, count=1, flags=re.S)
    html = re.sub(r'(<p class="text-\[10px\] md:text-xs font-bold tracking-widest uppercase text-black mb-4">).*?(</p>)',
                  r'\1{{CAT}}\2', html, count=1, flags=re.S)
    html = re.sub(r'(<h1 [^>]*>).*?(</h1>)', r'\1{{TITLE}}\2', html, count=1, flags=re.S)
    html = re.sub(r'(<p class="text-base md:text-lg text-gray-700 font-light mb-8 max-w-2xl mx-auto font-sans">).*?(</p>)',
                  r'\1{{DEK}}\2', html, count=1, flags=re.S)
    html = re.sub(r'(<p class="text-\[9px\] md:text-\[10px\] font-bold tracking-author uppercase text-black">).*?(</p>)',
                  r'\1POR DEVON\2', html, count=1, flags=re.S)
    html = re.sub(r'(<p class="font-normal mt-1 text-\[11px\] md:text-\[13px\] text-gray-500 lowercase">).*?(</p>)',
                  r'\1{{DATE}}\2', html, count=1, flags=re.S)

    # --- body ---
    html = re.sub(r'(<article class="w-full max-w-3xl mx-auto px-6 py-12 md:py-16 font-sans text-lg md:text-xl text-gray-800 leading-relaxed space-y-8">).*?(</article>)',
                  r'\1\n{{BODY}}\n        \2', html, count=1, flags=re.S)

    # --- related cards ---
    html = re.sub(r'(<div class="grid grid-cols-1 md:grid-cols-3 gap-8">).*?(</div>\n        </section>\n    </main>)',
                  r'\1\n{{RELATED}}\n            \2', html, count=1, flags=re.S)

    for token in ("{{TITLE}}", "{{DEK}}", "{{HERO}}", "{{CAT}}", "{{DATE}}", "{{BODY}}", "{{RELATED}}", "{{TITLE_ATTR}}"):
        assert token in html, f"missing {token}"
    # The newsletter block lives inside the article body in the source; make sure we kept it out of the template.
    assert "data-newsletter" not in html.split("{{BODY}}")[0].split("<main>")[-1], "newsletter leaked into template head"
    open(OUT, "w", encoding="utf-8").write(html)
    print("template written", len(html), "bytes")


if __name__ == "__main__":
    main()
