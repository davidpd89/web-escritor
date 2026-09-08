# Tracking — YouTube de autor

**Revisión:** 2026-09-08

**Estado:** `RESEARCHED · PUBLIC_CHANNEL_NOT_OBSERVED · NO_YOUTUBE_LINK_IN_REPO · CONDITIONAL_GO_WITH_REAL_VIDEO_ASSETS`

## Objetivo

Determinar si existe ya un canal oficial de David Porto Díaz y, solo si hay contenido real que justifique mantenerlo, convertirlo en una superficie pública coherente de identidad, entrevistas/presentaciones y descubrimiento hacia la web/libros.

No crear un canal vacío únicamente para obtener un perfil, backlink o `sameAs`.

## Valor potencial

YouTube puede aportar valor cuando hay vídeos reales porque permite:

- un handle/URL pública estable;
- nombre, descripción y branding del canal;
- hasta 14 enlaces de perfil, con el primero destacado;
- secciones de Home, vídeo destacado y tráiler;
- URLs clicables en descripciones/comentarios de vídeo largo cuando el canal tiene acceso a funciones avanzadas;
- descubrimiento adicional de entrevistas, presentaciones, lecturas o piezas audiovisuales existentes.

En cambio, un canal sin vídeos o con contenido creado solo por “tener YouTube” añade mantenimiento y una señal de identidad débil. Esta PR debe decidir por evidencia.

## Estado observado 2026-09-08

- No aparece `youtube.com` en el repo `main`.
- Las búsquedas públicas por `David Porto Díaz`, `Las manecillas del recuerdo` y `Samuel entre mundos` no han localizado un canal oficial inequívoco.
- Estado correcto: `PUBLIC_CHANNEL_NOT_OBSERVED`, no `ABSENT`.

Claude debe revisar la cuenta Google/YouTube autenticada antes de concluir que no existe canal.

## Modelo oficial actual

YouTube Studio permite actualmente personalizar:

- Home: tráiler, vídeo destacado y secciones;
- perfil: foto, banner, watermark, nombre, handle, descripción y enlaces;
- el handle genera una URL del tipo `youtube.com/@handle`;
- el perfil admite hasta 14 enlaces y el primero aparece destacado;
- los enlaces de perfil son clicables;
- URLs en descripciones/comentarios de vídeos largos pueden ser clicables con Advanced Features;
- URLs en descripciones y comentarios de Shorts **no son clicables**.

Fuentes oficiales:

- https://support.google.com/youtube/answer/3027950?hl=es
- https://support.google.com/youtube/answer/2657964?hl=es
- https://support.google.com/youtube/answer/13748639?hl=es
- https://support.google.com/youtube/answer/6180214?hl=es

## Filtro GO / NO-GO

### GO

Mantener/crear canal solo si se cumple al menos uno:

1. ya existe un canal legítimo con contenido de David; o
2. existen al menos **2 piezas de vídeo propias o con derechos de publicación claros** que puedan formar un canal útil; o
3. hay un evento/entrevista/presentación próxima confirmada que generará un pequeño catálogo inicial real.

Ejemplos válidos:

- entrevistas a David;
- presentaciones o firmas grabadas;
- lecturas autorizadas;
- vídeos editoriales/promocionales con derechos claros;
- charlas sobre escritura/worldbuilding si ya existen o están previstas.

### NO-GO

Si no existe canal ni inventario audiovisual razonable:

`NO_GO_NO_CONTENT_TRIGGER · NO_EMPTY_CHANNEL_CREATED`

No fabricar una estrategia semanal de vídeo para justificar la plataforma.

## Auditoría autenticada

1. Entrar en YouTube/YouTube Studio con la cuenta de Google que usaría David.
2. Comprobar si existe canal, incluso si no aparece en búsqueda pública.
3. Si existe:
   - guardar Channel ID;
   - guardar URL por handle si existe;
   - revisar nombre/handle;
   - revisar visibilidad;
   - listar vídeos públicos/no listados relevantes;
   - identificar duplicados/canales antiguos.
4. Si no existe, inventariar antes los vídeos disponibles y sus derechos.
5. Aplicar el filtro GO/NO-GO anterior.

No fijar handle en este documento porque debe capturarse de la cuenta real y comprobar disponibilidad.

## Configuración si hay GO

### Identidad

- Nombre: `David Porto Díaz`.
- Foto: retrato oficial coherente con web/prensa.
- Banner: usar sistema visual existente; no generar branding paralelo sin necesidad.
- Descripción: escritor, obras actuales y web oficial, factual y breve.
- Handle: el más cercano posible a la identidad canónica, pero solo registrar el que YouTube realmente permita.

### Enlaces de perfil

Prioridad:

1. `Web oficial` → https://davidportodiaz.com/
2. `Las manecillas del recuerdo` → https://davidportodiaz.com/las-manecillas-del-recuerdo/
3. `Samuel entre mundos` → página oficial del libro en la web.
4. `Prensa / contacto` → `/prensa/` si encaja con el uso profesional del canal.

No llenar los 14 huecos por completismo. Añadir Amazon/Goodreads/ORCID solo si existe una razón de UX real.

### Home / playlists

Crear secciones/playlists solo para contenido existente:

- `Entrevistas y prensa`;
- `Presentaciones y eventos`;
- `Las manecillas del recuerdo`;
- `Samuel entre mundos`;
- `Escritura / worldbuilding` si hay suficiente material.

No crear playlists vacías.

## Vídeos

### Metadata

Para cada vídeo relevante:

- título humano/descriptivo;
- descripción breve que explique qué verá el usuario;
- enlace canónico específico a la web cuando aporte valor;
- capítulos solo si el vídeo los necesita;
- thumbnail propia/legítima;
- subtítulos si la transcripción está disponible o puede revisarse correctamente.

No keyword stuffing ni títulos sensacionalistas ajenos al contenido.

### Links

- En vídeo largo, usar enlaces clicables hacia la página más específica posible si Advanced Features están activadas.
- En Shorts, no confiar en una URL escrita en la descripción: YouTube documenta que esas URLs no son clicables. Usar el enlace de perfil/canal y CTA verbal/textual natural solo cuando proceda.

## Derechos

Antes de resubir entrevistas o apariciones publicadas por terceros:

- comprobar quién posee el vídeo;
- obtener permiso si hace falta;
- preferir playlist/enlace al vídeo original cuando no hay derecho de reupload.

No descargar/republicar entrevistas de medios solo porque aparezca David.

## Web / sameAs

No hay cambio de código previo.

Si se confirma un canal público oficial, estable y controlado por David:

- valorar añadir su URL canónica a `Person.sameAs`;
- valorar añadirlo al bloque social solo si el canal tendrá contenido real.

Preferir la URL de handle estable una vez confirmada, manteniendo también el Channel ID como dato técnico interno.

Si se añade:

1. modificar el owner social/factual central;
2. regenerar derivados/shell;
3. actualizar tests/allowlists;
4. CI;
5. QA desktop/móvil;
6. verificar producción.

## Medición

Si hay GO:

Baseline:

- vídeos públicos;
- subscribers;
- views 28/90 días;
- top vídeos;
- tráfico desde YouTube hacia web en analítica propia.

Después medir 30/60/90 días sin exigir una cadencia artificial.

La métrica principal para este proyecto no es “publicar X vídeos”: es si el contenido audiovisual real genera descubrimiento, autoridad o referrals con coste de mantenimiento razonable.

## Guardrails

- No crear canal vacío por SEO/`sameAs`.
- No comprar views/subscribers.
- No republicar vídeo ajeno sin derechos.
- No crear calendario audiovisual semanal sin evidencia.
- No inventar handle/Channel ID.
- No añadir 14 enlaces porque YouTube lo permita.
- No usar URLs de Shorts como estrategia de referral porque no son clicables.
- No confundir un canal personal/de usuario con un canal oficial verificado hasta confirmar ownership.

## Pasos exactos para Claude

1. Auditar cuenta Google/YouTube autenticada.
2. Capturar canal/Channel ID/handle si existe.
3. Buscar posibles canales antiguos/duplicados.
4. Inventariar vídeos existentes y derechos.
5. Aplicar filtro de 2 activos reales / evento próximo / canal ya existente.
6. Si no supera el filtro, cerrar `NO_GO_NO_CONTENT_TRIGGER`.
7. Si supera el filtro, completar identidad y enlaces.
8. Ordenar Home/playlists solo con contenido real.
9. Optimizar metadata de vídeos existentes sin reescribirlos artificialmente.
10. Verificar enlaces clicables en vídeo largo y perfil.
11. QA escritorio/móvil/desconectado.
12. Guardar URL canónica estable.
13. Valorar `Person.sameAs` y cambio web en PR separada si procede.
14. Capturar baseline y revisar señal 30/60/90 días.

## Criterio de cierre

### GO

`CHANNEL_OWNERSHIP_CONFIRMED · CHANNEL_ID_RECORDED · HANDLE_URL_RECORDED · PROFILE_CURRENT · WEBSITE_LINKED · REAL_VIDEO_INVENTORY_PUBLISHED_OR_ORGANIZED · RIGHTS_VERIFIED · PLAYLISTS_NONEMPTY · PUBLIC_DESKTOP_MOBILE_QA · SITE_SAMEAS_UPDATED_IF_APPLICABLE · BASELINE_CAPTURED`

### NO-GO

`ACCOUNT_AUDITED · PUBLIC_CHANNEL_NOT_OBSERVED_OR_EMPTY · VIDEO_ASSET_INVENTORY_DONE · NO_CONTENT_TRIGGER · NO_EMPTY_CHANNEL_CREATED · REOPEN_TRIGGER_DOCUMENTED`

## Fuentes oficiales

- Channel customization: https://support.google.com/youtube/answer/3027950?hl=es
- Channel profile y enlaces: https://support.google.com/youtube/answer/2657964?hl=es
- Clickable external links: https://support.google.com/youtube/answer/13748639?hl=es
- Channel/handle URLs: https://support.google.com/youtube/answer/6180214?hl=es
