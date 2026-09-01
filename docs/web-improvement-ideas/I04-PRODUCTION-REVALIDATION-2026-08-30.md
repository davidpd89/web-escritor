# I.4 · Revalidación de producción — correlación contenido/newsletter

Fecha: 2026-08-30  
Base auditada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`

## Veredicto

`READY_NO_CODE · SOURCE_CONTRACT_ACTIVE · MANUAL_AGGREGATION_FIRST · NO_IDENTITY_GRAPH`

## Evidencia directa

- `cloudflare-worker-subscribe.js` acepta un `source` acotado por `SOURCE_MAP` y construye server-side el atributo Brevo `SOURCE`; el cliente no puede enviar atributos arbitrarios.
- `script.js` limita el contrato del navegador a `{ email, source, result?, website? }` y documenta los mismos labels de origen.
- El resultado `NOVERIS` solo se conserva para el quiz y está limitado a un enum cerrado; no es texto libre.
- `docs/brevo/04-CAMPANAS-AUTOMATIZACIONES-Y-CONTENIDO.md` ya define una taxonomía UTM estable (`utm_source=brevo`, `utm_medium=email`, `utm_campaign`, `utm_content` cuando aporta análisis).

## Qué significa realmente SOURCE

`SOURCE` identifica la superficie de captación (`home`, `fragmento`, `manecillas`, `cuaderno`, etc.). No representa el historial de navegación de una persona y no debe convertirse en uno.

La correlación útil puede empezar con exports/CSV agregados por semana/campaña/surface y comparar:

- visitas o acciones agregadas por contenido/campaña;
- altas confirmadas agrupadas por `SOURCE`;
- resultados de campaña agrupados mediante UTMs.

No hace falta añadir un identificador cross-page, joins por email, GA4, Clarity, Brevo Tracker o un event ledger para responder esta pregunta.

## Contrato operativo

1. Ejecutar primero un periodo manual acotado cuando exista volumen suficiente para que la comparación tenga sentido.
2. Mantener granularidad agregada; no publicar celdas de tamaño muy pequeño ni reconstruir comportamiento individual.
3. Registrar periodo, campaña/contenido, fuente, métrica y limitaciones de atribución.
4. No inferir causalidad a partir de mera correlación.
5. Automatizar solo si varias revisiones manuales demuestran trabajo repetitivo y una decisión real dependiente de esos datos.

## Lo que NO se implementa

- identity graph;
- user journey por email;
- nuevo tracker client-side;
- dashboard paralelo;
- nuevo atributo personal en Brevo;
- almacenamiento de query strings completos.

## Cierre

La infraestructura mínima necesaria ya existe. I.4 es una tarea de análisis agregado/manual, no una feature de runtime. La siguiente evidencia válida debe ser un experimento real y documentado; hasta entonces, añadir código aumentaría datos y complejidad sin mejorar la decisión.