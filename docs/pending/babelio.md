# Babelio — autor, libros y comunidad lectora

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · EXISTING_USER_PROFILE_KNOWN · PUBLIC_AUTHOR_PAGE_UNVERIFIED · READY_FOR_AUTHENTICATED_EXECUTION`

## Objetivo

Revisar y completar la presencia de David Porto Díaz, `Samuel entre mundos` y `Las manecillas del recuerdo` en Babelio, separando correctamente:

- perfil de usuario/lector;
- posible página pública de autor;
- fichas de libros/ediciones;
- contribuciones comunitarias.

Babelio interesa como comunidad lectora y superficie de descubrimiento; no se usará como autoridad bibliográfica primaria.

## Estado conocido

El proyecto ya registra este perfil:

`https://es.babelio.com/monprofil.php?id_user=114337`

Ese URL tiene forma de **perfil de usuario**, no de autoridad bibliográfica de autor. No meterlo automáticamente en `Person.sameAs` como si fuera una página oficial de autor hasta confirmar qué muestra públicamente y cómo lo interpreta Babelio.

La web pública de Babelio bloquea actualmente parte del crawling automatizado, por lo que la ejecución real debe hacerse con navegador autenticado y evidencia directa de la UI.

## Plataforma activa

La app oficial de Babelio sigue publicada y gratuita en 2026 como red social de lectores, con biblioteca, búsqueda/escaneo de libros, comentarios y descubrimiento de lecturas.

Babelio ha documentado históricamente un modelo comunitario de edición que permite a miembros autorizados:

- asociar variantes de autores;
- asociar ediciones;
- corregir títulos/nombres;
- añadir/eliminar coautores;
- añadir biografías, resúmenes, etiquetas y portadas.

Claude debe comprobar en la UI actual qué capacidades siguen vigentes antes de actuar; no dar por actual una guía antigua solo porque siga indexada.

## Datos canónicos

### Samuel entre mundos

- David Porto Díaz
- Libros Indie
- ISBN `9791387659776`
- 2025
- tapa blanda

### Las manecillas del recuerdo — papel

- David Porto Díaz
- Monza Ediciones
- ISBN `9798905149351`
- 2026-09-03
- ASIN `B0HHY9MYLM`

### Las manecillas del recuerdo — ebook

- David Porto Díaz
- Monza Ediciones
- ISBN `9798906781925`
- 2026-08-12
- ASIN `B0HHM71F46`

No resolver en Babelio las discrepancias de páginas `422/412` o `272/266`; primero cerrar upstream #429/#428/#404.

## Ejecución para Claude

### 1. Perfil de usuario

Abrir el perfil existente y comprobar:

- nombre visible;
- avatar/foto;
- bio;
- web o enlaces;
- privacidad;
- si el perfil se presenta como lector o permite identificación legítima como autor.

No convertirlo en perfil promocional agresivo.

### 2. Página de autor

Buscar:

- `David Porto Díaz`;
- variantes sin tilde;
- los dos títulos.

Confirmar si Babelio mantiene una **página de autor separada** del perfil de usuario.

Si existe:

- guardar URL canónica;
- revisar nombre, bio, foto y obras asociadas;
- revisar duplicados/variantes de autor.

Si no existe, documentar la vía actual para solicitar/crear asociación, sin inventar un author claim inexistente.

### 3. Samuel

Buscar por:

- ISBN `9791387659776`;
- título;
- autor.

Revisar:

- portada;
- editorial;
- fecha;
- idioma;
- ISBN;
- resumen;
- tags/géneros;
- relación con la página de autor;
- posibles ediciones/duplicados.

### 4. Manecillas

Buscar los dos ISBN y confirmar que Babelio no ha creado dos Works independientes cuando solo son formatos/ediciones de la misma obra.

Revisar papel y ebook por separado cuando la plataforma lo modele así.

### 5. Correcciones

Para cada error registrar:

`URL | campo actual | valor correcto | evidencia | vía de corrección`

Usar primero las herramientas comunitarias actuales; si requieren privilegios de editor o soporte, documentar la solicitud.

## Etiquetas / descubrimiento

Babelio permite etiquetar libros para ayudar a su clasificación y descubrimiento. Usarlas solo con términos descriptivos reales.

Samuel puede justificar etiquetas relacionadas con fantasía juvenil/portal fantasy/magia si el sistema actual las admite y corresponden al contenido.

Manecillas debe etiquetarse por sus temas reales, no reutilizando tags de Samuel.

No keyword stuffing ni etiquetas autopromocionales.

## Reseñas y ratings

No:

- reseñar los libros propios;
- votarlos para subir media;
- pedir intercambios de reseñas;
- crear cuentas adicionales.

Sí:

- mantener metadata correcta;
- participar como lector de forma genuina si se desea;
- responder/interactuar solo de manera natural y permitida.

## Posible cambio en la web

Si aparece una URL pública estable e inequívoca de **autor** en Babelio, valorar añadirla a `Person.sameAs`.

Si se obtienen fichas canónicas de obras, valorar `Book.sameAs` individualmente.

No usar el `monprofil.php?id_user=114337` como `Person.sameAs` por inercia si solo representa una cuenta personal de lector.

## Prioridad

`P1/P2`.

Babelio tiene especial valor por audiencia lectora hispanohablante y porque el proyecto ya tiene cuenta. Debe ejecutarse antes que plataformas genéricas de menor afinidad.

## Criterio de cierre

`USER_PROFILE_AUDITED · AUTHOR_PAGE_FOUND_OR_STATE_DOCUMENTED · SAMUEL_VERIFIED_OR_SUBMITTED · MANECILLAS_VERIFIED_OR_SUBMITTED · EDITIONS_REVIEWED · AUTHOR_DUPLICATES_REVIEWED · METADATA_CORRECT_OR_REQUESTED · SITE_SAMEAS_UPDATED_IF_APPLICABLE · NO_SELF_RATING`
