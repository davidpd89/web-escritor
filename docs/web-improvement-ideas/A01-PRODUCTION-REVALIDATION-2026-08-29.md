# A.1 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #150  
Decisión operativa: **READY_NO_CODE · ALREADY_COVERED**

## Decisión cerrada

No se implementa una segunda arquitectura de `pillar pages`, `topic clusters`, páginas por variación de keyword ni otro generador de hubs.

La necesidad legítima de A.1 ya está resuelta por la autoridad existente:

- `data/topic-collections.json` modela colecciones y series editoriales;
- `scripts/build-topic-collections.py` genera únicamente colecciones `ready`;
- `tests/test-topic-collections.py` protege URLs internas, duplicados, canonical, `noindex`, orden de series y salida reproducible;
- una colección `ready` exige al menos tres piezas reales;
- `como-construi-noveris` permanece correctamente en `draft` con dos piezas y declara expresamente que no se fabricará una tercera para cumplir el mínimo.

Por tanto, escribir más código para A.1 hoy sería duplicar una autoridad ya funcional.

## Revalidación con información oficial actual

### Google · guía de Search con IA generativa

Fuente primaria, consultada el 2026-08-29:
https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

La guía vigente de Google refuerza la decisión:

- SEO convencional sigue siendo la base de las funciones generativas;
- prioriza contenido único, útil, no genérico y basado en experiencia/conocimiento real;
- advierte expresamente contra crear contenido separado para cada posible variación de consulta o fan-out query;
- una gran cantidad de páginas no convierte el sitio en más relevante o de mayor calidad;
- no existe una receta especial de AEO/GEO que obligue a crear pillar pages.

### Google · Discover Core Update de febrero de 2026

Fuente primaria:
https://developers.google.com/search/blog/2026/02/discover-core-update

Google explica que sus sistemas pueden reconocer experiencia **tema por tema** incluso en sitios que cubren varias áreas. Esto favorece profundidad editorial real, pero no establece una estructura obligatoria de pillar/satellite ni un número de artículos por tema.

### Google · enlaces internos

Fuente primaria:
https://developers.google.com/search/docs/crawling-indexing/links-crawlable

Google recomienda que toda página importante tenga al menos un enlace interno rastreable y que los enlaces sean contextuales/descriptivos. También declara que no existe una cantidad ideal o mágica de enlaces por página.

El sistema actual de colecciones cumple esa necesidad sin añadir una taxonomía paralela.

## Evidencia de repo revalidada

### Colección publicada

`fantasia-de-portales`:

- `status=ready`;
- `mode=collection`;
- tres piezas con intención independiente;
- hub generado en `/cuaderno/temas/fantasia-de-portales/`.

### Serie deliberadamente no publicada

`como-construi-noveris`:

- `status=draft`;
- dos piezas;
- no se fuerza una tercera entrega.

Este comportamiento es exactamente el guardrail que A.1 necesita: **contenido sustancial primero; estructura después**.

## Alternativas descartadas definitivamente

1. **Otro builder de clusters** — duplicaría `build-topic-collections.py`.
2. **Una URL por keyword/query variant** — contradice la guía Google 2026 y aumenta riesgo de scaled/thin content y canibalización.
3. **Un “topical authority score” interno** — no existe una métrica Google equivalente y produciría falsa precisión.
4. **Forzar tres piezas para publicar una colección** — invierte el modelo editorial ya protegido por tests.
5. **Embellecer el sistema con más niveles de taxonomía** — no existe un problema de navegación o indexación demostrado que lo justifique.

## Único trigger de reapertura

A.1 solo vuelve a desarrollo si aparece evidencia nueva y concreta de que la autoridad actual no puede resolver una necesidad real, por ejemplo:

- una familia temática con al menos tres piezas independientes ya publicadas y una necesidad humana clara de agrupación;
- Search Console/Bing o investigación de usuarios demuestra que el hub existente no resuelve una intención importante;
- un defecto reproducible del builder/test actual impide discovery, canonicalización o navegación.

En cualquiera de esos casos se **extiende la autoridad existente**. No se crea un sistema paralelo.

## Definition of Done final

- [x] investigación histórica #135 preservada en la PR;
- [x] repo actual revalidado;
- [x] fuentes primarias 2026 revalidadas;
- [x] alternativas relevantes falsadas;
- [x] no existe gap de implementación actual;
- [x] decisión `NO CODE CHANGE` explícita y defendida;
- [x] trigger futuro objetivo y limitado.

**Conclusión:** A.1 está terminada. El mejor cambio de producción es no introducir ningún cambio de runtime.
