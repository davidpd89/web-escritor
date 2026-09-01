# K.2 · Bundle / edición coleccionista

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `DEFER`.

## Veredicto

#135 dejó K.2 diferida porque una oferta coleccionista no es una mejora web autónoma: exige producto real, derechos, stock, coste unitario, empaquetado, fulfillment, devoluciones y demanda suficiente. Sin eso, crear una landing o bundle sería inventar una oferta.

## Hipótesis original

La lista de 108 ideas proponía un paquete coleccionista o edición especial vendido mediante una pasarela externa confiable, evitando construir pagos propios.

La hipótesis buscaba aumentar monetización y valor percibido mediante un bundle físico.

## Evolución histórica

### Revisión 108/108 → `DEFER`

- valor bajo en el estado actual;
- coste operativo alto;
- no existe demanda/logística validada.

### Matriz final intermedia → `DEFERIR`

La formulación se endureció:

> bundle coleccionista solo tras validar demanda y derechos/stock.

### Autoridad final → `DEFER`

> «Bundle coleccionista tras validar demanda/derechos/stock.»

La revalidación independiente mantuvo el estado de todo K.1–K.5: comercio únicamente con derechos, logística y oferta reales.

## Estado actual de `main`

La inspección actual no encuentra una tienda, catálogo de merchandising ni bundle coleccionista en el repositorio.

Sí existe para *Samuel entre mundos* una vía manual de consulta de ejemplar firmado: la página explica que el usuario solicita información y recibe disponibilidad, dedicatoria y envío antes de confirmar nada. Esa prudencia **no equivale** a que exista un bundle.

Por tanto:

```text
signed-copy enquiry != collector bundle
book published != stock owned by author
retail price != margin available for bundle
assets/promotional objects != merchandise inventory
```

## Trigger de reapertura

Reabrir K.2 solo si existen simultáneamente:

1. producto físico definido;
2. derechos/permisos claros;
3. unidades/stock o proveedor confirmado;
4. coste unitario y margen;
5. embalaje y envío definidos;
6. política de incidencias/devoluciones;
7. demanda observada o experimento explícito de preventa/interés;
8. responsable operativo.

No basta una idea visual atractiva.

## Validación de demanda antes de construir

Orden recomendado:

1. detectar preguntas reales de lectores;
2. encuesta/lista de interés ligera si existe una oferta suficientemente concreta;
3. estimar coste total y umbral mínimo;
4. decidir si la producción es viable;
5. solo entonces diseñar la superficie web.

No recoger direcciones postales ni datos de pago durante una simple validación de interés.

## Qué podría contener un bundle real

Solo hechos confirmados, por ejemplo:

- libro firmado;
- marcapáginas producido;
- lámina/print con derechos;
- packaging definido;
- precio total real;
- unidades/disponibilidad;
- territorios de envío.

Nada de esto debe publicarse hasta existir físicamente o estar contractual/operativamente comprometido.

## Plataforma externa primero

#135 ya estableció para K.1 el principio de preferir plataforma externa antes que carrito propio. K.2 hereda esa regla:

- checkout alojado por tercero si se comercializa;
- no capturar tarjetas en el sitio;
- no construir sistema de pedidos propio por una campaña pequeña;
- no añadir dependencias de ecommerce antes de tener business case.

## Relación con K.1

K.1 trata la venta firmada unitaria. K.2 es más exigente porque introduce varios componentes, inventario y packaging. Que K.1 tenga una vía manual no dispara K.2.

## Relación con K.4

Si el bundle incluye merch, K.4 debe haber superado antes su propio gate de demanda/stock. No usar K.2 para saltarse esa decisión.

## Relación con H/email

Una lista de interés solo es razonable con oferta suficientemente concreta, consentimiento y propósito claros. No crear otro journey de Brevo por un producto hipotético.

## Riesgos

- stock muerto;
- costes de envío superiores al margen;
- pérdida/daño en transporte;
- derechos de imágenes/textos no claros;
- promesas de edición limitada sin control real;
- PII logística adicional;
- soporte manual desproporcionado;
- distraer conversión principal hacia libros/newsletter.

## Qué NO hacer

- landing «edición coleccionista próximamente» sin proyecto;
- mockups tratados como producto existente;
- contador de unidades artificial;
- reserva sin condiciones claras;
- recoger pago antes de definir fulfillment;
- integrar Shopify/WooCommerce/Stripe solo para explorar la idea;
- bundle generado únicamente porque «sube el ticket medio».

## Señal de salida del `DEFER`

Una decisión documentada debería incluir al menos:

```text
product
rights
supplier/stock
unit_cost
price
shipping_scope
returns/support
expected_demand
owner
go/no-go
```

## Trazabilidad preservada

- idea original de paquete coleccionista;
- revisión `DEFER`;
- matriz `DEFERIR`;
- autoridad final `DEFER`;
- principio K.1 de plataforma externa;
- revalidación independiente de comercio solo con oferta/logística real;
- contraste con la solicitud manual de firmado existente en Samuel.

## Recomendación para Clara/Claude

**No implementar ahora.** Si aparece una propuesta física real, primero cerrar business case, derechos, stock y logística. La web se diseña después, no antes.