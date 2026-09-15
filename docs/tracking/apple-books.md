# Apple Books — auditoría y plan de ejecución

Fecha de investigación: **2026-09-07** (ejecutado: 2026-09-15)  
PR owner: **#411 · `tracking/apple-books`**  
Estado: **CATALOG_ABSENCE_CONFIRMED_VIA_API · NO_ITUNES_CONNECT_ACCOUNT_LINKED · NEEDS_MONZA_DISTRIBUTION_DECISION · NOT_A_LOGIN_BLOCKER**

## Ejecución (2026-09-15)

Con la cuenta de Apple personal de David (`account.apple.com`, sesión
confirmada: "David Porto Díaz") ya autenticada:

### Ausencia confirmada de verdad (no solo "no observado")

En vez de una búsqueda web genérica, se consultó directamente el
catálogo público de Apple Books vía su API oficial de búsqueda
(`itunes.apple.com/search`, sin necesidad de login — es la misma API
que usan los widgets de afiliados), cubriendo autor, título y ambos
ISBN, en las tiendas de España y Estados Unidos:

| Consulta | Tienda | Resultado |
|---|---|---|
| "Las manecillas del recuerdo" | ES | Sin coincidencias |
| "Las manecillas del recuerdo" | US | Sin coincidencias |
| "Samuel entre mundos David Porto" | ES | Sin coincidencias |
| "David Porto Díaz" / "David Porto Diaz" | ES / US | Sin coincidencias |
| ISBN `9798906781925` (Manecillas ebook) | ES | Sin coincidencias |
| ISBN `9791387659776` (Samuel) | ES | Sin coincidencias |

Confirmado: **ninguno de los dos libros está en Apple Books**, en
ninguna tienda comprobada. Esto reemplaza el `NOT_OBSERVED` anterior
(que solo reflejaba una búsqueda web no concluyente) por una
comprobación directa y positiva del catálogo real.

### Por qué esto NO es un bloqueo de login

`authors.apple.com/publish` confirma que la cuenta de Apple personal de
David **no tiene ninguna cuenta de iTunes Connect vinculada todavía**
(la página ofrece "Get started with iTunes Connect" como alta nueva, no
como panel existente). Crear esa cuenta y publicar directamente sería
una decisión real, no un simple inicio de sesión:

- **Samuel entre mundos** no tiene ninguna edición digital
  autorizada/documentada en el proyecto — no hay nada que subir a Apple
  Books para este título todavía.
- **Las manecillas del recuerdo (ebook)** ya tiene una edición digital
  publicada por Monza Ediciones vía Amazon Kindle. Publicarla también
  en Apple Books usando la cuenta personal de David, sin confirmar
  primero con Monza quién controla los derechos de distribución digital
  y si ya existe o está prevista una vía propia (agregador/partner),
  arriesga crear una ficha duplicada o conflictiva con la distribución
  editorial real — exactamente lo que este documento ya advertía no
  hacer ("no publicar el mismo ebook desde otra cuenta solo para
  conseguir una URL Apple Books").

**Siguiente paso real**: no es un login adicional, es una decisión de
distribución que depende de Monza (#428) — confirmar si Apple Books
forma parte de su plan de distribución del ebook y, si no, si autorizan
que se publique de forma independiente. Hasta entonces, no hay acción
segura que ejecutar aquí.

## Objetivo

Comprobar si `Samuel entre mundos` y `Las manecillas del recuerdo` están disponibles en Apple Books, revisar su representación pública y determinar qué puede gestionar David y qué depende de publisher/distribuidor.

## Estado público observado hoy

Las búsquedas públicas realizadas hoy por título/autor no han devuelto una ficha inequívoca de Apple Books para Samuel o Manecillas.

Estado correcto:

`PUBLIC_APPLE_BOOKS_RECORD_NOT_OBSERVED`

No significa que no exista en el catálogo. Claude debe comprobar directamente Apple Books y, si hay acceso, iTunes Connect/owner editorial.

## Datos canónicos

### Samuel entre mundos

- Libros Indie
- ISBN papel `9791387659776`
- año editorial 2025
- no existe una edición digital autorizada/documentada en el proyecto

### Las manecillas del recuerdo — papel

- Monza Ediciones
- ISBN `9798905149351`
- publicación `2026-09-03`

### Las manecillas del recuerdo — ebook

- Monza Ediciones
- ISBN `9798906781925`
- ASIN Amazon `B0HHM71F46`
- publicación `2026-08-12`

## Cómo funciona Apple Books actualmente

Apple Books for Authors permite publicar ebooks directamente mediante iTunes Connect/Publishing Portal o utilizar un partner preferente.

Apple documenta actualmente:

- entrega EPUB directa;
- publicación mediante partners;
- metadata de título, autor, descripción, categoría, idioma y publisher;
- rights & pricing por territorios;
- product pages con portada, Publisher Description, categorías, ratings/reviews y precio;
- promo codes para títulos distribuidos por la cuenta/partner;
- herramientas de marketing y enlaces Apple Books.

Fuentes oficiales:

- https://authors.apple.com/publish
- https://authors.apple.com/support/4574-publish-book-from-web
- https://authors.apple.com/support/3969-craft-great-product-page-apple-books
- https://authors.apple.com/promote/

## Rights / ownership

### Samuel

No crear una edición digital de Samuel para Apple Books sin confirmar que David/Libros Indie posee y autoriza esos derechos.

### Manecillas

Antes de subir nada:

1. confirmar con Monza (#428) si Apple Books forma parte de su distribución;
2. identificar agregador o cuenta iTunes Connect que controla el producto;
3. confirmar territorios y pricing owner;
4. corregir metadata con ese owner.

No publicar el mismo ebook desde otra cuenta solo para conseguir una URL Apple Books.

## Metadata/product page a auditar

Si aparece una ficha:

- Apple Books ID / URL;
- título/subtítulo;
- nombre canónico del autor;
- publisher;
- ISBN si se expone;
- fecha;
- idioma;
- categorías;
- portada;
- Publisher Description;
- sample/preview;
- precio y territorios como snapshots;
- enlaces/ediciones relacionadas;
- duplicados.

## Punto importante: Publisher Description

Apple define la descripción como una de las principales herramientas de conversión de la product page y exige que represente fielmente el libro; recomienda no meter precios ni referencias a otros retailers.

Si Manecillas aparece con una sinopsis desactualizada, corregirla en el owner editorial/partner, no desde nuestra web.

## Apple Books for Authors no equivale a un Author Central reclamable

No asumir que existe un perfil de autor reclamable equivalente a Amazon Author Central o Goodreads.

El objetivo operativo aquí es:

- catálogo/product pages correctas;
- distribución correcta;
- enlaces promocionales si existen;
- reporting solo si David/owner tiene acceso.

No crear una falsa tarea de “claim author profile” si Apple no ofrece ese flujo para este catálogo/cuenta.

## Promo codes y marketing

Apple ofrece promo codes gratuitos para publishers/autores que distribuyen ebooks directamente bajo su cuenta. No asumir que David puede generarlos para Manecillas si la edición pertenece a Monza/aggregator.

Si el owner los tiene disponibles, pueden servir para prensa/reviewers, pero solo coordinados con la editorial.

## Apple Affiliate Program

Apple mantiene un programa de afiliación para libros y herramientas oficiales de links/badges. No es prioridad antes de confirmar que la edición está realmente en Apple Books.

Si se usa en el futuro:

- coordinar disclosure como con Amazon;
- no añadir afiliación solo por cerrar esta PR;
- medir si el canal aporta ventas/clics.

Fuente: https://authors.apple.com/support/3977-apple-affiliate-program-books-audiobooks

## Procedimiento Claude

1. Buscar `David Porto Díaz`, títulos e ISBN en Apple Books.
2. Guardar URLs/IDs inequívocos.
3. Confirmar si Manecillas ebook está distribuido por Monza/partner.
4. Si existe: auditar product page completa.
5. Si no existe: documentar owner de derechos y decidir con Monza si debe entrar.
6. No crear Samuel digital sin derechos.
7. Si hay metadata incorrecta, corregir en publisher/partner y esperar propagación.
8. Verificar en iPhone/iPad/web cuando exista ficha.
9. Valorar enlace secundario Apple Books en la web solo con URL estable y disponibilidad real.

## Criterio de cierre

`APPLE_SEARCH_DONE · DISTRIBUTION_OWNER_IDENTIFIED · MANECILLAS_APPLE_STATE_VERIFIED · SAMUEL_DIGITAL_STATUS_VERIFIED · PRODUCT_PAGE_AUDITED_IF_PRESENT · METADATA_CORRECT_OR_UPSTREAM_REQUESTED · NO_DUPLICATE_UPLOAD · MOBILE_WEB_QA_DONE · SITE_LINK_DECIDED`

Si no hay distribución autorizada:

`NO_GO_DIRECT_UPLOAD · PUBLISHER_DEPENDENCY_RECORDED`

## Fuentes

- https://authors.apple.com/publish
- https://authors.apple.com/support/4574-publish-book-from-web
- https://authors.apple.com/support/3969-craft-great-product-page-apple-books
- https://authors.apple.com/promote/
- https://authors.apple.com/support/3977-apple-affiliate-program-books-audiobooks
