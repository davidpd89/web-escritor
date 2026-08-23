# AE — Diseño final · Connection System V1

Fuente de diseño: `32 — CONNECTION SYSTEM V1 — RUTAS CONTEXTUALES · CROSS-LINKS · CONTINUIDAD ENTRE TERRITORIOS · SALIDAS`.
Base auditada: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

## Hallazgo real

`data/content-registry.json` ya reserva `relatedIds` como capacidad de datos, pero no existe un owner abierto que cierre de extremo a extremo:

- qué relación editorial existe;
- de qué tipo es;
- cómo se valida;
- qué páginas la consumen;
- cómo se representa sin cards genéricas;
- cómo se evita convertir el sistema en backlinks SEO artificiales.

Esta PR no crea un recomendador algorítmico. Define un grafo **manual, explicable y curado**.

## AE.1 — Modelo mínimo

Mantener el registro existente como autoridad preferida. Extenderlo solo lo necesario para expresar relaciones explícitas.

Capacidades mínimas:

- `relatedIds`: IDs destino curados;
- `relationshipType`: relación explicable como `about`, `excerptOf`, `mentions`, `eventFor`, `guideFor`, `sameSeries`, `writtenBy` o equivalente estable;
- sin inferencias opacas ni personalización;
- ninguna relación a contenido gated/noindex que no sea elegible para esa superficie pública.

Si `relationshipType` necesita estructura por destino, usar una forma que evite listas paralelas frágiles, por ejemplo objetos de relación; no mantener dos arrays cuyo orden deba coincidir.

## AE.2 — Relaciones admitidas

- book → fragment;
- book → article realmente relacionado;
- book → press/event;
- book → author;
- article → book cuando sea contexto real;
- article → article por serie/tema explícito;
- article → tool cuando ayuda a ejecutar lo explicado;
- tool → guide/article o hasta 2 herramientas por tarea real;
- press → book/author/event tratado;
- event → obra/autor/prensa/crónica real.

No:

- «otros usuarios vieron»;
- recomendación personalizada;
- coincidencia automática por tags;
- relación por densidad SEO;
- relación por ciudad/fecha sin vínculo editorial.

## AE.3 — Primitivas visibles

La visualización consume #89 y las familias correspondientes. Solo cinco primitivas:

A. jerarquía: breadcrumb/back;
B. contexto: «Relacionado con…» dentro del flujo;
C. continuación editorial: 1–3 destinos;
D. continuidad visual: hairline/costura/metadata;
E. View Transition únicamente cuando existe pareja semántica real.

Componentes a soportar:

- `related route`: label + título enlazado + hairline + subcopy opcional;
- `next editorial`: cierre tipográfico fuerte para artículo/fragmento;
- `series`: solo si existe serie real;
- context chip como pill queda rechazado: resolver con texto/hairline.

## AE.4 — Cantidad y vacío

- normalmente 1–3 destinos por región;
- si existen más relaciones válidas, seleccionar las más útiles y enlazar al índice/archivo;
- 0 relaciones = módulo completo ausente, sin heading/hairline/padding huérfanos;
- 1 relación puede ganar escala sin inventar otra variante visual;
- nunca carrusel móvil.

## AE.5 — Flujos piloto

Probar antes de extensión global:

1. Home → Manecillas → fragmento → Manecillas;
2. Home → Cuaderno → artículo relacionado con Manecillas → Manecillas;
3. entrada Google → artículo → herramienta → resultado → guía;
4. entrada Google → Manecillas → prensa → medio externo;
5. Home → Autor → Samuel;
6. Home → evento → obra relacionada.

Cada flujo debe mantener orientación y navegador/back normal.

## AE.6 — SEO y semántica

- enlaces HTML reales, no injected backlinks opacos;
- anchor text natural/descriptivo;
- no cambiar canonical/URL;
- no ocultar crosslinks esenciales en JS-only widgets;
- regla editorial: «¿mantendríamos este enlace si Google no existiera?»; si la respuesta es no, se revisa/elimina.

## AE.7 — Analítica

Solo si #63 ya define telemetría adecuada:

- `related_link_click` con source/destination/relationship type;
- `series_next_click`;
- `tool_guide_click`.

No trackear hover ni usar datos para personalización opaca V1.

## Coordinación

- #68: jerarquía/navigation global.
- #89: primitivas visuales, redlines, microcopy y motion.
- #85: relaciones de libros/fragmentos/prensa.
- #86: artículos/series/next editorial.
- #87: Autor/Prensa/Eventos.
- #88: herramientas→guías/utilidades.
- #76: relación estructurada Book↔fragmentos en JSON-LD; AE no duplica schema.
- #63: analítica, si se instrumenta.
- #78: edge states/mobile.
- #84: certificación final.

## No hacer

- no crear motor de recomendaciones;
- no poblar relaciones inventando vínculos;
- no relacionar contenido gated para rellenar huecos;
- no mostrar todas las relaciones del grafo;
- no crear cards repetidas;
- no auto-open related ni overlay «antes de irte»;
- no construir relaciones solo para SEO.

## Definition of Done

- autoridad de relaciones única y validable;
- tipos de relación explícitos y consistentes;
- cada ID destino existe y es elegible en su contexto;
- 0/1/3 relaciones probadas;
- pilotos A–F sin callejones sin salida;
- relaciones renderizadas como HTML normal y con propósito comprensible;
- mobile vertical, sin carruseles;
- related nunca supera en peso al contenido principal;
- no duplicación visible del mismo destino en CTA + related + sticky + popup;
- #84 puede evaluar continuidad sin que la web parezca grafo o SEO visible.

PR DRAFT. No tocar `main`, no deploy, no auto-merge.