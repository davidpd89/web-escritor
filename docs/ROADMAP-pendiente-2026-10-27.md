# Roadmap de lo que falta (27/10/2026)

Estado tras cerrar las PRs ≥500. Lo que sigue **no está en ninguna PR abierta**: es trabajo nuevo.
Orden propuesto: de lo más barato y visible a lo más grande.

## Comprobado en `main`

| Área | Estado real |
|---|---|
| Atlas literario | Existen constructor (`scripts/build-atlas-literario.py`), contrato (`scripts/check_atlas_release_contract.py`) y datos (`data/atlas-literario.json`), pero los 12 artículos están en `planned`: **0 publicados**. La salida va a `dist/atlas-literario`, no a la raíz. No está en `data/navigation.json` ni en `sitemap.xml`. |
| Redes sociales | `/redes-sociales/` es pública e indexable y está en el sitemap, pero **no tiene entrada en el menú ni en el pie** (`data/navigation.json` no la menciona). Las investigaciones por red (Threads, Meta, TikTok, X, Pinterest, Reddit, LinkedIn/YouTube) son solo documentos. |
| Donaciones | Solo hay una vista previa no publicable en `lab/donaciones-preview/` y validadores offline de PayPal/Stripe. No hay página pública ni enlace. |
| Libros | El catálogo tiene 83 libros publicados y el bot diario sigue añadiendo (`max_new_books: 5`, Planeta y Penguin como fuentes, valoraciones, biografías de Wikipedia). Los precios editoriales (`scripts/reading_free_prices.py`) están sin conectar a la web a propósito. |
| Rendimiento | Hay presupuestos (`data/performance-budgets.json`) y un gate; no hay trabajo activo de mejora. |

## Siguientes PRs, por orden

1. **Menú y pie: Redes sociales** (pequeña). Añadir la página a `data/navigation.json` (pie, bloque «Información») y regenerar el shell con `build-site-shell.py`.
2. **Atlas literario MVP** (media).
   - Pasar a `published` 3–4 artículos con contenido real (una categoría completa).
   - Publicar la salida en `/atlas-literario/` en la raíz.
   - Entrada en el menú «Leer y recursos» y en el sitemap.
   - Pasar `check_atlas_release_contract.py` en CI.
   - Mapa interactivo después, no antes.
3. **Donaciones `/apoyar/`** (media). Decisión de ubicación pendiente: propuesta, enlace discreto en el pie y en la página de cada obra. Requiere que el titular compruebe el receptor (PayPal/Stripe) antes de publicar; sin eso no se enlaza.
4. **Libros que se llenan solos** (media).
   - Subir el techo de altas por día cuando las últimas semanas salgan sin errores.
   - Conectar un tercer origen de novedades (hoy: Penguin y Planeta).
   - Activar los precios editoriales cuando el piloto en vivo confirme el marcado de la tienda.
5. **Fichas de libro** (media). Mejores bloques de comprar/valoraciones/autor, tras activar el punto 4.
6. **Rendimiento** (media). Auditoría de peso por plantilla (Lighthouse/CrUX) y reducción de CSS/JS no usado en las páginas más pesadas; el gate existente impide regresiones.

## Decisiones ya tomadas

- Los enlaces de compra **llevan afiliado**. El modo `publisher_only` de #683 no se conecta.
- El popup de newsletter no reaparece a quien ya pidió la suscripción (`nl-requested`, 180 días).
- Los bots y automatismos no se tocan: catálogo diario, radar, qa-gpt.

## Solo con acceso local o autenticado (lo hace Claude de escritorio o el titular)

- Las 15 PRs de seguimiento #400–#466 y los runbooks de `docs/pending/`.
- Borrado de ramas remotas ya fusionadas o muertas (`git push origin --delete`), que la nube tiene bloqueado.
- Comprobar el receptor de pagos antes del punto 3.
