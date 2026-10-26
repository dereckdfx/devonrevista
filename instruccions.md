# Instrucciones para la IA — Devon México

## Tipografías

La página usa tres familias cargadas desde Google Fonts:

| Nombre | Variable Tailwind | Uso |
|---|---|---|
| **Jost** | `font-sans` (default) | Cuerpo general, categorías, autores, fechas, menú, footer |
| **Bodoni Moda** | `font-serif` | Logo DEVON |
| **Questrial / Century Gothic** | `font-geometric` | Subtítulos del header, menú de categorías, pestañas móvil |

### Pesos usados
- `font-light` — encabezados de sección (HOY)
- `font-normal` — títulos de artículos
- `font-bold` — logo, categorías, botones

### Letter-spacing
- `tracking-widest` = 0.2em — categorías, etiquetas
- `tracking-wide` — encabezados de sección
- `tracking-[0.15em]` — autores, links del footer

---

## Estructura de la página (orden de arriba a abajo)

1. **Sidebar / Overlay** — menú hamburguesa lateral
2. **Header sticky** — dos filas
3. **Pestañas móvil** — solo en móvil
4. **Banner principal** — imagen grande con título, autor y fecha
5. **Sección HOY** — encabezado + grid de artículos
6. **(Actualizado todos los dìas)** — encabezado
7. **Footer** negro

---

## Header

- `sticky top-0 z-40`, fondo blanco, borde inferior gris
- **Fila superior**: hamburguesa (izq) · Logo DEVON + isla dinámica (centro) · SUSCRIPCIÓN (der)
- **Fila inferior** (`#secondary-nav`): menú de categorías, solo desktop. Al hacer scroll > 20px se colapsa (`height: 0`, `opacity: 0`) con transición suave
- El logo **DEVON** usa `font-serif` (Bodoni Moda), bold, con una animación de línea diagonal que cruza la O (`animated-slash`, ciclo de 4s)
- Debajo del logo: "MÉXICO Y LATINOAMÉRICA" en `font-geometric`, 7–8px, mayúsculas

---

## Isla Dinámica (`#dynamic-island`)

- **Pulsación larga (500ms)** sobre el logo → aparece la isla con "DEVON" en serif blanco sobre fondo oscuro
- **Segunda pulsación larga** → se cierra y el logo reaparece
- Vibración háptica en móvil: 20ms al iniciar, 50ms al activar
- Animación de entrada con rebote `cubic-bezier(0.68, -0.55, 0.265, 1.55)`
- Click corto no hace nada

---

## Sidebar (Menú hamburguesa)

- Se abre desde la izquierda (`translateX(-100%)` → `translateX(0)`)
- Fondo blanco, borde derecho gris, `shadow-2xl`
- Los links entran con delays escalonados (0.10s–0.55s)
- Overlay oscuro (`bg-black/70`) al fondo; click en él cierra el menú
- Links: Suscripción, Inicio, Moda, Belleza, Estilo de Vida, Compras, (Re)Devon, Hollywood, Podcast, Espacio Devon

---

## Encabezados de sección

Patrón para todos los títulos (HOY, RUMBO AL MUNDIAL 2026…):

```html
<div class="border-t border-b border-gray-200 py-3 md:py-4">
  <h2 class="text-lg md:text-xl font-light tracking-wide text-gray-700"
      style="font-family: 'Jost', sans-serif;">
    NOMBRE SECCIÓN
  </h2>
</div>
```

---

## Banner principal (primera imagen grande)

```html
<section class="w-full border-b border-gray-200 pb-10 cursor-pointer hover:opacity-95 transition-opacity"
         onclick="window.location.href='ruta.html'">
  <div class="w-full max-w-6xl mx-auto px-4 md:px-8 lg:px-12 pt-4 md:pt-6">
    <img ... class="w-full h-auto max-h-[85vh] object-cover object-center"/>
  </div>
  <div class="max-w-4xl mx-auto flex flex-col items-center text-center mt-6 md:mt-8 px-4 font-geometric">
    <p class="text-[10px] md:text-xs font-bold tracking-[0.2em] uppercase text-black mb-3">CATEGORÍA</p>
    <h2 class="text-3xl md:text-4xl lg:text-[44px] font-normal text-black leading-[1.15] mb-6"
        style="letter-spacing: -0.02em;">Título</h2>
    <p class="text-[9px] md:text-[10px] font-bold tracking-[0.15em] uppercase text-black">POR AUTOR</p>
    <p class="font-semibold mt-1 text-[11px] md:text-[13px]">Fecha</p>
  </div>
</section>
```

---

## Tarjetas de artículo

### Artículo grande (hero de sección)
- Imagen `aspect-[2/3]`, 1 columna completa
- Texto superpuesto con gradiente negro (`from-black/80`)
- Categoría: 9px, light, tracking 0.2em, uppercase, blanco
- Título: 2xl–3xl, font-normal, Jost, blanco
- Autor y fecha: 9px–11px, font-light, blanco

### Artículos pequeños (grid 2×2)
- Imagen `aspect-square` o `aspect-[2/3]`
- Categoría: 9px, light, tracking 0.2em, uppercase, negro
- Título: `text-sm`, font-normal, negro
- Autor y fecha: 9px–11px, font-light, negro

### Interacción
```html
<div class="cursor-pointer group" onclick="window.location.href='ruta.html'">
  <img class="... group-hover:opacity-90 transition-opacity duration-300"/>
</div>
```

---

## Footer

- Fondo negro, texto blanco, `mt-20`
- Grid 12 columnas desktop / 1 columna móvil
- **Col izq (4)**: Logo DEVON blanco con `animated-slash` + ícono Instagram
- **Col centro (4)**: "MÁS EN DEVON" — Moda, Belleza, Estilo de Vida, Compras, (Re)Devon, Red Carpet, Pasarelas, Videos, Espacio Devon, PhotoDevon
- **Col der (4)**: "CONDÉ NAST MÉXICO" — AD, Glamour, Devon, GQ, Wired
- **Franja inferior**: links legales (Convenio, Privacidad, Quiénes Somos, Media Kit, Newsletter, Suscripción, Site Map) + selector de país (México / EE.UU) con dropdown hacia arriba

---

## Colores del sistema

| Variable Tailwind | Valor | Uso |
|---|---|---|
| `brandPink` | `#E8A5D6` | Acento rosa |
| `brandDark` | `#0B1320` | Fondo oscuro alternativo |
| `brandGray` | `#F2F2F2` | Gris claro de fondo |
| `vanCleefBg` | `#E5F0E6` | Verde suave (secciones especiales) |
| `bg-black` | `#000000` | Footer, overlay isla |
| `border-gray-200` | — | Separadores de secciones |

---

## Reglas generales para agregar contenido

- Todas las imágenes son de `upload.wikimedia.org` (Wikimedia Commons, con licencia libre) y el crédito se indica en el `<figcaption>` del artículo
- Contenedor máximo: `max-w-7xl mx-auto px-6`
- Grid principal: `grid-cols-1 md:grid-cols-3 gap-0 md:gap-8`
- Subgrid artículos pequeños: `grid-cols-2 gap-6 md:gap-8`
- Categorías siempre en MAYÚSCULAS, 9–10px, tracking 0.2em
- Fechas siempre en minúsculas: "28 de mayo de 2026"
- Autores siempre en MAYÚSCULAS con prefijo "POR"; la firma de todo el sitio es `POR DEVON`
- Secciones llevan `border-b border-gray-200` como separador inferior
