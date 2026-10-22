# Stripe — aportación voluntaria por contenido ya ofrecido (implementación V1)

**22/10/2026 · Estado: código reusable y prueba local aislada superada; integración en página/checkout real PENDIENTE.** No hay cuenta Stripe vinculada, Payment Link real, cobros ni edición de `main`.

## 1. Problema real detectado y decisión

La versión anterior describía el apoyo al autor como «donación». **No es una donación benéfica** y Stripe distingue expresamente dos categorías:
- **Propina**: recompensa por contenido o servicios proporcionados, por ejemplo una herramienta gratuita que el visitante acaba de utilizar.
- **Donación**: destinada a un fin benéfico específico; no usar esta clasificación para financiar genéricamente una web personal.

**Conclusión:** proponer a Stripe «aportación voluntaria/propina por contenido gratuito publicado», sin prometer productos nuevos, contrapartidas ni desgravación. Verificar que la actividad real declarada a Stripe y el checkout concuerden. Stripe indica que creadores que distribuyen *su propio contenido en su propia web* no precisan aprobación previa como plataforma, **pero deben cumplir el contrato y están sujetos a revisión**. No afirmar que la cuenta está aprobada antes del alta.

Fuentes primarias, comprobadas el 22/10:
- [Stripe — requisitos para propinas/donaciones](https://support.stripe.com/questions/requirements-for-accepting-tips-or-donations?locale=es-ES).
- [Stripe — preguntas frecuentes de creación de contenido](https://support.stripe.com/questions/prohibited-and-restricted-businesses-list-faqs?locale=es-ES).
- [Stripe — reglas de negocios restringidos, última actualización 22/09/2026](https://stripe.com/legal/restricted-businesses).

**Bloqueador real:** la cuenta no está dada de alta ni hemos verificado su aprobación, identidad visible o enlace real. Un ejemplo HTML no resuelve ese punto y no debe publicarse como opción de cobro.

## 2. Función elegida: Payment Links, sin SDK ni servidor

La documentación oficial [Create a payment link](https://docs.stripe.com/payment-links/create) confirma:
- `Customers choose what to pay` (pago único; **no** recurrencia), con importe sugerido y mínimo/máximo opcionales.
- Enlace alojado en Stripe, compartible y reutilizable. El sitio solo necesita un enlace HTML.
- Stripe gestiona tarjeta y métodos dinámicos; Apple Pay/Google Pay dependen de cuenta, navegador, dispositivo y elegibilidad, **no se prometen**.
- El panel permite consultar pagos; no se deduce un pago exitoso de una redirección o un clic.
- Para la V1 no incorporar `stripe.js`, API, webhooks, botón JS embebido ni backend: no aportan nada al objetivo actual.

También ver [Sharing a Payment Link](https://docs.stripe.com/payment-links/share), [After a payment](https://docs.stripe.com/payment-links/post-payment) y [Payment Links, prestaciones](https://docs.stripe.com/payment-links).

## 3. Código REAL incorporado en esta PR

| Archivo | Función práctica |
| --- | --- |
| `scripts/support_stripe_link.py` | `validate_stripe_payment_link(url, production=True)`: solo URL `https://buy.stripe.com/<id>` sin parámetros; rechaza dominio impostor, `javascript:`, credenciales, querystring, URL malformada y enlace `test_` en producción. |
| `scripts/support_stripe_link.py` | `render_stripe_support_link(url)`: HTML de enlace accesible en español; devuelve cadena vacía si aún no hay URL: **no genera botones ficticios**. |
| `tests/test-support-stripe-link.py` | Contratos locales de dominio, modo test vs live, HTML sin script/iframe/secretos y sin render si falta configuración. |

Este código reutiliza solo el módulo estándar Python y el patrón de enlace alojado que Stripe documenta. No hemos copiado un servidor de Checkout del repositorio oficial porque sería trabajo inútil para este sitio estático. Repositorio evaluado: [stripe-samples/checkout-one-time-payments](https://github.com/stripe-samples/checkout-one-time-payments), licencia [MIT](https://github.com/stripe-samples/checkout-one-time-payments/blob/main/LICENSE); **no se ha incorporado su código**.

### Conexión exacta para el futuro generador de `/apoyar/`

En el generador Python de la página de apoyo, **una vez obtenida y verificada la URL de Stripe**, importar la función:

```python
from scripts.support_stripe_link import render_stripe_support_link

# Configuración pública leída de forma explícita. No introducir enlaces de ejemplo.
STRIPE_PAYMENT_LINK = ""  # vacío = Stripe oculto; reemplazar SOLO por URL del panel
stripe_method_html = render_stripe_support_link(STRIPE_PAYMENT_LINK)
# Inyectar stripe_method_html dentro de <div class="support-methods">...
```

No hay que añadir componentes por cada herramienta. La conexión de `/apoyar/` y la del footer corresponden a la PR UX **#703**, con `data/navigation.json` + `data/content-registry.json` y regeneración del shell. Esta hija **no modifica páginas publicadas**.

## 4. Configuración en Dashboard — acción concreta sin inventar URLs

1. Abrir [Crear Payment Link](https://dashboard.stripe.com/payment-links/create/customer-chooses-pricing) en la **cuenta real y revisada** del autor.
2. Elegir `Customers choose what to pay`, importe único en EUR. Título: **«Apoyo voluntario por los recursos gratuitos»**; descripción: «Si las herramientas o guías de davidportodiaz.com te han servido, puedes dejar una aportación opcional. No es una donación benéfica ni concede acceso adicional».
3. Sugerir 5 € (opcional). No imponer mínimo alto; validar mínimo/máximo aceptados por Stripe en EUR. No inventar cantidades fijas ni crear suscripciones.
4. Desactivar campos adicionales innecesarios, promociones, dirección de envío y cobros recurrentes cuando el Dashboard lo permita. Elegir métodos apropiados para el pago puntual.
5. En detalles públicos/branding, comprobar **nombre y descriptor en extracto y recibo**, no solo nombre interno de la cuenta. Ver [Stripe: nombre de cuenta vs nombre visible](https://support.stripe.com/questions/update-account-name-shown-in-the-dashboard?locale=es-ES). No se puede prometer ocultar toda identidad legal: la pantalla y el justificante real mandan.
6. Obtener la URL con «Copy link» (formato `https://buy.stripe.com/...`). Antes de publicar confirmar que la cuenta es real y el enlace está activo, moneda, destino y modo de prueba/live.
7. Sustituir la cadena vacía por la URL real **solo en la configuración fuente** del generador, nunca editando 100 HTML regenerados a mano.
8. Elegir confirmación alojada por Stripe, sin redirección a una página propia que finja pago verificado. Conciliar pagos desde [Stripe Dashboard](https://dashboard.stripe.com/payments).

## 5. Costes verificados, sin falsas garantías

[Stripe España, tarifas](https://stripe.com/es/pricing): 1,5 % + 0,25 € en tarjeta estándar EEE; 2,8 % + 0,25 € premium EEE; 2,5 % + 0,25 € tarjeta UK; 3,15 % + 0,25 € internacional, más +2 % cuando proceda conversión. Son **tarifas orientativas por tipo**, no la comisión definitiva de la cuenta ni de cualquier método.

## 6. Definición de terminado: evidencia y pruebas

**Comprobable sin credenciales (incluido ahora en la rama):**
- [x] Código independiente del SDK y sin claves en cliente.
- [x] Tests de rechazo para host falso, URL de prueba en producción y ausencia de link. **Ejecutados localmente en una copia aislada de estos dos archivos: OK; compilación Python OK. No es prueba del árbol completo ni CI.**
- [x] Ubicación de código en repo y contrato de incorporación al futuro generador.

**Pendiente de cuenta y navegador reales (NO declarar verificado):**
- [ ] Stripe aprueba la actividad declarada de propinas por contenido publicado.
- [ ] Enlace real `live` con importe libre/único EUR activo y disponible; se comprueba también apertura en móvil.
- [ ] Desde navegador privado probar monto, tarjeta, SCA/3DS si aplica; comprobar la identidad pública que ve un pagador, el recibo y el descriptor. No subir imágenes con datos del comprador al repo.
- [ ] Confirmar en Dashboard pago/comisión y destino receptor (o simular en sandbox sin confundirlo con live).
- [ ] Revisar clasificación fiscal/IVA del supuesto real en España con asesor antes de cobrar.
- [x] Ejecutado `python tests/test-support-stripe-link.py` en copia local aislada: OK (22/10/2026).
- [x] Verificado **sin lanzar workflows** que `.github/workflows/required-merge-gate.yml` (línea 43) y `.github/workflows/tool-tests.yml` (línea 71) recorren `tests/test-*.py`: el nuevo nombre entra en ambos contratos de descubrimiento.
- [ ] Repetir `python tests/test-support-stripe-link.py` contra el árbol completo del repositorio y ejecutar los tests de shell/sitemap/UX en la fase de integración; **no ejecutar Actions manualmente durante esta investigación**.
- [ ] Integrar HTML generado en `/apoyar/` mediante PR #703 y verificar que link ausente no se publica.

**No ampliar la integración Stripe** a SDK, página falsa de confirmación, suscripciones, Klarna ni webhooks hasta demostrar que el enlace alojado no basta.
