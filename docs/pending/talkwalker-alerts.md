# Talkwalker Alerts — monitorización gratuita de menciones

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · FREE_SERVICE_CONFIRMED · BOOLEAN_AND_RSS_AVAILABLE · READY_FOR_EXECUTION`

## Objetivo

Configurar Talkwalker Alerts para detectar menciones nuevas de David Porto Díaz, sus libros y `davidportodiaz.com`, y convertir solo los hallazgos útiles en:

- correcciones de metadatos;
- entradas de prensa;
- oportunidades de backlink natural;
- descubrimiento de reseñas/entrevistas;
- detección de copias o atribuciones incorrectas.

No usarlo como una suite de social listening ni pagar por funcionalidades premium.

## Estado actual del servicio

Talkwalker mantiene en 2026 **Talkwalker Alerts gratuito**.

La página oficial indica actualmente:

- cobertura de blogs, foros, páginas web y menciones sociales;
- cobertura de conversaciones de X/Twitter;
- operadores booleanos;
- filtros por tipo de fuente;
- entrega por email;
- entrega mediante RSS;
- integración con Slack;
- uso gratuito independiente de la suite de Social Listening.

Fuente:

- https://www.talkwalker.com/es/alerts

## Por qué mantenerlo aunque tengamos Google Alerts

No sustituye Google Alerts: lo complementa.

Talkwalker puede cubrir menciones sociales/web que Google Alerts no entregue de la misma manera, y el soporte de booleanos permite reducir ruido.

No duplicar manualmente toda mención recibida por ambos sistemas. El objetivo es cobertura, no generar dos tareas por el mismo enlace.

## Alertas recomendadas

### P0 — identidad

`"David Porto Díaz"`

Motivo: entrevistas, perfiles, premios, autoría, errores de nombre.

Añadir una segunda variante solo si existe señal real:

`"David Porto Diaz"`

No alertar `David Porto` sin más: demasiado ambiguo.

### P0 — libro principal

`"Las manecillas del recuerdo"`

Debe detectar reseñas, catálogos, menciones editoriales, prensa y conversaciones.

### P0 — Samuel

`"Samuel entre mundos"`

### P0 — dominio

`"davidportodiaz.com"`

Sirve para backlinks/menciones del sitio.

### P1 — identificadores de Manecillas

Crear solo si generan resultados:

- `"9798905149351"`
- `"9798906781925"`
- `"B0HHY9MYLM"`
- `"B0HHM71F46"`

Son útiles para descubrir nuevas fichas comerciales/bibliográficas, pero eliminarlos si solo generan Amazon/duplicados sin señal.

### P1 — Samuel ISBN

`"9791387659776"`

Útil para nuevas librerías, catálogos y bibliotecas.

## Configuración recomendada

Empezar con:

- entrega: **email**;
- frecuencia: una vez al día si la UI actual lo permite;
- idioma: español cuando reduzca ruido sin ocultar fichas internacionales;
- fuentes: todas al principio;
- después separar web/social solo si el volumen lo exige.

RSS es útil si más adelante queremos centralizar alertas, pero no añadir infraestructura ahora solo porque existe.

## Booleanos / reducción de ruido

Si una consulta produce homónimos o ruido, usar booleanos en lugar de borrar la alerta útil.

Ejemplo conceptual:

`"David Porto Díaz" OR "David Porto Diaz"`

Para libro+autor si aparece ruido por títulos homónimos:

`"Las manecillas del recuerdo" AND ("David Porto" OR "Porto Díaz")`

No hacer filtros tan estrictos que oculten una mención real sin autor explícito.

## Proceso al recibir una mención

Clasificar cada resultado:

- `NEW_BACKLINK`
- `PRESS_OR_INTERVIEW`
- `REVIEW`
- `BOOK_CATALOG_RECORD`
- `AUTHOR_PROFILE`
- `METADATA_ERROR`
- `COPY_OR_ATTRIBUTION_ISSUE`
- `SOCIAL_MENTION`
- `DUPLICATE_NO_ACTION`
- `SPAM`

### Si es backlink/prensa

- comprobar calidad/dominio;
- guardar URL;
- añadir a prensa/referencias solo si realmente procede;
- no pedir cambios solo para manipular anchor text.

### Si es ficha de libro

- comparar datos con owner canónico;
- si hay error, corregir upstream cuando sea posible;
- coordinar con las PR de plataforma correspondiente.

### Si es reseña

- no copiar texto sin permiso/licencia;
- guardar URL;
- reutilizar solo citas breves cuando legalmente proceda y aporten algo.

### Si es mención social

- interactuar solo cuando sea natural;
- no convertir cualquier mención en pitch de venta.

## Tracking de utilidad

Después de 30 días registrar:

- alertas recibidas;
- resultados únicos útiles;
- backlinks descubiertos;
- errores corregidos;
- perfiles/fichas nuevas;
- reseñas/prensa detectadas;
- ratio ruido/señal.

Si una alerta produce cero valor o ruido constante, eliminarla.

## Relación con otras PR

- #460 Google Alerts — cobertura complementaria.
- #394 backlinks — incorporar enlaces de calidad descubiertos.
- #410 retailers — fichas comerciales nuevas.
- #396/#397/#398 — identidad/entidades.
- #428/#429 — metadata editorial upstream.

## Guardrails

- cero pago;
- no contratar Talkwalker Social Listening;
- no crear una automatización compleja todavía;
- no guardar datos personales innecesarios;
- no responder a todo;
- no considerar un backlink bueno solo porque existe.

## Criterio de cierre

`ALERTS_CREATED · BOOLEAN_QUERIES_TUNED · DELIVERY_VERIFIED · FIRST_30_DAY_REVIEW_PLANNED · RESPONSE_CLASSIFICATION_DOCUMENTED · ZERO_PAID_FEATURES`
