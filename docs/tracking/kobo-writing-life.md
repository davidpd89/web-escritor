# Kobo / Kobo Writing Life — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07**  
PR owner: **#412 · `tracking/kobo-writing-life`**  
Estado: **RESEARCHED · PUBLIC_KOBO_RECORD_NOT_OBSERVED · DIGITAL_RIGHTS_OWNER_NOT_VERIFIED · READY_FOR_CATALOG_AUDIT**

## Objetivo

Comprobar si las obras de David Porto Díaz están en Kobo, corregir metadata si procede y determinar si existe una oportunidad legítima de distribución digital sin interferir con derechos editoriales.

## Estado público observado hoy

Las búsquedas públicas realizadas hoy por título/autor no han devuelto una ficha inequívoca de Kobo para Samuel o Manecillas.

Clasificación:

`PUBLIC_KOBO_RECORD_NOT_OBSERVED`

No significa `ABSENT_FROM_KOBO`.

Claude debe buscar dentro de Kobo y, si existe, identificar la ficha/partner real.

## Datos canónicos

### Samuel entre mundos

- Libros Indie
- ISBN papel `9791387659776`
- 2025
- no existe una edición digital autorizada/documentada en el proyecto

### Las manecillas del recuerdo — papel

- Monza Ediciones
- ISBN `9798905149351`
- publicación `2026-09-03`

### Las manecillas del recuerdo — ebook

- Monza Ediciones
- ISBN `9798906781925`
- ASIN `B0HHM71F46`
- publicación `2026-08-12`

## Kobo Writing Life hoy

Kobo Writing Life es el portal gratuito de autopublicación de Rakuten Kobo para autores y publishers que **poseen los derechos digitales**.

Kobo indica actualmente:

- distribución en más de 200 países;
- red de partners retail internacional;
- ebooks y audiobooks;
- posibilidad de Kobo Plus;
- posibilidad de distribución a bibliotecas mediante OverDrive;
- control de precio/territorios/DRM para el owner;
- metadata completa como requisito importante para descubrimiento/promociones.

Fuentes actuales:

- https://www.kobo.com/es/es/p/writinglife
- https://help.kobo.com/hc/es/articles/360017771754--Qu%C3%A9-es-Kobo-Writing-Life
- https://www.kobo.com/kobo-writing-life/blog/frequently-asked-questions
- https://www.kobo.com/kobo-writing-life/blog/how-to-publish-a-book

## Guardrail de derechos

La propia ayuda de Kobo dice que KWL está pensado para quien posee los derechos digitales.

Por tanto:

### Samuel

No crear un ebook de Samuel solo para “estar en Kobo”. Antes habría que confirmar derechos digitales con Libros Indie.

### Manecillas

No subir directamente el EPUB a KWL mientras Monza o su distribuidor puedan controlar esa edición.

Primero:

1. preguntar a Monza (#428) si distribuye a Kobo;
2. identificar agregador/distribuidor;
3. confirmar territorios;
4. comprobar si el mismo ISBN digital ya está en su feed.

Duplicar la edición desde otra cuenta puede fragmentar ficha, precio, reporting y derechos.

## Metadata a revisar si existe ficha

- título;
- autor;
- publisher;
- ISBN;
- formato;
- idioma;
- fecha;
- portada;
- descripción;
- categorías/genres;
- precio como snapshot;
- territorios;
- DRM;
- Kobo Plus si aparece;
- retail partner/source;
- duplicados.

## Procedimiento Claude

1. Buscar los tres ISBN en Kobo/KWL si la UI lo permite.
2. Buscar títulos + David Porto Díaz.
3. Guardar URL canónica de cada resultado.
4. Distinguir ficha de producto de edición/obra.
5. Confirmar si Manecillas ebook ya llega mediante Monza/distribuidor.
6. Si existe pero tiene metadata errónea, corregir upstream, no crear otro producto.
7. Si no existe, documentar quién tiene los derechos y decidir con ese owner si Kobo debe añadirse.
8. No tocar Samuel digital hasta derechos confirmados.
9. Revalidar Kobo tras cualquier alta/corrección.

## OverDrive

KWL puede ofrecer distribución a bibliotecas vía OverDrive, pero #433 es el owner específico de OverDrive/Libby.

No ejecutar dos vías paralelas. Si Kobo es el canal real, actualizar #433 con esa evidencia.

## Oportunidad web

Si Manecillas ebook queda disponible en Kobo con URL estable:

- valorar enlace secundario `Kobo` en la zona digital;
- no inventar disponibilidad global;
- no congelar precio;
- medir clics antes de darle más prominencia.

## Criterio de cierre

`KOBO_SEARCH_DONE · DIGITAL_RIGHTS_OWNER_IDENTIFIED · MANECILLAS_KOBO_STATE_VERIFIED · SAMUEL_DIGITAL_STATUS_VERIFIED · METADATA_CORRECT_OR_UPSTREAM_REQUESTED · NO_DUPLICATE_DISTRIBUTION · OVERDRIVE_COORDINATED · SITE_LINK_DECIDED`

Si no hay derechos/direct distribution:

`NO_GO_DIRECT_KWL · PUBLISHER_OWNER_RECORDED`

## Fuentes

- https://www.kobo.com/es/es/p/writinglife
- https://help.kobo.com/hc/es/articles/360017771754--Qu%C3%A9-es-Kobo-Writing-Life
- https://www.kobo.com/kobo-writing-life/blog/frequently-asked-questions
- https://www.kobo.com/kobo-writing-life/blog/how-to-publish-a-book
