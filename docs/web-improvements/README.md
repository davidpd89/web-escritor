# Mejoras web 2026 — autoridad de decisión

Esta carpeta sustituye el backlog abierto de PR #135 por una autoridad compacta y revalidada.

## Qué ocurrió con PR #135

La PR original terminó cerrada/reset y hoy parece vacía, pero Git conserva su investigación extensa en el antiguo HEAD `8e72321d047c0445c5ac411ebe242af8a0386929`. Aquella rama acumuló más de cien commits y muchas pasadas intermedias.

**No se recuperan esas pasadas.** El proyecto ya sufrió exceso de documentación histórica y la investigación intermedia no debe volver a ser estado activo. Se rescatan únicamente las conclusiones durables que sobrevivieron a:

1. contraste con `main@c70852eeaac9fcdc0e73811687e62ab731f352a9`;
2. segunda revisión de las 108 ideas;
3. fuentes primarias actuales a 2026-08-28;
4. revisión de duplicados con lo que el repo ya implementa;
5. gates de seguridad/privacidad/derechos/coste;
6. tests machine-readable.

## Archivos

- `01-FINAL-AUTHORITY-108.md`: decisión humana 108/108.
- `02-PRIMARY-SOURCES-2026-08-28.md`: fuentes primarias y correcciones de vigencia.
- `03-IMPLEMENTATION-PLAN.md`: pasos, archivos, snippets y DoD de lo que sí merece ejecución.
- `04-INTEGRATIONS-TOOLS-AND-REPOS.md`: herramientas/cuentas/repos evaluados con trigger y límites.
- `../../data/web-improvement-decisions-2026-08-28.json`: registry machine-readable.
- `../../data/web-improvement-execution-plan-2026-08-28.json`: solo IDs ejecutables sin trigger editorial.
- `../../tests/test-web-improvement-authority.py`: cobertura 108/108 y guardrails.

## Correcciones importantes respecto a pasadas antiguas

- `FAQPage` no se trata como mejora genérica de rich results.
- No se agregan ratings/reviews de Amazon/Goodreads/otros sitios en schema propio.
- `llms.txt` no es ranking signal especial y ya está cubierto en el sitio.
- `robots.txt` ya distingue crawlers/bots de IA relevantes; no duplicar trabajo.
- `feed.xml` es el feed real del repo; no `rss.xml`.
- Compresión se **mide live** mediante `Content-Encoding`; no se infiere de que el dominio esté en Cloudflare.
- Microsoft Clarity MCP **sigue activo en 2026**; se mantiene condicional por privacidad/hipótesis, no por inexistencia.
- Brevo Consent Groups no justifica por sí solo subir de plan; listas/segments son baseline.
- PWA shortcuts/offline ya existen; web push/badging no se añaden por checklist.
- `hreflang` espera páginas localizadas reales.
- Ahrefs Free/Screaming Frog son segunda opinión, no nuevas fuentes de verdad.

## Cómo debe usarlo Claude

1. Leer el registry antes de proponer cualquiera de las 108 ideas.
2. `REJECT`/`DEFER`: no crear código ni ticket salvo cambio explícito del trigger.
3. `ALREADY_COVERED`: buscar la implementación real y mejorarla, no duplicarla.
4. `PARTIAL_AUDIT`: medir antes de cambiar.
5. `CONDITIONAL`: documentar primero qué trigger se ha cumplido.
6. `EXTERNAL_OPERATION`: no ejecutar sin acceso/autorización y evidencia live.
7. `IMPLEMENT_NOW`/`IMPLEMENT_AFTER_CURRENT_DEBT`: seguir `03-IMPLEMENTATION-PLAN.md` y crear PR pequeña por capacidad, no una mega-PR de 30 features.

## Definition of Done de esta autoridad

- 108/108 IDs cubiertos y testeados.
- Fuentes primarias exactas para afirmaciones normativas/proveedor.
- Ninguna feature inventada por “tendencia”.
- Ningún coste/servicio externo activado desde esta documentación.
- Ninguna afirmación live sin observación live.
- Ningún hecho editorial/comercial inventado.
- Historial de investigación preservado en Git, pero no reintroducido en `docs/` activo.
