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

## Estado a 28/10/2026

| Tarea | Estado |
|---|---|
| Redes sociales en el pie | Hecho y desplegado. |
| Atlas literario | Publicado: hub + 10 fichas (4 destinos, 4 lugares, 2 rutas) en menú «Libros recomendados», pie, mapa del sitio, sitemap y buscador. Contrato de publicación en CI. Revisión editorial del titular pendiente. |
| Donaciones `/apoyar/` | Preparado, **no activado**: `python scripts/build-support-page.py --paypal-url ...` (ver `docs/donaciones/05-activar-apoyar.md`). Falta el enlace de PayPal Business del titular. |
| Bot diario de libros | Arreglado el fallo más frecuente (el PR del bot quedaba en conflicto si `main` avanzaba durante su CI): regenera desde `main` y reintenta una vez. |
| Rendimiento | Imágenes de Samuel y Autor a su tamaño real (−320 KiB). La portada (vídeo de intro y CSS en varios archivos) queda sin tocar por riesgo en Safari. |

## Lo que sigue

1. **Atlas**: más fichas (nuevas ciudades, bibliotecas y librerías) y, más adelante, mapa interactivo. Cada ficha con etiqueta de certeza y fuentes.
2. **Libros**: una tercera fuente de novedades (Anagrama tiene fichas con ISBN, PVP, páginas y fecha) exige decidir uso de portadas y leer encuadernación; precios editoriales cuando el piloto en vivo confirme el marcado de la tienda.
3. **Rendimiento**: CSS crítico y menos peticiones en portada, con baseline visual regenerado.
4. **Donaciones**: activar `/apoyar/` con el enlace de PayPal y enlaces contextuales discretos (después de resultados de herramientas).

## Decisiones ya tomadas

- Los enlaces de compra **llevan afiliado**. El modo `publisher_only` de #683 no se conecta.
- El popup de newsletter no reaparece a quien ya pidió la suscripción (`nl-requested`, 180 días).
- Los bots y automatismos no se tocan: catálogo diario, radar, qa-gpt.

## Solo con acceso local o autenticado (lo hace Claude de escritorio o el titular)

- Las 15 PRs de seguimiento #400–#466 y los runbooks de `docs/pending/`.
- Borrado de ramas remotas ya fusionadas o muertas (`git push origin --delete`), que la nube tiene bloqueado.
- Comprobar el receptor de pagos antes del punto 3.
