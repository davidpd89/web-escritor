# 40 — INVENTARIO DE RUTAS Y FAMILIAS V1

Baseline: `implementacion-web-2026@5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.
Fuente pública actual: 55 URLs de `sitemap.xml`.
Operativas fuera de sitemap verificadas: `/404.html`, `/privacidad.html`, `/aviso-legal.html`.
Ruta adicional autorizada para construir en staging: `/donde-empieza-la-jaula/`.

Total controlado por el paquete: **59 entradas** = 55 sitemap + 3 operativas + 1 autorizada aún fuera de sitemap.

La fuente máquina es `data/route-inventory.json`; este documento define la política.

## Reglas

- Cada una de las 55 rutas indexadas tiene `family`, scaffold y `designStatus: IMPLEMENT_READY`.
- Samuel usa `book-samuel.html`, no el scaffold de Manecillas.
- Premios usa `awards.html`, no Prensa.
- 404, Privacidad y Aviso legal conservan semántica/robots aunque compartan familia secundaria.
- Jaula usa `book-jaula.html` + `data/jaula-preservation.json`; estado `AUTHORIZED_FOR_STAGING`, `designStatus: IMPLEMENT_READY`, `productionAllowed: false`.
- Que el contenido esté autorizado NO significa que la ruta exista en la rama: `branch-baseline.json` sigue declarando `jaulaPublicRouteExists: false` hasta que se implemente y audite.
- Jaula no entra en sitemap ni se enlaza desde producción hasta que staging responda 200, el capítulo coincida con el contrato fuente, SEO/schema pasen y el sistema de navegación vigente le dé una vía de descubrimiento.
- Si cambia `sitemap.xml`, el inventario deja de ser válido hasta reauditar el delta.

## SINCRONIZACIÓN CON EL REGISTRO REAL — 21/08/2026

La rama `implementacion-web-2026` ya dispone de `data/content-registry.json` + `data/navigation.json` + `scripts/check-navigation-coverage.py`. Desde ahora:

- `data/route-inventory.json` de este paquete = **mapa de cobertura de diseño/scaffold**;
- `data/content-registry.json` del repositorio = **fuente canónica de existencia/estado/discoverability**;
- `data/navigation.json` del repositorio = **fuente canónica de superficies navegables**;
- `sitemap.xml` = superficie indexable pública que debe coincidir con las entradas `status:public` + `sitemap:true`.

No mantener estas cuatro capas a mano de forma independiente. Toda migración de ruta debe terminar con `python scripts/check-navigation-coverage.py` en verde.

Para Jaula, el inventario de diseño ya la conoce, pero el registry real no debe conocerla hasta que exista el fichero de ruta en staging. En ese momento entra como `status:noindex`; navegación y sitemap continúan sin ella hasta promoción explícita.
