#!/usr/bin/env python3
"""Build Devon's daily original articles and rewire every card on the site to them."""
import html as htmlmod
import json
import os
import random
import re
import sys

import paths

ARTDIR = paths.ARTDIR
TPL = open(paths.TEMPLATE, encoding="utf-8").read()
IMGS = json.load(open(paths.IMGCACHE, encoding="utf-8"))

NEWSLETTER = """            <div class="my-14 pl-6 border-l-[4px] border-black max-w-4xl">
                <h3 class="font-serif font-normal text-3xl md:text-4xl mb-6 text-black tracking-normal">Devon más cerca de ti: ¡Suscríbete!</h3>
                <form class="flex flex-col sm:flex-row w-full mb-4" data-newsletter novalidate>
                    <input type="email" class="flex-1 border border-gray-300 p-4 text-sm focus:outline-none focus:border-black font-sans rounded-none" aria-label="Tu correo electrónico" required>
                    <button type="submit" class="bg-black text-white px-8 py-4 text-xs tracking-widest font-bold font-geometric uppercase hover:bg-gray-800 transition rounded-none">INSCRIBIRSE</button>
                </form>
                <p class="text-[13px] md:text-sm text-black font-sans font-light leading-relaxed">Ingresa tu dirección de correo electrónico para suscribirte a nuestro newsletter y formar parte del universo Devon. Tus datos personales serán tratados de acuerdo con nuestro <a href="../convenio.html" class="font-bold underline underline-offset-2">Convenio de Usuario</a> y <a href="../privacidad.html" class="font-bold underline underline-offset-2">Aviso de Privacidad.</a></p>
            </div>"""

# Which Commons pool feeds which kind of story.
POOL_RULES = [
    (r"runway|catwalk|fashion show", "fashion show"),
    (r"paris fashion week|street style|fashion week", "fashion week"),
    (r"corset|satin|sheer|transparent|balloon skirt|voluminous", "haute couture dress"),
    (r"midi skirt|clothing store|retail|denim|jeans|vintage clothing", "denim jeans"),
    (r"second hand|thrift|textile waste|recycled", "recycled clothes textile waste"),
    (r"wool|coat", "wool yarn knitting"),
    (r"linen|cotton|natural fiber", "linen cloth texture"),
    (r"floral print|pattern|pastel colour|textile", "textile weaving loom"),
    (r"mexican textile|artisan|weaving|beadwork|handicraft", "mexican textile embroidery"),
    (r"silver jewelry|jewellery", "artisan market mexico"),
    (r"pottery|ceramics", "pottery ceramics mexico"),
    (r"sewing|repair|tailor|alteration", "sewing machine tailor"),
    (r"label|tag|garment detail", "textile weaving loom"),
    (r"tailoring|blazer|suit jacket", "fashion week"),
    (r"lipstick|lips", "lipstick makeup"),
    (r"eyeshadow|eye makeup|eyeliner|eye make-up", "eye make-up model"),
    (r"blush|cheek|makeup face|cosmetics", "cosmetics products"),
    (r"haircut|hairstyle|hairdress|bob|brunette|hair color", "hairdresser salon"),
    (r"updo|braid|ponytail|long hair", "woman long hair portrait"),
    (r"day of the dead|ofrenda|altar", "day of the dead"),
    (r"catrina|parade", "catrina costume parade"),
    (r"cempasuchil|marigold", "cempasuchil marigold"),
    (r"zocalo", "zocalo mexico city"),
    (r"chapultepec", "chapultepec park"),
    (r"restaurant interior|dining", "restaurant interior"),
    (r"chef|kitchen|food|dish", "gourmet dish plate"),
    (r"art nouveau|mucha", "art nouveau poster mucha"),
    (r"museum|gallery|exhibition|contemporary art", "art museum interior"),
    (r"resort|hotel|pool", "hotel swimming pool resort"),
    (r"red carpet|celebrity|premiere", "red carpet premiere"),
    (r"evening|sequin|metallic|gown", "evening gown dress"),
    (r"award|trophy|concert|stage", "latin grammy award"),
    (r"theatre|auditorium|audience|formal event", "theatre auditorium"),
    (r"television|screen|streaming|cinema", "television studio"),
    (r"football|stadium|sport", "american football game"),
    (r"bogota|colombia", "bogota colombia"),
    (r"neon|cyberpunk|night|skyline", "city skyline night"),
    (r"corridor|gothic|school", "corridor school interior"),
    (r"office|computer|finance", "city skyline night"),
    (r"fantasy|mountain|volcano", "chapultepec park"),
    (r"mexico city", "mexico city street"),
]
CAT_FALLBACK = {
    "MODA": "fashion show",
    "PASARELAS": "runway model",
    "BELLEZA": "woman long hair portrait",
    "ESTILO DE VIDA": "mexico city street",
    "COMPRAS": "clothing store interior",
    "(RE)DEVON": "textile weaving loom",
    "HOLLYWOOD": "television studio",
    "RED CARPET": "red carpet premiere",
}


def esc(text):
    return htmlmod.escape(text, quote=True)


CAT_EXTRA = {
    "MODA": ["fashion show", "fashion week", "clothing store interior"],
    "PASARELAS": ["runway model", "haute couture dress", "fashion show"],
    "BELLEZA": ["woman long hair portrait", "hairdresser salon", "cosmetics products"],
    "ESTILO DE VIDA": ["mexico city street", "zocalo mexico city", "cempasuchil marigold"],
    "COMPRAS": ["clothing store interior", "denim jeans", "pottery ceramics mexico"],
    "(RE)DEVON": ["textile weaving loom", "recycled clothes textile waste", "sewing machine tailor"],
    "HOLLYWOOD": ["television studio", "city skyline night", "theatre auditorium"],
    "RED CARPET": ["red carpet premiere", "evening gown dress", "award ceremony stage"],
}


def pools_for(article):
    """Candidate Commons pools for one story, most specific first."""
    q = article["q"].lower()
    candidates = [pool for pattern, pool in POOL_RULES if re.search(pattern, q)]
    candidates += CAT_EXTRA[article["cat"]]
    candidates.append(CAT_FALLBACK[article["cat"]])
    usable = [p for p in dict.fromkeys(candidates) if len(IMGS.get(p, [])) >= 3]
    if not usable:
        raise SystemExit(f"no usable image pool for {article['slug']}")
    return usable


def load_articles():
    return json.load(open(paths.latest_content(), encoding="utf-8"))


def assign_images(articles):
    """Give every story its own hero image, spreading stories across the pools."""
    pool_use = {}
    heroes = set()
    for art in articles:
        usable = pools_for(art)
        pool = min(usable, key=lambda p: (pool_use.get(p, 0), usable.index(p)))
        pool_use[pool] = pool_use.get(pool, 0) + 1
        bucket = IMGS[pool]
        hero = next((i for i in bucket if i["url"] not in heroes), bucket[0])
        heroes.add(hero["url"])
        start = bucket.index(hero)
        figures = [bucket[(start + 1) % len(bucket)], bucket[(start + 2) % len(bucket)]]
        art["images"] = [hero] + figures
        art["pool"] = pool


def render_body(art):
    out = []
    figures = art["images"][1:]
    fig_i = 0
    para_count = 0
    for chunk in art["body"]:
        if chunk == "@@FIG":
            img = figures[fig_i % len(figures)]
            fig_i += 1
            out.append(
                f'<figure class="my-10"><img src="{esc(img["url"])}" alt="{esc(art["title"])}" loading="lazy" '
                f'class="w-full h-auto"/><figcaption class="text-[11px] tracking-wide text-gray-500 mt-2 '
                f'font-geometric uppercase">{esc(img["credit"])}</figcaption></figure>'
            )
        elif chunk.startswith("## "):
            out.append(f'<h2 class="text-2xl md:text-3xl font-medium text-black pt-4 font-sans">{esc(chunk[3:])}</h2>')
        else:
            out.append(f"<p>{esc(chunk)}</p>")
            para_count += 1
            if para_count == 2:
                out.append(NEWSLETTER)
    return "\n".join(out)


def render_related(art, articles):
    others = [a for a in articles if a["slug"] != art["slug"]]
    same = [a for a in others if a["cat"] == art["cat"]]
    rng = random.Random(art["slug"])
    picks = rng.sample(same, min(3, len(same)))
    if len(picks) < 3:
        rest = [a for a in others if a not in picks]
        picks += rng.sample(rest, 3 - len(picks))
    cards = []
    for other in picks:
        img = other["images"][0]
        cards.append(
            f'                <a href="{other["slug"]}.html" class="group flex flex-col items-start">\n'
            f'                    <div class="w-full overflow-hidden mb-4 bg-gray-100 aspect-[4/5]">\n'
            f'                        <img src="{esc(img["url"])}" alt="{esc(other["title"])}" loading="lazy" '
            f'class="w-full h-full object-cover group-hover:opacity-90 transition-opacity duration-300"/>\n'
            f'                    </div>\n'
            f'                    <p class="text-[9px] md:text-[10px] font-bold tracking-widest uppercase text-black mb-2">{esc(other["cat"])}</p>\n'
            f'                    <h3 class="text-xl md:text-2xl font-normal text-black leading-snug mb-2 font-sans '
            f'group-hover:text-gray-600 transition-colors">{esc(other["title"])}</h3>\n'
            f'                </a>'
        )
    return "\n".join(cards)


def write_articles(articles):
    for art in articles:
        page = TPL
        page = page.replace("{{HERO}}", esc(art["images"][0]["url"]))
        page = page.replace("{{TITLE_ATTR}}", esc(art["title"]))
        page = page.replace("{{TITLE}}", esc(art["title"]))
        page = page.replace("{{DEK}}", esc(art["dek"]))
        page = page.replace("{{CAT}}", esc(art["cat"]))
        page = page.replace("{{DATE}}", art["date"])
        page = page.replace("{{BODY}}", render_body(art))
        page = page.replace("{{RELATED}}", render_related(art, articles))
        assert "{{" not in page
        with open(os.path.join(ARTDIR, art["slug"] + ".html"), "w", encoding="utf-8") as fh:
            fh.write(page)


def main():
    articles = load_articles()
    assign_images(articles)
    if "--purge" in sys.argv:
        keep = {a["slug"] + ".html" for a in articles}
        removed = 0
        for name in os.listdir(ARTDIR):
            if name.endswith(".html") and name not in keep:
                os.remove(os.path.join(ARTDIR, name))
                removed += 1
        print(f"removed {removed} legacy article pages")
    write_articles(articles)
    json.dump(
        [{k: v for k, v in a.items() if k != "body"} for a in articles],
        open(paths.MANIFEST, "w"), ensure_ascii=False, indent=1,
    )
    print(f"wrote {len(articles)} article pages")


if __name__ == "__main__":
    main()
