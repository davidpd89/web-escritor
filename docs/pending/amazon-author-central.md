# Amazon Author Central — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#396 · `tracking/amazon-author-central`**  
Estado: **RESEARCHED · EXTERNAL_ACTION_PENDING · NO_ACCOUNT_CHANGES_PERFORMED**

## Objetivo

Dejar la presencia de **David Porto Díaz** en Amazon Author Central coherente con la realidad editorial actual y preparada para que una sesión autenticada pueda cerrarla sin volver a investigar desde cero.

El resultado buscado no es «crear más perfiles», sino consolidar una única identidad de autor, asociar correctamente las obras/ediciones existentes y dejar clara la frontera entre:

- lo que el autor puede gestionar directamente en **Author Central**;
- lo que depende de la **ficha editorial/KDP/Amazon**;
- lo que, para `Las manecillas del recuerdo`, puede requerir a **Monza Ediciones** o soporte de Amazon.

## Estado factual canónico a 2026-09-07

### Autor

- Nombre público canónico: **David Porto Díaz**.
- Web oficial: **https://davidportodiaz.com/**.
- Perfil de autor Amazon registrado en el repo: **https://www.amazon.es/stores/author/B0GZFP1JV3**.
- La URL anterior debe tratarse como perfil candidato/canónico ya existente, no crear otro perfil sin comprobar primero su estado autenticado.
- La web oficial presenta actualmente a David Porto Díaz como escritor nacido en Pontevedra y residente en Madrid, autor de `Samuel entre mundos` y `Las manecillas del recuerdo`, ganador del Primer Premio del XII Certamen de Microrrelatos «De amor» de Letras Como Espada 2026 y finalista del I Premio de Literatura Infantil Juan Andrés Teno 2026.

### Obras que deben quedar asociadas

| Obra / formato | Editorial | Identificador | Publicación / estado | Acción en Author Central |
|---|---|---|---|---|
| `Samuel entre mundos` · tapa blanda | Libros Indie | ISBN `9791387659776`; enlace Amazon actual de la web apunta al ASIN `B0GB6LGQFH` | Publicada; 422 páginas | Debe aparecer como obra del autor. No crear una edición inexistente en ebook. |
| `Las manecillas del recuerdo` · Kindle | Monza Ediciones | ASIN `B0HHM71F46`; ISBN-13 `9798906781925` | Publicada el **2026-08-12**; la web oficial registra 2,99 € en el corte actual | Reclamar/asociar al mismo autor y comprobar que Amazon la presenta como formato de la misma obra. |
| `Las manecillas del recuerdo` · tapa blanda | Monza Ediciones | ASIN registrado `B0HHY9MYLM`; ISBN `9798905149351` (`979-8-90514-935-1`) | Publicación editorial **2026-09-03**; 272 páginas; PVP editorial documentado 16 € | Reclamar/asociar al mismo autor y comprobar agrupación correcta con Kindle. |

Enlaces de trabajo registrados para Manecillas:

- Papel: `https://www.amazon.es/dp/B0HHY9MYLM` (shortlink usado por el proyecto: `https://amzn.to/4zW6Yeu`).
- Kindle: `https://www.amazon.es/dp/B0HHM71F46` (shortlink: `https://amzn.to/3SM4Oxu`).

**No fijar precio, stock, ranking, número de reseñas o disponibilidad como dato estable de la PR.** Son datos volátiles y deben comprobarse durante la sesión autenticada/live.

## Qué permite Amazon Author Central actualmente

La documentación oficial de Amazon KDP consultada el 2026-09-07 confirma que Author Central permite, entre otras cosas:

- añadir libros a la página de autor;
- añadir biografía en distintos idiomas;
- añadir foto y, según mercado, otros medios del perfil;
- consultar ranking de ventas y reseñas;
- consultar el número total de seguidores del autor;
- hacer que los libros reclamados formen parte del ecosistema de **Author Follow**.

Amazon indica que el botón **Seguir** puede aparecer en la página del autor y en fichas de libro. Los seguidores pueden recibir avisos de nuevos lanzamientos/preventas cuando la obra cumple los requisitos y el usuario ha aceptado comunicaciones de Amazon. El número de seguidores **no modifica el ranking de best sellers**.

Author Central figura actualmente disponible para **Amazon.es** en la ayuda española de KDP.

Fuente primaria: `https://kdp.amazon.com/es_ES/help/topic/G200644310`

## Cómo reclamar una obra — flujo oficial

Amazon documenta este flujo:

1. Entrar en Amazon Author Central.
2. Abrir **Libros**.
3. Elegir **Añadir un libro**.
4. Buscar por título, ISBN, ASIN o nombre de autor.
5. Seleccionar la portada correcta.
6. Elegir **Añadir este libro**.

Fuente primaria: `https://kdp.amazon.com/es_ES/help/topic/G201499010`

Para esta cuenta, el orden recomendado es buscar primero por identificador exacto, no por texto libre:

1. `9791387659776` — Samuel.
2. `B0HHM71F46` — Manecillas Kindle.
3. `B0HHY9MYLM` — Manecillas papel.

Esto reduce el riesgo de reclamar una edición homónima o un registro incorrecto.

## Distinción crítica: Author Central no es el editor de todos los metadatos

No mezclar «asociar el libro al autor» con «editar la ficha bibliográfica».

Amazon KDP confirma que ciertos metadatos de títulos KDP publicados pueden actualizarse, mientras otros quedan bloqueados o exigen una nueva edición. El nombre del autor principal, título, ISBN y otros campos estructurales tienen restricciones específicas después de publicación.

Fuentes primarias:

- `https://kdp.amazon.com/es_ES/help/topic/G200736410`
- `https://kdp.amazon.com/es_ES/help/topic/G2BWJN2BY98T5PV2`

En particular:

- **Author Central**: perfil, bio/foto, asociación autor↔libro y supervisión de catálogo.
- **KDP/editor/distribuidor/Amazon**: metadatos del producto, ISBN, autor principal, categorías, descripción, precio, disponibilidad y consolidación técnica cuando corresponda.
- `Las manecillas del recuerdo` es una publicación de **Monza Ediciones**. No asumir que David dispone de permisos KDP sobre esas ediciones. Si un dato duro está mal y no existe control directo, documentar exactamente el error y escalarlo a Monza/Amazon; no intentar «arreglarlo» creando otra edición.

## Vinculación papel + Kindle de `Las manecillas del recuerdo`

Objetivo visual: una sola obra con acceso claro a sus formatos cuando Amazon lo permita.

Amazon explica que la vinculación automática de formatos depende de que los metadatos coincidan (especialmente título y autor) y, en el flujo KDP, de que los formatos correspondan a la misma cuenta. Si no se vinculan después del plazo normal, Amazon indica contactar con soporte con los identificadores de los formatos.

Fuente primaria: `https://kdp.amazon.com/es_ES/help/topic/GTQGN866DSS6XBD2`

Para Manecillas no inferir que el mecanismo KDP sea aplicable tal cual: al ser publicación editorial, primero inspeccionar cómo aparecen ambas fichas y quién controla cada registro.

Si están separadas:

1. comprobar que ambas muestran exactamente `Las manecillas del recuerdo`;
2. comprobar que ambas muestran exactamente `David Porto Díaz`;
3. comprobar editorial/sello e identificadores;
4. comprobar que ambas están reclamadas en Author Central;
5. si siguen separadas, registrar capturas/URLs/ASINs y abrir incidencia con Amazon o trasladarla a Monza según ownership.

**No crear un duplicado para forzar la unión.**

## Perfil de autor — datos preparados

### Nombre

Usar exactamente:

**David Porto Díaz**

No alternar con `David Porto`, `David P. Díaz`, variantes sin tilde ni otro nombre salvo que se demuestre un registro editorial real que lo exija.

### Web

**https://davidportodiaz.com/**

### Biografía propuesta para Author Central

> David Porto Díaz (Pontevedra, 1989) es un escritor español afincado en Madrid. Es autor de *Las manecillas del recuerdo* (Monza Ediciones, 2026), una novela coral sobre memoria, familia y los objetos que heredamos, y de *Samuel entre mundos* (Libros Indie, 2025), su debut de fantasía juvenil y portal fantasy ambientado en Noveris. En 2026 obtuvo el Primer Premio en el XII Certamen de Microrrelatos «De amor» de Letras Como Espada y fue finalista del I Premio de Literatura Infantil Juan Andrés Teno. También participa en la antología colaborativa *La memoria de las tierras del norte*. Escribe ficción en español con especial interés por la identidad, la memoria, la pertenencia y las historias donde cada decisión tiene consecuencias.

Esta bio está derivada de la biografía pública actual de `davidportodiaz.com/autor.html`. Antes de publicarla en Amazon comprobar que no haya restricciones de longitud/formato en la interfaz del día de ejecución. No añadir cifras de ventas, rankings, estrellas ni afirmaciones promocionales no verificables.

### Foto

Usar preferentemente **la misma fotografía de autor canónica del sitio oficial/kit de prensa**, en alta resolución y con derechos claros. Evitar generar otra imagen para Amazon: la consistencia visual entre web, prensa, Goodreads, Amazon y otros perfiles ayuda a identificar correctamente a la misma persona.

Antes de sustituir una foto existente, comparar ambas. Si la actual ya es la canónica y tiene calidad suficiente, **NO_ACTION**.

## Auditoría exacta que debe ejecutar Claude en la sesión autenticada

### A. Identidad y propiedad

- [ ] Entrar en Author Central con la cuenta correcta.
- [ ] Confirmar que el perfil gestionado corresponde al ID público `B0GZFP1JV3`.
- [ ] Confirmar que no existe otro perfil reclamado de `David Porto Díaz`.
- [ ] Registrar el estado como `CLAIMED`, `CLAIM_REQUIRED` o `DUPLICATE_REVIEW_REQUIRED`.
- [ ] No crear un segundo author page si la existente es recuperable.

### B. Perfil

- [ ] Nombre exacto `David Porto Díaz`.
- [ ] Foto correcta y actual.
- [ ] Bio coherente con la web oficial.
- [ ] Añadir/confirmar bio en español; otros idiomas solo si la interfaz y estrategia lo justifican.
- [ ] Web oficial enlazada si el campo existe en la interfaz actual.
- [ ] Comprobar que no sobreviven menciones tipo «próxima novela» para Manecillas: desde el 2026-09-03 ya es obra publicada.

### C. Catálogo

- [ ] `Samuel entre mundos` presente.
- [ ] `Las manecillas del recuerdo` Kindle presente.
- [ ] `Las manecillas del recuerdo` tapa blanda presente.
- [ ] No aparece ninguna obra ajena/homónima reclamada accidentalmente.
- [ ] No aparece una edición duplicada que represente el mismo formato.
- [ ] Samuel no aparece con un ebook inexistente.

### D. Manecillas — formatos

- [ ] Abrir ASIN `B0HHM71F46`.
- [ ] Abrir ASIN `B0HHY9MYLM`.
- [ ] Comparar título, autor, editorial, portada y datos visibles.
- [ ] Confirmar si Amazon agrupa Kindle/papel como formatos de la misma obra.
- [ ] Si no: determinar si el owner es Amazon, Monza o una cuenta KDP controlable antes de solicitar ningún cambio.

### E. Duplicados

Buscar como mínimo:

- `David Porto Díaz`
- `David Porto Diaz`
- `Samuel entre mundos`
- `Las manecillas del recuerdo`
- los ISBN/ASIN exactos anteriores.

Cualquier posible duplicado debe documentarse con URL/ASIN y diferencia concreta. No solicitar fusión solo porque el título sea parecido.

### F. QA público final

Después de guardar cambios y esperar su propagación:

- [ ] abrir la página pública en sesión anónima;
- [ ] revisar escritorio;
- [ ] revisar móvil;
- [ ] comprobar navegación autor → Samuel;
- [ ] comprobar navegación autor → Manecillas;
- [ ] comprobar que ambas ediciones de Manecillas se encuentran desde el perfil;
- [ ] comprobar botón/estado de **Seguir** si Amazon lo muestra;
- [ ] comprobar que foto y bio no están truncadas de forma problemática;
- [ ] comprobar que no se ha perdido ninguna obra durante la reclamación.

## Evidencia a guardar en esta PR

Al cerrar la operación, añadir un comentario o ampliar este documento con:

- fecha y hora de verificación;
- URL final del author page;
- estado `CLAIMED/VERIFIED`;
- lista de obras visibles con ASIN/ISBN;
- estado de vinculación de formatos de Manecillas;
- duplicados: `NONE_FOUND` o lista exacta;
- cambios de bio/foto: `UPDATED` o `NO_ACTION`;
- cualquier incidencia enviada a Amazon/Monza con owner y estado;
- capturas manuales solo si son necesarias para probar un problema visual/duplicado; no versionar datos privados de la cuenta.

No registrar en GitHub datos de login, emails privados de cuenta, información fiscal, bancaria, direcciones, teléfonos ni capturas de panel que contengan información sensible.

## Qué NO hacer

- No crear otra cuenta Author Central si la existente funciona.
- No crear nuevas ediciones para corregir asociaciones.
- No autopublicar una copia de `Las manecillas del recuerdo` para «arreglar» Amazon.
- No modificar datos editoriales de Monza sin confirmar ownership/autorización.
- No inventar premios, rankings, ventas, seguidores o reseñas.
- No usar reseñas de clientes como «premios» o aval editorial.
- No asumir que `rel=sponsored`, afiliación o Amazon Associates tienen relación con Author Central: son sistemas separados.
- No considerar que una obra «está bien» solo porque aparece en búsqueda; debe estar asociada al perfil correcto.

## Mejora adicional de bajo riesgo

Una vez el catálogo esté correcto, revisar si el perfil público muestra de forma clara **Seguir**. Amazon documenta que los libros añadidos a Author Central pueden entrar en el ecosistema Author Follow y que los seguidores pueden recibir avisos de lanzamientos elegibles. No prometer que todos los seguidores reciben emails ni que esto mejora rankings.

No abrir Amazon Ads ni campañas desde esta PR. La publicidad es un flujo distinto y debe evaluarse por separado después de que la identidad y las fichas estén correctas.

## Fuentes verificadas el 2026-09-07

Amazon / KDP:

- Author Central: `https://kdp.amazon.com/es_ES/help/topic/G200644310`
- Añadir libros / preparación para ads: `https://kdp.amazon.com/es_ES/help/topic/G201499010`
- Autores y colaboradores: `https://kdp.amazon.com/es_ES/help/topic/G2BWJN2BY98T5PV2`
- Actualizar detalles del libro: `https://kdp.amazon.com/es_ES/help/topic/G200736410`
- Vincular formatos: `https://kdp.amazon.com/es_ES/help/topic/GTQGN866DSS6XBD2`
- Enlaces directos por ASIN: `https://kdp.amazon.com/es_ES/help/topic/G200652190`

Autoridad propia del proyecto:

- `https://davidportodiaz.com/autor.html`
- `https://davidportodiaz.com/`
- `https://davidportodiaz.com/las-manecillas-del-recuerdo/kindle/`
- `https://davidportodiaz.com/clubes-de-lectura/samuel-entre-mundos/`

## Criterio de cierre

Marcar #396 cerrada solo cuando exista evidencia de sesión real suficiente para afirmar:

`AUTHOR_PAGE_CLAIMED · PROFILE_COHERENT · SAMUEL_ASSOCIATED · MANECILLAS_KINDLE_ASSOCIATED · MANECILLAS_PAPER_ASSOCIATED · DUPLICATES_REVIEWED · FORMAT_LINKING_VERIFIED_OR_ESCALATED · PUBLIC_DESKTOP_MOBILE_QA_DONE`

Si una corrección depende de Monza/Amazon y ya está correctamente documentada/escalada, la PR puede cerrar como:

`EXTERNAL_DEPENDENCY_RECORDED`

sin fingir que el cambio ya está aplicado.
