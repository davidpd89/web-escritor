# Amazon — vinculación de formatos de Las manecillas del recuerdo

Fecha: 2026-09-08

Estado: `LINKED_OK · NO_TICKET_NEEDED · RESOLVED`

## Cierre (2026-09-09) — Amazon ya agrupó los formatos, sin intervención necesaria

David dio permiso para abrir un ticket a Amazon esta noche, pero antes de escribirlo se comprobó en vivo `https://www.amazon.es/dp/B0HHY9MYLM` (tapa blanda): la ficha ya muestra **ambos formatos como pestañas de la misma página** ("Versión Kindle · 2,99 €" y "Tapa blanda · 15,99 €"), con "Ver todos los formatos y ediciones" visible — exactamente lo que el documento definía como `LINKED_OK`. Coincide con lo que la propia ayuda de Amazon documentaba: la vinculación automática puede tardar hasta una semana, y esa ventana ya pasó desde que se investigó esto por primera vez.

**No hace falta enviar el ticket preparado más abajo.** Nada que ejecutar.

Nota aparte, sin relación con este cierre: la ficha muestra "Longitud de impresión: 266 páginas" para la tapa blanda, que no coincide con las 272 páginas que usa la web. Siguiendo el criterio que David ya dio esta noche ("esto le pasa a cada libro, no se puede corregir en cada web... solo revisar en los que lo ponemos nosotros"), no se toca Amazon por esto — es la misma discrepancia de páginas ya rastreada en #428/#404, sin acción nueva aquí.

## Problema

Las dos ediciones reales de `Las manecillas del recuerdo` están correctamente asociadas al autor, pero Amazon todavía no las presenta agrupadas como formatos de la misma obra.

Datos:

### Papel
- ASIN: `B0HHY9MYLM`
- ISBN-13: `9798905149351`
- URL: `https://www.amazon.es/dp/B0HHY9MYLM`
- PVP actual: `15,99 €`

### Kindle
- ASIN: `B0HHM71F46`
- ISBN-13: `9798906781925`
- URL: `https://www.amazon.es/dp/B0HHM71F46`
- PVP actual: `2,99 €`

Autor: `David Porto Díaz`
Author Page: `https://www.amazon.es/stores/author/B0GZFP1JV3`

## Lo que dice Amazon

Amazon/KDP intenta vincular eBook, tapa blanda y tapa dura automáticamente cuando los metadatos coinciden. Los campos relevantes incluyen:

- título;
- subtítulo;
- autor;
- contributors;
- serie;
- idioma;
- edición;
- volumen;
- tipo de interior para formatos impresos.

Amazon indica que la vinculación puede tardar hasta una semana desde que cada edición está publicada y que reclamar ambos libros en Author Central ayuda al proceso. Si después sigue sin vincularse, recomienda contactar con soporte aportando el ASIN del eBook y el ISBN/identificador del formato impreso.

Fuentes oficiales:

- https://kdp.amazon.com/es_ES/help/topic/GTQGN866DSS6XBD2
- https://kdp.amazon.com/en_US/help/topic/GW7J4WEKBVU25YEC

## Importante para este caso

Manecillas está publicada por Monza Ediciones, no por una cuenta KDP controlada por David. Por tanto, David no debe modificar ni republicar metadatos para forzar la unión.

Si el problema procede de metadata upstream, la corrección debe hacerla Monza / el owner real de la ficha / Amazon.

## Comprobación manual para David

### 1. Abrir ambas fichas en incógnito

- `https://www.amazon.es/dp/B0HHY9MYLM`
- `https://www.amazon.es/dp/B0HHM71F46`

En cada una comprobar si aparece:

- `Ver todos los formatos y ediciones`;
- selector `Kindle` / `Tapa blanda`;
- enlace visible al otro formato.

Guardar resultado exacto.

### 2. Comparar metadata visible

Anotar literalmente en cada ficha:

- título;
- subtítulo si existe;
- autor tal como aparece;
- idioma;
- editorial;
- fecha de publicación;
- edición, si se muestra.

Buscar cualquier diferencia real, incluso espacios/puntuación/nombre del autor.

### 3. Author Central

Entrar en Author Central y confirmar que bajo David Porto Díaz aparecen los dos productos:

- `B0HHY9MYLM`
- `B0HHM71F46`

Si ambos ya están reclamados/asociados, no volver a añadirlos ni crear perfiles duplicados.

### 4. Espera razonable

Si la edición física acaba de publicarse o de asociarse, esperar hasta 7 días desde la última corrección/asociación antes de abrir ticket repetido.

### 5. Si sigue sin agruparse: abrir incidencia Amazon

Usar el contacto de Author Central/KDP/Amazon correspondiente y enviar un único ticket claro.

Texto preparado:

> Hola. Soy David Porto Díaz, autor de `Las manecillas del recuerdo`. Las dos ediciones reales de la misma obra están correctamente asociadas a mi Author Page, pero Amazon.es todavía las muestra en páginas separadas y no como formatos de la misma obra. ¿Podrían revisar la vinculación de formatos?
>
> Kindle: ASIN `B0HHM71F46` — https://www.amazon.es/dp/B0HHM71F46
>
> Tapa blanda: ASIN `B0HHY9MYLM`, ISBN-13 `9798905149351` — https://www.amazon.es/dp/B0HHY9MYLM
>
> Autor en ambas: David Porto Díaz
>
> Author Page: https://www.amazon.es/stores/author/B0GZFP1JV3
>
> Son dos formatos de la misma obra. Si existe alguna discrepancia de metadata que impida la vinculación, agradecería que me indiquen el campo exacto para pedir su corrección a la editorial.

No afirmar que ambas fueron publicadas desde la misma cuenta KDP.

## Diagnóstico posible

Clasificar el resultado como uno de:

- `AUTO_LINK_PENDING`
- `VISIBLE_METADATA_MISMATCH`
- `HIDDEN_METADATA_MISMATCH`
- `PUBLISHER_ACCOUNT_DEPENDENCY`
- `AMAZON_SUPPORT_REQUIRED`
- `LINKED_OK`

## Si Amazon identifica un campo incorrecto

No parchear nuestra web para imitar el error de Amazon.

1. comparar con metadata canónica/Monza;
2. confirmar cuál es el valor correcto;
3. pedir corrección al owner upstream;
4. esperar propagación;
5. verificar que los dos formatos quedan unidos.

## Repo

No hay actualmente un bug conocido en `davidportodiaz.com` que pueda causar la agrupación de formatos dentro de Amazon. La web ya mantiene papel y Kindle como ediciones distintas con los enlaces correctos.

Solo tocar el repo si la investigación demuestra una URL/ASIN/ISBN canónico incorrecto en nuestra web.

## Criterio de cierre

`BOTH_FORMATS_ASSOCIATED_TO_AUTHOR · VISIBLE_METADATA_COMPARED · AMAZON_LINKING_STATE_VERIFIED · SUPPORT_TICKET_SENT_IF_NEEDED · MONZA_FIELD_CORRECTION_REQUESTED_IF_NEEDED · LINKED_OK_OR_EXTERNAL_PENDING_DOCUMENTED`