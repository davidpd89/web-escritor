# K.1 · Revalidación de producción — venta firmada directa

Fecha: 2026-08-30  
Base auditada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
Tree de la base: `68d02e1fe8ac2cfa239f4a716929e992abb672fd`

## Veredicto

`CONDITIONAL · CONCIERGE_DEMAND_CAPTURE_EXISTS · TRANSACTIONAL_OPERATION_NOT_VERIFIED · MANECILLAS_PRELAUNCH_GATE_CLOSED · NO_CUSTOM_CHECKOUT`

K.1 **no parte de cero**. La web ya tiene en `/libros/samuel-entre-mundos/` una experiencia prudente de ejemplar firmado: el lector contacta por email y la página explica que se responderá con disponibilidad, dedicatoria y envío antes de confirmar nada. Eso es una capa real de intención/demanda y es el nivel correcto mientras la operación comercial no esté cerrada.

Lo que no existe todavía es una venta directa transaccional verificable: no hay checkout propio, orden, stock autoritativo, cálculo de envío, política operativa de incidencias/devoluciones ni prueba en el repo de que Manecillas pueda venderse directamente por el autor.

## Evidencia actual de `main`

### Samuel entre mundos

- `editorial-facts.json` mantiene tres destinos de compra factuales: editorial, Amazon y Casa del Libro.
- La página canónica ofrece `#ejemplar-firmado` como **solicitud**, no como compra completada.
- El flujo usa `mailto:` y pide contactar al autor; no procesa tarjeta ni crea una orden.
- El copy evita una promesa falsa de stock: disponibilidad, dedicatoria y envío se confirman antes de cerrar nada.

Conclusión: la web ya dispone de un experimento concierge de demanda con riesgo técnico bajo. No hay razón para sustituirlo por ecommerce mientras no exista evidencia operativa que lo justifique.

### Las manecillas del recuerdo

`editorial-facts.json` mantiene en la base auditada:

- `releaseDate: 2026-09-03`;
- `availability: not_available`;
- `editionStatus: not-published`;
- `purchaseUrl: null`.

`scripts/check-editorial-facts.py` es el owner existente de ese contrato y aplica un gate específico de prelaunch según `Europe/Madrid`. K.1 no debe crear un atajo comercial que contradiga ese owner.

## Qué problema resolveríamos realmente

La pregunta no es «¿podemos programar un checkout?». Sí podemos. La pregunta es si existe una operación que el checkout pueda representar de forma verdadera y sostenible.

Antes de aceptar un pago deben existir, como mínimo:

1. **seller/relación contractual** — quién vende formalmente y qué edición puede vender;
2. **stock autoritativo** — unidades, reposición, agotado y owner de actualización;
3. **precio total** — PVP real permitido, impuestos aplicables y costes;
4. **fulfillment** — embalaje, transportista, territorios, gastos y tiempos reales;
5. **incidencias** — pérdida, daño, dirección errónea, reenvío y soporte;
6. **devoluciones/desistimiento** — política validada para el producto concreto;
7. **fiscalidad/contabilidad** — cobro, registro y justificantes/facturación cuando corresponda;
8. **privacidad** — nombre, email, dirección y texto de dedicatoria con finalidad/retención/owner;
9. **demanda** — evidencia de que automatizar mejora una carga real, no una hipótesis.

## Mercado actual y alternativas

### A. Mantener el flujo concierge actual — opción por defecto

Ventajas:

- valida demanda antes de construir infraestructura;
- permite comprobar manualmente stock y condiciones;
- no introduce proveedor de pago ni tarjeta en la web;
- conserva una relación personal adecuada para una copia firmada;
- coste de implementación prácticamente nulo.

Limitación: no escala. Esa limitación solo importa cuando exista volumen real.

### B. Checkout alojado / Payment Link — primera automatización razonable

Stripe Payment Links permite actualmente crear una página de pago alojada sin construir un carrito propio. La página oficial de Stripe España publica Payment Links dentro de Payments y una tarifa estándar de `1,5 % + 0,25 €` para tarjetas estándar del EEE (consultado 2026-08-30).

Fuentes:

- https://stripe.com/es/payments/payment-links
- https://stripe.com/es/pricing

Este patrón es preferible a un checkout casero cuando exista una oferta real: reduce superficie PCI y complejidad frontend/backend. **No resuelve** stock, seller, impuestos, envío, desistimiento, soporte ni privacidad; por eso no es el trigger de implementación por sí mismo.

### C. Ecommerce/carrito propio — no justificado ahora

Solo tendría sentido con catálogo/volumen que requiera:

- stock sincronizado;
- múltiples productos/variantes;
- órdenes persistentes;
- webhooks/idempotencia;
- refunds;
- emails transaccionales;
- soporte y observabilidad E2E.

Construirlo ahora sería más superficie de seguridad y mantenimiento para una demanda no demostrada.

## Obligaciones de consumo que cambian el diseño

La guía oficial de Your Europe para venta B2C a distancia mantiene el derecho general de desistimiento de 14 días y exige información clara antes de la compra sobre características, precio/condiciones, entrega y desistimiento. Los bienes fabricados según especificaciones o claramente personalizados pueden quedar exceptuados, pero esa excepción debe interpretarse de forma estricta y no debe asumirse automáticamente para cualquier ejemplar simplemente «firmado».

Fuentes consultadas 2026-08-30:

- https://europa.eu/youreurope/business/selling-in-eu/selling-goods-services/ecommerce-distance-selling/index_es.htm
- https://europa.eu/youreurope/citizens/consumers/shopping/shopping-consumer-rights/index_es.htm
- https://eur-lex.europa.eu/legal-content/ES/ALL/?uri=CELEX:52021XC1229(04)

Esta documentación no sustituye una validación fiscal/jurídica aplicable al vendedor concreto.

## Gate medible para pasar de concierge a pago

No implementar cobro hasta que exista un registro de decisión con todos estos campos resueltos:

```text
seller
edition_or_product
right_to_sell = verified
stock_source
stock_owner
unit_cost
public_price
shipping_countries
shipping_rates
fulfillment_sla
returns_withdrawal_policy
support_owner
payment_provider
privacy_data_map
demand_signal
reviewed_at
```

Además, exigir una señal de demanda definida antes del piloto. No fijamos aquí un umbral ficticio de pedidos: el owner comercial debe elegirlo y documentarlo. La evidencia puede ser, por ejemplo, solicitudes reales del flujo actual durante una ventana temporal acordada.

## Plan de implementación cuando el gate se abra

1. Mantener el contrato editorial como autoridad de disponibilidad; no hardcodear stock en HTML.
2. Añadir la oferta comercial a una autoridad de datos explícita y revisable.
3. Empezar por checkout alojado, no tarjeta propia.
4. Pedir solo PII necesaria para fulfillment/dedicatoria.
5. Separar compra y consentimiento de marketing.
6. Actualizar privacidad/terceros antes de producción.
7. Añadir QA para estados disponible/agotado/error y para no aceptar pedidos cuando el gate esté cerrado.
8. Probar teclado, reflow 200 %, errores, doble submit y confirmación de pedido/pago.
9. Mantener una vía humana de soporte.

## Qué NO hacer

- convertir el `mailto:` actual en un formulario que parezca una compra sin operación detrás;
- afirmar «stock disponible», «24/48 h», «envío internacional» o «edición exclusiva» sin owner factual;
- asumir que una dedicatoria elimina automáticamente el derecho de desistimiento;
- almacenar tarjeta/CVV en infraestructura propia;
- añadir compradores a newsletter por defecto;
- crear un backend de pedidos para validar una demanda que el flujo concierge ya puede medir;
- reutilizar los hechos de Manecillas para saltarse su gate de prelaunch.

## QA / CI de esta PR

HEAD auditado antes de esta ampliación: `71c3ba252d602dde03397397ae5139a3cb1b980f`.

Runs de PR observados en `success`:

- Check content indexes — `33312948763`;
- Required merge gate — `33312948781`;
- Runtime scoping QA — `33312948802`;
- Public artifact contract — `33312948764`;
- Sitewide Reflow QA — `33312948773`;
- Accessibility baseline (Pa11y) — `33312948768`;
- Analytics taxonomy QA — `33312948767`;
- CSP public shell QA — `33312948774`.

La modificación de esta revalidación debe volver a pasar los checks de la rama antes de considerar el documento cerrado.

## Cierre

K.1 ya tiene una **Fase 1 útil**: captar y resolver manualmente interés por ejemplares firmados de Samuel sin fingir ecommerce. El siguiente paso no es programar más, sino convertir esa señal en una operación comercial verificable. Cuando exista, la opción técnica preferida es un checkout alojado y de bajo código antes que un carrito propio.

Estado final: `CONDITIONAL`; mantener DRAFT.