# A.2 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #151  
Decisión operativa: **READY_NO_CODE · ALREADY_COVERED**

## Decisión cerrada

No se crean nuevas “pillar pages” para Samuel, Las manecillas del recuerdo o Noveris.

La jerarquía editorial canónica ya está modelada de forma explícita en `data/content-registry.json` y protegida por QA:

- `works-hub` → `/libros/` como destino primario de Obras;
- `work-manecillas` y `work-samuel` como hijos públicos/indexables de `works-hub`;
- `samuel-noveris` como recurso contextual de Samuel;
- `notebook-hub` → `/cuaderno/` y `notebook-topics` → `/cuaderno/temas/`;
- `recommendations-hub` bajo Cuaderno;
- relaciones `parentId`, `hubId`, `discoverability` y `relatedIds` canónicas.

`check-navigation-coverage.py` y `check-global-discoverability.py` ya verifican que la arquitectura no se rompa: registry, sitemap, navegación, Obras, enlaces directos y exposición pública deben mantenerse coherentes.

## Revalidación con información oficial actual

### Google · estructura técnica clara para Search e IA

Fuente primaria:
https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

La guía vigente insiste en una estructura técnica clara, contenido rastreable y útil y fundamentos SEO convencionales. No prescribe una página pilar adicional por entidad ni una arquitectura SEO distinta para las funciones generativas.

### Google · enlaces internos

Fuente primaria:
https://developers.google.com/search/docs/crawling-indexing/links-crawlable

Google recomienda enlaces internos rastreables y contextuales hacia las páginas importantes. La arquitectura actual lo resuelve mediante hubs canónicos, footer, mapa del sitio y navegación contextual. No existe un número mágico de enlaces ni una exigencia de duplicar hubs.

### Google · Discover 2026

Fuente primaria:
https://developers.google.com/search/blog/2026/02/discover-core-update

La actualización reconoce experiencia tema por tema. Esto favorece que cada hub represente con claridad su territorio editorial; no justifica crear varias páginas que compitan por representar la misma obra/universo.

## Evidencia del repo actual

`check-navigation-coverage.py` protege, entre otros contratos:

- `works-hub` debe seguir siendo `/libros/`, público y `primary`;
- Manecillas y Samuel deben seguir siendo obras públicas, `secondary`, hijas de `works-hub`, indexables y presentes en sitemap;
- `/libros/` debe enlazar directamente a ambas obras desde el contenido principal;
- el footer debe mantener acceso canónico a ambas;
- las referencias de navegación deben resolver a IDs públicos del registry;
- `parentId`, `hubId` y `relatedIds` deben resolver a IDs existentes.

`check-global-discoverability.py` añade paridad registry↔sitemap↔HTML público y comprobaciones de navegación/territorios.

La función que A.2 proponía construir está, por tanto, implementada y protegida por regresión.

## Alternativas descartadas definitivamente

1. **Pillar paralelo para Manecillas o Samuel** — dividiría señales y navegación entre la ficha canónica y una segunda URL sin intención distinta.
2. **Pillar adicional para Noveris** — `/universo/noveris/` ya es la superficie canónica.
3. **Duplicar `/libros/` como “hub SEO”** — `/libros/` ya cumple la función humana y técnica.
4. **Promover cada obra a territorio principal de Explorar** — contradice el contrato actual: Obras es el territorio; cada libro es contenido dentro de él.
5. **Crear hubs por keyword en lugar de entidad/intención** — aumenta canibalización y mantenimiento sin necesidad demostrada.

## Único trigger de reapertura

Solo se modifica A.2 si una investigación de usuarios o datos reales demuestra que un hub canónico existente no permite encontrar/comprender una obra o universo. La corrección deberá hacerse **sobre el hub actual o sus enlaces**, no creando una segunda URL equivalente.

## Definition of Done final

- [x] jerarquía canónica revalidada contra `main`;
- [x] QA de navegación/discoverability revalidado;
- [x] fuentes Google 2026 contrastadas;
- [x] ausencia de requisito oficial de pillar pages confirmada;
- [x] duplicaciones plausibles descartadas;
- [x] no existe trabajo de runtime neto.

**Conclusión:** A.2 está terminada. La arquitectura actual debe preservarse; añadir otro hub sería una regresión, no una mejora.
