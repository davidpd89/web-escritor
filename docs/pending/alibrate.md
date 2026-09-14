# ALIBRATE — presencia lectora en español

Fecha de revisión: 2026-09-07

Estado: `DOMAIN_NO_LONGER_THE_SERVICE · NOT_ACTIONABLE · NO_GO`

## Hallazgo (2026-09-08) — el dominio ya no es Alibrate

`alibrate.com` **ya no aloja la plataforma de lectura investigada** en
este documento. Hoy el dominio redirige a un sitio de afiliación de
casinos de criptomonedas ("Crypto Casinos en España 2025 — Mejores
Casinos de Bitcoin", con fecha de "última actualización" del 16 de
septiembre de 2025), sin ninguna relación con libros ni lectura.

Lo más probable: la plataforma original cerró o dejó caducar el dominio
en algún momento del último año, y alguien lo registró de nuevo para un
sitio de afiliados sin relación. No se ha localizado en esta sesión un
dominio alternativo donde la comunidad Alibrate original siga activa.

**No hay nada que hacer aquí.** Cerrando como `NO_GO`: la plataforma
investigada ya no existe en la forma descrita por este documento. Si en
el futuro reaparece bajo otro dominio, habría que volver a evaluarla
desde cero, no reutilizar los datos canónicos preparados aquí sin
verificar primero que el nuevo sitio es genuinamente el mismo servicio.

## Objetivo

Aprovechar ALIBRATE como superficie gratuita de descubrimiento entre lectores hispanohablantes, manteniendo fichas correctas de David Porto Díaz y sus libros sin tratar la plataforma como autoridad bibliográfica primaria.

## Valor real

ALIBRATE declara actualmente una comunidad de más de 2 millones de lectores y acceso gratuito. Permite:
- buscar libros y autores;
- bibliotecas personales;
- reseñas;
- recomendaciones;
- listas;
- rankings;
- categorías específicas como Literatura Juvenil y Ciencia Ficción y Fantasía.

Fuentes actuales:
- https://www.alibrate.com/acerca-de-alibrate
- https://www.alibrate.com/buscar
- https://www.alibrate.com/rankings
- https://www.alibrate.com/terminos-y-condiciones

## Guardrail de calidad

Las fichas son comunitarias y pueden contener errores. ALIBRATE no debe usarse para corregir nuestra web, ISBN, DILVE o Wikidata. El flujo correcto es llevar datos canónicos verificados hacia ALIBRATE.

## Datos preparados

- David Porto Díaz
- Samuel entre mundos — ISBN 9791387659776 — Libros Indie — 2025
- Las manecillas del recuerdo, papel — ISBN 9798905149351 — Monza Ediciones — 2026-09-03
- Las manecillas del recuerdo, ebook — ISBN 9798906781925 — Monza Ediciones — 2026-08-12

No propagar 422/412 páginas de Samuel ni 272/266 de Manecillas hasta cerrar #429/#428/#404.

## Procedimiento Claude

1. Buscar autor, títulos e ISBN exactos.
2. Guardar URLs existentes y comprobar autoría, portada, editorial, fecha, ISBN, formato y género.
3. Si falta una ficha y la plataforma permite aportes de usuarios, proponerla con los datos anteriores.
4. Revisar duplicados y no crear una segunda obra solo por existir papel/ebook si el modelo de ALIBRATE agrupa formatos.
5. Crear perfil de usuario solo si facilita gestión o participación genuina.
6. No auto-reseñar ni auto-calificar para aumentar ranking.
7. No hacer spam en comunidad/listas/publicaciones.
8. Si existe una ficha de autor pública, estable e inequívoca, valorar `Person.sameAs`.
9. Usar `Book.sameAs` solo para fichas que representen de forma inequívoca la obra correcta.

## Prioridad

`P1/P2`: por detrás de Amazon Author Central, Goodreads, Wikidata, BNE, ISNI, VIAF y Open Library, pero útil por su audiencia lectora hispanohablante y mucho más relevante que directorios genéricos.

## Criterio de cierre

`ACCOUNT_IF_NEEDED · AUTHOR_AUDITED · SAMUEL_AUDITED · MANECILLAS_AUDITED · METADATA_CORRECT_OR_SUBMITTED · DUPLICATES_REVIEWED · NO_SELF_RATING · NO_PAID_FEATURES`
