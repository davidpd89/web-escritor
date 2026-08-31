# Las manecillas del recuerdo · reconciliación de CTA comercial y autoridad factual

Fecha: 2026-08-31

Estado: contrato funcional previo a implementación. Rama creada desde el HEAD exacto de #291 (`e568aac1e500ca4cc4b29bbffef3e9e0ae7d10da`). Mantener DRAFT y sin merge hasta implementar el fix, añadir QA y validar el HEAD exacto.

## 1. Motivo

La segunda pasada de integración detectó una contradicción objetiva entre la autoridad factual de la obra y el runtime de HOME.

En `editorial-facts.json`, `books.lasManecillasDelRecuerdo` declara:

- `publicationDate: "2026-09-03"`;
- `statusBeforePublication: "published"` y `statusFromPublicationDate: "published"` por decisión editorial explícita;
- `purchaseUrl: null`;
- nota canónica: la disponibilidad comercial está separada del estado editorial y **no deben existir enlaces comerciales ni `Offer` hasta que haya una URL de compra real y verificada**.

En cambio, `assets/v1-home-editorial-v3.js` declara en el mismo HEAD:

```js
const SAMUEL_AMAZON_URL = 'https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21';
const MANECILLAS_BUY_URL = SAMUEL_AMAZON_URL;
```

y el rail de la obra actual renderiza:

```js
['Comprar', 'Comprar en Amazon', '', MANECILLAS_BUY_URL]
```

Por tanto la tarjeta presentada como compra de *Las manecillas del recuerdo* conduce realmente a la ficha Amazon de *Samuel entre mundos*.

No es un problema de fecha ni del wording `published`: el contrato editorial autoriza ese wording antes del 03/09. El defecto es de **destino comercial e identidad de producto**.

## 2. Precedencia

Para disponibilidad y destino de compra, la autoridad vigente es `editorial-facts.json` y los contratos que ya la protegen, entre ellos C.1/#176 y la revisión factual de #289.

La decisión visual histórica registrada en #163 según la cual «durante prepublicación, Comprar en Amazon apunta intencionalmente al Amazon de Samuel» queda superseded únicamente en este punto porque contradice la autoridad factual posterior/más específica sobre disponibilidad comercial.

Esto no reabre el diseño general de HOME. Solo impide representar como CTA de compra de una obra un retailer perteneciente a otra obra.

## 3. Estado verificable actual

```text
MANECILLAS_STATUS_COPY = published (intencional)
MANECILLAS_PURCHASE_URL = null
VERIFIED_MANECILLAS_RETAILER = none in canonical authority
HOME_LABEL = Comprar en Amazon
HOME_DESTINATION = Samuel entre mundos / Amazon ES
PRODUCT_IDENTITY_MATCH = false
COMMERCIAL_CTA_ALLOWED_BY_AUTHORITY = false while purchaseUrl is null
```

No inferir por ello que el libro no existe, no está publicado editorialmente o deba cambiarse a `forthcoming`. Son contratos diferentes.

## 4. Owner de implementación

Owner principal del bug: `assets/v1-home-editorial-v3.js`, coordinado con `editorial-facts.json`.

La implementación debe evitar volver a crear una segunda autoridad hardcodeada de disponibilidad.

Opciones admisibles, por orden de preferencia:

1. derivar el estado/destino comercial de una fuente canónica generada o disponible en build/runtime;
2. si la arquitectura actual no permite consumir esa autoridad sin introducir complejidad desproporcionada, mantener HOME sin CTA comercial de Manecillas mientras `purchaseUrl` sea `null` y protegerlo con test;
3. cuando exista una `purchaseUrl` real y verificada, habilitar el CTA con el label/destino correcto mediante el owner factual, no mediante copia manual del ASIN de Samuel.

No es admisible conservar `MANECILLAS_BUY_URL = SAMUEL_AMAZON_URL` como fallback.

## 5. Comportamiento requerido mientras `purchaseUrl` sea null

HOME puede conservar los accesos no comerciales existentes:

- `Ver la obra`;
- `Leer fragmentos`;
- Autor;
- Lectores beta;
- contacto.

Pero no debe mostrar una acción que semánticamente afirme compra de Manecillas y conduzca a Samuel.

Si visualmente se necesita conservar el cuarto slot del rail, su contenido debe ser no comercial y coherente con la arquitectura aprobada; no inventar retailer, preventa, stock ni disponibilidad.

No modificar por esta PR el status editorial `published` ni la fecha de publicación.

## 6. Activación futura de compra

Solo activar una acción comercial de Manecillas cuando exista evidencia versionada/verificada de destino.

Como mínimo, antes de activar:

- `editorial-facts.json` o su autoridad sucesora contiene una URL de compra específica de Manecillas;
- la URL resuelve a la obra correcta;
- título/ISBN/edición corresponden a Manecillas;
- no se reutiliza el ASIN de Samuel;
- cualquier relación de afiliación está declarada de forma correcta;
- si la URL lleva tag afiliado, se compone con K.3/#237 para `rel=sponsored` y disclosure humano;
- QA prueba producto, label, href y ausencia de fallback cruzado.

La llegada del 03/09 por sí sola **no** convierte `purchaseUrl:null` en una URL válida.

## 7. Relación con K.3/#237

#237 sigue siendo owner del contrato de afiliación Amazon:

- `rel=sponsored`/`nofollow` donde corresponda;
- disclosure próximo;
- declaración global requerida;
- reconciliación shell + Home dinámica.

Este owner es distinto:

- #237 pregunta si un enlace afiliado existente está correctamente marcado/declarado;
- esta PR pregunta si **debe existir ese CTA comercial para Manecillas y si apunta a la obra correcta**.

Orden lógico al integrar:

1. resolver identidad/destino comercial mediante esta PR;
2. si el destino final es afiliado, aplicar además #237;
3. ejecutar QA combinada.

No usar la corrección de `rel=sponsored` para legitimar un href que sigue apuntando al libro equivocado.

## 8. Relación con #163 y cadena DISEÑO

#163 conserva autoridad sobre la composición visual de HOME. Esta PR no debe reinterpretar paleta, rails, tipografía, spacing o identidad.

Solo queda superseded la decisión de negocio/URL que permitía usar Samuel como placeholder comercial de Manecillas.

Al integrar contra la cadena de diseño vigente:

- preservar la composición aprobada;
- no recuperar el placeholder por resolver un conflicto de rama;
- revisar el diff propio después del retarget/rebase;
- ejecutar QA visual de HOME además del contrato factual.

## 9. Relación con #176/C.1 y #289

C.1/#176 ya establece `purchaseUrl:null = sin Offer/retailer/CTA de compra inventado`.

#289 confirma que:

- el copy `published/publicada` es intencional;
- la disponibilidad comercial sigue separada;
- no se debe inferir retailer mientras no haya `purchaseUrl` verificada.

Esta PR materializa la consecuencia funcional de esos dos contratos sobre HOME; no crea una nueva política editorial.

## 10. QA obligatoria

Añadir una protección automatizada específica que falle si vuelve cualquiera de estos estados:

- `MANECILLAS_BUY_URL` reutiliza `SAMUEL_AMAZON_URL`;
- un CTA etiquetado como compra de Manecillas contiene el ASIN de Samuel `B0GB6LGQFH`;
- `purchaseUrl:null` coexiste con un CTA comercial de Manecillas en la HOME mejorada;
- una URL de compra futura no corresponde a Manecillas;
- el fix elimina accidentalmente `Ver la obra` o `Leer fragmentos`;
- el cambio modifica status/fecha editorial para resolver un problema que no es temporal.

Browser QA mínimo:

1. HOME mejorada con JS: no aparece compra de Manecillas mientras `purchaseUrl` sea null;
2. los accesos no comerciales siguen operativos;
3. Samuel conserva sus propios enlaces comerciales sin ser presentado como Manecillas;
4. teclado/focus/reflow/320–390 px y 200 % no se degradan si cambia el número/contenido del rail;
5. si se simula una `purchaseUrl` futura en fixture, el CTA resultante apunta a la URL exacta de Manecillas;
6. si esa URL es afiliada, el QA combinado con #237 exige `sponsored` y disclosure correspondiente.

## 11. Fuera de alcance

- inventar o buscar una URL de compra que no esté verificada;
- cambiar `statusBeforePublication`/`statusFromPublicationDate`;
- cambiar ISBN, precio, editorial o fecha;
- crear checkout propio;
- resolver stock/fulfillment;
- rediseñar HOME;
- resolver íntegramente K.3;
- merge automático de ninguna PR.

## 12. Taxonomía de verdad de esta rama

Hasta que exista código funcional:

```text
DOCUMENTED = true
FUNCTIONAL_OWNER_ASSIGNED = true
IMPLEMENTED_IN_PR = false
BUG_FIXED = false
MERGED_MAIN = false
CONFIGURED_LIVE = false / not proven
VERIFIED_E2E = false
```

Un CI verde sobre este contrato docs-only no podrá considerarse prueba de corrección del CTA.

## 13. Criterio de cierre

La PR solo puede cerrarse técnicamente cuando:

- HOME deja de dirigir una compra de Manecillas al producto Samuel;
- el comportamiento deriva o respeta la autoridad factual vigente;
- `purchaseUrl:null` impide CTA comercial de Manecillas;
- una URL futura solo se activa tras verificación y corresponde a la obra correcta;
- #237 se compone si existe afiliación;
- QA estática/browser reproduce el defecto anterior y prueba su ausencia;
- CI del HEAD funcional exacto está verde;
- sigue DRAFT hasta revisión humana y no se ha modificado `main` desde esta auditoría.
