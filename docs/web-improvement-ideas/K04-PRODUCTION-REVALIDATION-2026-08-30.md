# K.4 · Revalidación de producción — merchandising

Fecha: 2026-08-30  
Base auditada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
Tree: `68d02e1fe8ac2cfa239f4a716929e992abb672fd`

## Veredicto

`DEFER · POD_REDUCES_INVENTORY_RISK_NOT_PRODUCT_RISK · NO_VERIFIED_MERCH_PRODUCT · DEMAND_AND_MARGIN_GATES_OPEN · NO_STORE`

El `main` auditado no presenta catálogo de merchandising ni una autoridad de productos físicos. Recursos gráficos, portadas, banners o mockups promocionales no son productos comercializables.

La revisión de mercado actual corrige un supuesto del planteamiento histórico: **MOQ e inventario ya no son requisitos inevitables**. El print-on-demand puede fabricar y enviar por pedido, incluso desde España. Eso reduce riesgo de stock, pero no resuelve la decisión de producto, derechos, calidad, margen, atención al cliente o experiencia de marca.

## Mercado actual: stock vs print-on-demand

Printful declara actualmente:

- sin pedidos mínimos;
- sin necesidad de inventario previo;
- pago por gestión cuando entra un pedido;
- centro de gestión en Barcelona para productos compatibles;
- costes de envío separados del precio base;
- necesidad de una tienda/marketplace conectado para vender automáticamente.

Fuentes consultadas 2026-08-30:

- https://www.printful.com/es/print-on-demand
- https://www.printful.com/es/print-on-demand-espana
- https://www.printful.com/es/guia-precios
- https://www.printful.com/es/vender-con-printful

Por tanto, el gate correcto no es `has_MOQ`; debe admitir dos modelos:

```text
fulfillment_model = owned_stock | print_on_demand
```

## Gates que siguen siendo obligatorios

Para un producto concreto:

1. propuesta que tenga sentido para lectores de esta obra/autor;
2. derechos de reproducción de portada, arte, fuentes, fotografías y marcas;
3. proveedor/producto exacto;
4. muestra física aprobada antes de promocionar calidad;
5. coste base + personalización + shipping + impuestos/costes aplicables;
6. PVP y margen neto razonable;
7. territorios y tiempos de entrega;
8. devoluciones, producto defectuoso y soporte;
9. owner de catálogo/retirada si cambia el proveedor;
10. señal de demanda suficiente.

## Dos caminos válidos

### A. Stock propio / tirada pequeña

Puede encajar mejor para marcapáginas, láminas firmadas o materiales de evento cuando:

- el coste unitario mejora con tirada;
- el autor controla calidad;
- la logística K.1 ya existe;
- el producto es ligero y simple.

Riesgo: inventario inmovilizado y fulfillment manual.

### B. Print-on-demand

Puede encajar para productos donde evitar inventario sea más importante que controlar cada unidad.

Ventajas:

- no MOQ;
- bajo riesgo de stock muerto;
- fulfillment delegado.

Costes/riesgos que siguen presentes:

- margen menor;
- shipping puede dominar el ticket;
- calidad debe validarse con muestras;
- variaciones/disponibilidad del catálogo del proveedor;
- atención al comprador no desaparece;
- requiere storefront/checkout compatible;
- branding/packaging limitado según producto/plan.

No instalar una tienda conectada a POD solo para «probar si gusta».

## Validación antes de integración

1. Elegir **un** producto, no un catálogo.
2. Resolver derechos.
3. Pedir muestra real y aprobar calidad.
4. Obtener coste total para España y, si aplica, UE.
5. Definir PVP/margen.
6. Mostrar concepto/interés a lectores sin prometer stock.
7. Fijar un umbral `GO/NO-GO` documentado.
8. Elegir stock propio o POD según economics/experiencia.
9. Reutilizar la operación K.1/K.2; no crear un tercer sistema comercial.

## Qué medir

- intención cualificada sobre el producto específico;
- conversión de interés a compra en piloto;
- margen después de producto, envío, fee e incidencias;
- defectos/devoluciones;
- tiempo de soporte por pedido;
- impacto en CTA principal de libros.

Likes, encuestas abstractas o mockups compartidos no equivalen a demanda pagadora.

## Productos de menor riesgo si aparece demanda

Por encaje editorial/logístico, evaluar primero elementos pequeños y directamente vinculados a la experiencia lectora:

- marcapáginas;
- postal/lámina;
- print firmado;
- pegatina solo si existe una dirección visual que realmente la justifique.

No priorizar ropa/tazas por disponibilidad de catálogo POD: que el proveedor pueda fabricarlo no significa que la marca de autor deba venderlo.

## Qué NO hacer

- crear `/tienda/` vacía;
- tratar un mockup de IA como producto real;
- fabricar varias referencias por catálogo disponible;
- asumir que POD elimina obligaciones de vendedor;
- conectar Printful/Shopify/etc. antes de validar producto y margen;
- usar assets de portada sin revisar derechos de reproducción;
- publicar `Offer`, precio, stock o tiempos que no tengan owner;
- abrir K.4 para saltarse K.1/K.2.

## QA / CI

HEAD auditado antes de esta ampliación: `8ba75c0556fc8122279b8b01b3875caadcb8b320`.

Ocho workflows de PR estaban en `success`: Public artifact contract `33313199561`, Runtime scoping `33313199546`, Analytics taxonomy `33313199586`, Required merge gate `33313199562`, Check content indexes `33313199549`, CSP public shell `33313199556`, Pa11y `33313199590` y Sitewide Reflow `33313199575`.

El nuevo commit debe volver a pasar CI.

## Cierre

K.4 permanece `DEFER`, pero por una razón más precisa: **el mercado ya permite eliminar casi todo el riesgo de inventario mediante POD, pero todavía no existe un producto ni una demanda que merezcan introducir una tienda**. Si aparece esa señal, comparar stock pequeño vs POD con muestra y economics reales y reutilizar la operación comercial existente.

Mantener DRAFT.