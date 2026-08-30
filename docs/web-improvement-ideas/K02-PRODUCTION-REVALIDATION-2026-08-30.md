# K.2 · Revalidación de producción — bundle / edición coleccionista

Fecha: 2026-08-30  
Base auditada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
Tree de la base: `68d02e1fe8ac2cfa239f4a716929e992abb672fd`

## Veredicto

`DEFER · DEPENDS_ON_K1_OPERATION · MANECILLAS_PRELAUNCH · NO_VERIFIED_BUNDLE_SKU · NO_HYPOTHETICAL_OFFER`

K.2 no es una feature web independiente. Es una variante de producto y fulfillment **más compleja** que K.1. Mientras no exista una operación repetible para vender al menos un producto físico propio, un bundle solo multiplicaría stock, coste, packaging, devoluciones y soporte.

## Evidencia directa de `main`

### Samuel

La web ya ofrece una solicitud manual de ejemplar firmado, pero no un pedido transaccional. El lector contacta y la disponibilidad/dedicatoria/envío se confirman antes de cerrar nada.

Esto sirve como señal de demanda para K.1, pero no acredita:

- stock propio estable;
- stock de componentes adicionales;
- packaging;
- coste/margen de un pack;
- capacidad de fulfillment repetible;
- demanda de un bundle concreto.

### Las manecillas del recuerdo

En la base auditada `editorial-facts.json` mantiene:

- `releaseDate: 2026-09-03`;
- `availability: not_available`;
- `editionStatus: not-published`;
- `purchaseUrl: null`.

`scripts/check-editorial-facts.py` gobierna el prelaunch. K.2 no puede usar una futura edición de Manecillas como componente comercial antes de que esa autoridad pase correctamente a estado publicado/disponible.

## Dependencia obligatoria con K.1

K.2 hereda todos los gates de K.1 y añade otros.

```text
K.1 seller/rights/stock/payment/shipping/support
+ bundle SKU exacto
+ stock por componente
+ packaging
+ coste de ensamblado
+ peso/volumen y tarifa de envío
+ margen total
+ sustituciones/agotados
+ política de bundle parcial/dañado
+ demanda específica
= K.2 reabrible
```

No crear una segunda infraestructura comercial. Si K.1 llega a usar checkout alojado o una operación manual controlada, K.2 debe reutilizar ese mismo owner y flujo.

## Gate de reapertura

Reabrir únicamente cuando se cumplan **todas** estas condiciones:

1. Manecillas está en estado de lanzamiento/publicación autorizado por el contrato editorial si forma parte del pack.
2. Existe una operación K.1 real o equivalente con seller, stock, fulfillment y soporte definidos.
3. El bundle tiene un SKU/producto exacto, no una lista de ideas.
4. Cada componente tiene derechos/permiso de venta claros.
5. Existe stock o proveedor comprometido para cada componente.
6. Se conocen coste unitario, packaging, coste de preparación y PVP.
7. Se ha calculado margen después de pago, embalaje, envío, incidencias e impuestos/costes aplicables.
8. Se conocen territorios y tarifa/peso real de envío.
9. Hay política para pérdida, daño, agotado de un componente y devolución.
10. Hay demanda observada o un experimento de interés explícito suficientemente concreto.
11. Existe owner operativo.

## Cómo validar demanda sin inventar un producto

Orden recomendado:

1. observar primero demanda real de ejemplares firmados mediante K.1;
2. detectar qué extras piden realmente los lectores;
3. definir una propuesta física con coste real;
4. validar interés con una descripción concreta y sin cobrar;
5. fijar umbral de producción/go-no-go;
6. solo después construir superficie comercial.

No recoger dirección postal ni pago durante una prueba de interés. Si se usa email, debe quedar clara la finalidad y no convertirse automáticamente en newsletter.

## Qué puede considerarse un bundle real

Solo elementos confirmados. Por ejemplo:

```text
sku
book_edition
signed = true|false
included_items[]
item_rights[]
stock_by_item
packaging
weight
unit_cost
price
shipping_scope
returns_rule
owner
status
```

Un mockup, una imagen promocional, un marcapáginas diseñado o un objeto mostrado en creatividades **no son inventario**.

## Alternativas evaluadas

### A. No bundle — correcta ahora

Mantiene foco en la conversión principal de los libros y evita stock muerto antes de conocer demanda.

### B. Pack manual limitado — primera opción si aparece demanda

Si K.1 ya funciona manualmente y existen unidades/componentes reales, un lote pequeño y acotado permite medir:

- tiempo de preparación;
- roturas/incidencias;
- coste de packaging;
- coste de envío;
- margen;
- demanda.

Debe seguir siendo una oferta real con condiciones claras; «manual» no elimina obligaciones comerciales.

### C. Checkout alojado — solo después del producto

Puede reutilizar la solución de K.1. No instalar Shopify/WooCommerce/otra plataforma solo para explorar si el bundle interesa.

### D. Ecommerce propio — rechazado en esta fase

No hay volumen ni catálogo que justifique otra capa de stock/órdenes/backend.

## Definition of Ready para diseño web

Antes de diseñar una landing de venta debe existir un registro parecido a:

```text
product_name
sku
components
rights_verified
supplier_or_stock_source
stock_owner
unit_cost
packaging_cost
shipping_cost_model
price
margin_estimate
territories
returns_support
expected_demand
go_no_go
reviewed_at
```

Si falta esa ficha, la web no tiene un producto que representar.

## Qué NO hacer

- «Edición coleccionista próximamente» sin proyecto aprobado;
- mockups tratados como producto existente;
- contador de unidades artificial;
- `Offer` schema sin oferta real;
- precio o disponibilidad hipotéticos;
- preventa sin condiciones/fulfillment resueltos;
- crear otro journey de Brevo para un producto no definido;
- usar K.2 para saltarse el gate editorial de Manecillas;
- crear infraestructura distinta a K.1.

## QA / CI de esta PR

HEAD auditado antes de esta ampliación: `7c526c087436f7eada835b5f476d9f727eb939b4`.

Runs observados en `success`:

- Check content indexes — `33312959493`;
- Required merge gate — `33312959478`;
- Accessibility baseline (Pa11y) — `33312959490`;
- Runtime scoping QA — `33312959470`;
- Public artifact contract — `33312959494`;
- Analytics taxonomy QA — `33312959545`;
- CSP public shell QA — `33312959525`;
- Sitewide Reflow QA — `33312959481`.

La modificación de esta revalidación debe volver a pasar los checks de la rama.

## Cierre

K.2 sigue en `DEFER`, pero ya no como una idea aparcada sin criterio: queda formalmente subordinada a K.1, al estado editorial real de Manecillas y a una ficha de producto/margen/logística verificable. Si esos gates se abren, la primera prueba debe ser pequeña y reutilizar la operación existente; no crear una segunda plataforma comercial.

Mantener DRAFT.