# PayPal — Payment Links de precio libre (V1, probado offline)

**Revisión 22/10/2026.** Estado: módulo Python + pruebas offline en esta PR. **No existe enlace del titular, cuenta comprobada, pago real ni página `/apoyar/` conectada.**

## Problema → decisión con fuente oficial

1. **Queremos PayPal, tarjetas e importe libre sin backend.** PayPal documenta que **Payment Links and Buttons** admite **Customer-set price** para *tips* y aportaciones, y que el checkout puede mostrar PayPal y tarjetas, según cuenta y región: [Create Payment Link, actualización 08/09/2026](https://developer.paypal.com/payment-links-buttons/create-payment-link/) y [Overview, actualización 19/08/2026](https://developer.paypal.com/payment-links-buttons/overview/). **Resultado: un enlace de PayPal podría bastar para la V1; Stripe solo si un flujo real demuestra que hace falta.**
2. **No es una campaña benéfica.** Describirlo como «Apoyo voluntario por los recursos gratuitos ya publicados», una aportación única de cuantía elegida por el visitante. No prometer deducción fiscal, membresía ni contraprestación. El **Donate SDK** oficial tiene elegibilidad específica y añade `paypalobjects.com`, popup y permisos CSP ([SDK, actualización 14/09/2026](https://developer.paypal.com/sdk/donate/)): **no usarlo en V1**.
3. **Privacidad del receptor.** Cuenta **Business** con nombre comercial y logo configurables según [Customize your checkout, 08/09/2026](https://developer.paypal.com/payment-links-buttons/customize/). PayPal [distingue las cuentas Business](https://www.paypal.com/es/cshelp/article/%C2%BFcu%C3%A1l-es-la-diferencia-entre-las-cuentas-personales-y-business%E2%80%AF-help318). **No garantiza anonimato**: probar qué nombre, dirección, teléfono y email aparecen en checkout y recibo antes de hacer público el enlace. Los datos reales/KYC y banco se facilitan **solo a PayPal**, no al repo.
4. **Precio y comisión reales.** [PayPal ES — tarifas de vendedor, actualizadas 07/09/2026](https://www.paypal.com/es/business/paypal-business-fees): la tabla general de transacciones comerciales nacionales indica **2,90 % + tarifa fija (0,35 € en EUR)** para «las demás transacciones comerciales» y **1,20 % + tarifa fija** para ciertos pagos con tarjeta sin cuenta. **El porcentaje aplicable a este checkout concreto está pendiente de comprobar en el detalle del pago**; no atribuirle tarifa benéfica ni afirmar que toda tarjeta tendrá 1,20 %.

## Implementación ya aportada en esta rama

| Archivo | Para qué sirve |
| --- | --- |
| `scripts/support_paypal_link.py` | `validate_paypal_payment_link(url)` acepta solo `https://www.paypal.com/ncp/payment/ID` o `https://paypal.com/ncp/payment/ID`, el patrón que figura en la [FAQ oficial de PayPal España](https://securepayments.paypal.com/es/cshelp/article/consejos-de-soluci%C3%B3n-de-problemas-con-los-enlaces-y-botones-de-pago-de-paypal-help1137). Rechaza hosts parecidos, enlaces personales `paypal.me`, Donate SDK, protocolos peligrosos y parámetros no previstos. |
| `scripts/support_paypal_link.py` | `render_paypal_support_link(url)` devuelve HTML accesible con salida a PayPal, o cadena vacía si aún no hay URL real; nunca muestra un `href="#"`. |
| `tests/test-support-paypal-link.py` | Contrato Python offline para casos válidos y maliciosos. Verifica que no se cargan iframe/SDK. **Ejecutado en copia aislada idéntica a los archivos añadidos: py_compile + test OK el 22/10/2026.** CI no ejecutado. |

**Conexión exacta** cuando Claude implemente `/apoyar/` (PR #703):

```python
from scripts.support_paypal_link import render_paypal_support_link

# Vacío significa «no mostrar PayPal», no una URL inventada.
PAYPAL_PAYMENT_LINK = ""
paypal_method_html = render_paypal_support_link(PAYPAL_PAYMENT_LINK)
# Inserta paypal_method_html en el área de métodos de /apoyar/.
```

**No pegar la URL de muestra de los tests**: es un enlace publicado como ejemplo por la documentación de PayPal, **no pertenece a este autor** ni sirve para demostrar un pago real. El validador inspecciona **forma**, no titularidad ni actividad; en los enlaces de PayPal no existe marcador test/live fiable comparable al prefijo `test_` de Stripe. El validador admite el enlace oficial limpio y **solo** el par `locale.x` + `country.x` documentado por PayPal (por ejemplo `locale.x=es_ES&country.x=ES`), comprobando su forma, nunca la disponibilidad del checkout. Rechaza parámetros extra, repetidos, valores mal formados y fragmentos. El generador HTML escapa correctamente `&` a `&amp;`. Fuente oficial actualizada 11/09/2026: https://developer.paypal.com/payment-links-buttons/troubleshooting/ ; códigos de España: https://developer.paypal.com/api/codes/locale/ . Prueba aislada local: 5 casos válidos, 10 inválidos, escape de HTML OK (22/10/2026); el test del árbol completo y el cobro real siguen pendientes.

## Pasos reales para cerrar la implementación

1. Cuenta **PayPal Business**, configuración de nombre público, logo, email comercial y datos de facturación; registrar la finalidad como **propina/apoyo a contenido gratuito**, sin fingir ser ONG.
2. En el panel: **Pay & Get Paid → Create Payment Links and Buttons → Product / Price → Customer-set price**, EUR y pago único. **No activar** precio fijo, cantidades, transporte, impuestos de venta imaginarios ni auto-return. [Pasos del proveedor](https://developer.paypal.com/payment-links-buttons/create-payment-link/).
3. Configurar métodos de pago admitidos; comprobar en la cuenta española que un visitante sin PayPal puede pagar con tarjeta (métodos dependen de la región y configuración). [Personalización PayPal](https://developer.paypal.com/payment-links-buttons/customize/).
4. Copiar URL real de `PayPal.com/ncp/payment/...`, conectar desde el **generador de `/apoyar/`**, no editar todos los HTML derivados. Abrir incógnito y en móvil.
5. Ejecutar un pago de valor pequeño (o sandbox si la cuenta/entorno lo permite), inspeccionar **destinatario, importe en EUR, recibo y detalles comerciales que ve el pagador**, conciliar transacción y tarifa real en el panel. No guardar pruebas con datos personales en GitHub. [PayPal exige comprobar pago y actividad](https://developer.paypal.com/payment-links-buttons/create-payment-link/).
6. **Solo si el flujo cumple estas pruebas**, decidir si Stripe debe aparecer en el selector: no añadir una segunda plataforma por defecto.

## Pendientes y resultados medibles

- [x] Modo «precio elegido por el visitante» localizado en documentación PayPal actual.
- [x] URL oficial de pago alojado y variante HTML sin JS, con validador y test de regresión.
- [x] `py_compile` y test local aislado OK; **no equivale a CI ni a prueba real de cobro**.
- [ ] Cuenta Business validada; URL real y recepción de fondos confirmadas en PayPal.
- [ ] Checkout sin cuenta PayPal verificado con tarjeta **desde España**; sin suposiciones de compatibilidad.
- [ ] Confirmar nombre/email/teléfono/dirección vistos por el pagador y en justificante.
- [ ] Tarifa y clasificación del pago reales comprobadas en Dashboard; tratamiento fiscal español revisado.
- [ ] Conexión a `/apoyar/`, footer y QA del sitio de PR #703, sin ejecutar Actions ni merge ahora.

No hay código de repositorio externo copiado porque el flujo alojado oficial requiere **solo un enlace**. Usar `paypal/paypal-js` (Apache-2.0) añadiría una dependencia que no resuelve ningún problema actual.
