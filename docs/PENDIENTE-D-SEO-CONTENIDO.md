# Pendiente D — SEO/contenido: piezas de infraestructura documentadas y nunca construidas

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-d-seo-contenido`

> **Alcance de esta PR y solo esta.** Cuatro sub-tareas independientes entre
> sí (D.1–D.4), todas de contenido/SEO técnico. No toca `script.js`,
> `cloudflare-worker-subscribe.js` ni ningún workflow — otras PRs (A, B, C, E)
> cubren eso y no deben pisarse. Si el tiempo no da para las cuatro, prioriza
> D.1 y D.4 (impacto real) y deja D.2/D.3 explícitamente fuera en la
> descripción de la PR.
>
> **No requiere claves ni acceso externo.**
>
> **No es diseño final.** D.1 y D.3 tocan visualización de una fecha y de un
> feed — usa clases/estilos ya existentes en el sitio, sin inventar un
> sistema visual nuevo.

---

## D.1 — Sin fecha "Última actualización" visible en artículos (prioridad alta)

### El problema

```bash
$ grep -n "Última actualización\|Actualizado el" cuaderno/que-es-el-portal-fantasy/index.html
(sin resultados)
```

Los artículos de `/cuaderno/` pueden llevar `dateModified` en su JSON-LD sin
que el lector vea ninguna fecha de revisión en la página. Eso es "frescura
falsa" no detectable a simple vista — un dato ya señalado como P0 de
confianza editorial en el dossier (`WEB DAVID PORTO nuevas ideas/15_REGISTRO_DE_CORRECCIONES.md`,
hallazgo C-087): *"Artículos pueden declarar `dateModified` en JSON-LD sin
mostrar al lector la fecha de revisión."*

`scripts/check-article-dates.py`, que el dossier documentaba como preparado,
**no existe en el repo** — nunca se llegó a construir, ni el checker ni el
bloque visible.

### Qué hacer

1. Define el patrón visible: un bloque pequeño y consistente cerca del título
   o al final del artículo, tipo `Publicado el DD/MM/AAAA · Actualizado el
   DD/MM/AAAA` (omite "Actualizado" si coincide con "Publicado"). Usa
   `datetime` en un `<time>` real, coherente con el valor de `dateModified`/
   `datePublished` del JSON-LD de la misma página — **no dupliques la fuente
   de verdad**, el HTML visible y el JSON-LD deben leer del mismo dato.
2. Aplícalo a los artículos de `/cuaderno/*/index.html` que ya tienen fechas
   reales en su JSON-LD (no inventes fechas donde no las haya).
3. Construye `scripts/check-article-dates.py`: recorre `cuaderno/*/index.html`
   con canonical del dominio, extrae `datePublished`/`dateModified` del
   JSON-LD y confirma que existe un bloque de fecha visible en el HTML cuyo
   valor coincide. Sigue el patrón de otros checkers del repo (por ejemplo
   `scripts/check-editorial-facts.py` o `scripts/check-internal-graph.py` para
   estilo: biblioteca estándar de Python, modo `--check` para CI, salida clara
   de qué página falla y por qué).
4. Añade el checker a `.github/workflows/content-index-check.yml` en el mismo
   job que ya corre `build-sitemap.py`/`build-feed.py`.

### Criterio de aceptación

- Todos los artículos de `/cuaderno/` con `dateModified` real muestran su
  fecha visible, coherente con el JSON-LD.
- `python scripts/check-article-dates.py --check` existe, pasa en local, y
  falla deliberadamente si rompes la coherencia a propósito (pruébalo: cambia
  una fecha visible sin tocar el JSON-LD, confirma que el checker lo detecta,
  revierte).
- Wireado en `content-index-check.yml`.

---

## D.2 — Sin permalinks de sección en artículos (opcional, sin urgencia)

Ningún artículo tiene forma de enlazar directamente a un H2/H3 concreto
(dossier: hallazgo C-086). `assets/article-tools.js` ya genera IDs estables
para H2/H3 y un índice (TOC), pero al compartir se limpian todos los hashes;
no hay un botón/enlace de "permalink de esta sección".

### Qué hacer (si hay margen)

En `assets/article-tools.js`, junto a cada H2/H3 con ID generado, añade un
enlace ancla discreto (visible al hover/focus, tipo los patrones de AnchorJS)
que apunte a `#id-de-la-seccion`. Al compartir desde ese contexto, conserva el
hash solo si corresponde a un H2/H3 real del artículo (no arrastres un hash
residual de otra navegación).

### Criterio de aceptación

- Cada H2/H3 con ID tiene un permalink visible al hover/focus.
- El hash se conserva al compartir solo si pertenece a un encabezado real.

---

## D.3 — Sin vista humana del RSS (opcional, sin urgencia)

```bash
$ find . -iname "*rss-human*" -o -iname "feed.xsl"
(sin resultados, fuera de la carpeta del dossier)
```

`/cuaderno/feed.xml` se abre como XML crudo en el navegador (dossier:
hallazgo C-088). No es bloqueante — es UX de una URL de nicho para quien la
abra manualmente en vez de en un lector RSS — pero está documentado y
preparado en el dossier sin construirse.

### Qué hacer (si hay margen)

Añade una hoja `xsl:stylesheet` (`rss-human-view.xsl` o similar) que
transforme el feed en una vista legible cuando se abre en navegador, sin
cambiar el contrato RSS 2.0 ni la URL. Debe declararse con
`<?xml-stylesheet?>` en `cuaderno/feed.xml` — revisa cómo lo genera
`scripts/build-feed.py` para añadir esa línea al output sin romper el `--check`
existente.

### Criterio de aceptación

- `/cuaderno/feed.xml` sigue siendo RSS 2.0 válido y parseable por lectores
  normales (no rompas el consumo por máquina por mejorar el consumo humano).
- Abrir la URL en un navegador muestra una vista legible en vez de XML crudo.
- `python scripts/build-feed.py --check` sigue en verde.

---

## D.4 — `premios.html` es la única página sin migrar el Speculation Rules (prioridad alta, cambio trivial)

### El problema

El resto del sitio ya migró de `prerender` de Samuel/Noveris a `prefetch`
conservador de Manecillas/Libros (dossier: hallazgo C-055). `premios.html`
se quedó fuera de esa migración.

Estado actual de `premios.html` (líneas 29-36):

```html
<script type="speculationrules">
{
  "prerender": [{
    "urls": ["/libros/samuel-entre-mundos/", "/universo/noveris/"],
    "eagerness": "moderate"
  }]
}
</script>
```

Patrón ya aplicado en el resto del sitio, por ejemplo `autor.html` (líneas
32-42):

```html
<script type="speculationrules">
{
  "prefetch": [
    {
      "source": "list",
      "urls": [
        "/las-manecillas-del-recuerdo/",
        "/libros/"
      ],
      "eagerness": "moderate"
    }
  ]
}
</script>
```

### Qué hacer

Sustituye el bloque de `premios.html` por el mismo patrón `prefetch` +
`source: "list"` que usa `autor.html`, con las URLs `/las-manecillas-del-recuerdo/`
y `/libros/` (las mismas que el resto del sitio, salvo que el contenido de
`premios.html` justifique otras URLs más relevantes — revisa el contenido de
la página antes de copiar sin pensar).

### Criterio de aceptación

- `premios.html` ya no contiene `"prerender"`.
- El bloque `speculationrules` de `premios.html` es idéntico en estructura al
  del resto de páginas migradas (`autor.html` como referencia).
- HTML sigue siendo válido (revisa con el validador que ya usa el CI del
  repo si aplica).

---

## Reglas de la casa

1. No se toca `main`.
2. No inventes fechas, datos ni contenido — D.1 solo puede mostrar fechas que
   ya existan en el JSON-LD real de cada página.
3. Si añades un checker nuevo a CI, rómpelo a propósito primero (verifícalo
   en rojo con un caso malo), luego corrige, y dilo en la PR.
4. No debilites `build-feed.py --check` ni ningún test existente para que
   pase D.3.

## Test plan

- [ ] D.1: `check-article-dates.py --check` en verde, wireado en CI, probado en rojo primero
- [ ] D.4: `premios.html` sin `prerender`, patrón idéntico a `autor.html`
- [ ] D.2/D.3 (si se abordan): evidencia de que no rompen nada existente
- [ ] Sub-tareas no abordadas, marcadas explícitamente como "fuera de esta PR" en la descripción
