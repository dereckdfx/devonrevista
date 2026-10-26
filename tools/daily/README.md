# Publicación diaria de Devon

Esta carpeta contiene la tubería que publica los artículos de Devon cada día.
Nada de aquí se despliega: Vercel solo sirve el HTML de la raíz y `api/`.

## Reglas que la tubería garantiza

- **Ningún contenido de Vogue.** Ni artículos, ni imágenes, ni nombres de
  archivo, ni comentarios, ni parámetros de seguimiento.
- **El diseño no se toca.** `article.tpl` es una página real del sitio con el
  contenido sustituido por tokens, así que el marcado, las clases de Tailwind y
  el sistema tipográfico se conservan byte a byte fuera de los huecos de texto.
- **Toda firma es `POR DEVON`.**
- **Imágenes libres y verificadas.** Vienen de Wikimedia Commons con licencia
  CC0, dominio público, CC BY o CC BY-SA, y el crédito aparece en el
  `<figcaption>` de cada figura.

## Orden de ejecución

```bash
cd tools/daily

# 1. (Opcional) Refrescar el banco de imágenes. Solo si pools.json cambió.
python3 fetch_images.py pools.json imgcache.json 8

# 2. (Opcional) Regenerar la plantilla desde una página real del sitio.
python3 extract_template.py

# 3. Escribir los artículos del día. --purge borra los que ya no están
#    en el conjunto de content/.
python3 build_articles.py --purge

# 4. Apuntar todas las tarjetas del sitio a los artículos nuevos.
python3 rewire_cards.py

# 5. Rehacer el boletín con las historias del día.
python3 build_newsletter.py
```

Los pasos 3 a 5 son idempotentes: ejecutarlos dos veces da el mismo resultado.

## Dónde va el contenido nuevo

Cada día se añade un archivo `content/AAAA-MM-DD.json`; `build_articles.py`
siempre usa el más reciente. Cada entrada tiene esta forma:

```json
{
  "slug": "chanel-matthieu-blazy-primavera-verano-2027",
  "cat": "PASARELAS",
  "title": "Chanel por Matthieu Blazy: el largo exacto...",
  "dek": "Una frase que resume la nota.",
  "date": "26 de octubre de 2026",
  "q": "runway fashion show chanel tweed skirt",
  "body": ["Primer párrafo.", "## Subtítulo", "@@FIG", "Otro párrafo."]
}
```

- `cat` debe ser una de `MODA`, `PASARELAS`, `BELLEZA`, `ESTILO DE VIDA`,
  `COMPRAS`, `(RE)DEVON`, `HOLLYWOOD`, `RED CARPET`.
- `q` son palabras en inglés que `build_articles.py` cruza con `POOL_RULES`
  para elegir el banco de imágenes; si no coincide nada usa el de la categoría.
- `@@FIG` inserta una figura con su crédito. El bloque del boletín se añade
  solo, después del segundo párrafo.
