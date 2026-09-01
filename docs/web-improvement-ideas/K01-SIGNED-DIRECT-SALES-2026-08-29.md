# K.1 · Venta directa de ejemplares firmados/dedicados

**Estado histórico final de PR #135:** `CONDITIONAL`  
**Matriz intermedia:** `CONDICIONAL`  
**Regla:** no presentar una oferta de venta directa hasta que existan derechos/permiso, stock, precio/proceso comercial, fulfillment, fiscalidad y tratamiento de datos definidos. Preferir un tercero o flujo controlado antes que construir carrito propio.

> Esta especificación identifica requisitos de producto/operación. No sustituye asesoramiento fiscal, contable, contractual o jurídico cuando sea necesario.

## 1. Hipótesis original

K.1 proponía ofrecer un canal propio para quien quisiera comprar un ejemplar firmado/dedicado directamente al autor en lugar de acudir a Amazon/librería. La idea original incluso contemplaba una solución aparentemente sencilla, como derivar a un formulario de contacto en vez de crear un carrito.

La revisión de #135 corrigió precisamente esa aparente sencillez: **en cuanto el sitio acepta una solicitud de compra real, aparece una operación comercial y logística**, aunque el pago no ocurra dentro de la web.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Canal propio para copias firmadas; quizá formulario simple. |
| Revisión 108/108 | `CONDITIONAL` | Stock, cobro/factura, envío, devoluciones y PII; business case/logística primero; preferir plataforma externa. |
| Matriz operativa | `CONDICIONAL` | Solo con stock/logística/fiscalidad/proceso real; tercero/formulario controlado antes que carrito propio. |
| Repo cross-check/overrides | operación real obligatoria | No inventar oferta, disponibilidad, retailer o relación comercial. |
| Autoridad final | `CONDITIONAL` | Venta firmada solo si existe operación/comisión/disponibilidad real. |
| Revalidación independiente | mantenido | Comercio solo con derechos, logística y oferta reales. |

El estado nunca fue `IMPLEMENT_NOW`: primero debe existir el producto/operación fuera del código.

## 3. Estado real de `main` al 29/08/2026

La página canónica de *Las manecillas del recuerdo* publica actualmente hechos editoriales como:

- Monza Ediciones;
- publicación: 3 de septiembre de 2026;
- 272 páginas;
- PVP indicado: 16 €.

Estos hechos **no demuestran**:

- que el autor disponga de stock propio;
- que el contrato/editorial permita o contemple venta directa;
- qué margen/coste de ejemplar existe;
- que se puedan ofrecer ejemplares firmados como producto propio;
- qué territorios se pueden servir;
- cómo se facturaría/cobraría;
- quién responde por envío, pérdida, daño o devolución.

En la evidencia de la página de Manecillas inspeccionada no se ha localizado un flujo de compra directa firmada ya implementado. Una búsqueda de código por `firmada` tampoco devolvió resultados, pero el índice de búsqueda del conector ha dado falsos negativos en este repositorio; por eso esa ausencia se trata solo como señal secundaria, no como prueba absoluta.

## 4. Trigger comercial obligatorio

K.1 solo puede reabrirse cuando estén respondidas, como mínimo, estas preguntas:

### Derechos / relación editorial

- ¿puede el autor vender directamente ejemplares de esa edición?
- ¿cómo obtiene legal/contractualmente el stock?
- ¿hay restricciones de precio, territorio, canal o presentación?
- ¿puede publicitar una “edición firmada/dedicada” con ese ejemplar?

No inferir estas respuestas del hecho de ser autor del libro.

### Stock

- unidades disponibles;
- reposición;
- coste por unidad;
- stock reservado para eventos/ferias;
- qué ocurre cuando se agota;
- quién actualiza disponibilidad.

### Cobro/fiscalidad

- quién vende formalmente;
- cómo se registra/cobra la operación;
- método de pago;
- justificante/factura cuando corresponda;
- impuestos/obligaciones aplicables validados con profesional si hace falta.

### Fulfillment

- preparación/embalaje;
- transportista;
- coste de envío;
- países/zonas servidas;
- tracking cuando exista;
- pérdida/daño;
- tiempos de preparación realistas;
- quién atiende incidencias.

### Devoluciones/cancelaciones

- política aplicable;
- particularidades de una dedicatoria personalizada si las hubiera, validadas jurídicamente antes de comunicarlas;
- proceso de contacto y reembolso.

### Datos

- nombre;
- email;
- dirección postal;
- dedicatoria solicitada;
- datos de pago solo en proveedor autorizado, nunca almacenados directamente por la web;
- retención/borrado/owner.

Hasta tener este diseño, no existe una oferta que el sitio deba “implementar”.

## 5. Business case mínimo

Antes de escribir código, estimar con cifras reales:

```text
PVP real permitido
- coste del ejemplar
- embalaje
- comisión de pago/plataforma
- coste/parte de envío asumida
- impuestos/costes administrativos
- tiempo manual de firma/preparación/soporte
= margen y carga operativa aproximados
```

También estimar demanda:

- consultas reales en firmas/redes/email;
- interés por dedicatoria;
- volumen mensual plausible;
- si la ventaja frente a comprar en librería compensa la operación.

No crear checkout para validar una demanda que puede comprobarse primero de forma más barata y segura.

## 6. Escalera de implementación preferida

### Fase 0 — sin oferta

Mantener retailers/canales reales actuales. Es la opción correcta mientras los gates anteriores estén abiertos.

### Fase 1 — tercero externo de confianza

Si existe una plataforma adecuada que gestione pago/confirmaciones y encaje con la logística real:

- enlace claro;
- disclosure de relación si aplica;
- datos sensibles en el proveedor;
- la web no procesa tarjeta;
- disponibilidad factual.

Esta es la ruta preferida frente a construir e-commerce propio.

### Fase 2 — solicitud controlada, no checkout

Solo si existe un proceso manual válido de venta/cobro posterior y el volumen es pequeño.

El formulario debe decir claramente que es, por ejemplo, una **solicitud/reserva/contacto**, no “compra completada”, si el pago/stock aún requieren confirmación.

Aun así procesa PII y crea obligaciones operativas; no es gratis desde el punto de vista de privacidad/soporte.

### Fase 3 — carrito/checkout propio

Solo si el volumen real demuestra que las fases anteriores son insuficientes y hay capacidad para mantener:

- catálogo/stock;
- backend/orden;
- pagos mediante proveedor especializado;
- webhooks/idempotencia;
- emails transaccionales;
- reembolsos;
- seguridad;
- soporte;
- accesibilidad;
- QA E2E.

No construir esta fase por prestigio de marca.

## 7. Dedicatoria: modelar sin sorpresas

Si se ofrece dedicatoria:

- definir longitud/formatos permitidos;
- evitar campo ilimitado si no aporta;
- no prometer texto exacto antes de revisar límites;
- tratar el texto como dato potencialmente personal;
- no reutilizar dedicatorias para marketing;
- mostrar preview/resumen antes de confirmar si hay checkout;
- aclarar qué se puede/no se puede solicitar si existen límites editoriales.

Nunca publicar dedicatorias de clientes como testimonios/contenido sin permiso.

## 8. No procesar tarjetas directamente

La web no debe recibir/guardar:

- PAN/número de tarjeta;
- CVV;
- credenciales bancarias.

Usar un proveedor de pagos/plataforma que asuma la superficie correspondiente si se llega a esa fase. K.1 no autoriza ampliar el sitio estático con un backend casero de pagos.

## 9. Disponibilidad y copy

No publicar frases como:

- “Compra tu ejemplar firmado ahora”;
- “Stock disponible”;
- “Envío en 24/48 h”;
- “Edición exclusiva”;
- “Envío internacional”

hasta que cada afirmación sea operativamente cierta y mantenible.

Si la oferta se agota/pausa, la UI debe cambiar rápidamente y ofrecer una alternativa real, no aceptar pedidos imposibles.

## 10. Privacidad y seguridad

K.1 dispararía una revisión extraordinaria de I.2/I.5 porque introduce categorías nuevas:

- identidad de comprador;
- dirección;
- contenido de dedicatoria;
- estado de pedido;
- potenciales datos fiscales/transaccionales;
- proveedores de pago/envío.

Necesita definir:

- finalidad;
- campos mínimos;
- receptor/proveedor;
- retención;
- acceso interno;
- export/delete cuando aplique;
- logs;
- CSP/network hosts si se integra un proveedor;
- política pública actualizada antes de producción.

No enviar datos de pedido a analytics.

## 11. UX y accesibilidad

Si llega a existir:

- precio total/condiciones claros antes de confirmar;
- gastos de envío no ocultos hasta el último momento;
- errores de formulario accionables;
- teclado/focus/labels correctos;
- estados de loading/success/error robustos;
- no doble-submit;
- confirmación que diferencie pedido recibido de pago completado;
- móvil/reflow 200 %;
- alternativa de contacto para incidencias.

No usar dark patterns de escasez o urgencia artificial.

## 12. Relación con otras ideas

- **K.2/K.4:** no crear bundles/merch antes de validar esta operación básica.
- **K.3:** afiliación es un canal distinto; no mezclar comisión externa con venta propia.
- **I.2/I.5:** nuevos datos/proveedores obligan a actualizar inventario/minimización.
- **M.1:** checkout/backend ampliaría superficie de seguridad.
- **H.1/H.2:** compra no equivale automáticamente a consentimiento de newsletter.
- **C.1/Q.4:** lanzamiento y disponibilidad deben derivar de hechos actuales.

## 13. Qué no hacer

- No asumir permiso de venta directa por ser el autor.
- No anunciar stock inexistente/no verificado.
- No crear un carrito antes del business case.
- No recoger dirección “por si acaso”.
- No tratar un formulario de solicitud como pago completado.
- No guardar datos de tarjeta.
- No añadir automáticamente compradores a newsletter.
- No inventar política de devolución para una dedicatoria personalizada sin validación.
- No prometer envío/territorios no operativos.
- No mezclar pedidos reales con analytics/CRM de marketing sin finalidad/base separadas.

## 14. Definition of Done antes de publicar una oferta

- [ ] derechos/permiso contractual confirmados;
- [ ] stock y reposición definidos;
- [ ] PVP/margen/costes calculados;
- [ ] proceso fiscal/contable validado;
- [ ] territorios/envío/embalaje/transportista definidos;
- [ ] política de incidencias/devoluciones validada;
- [ ] proveedor de pago/plataforma elegido si aplica;
- [ ] no se procesan tarjetas directamente;
- [ ] campos de pedido minimizados;
- [ ] I.2/I.5 y privacidad actualizados;
- [ ] estados stock/error/agotado diseñados;
- [ ] accesibilidad/seguridad/E2E probados;
- [ ] copy no afirma nada más allá de la operación real;
- [ ] existe owner para atención y cumplimiento de pedidos.

## 15. Trazabilidad #135

Revisados:

- `IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis K.1;
- `IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `CONDITIONAL`, stock/cobro/factura/envío/devoluciones/PII y preferencia por tercero;
- `IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `CONDICIONAL`, business/logística/fiscalidad primero;
- repo cross-check/overrides — no inventar oferta/comisión/disponibilidad;
- autoridad machine-readable;
- `PR135-FINAL-AUTHORITY-2026-08-28.md` — `CONDITIONAL`;
- `PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — comercio solo con derechos/logística/oferta reales;
- revalidación de `main` 29/08/2026 — datos editoriales de Manecillas sí; operación de venta directa firmada no demostrada en la evidencia inspeccionada.

## 16. Cierre

K.1 puede tener valor comercial y de relación con lectores, pero solo después de existir como **operación real**. El orden correcto es derechos + stock + números + fulfillment + privacidad + pago; la web es la última capa. Un formulario no elimina esas obligaciones, solo las desplaza a una operación manual.