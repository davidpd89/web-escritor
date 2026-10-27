# fuzzysearch · búsqueda ligera para facetas (archivado literal 21/10/2026)

**Hija [#668](https://github.com/davidpd89/web-escritor/pull/668)**. [Upstream](https://github.com/bevacqua/fuzzysearch) MIT. El original es CommonJS y su código JS **ocupa 479 bytes** según contenido obtenido de GitHub (no tamaño comprimido medido); hace *subsequence matching*, **NO corrige errores ortográficos ni usa distancia Levenshtein**.

- `research/vendor/fuzzysearch/index.js`: copiado **literal** de [index.js](https://github.com/bevacqua/fuzzysearch/blob/master/index.js), Git blob `9efe386828fb977113fe2611cf53a064417a1a91`.
- `research/vendor/fuzzysearch/LICENSE.upstream`: copiado **literal** de [LICENSE](https://github.com/bevacqua/fuzzysearch/blob/master/LICENSE), Git blob `566d0933ae925f69c02129a024ad071d47800d52`.
- Se mantiene sin import en web; habría que convertir el export CommonJS/encapsularlo para un módulo ES moderno.
- Uso potencial tras QA: permitir `bbltc` coincidir con `biblioteca` o búsquedas con letras salteadas dentro de **un shard pequeño por destino**, normalizando acentos y mayúsculas previamente.
- **No usar esta función para buscar TODO el planeta en cliente**. Pagefind existente debe seguir siendo la entrada global de texto; esta librería opcional solo si aporta resultados a los filtros locales y su tamaño real y accesibilidad superan `String.includes` actual.
- No interpretar fuzzy textual como equivalencia de entidades para merge editorial: autor/libro/POI con nombre parecido no es identidad aprobada.

**Estado**: código exacto y licencia preservada, sin Action, sin carga en bundle ni prueba ejecutada.
