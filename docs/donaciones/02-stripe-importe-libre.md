# Stripe Payment Links — aportación con importe elegido por visitante

**Revisado 22/10/2026.** Propuesta sin SDK, claves API, cuenta bancaria publicada ni backend; todo el checkout lo aloja Stripe. Este documento no crea una cuenta, enlace real ni cobra.

## Funcionalidad verificada por Stripe

Documentación del proveedor: https://support.stripe.com/questions/how-to-accept-donations-through-stripe . Stripe Payment Links ofrece:
- **Importe variable**: modo `Customers choose what to pay`, pago **único**.
- Importe sugerido opcional, mínimo y máximo desde el Dashboard.
- Título, descripción, branding y CTA «Donate» si corresponde.
- Enlace compartible, que sigue activo hasta desactivarlo.
- **Importe recurrente** solo mediante pago de cuantía fija/suscripción; no prometer recurrencia con importe libre.

En Stripe Dashboard: **Payment Links → Create → Customers choose what to pay**. Nombre sugerido `Apoyo voluntario a los recursos de David Porto Díaz`; EUR, mínimo sugerido a validar por el proveedor, sin recibir producto ni ventaja a cambio. Revisar descripción fiscal/actividad y configuración de correo recibo.

## HTML V1 listo para adaptar

```html
<!-- Pegar solo una URL real obtenida en el Dashboard; NO enviar amount arbitrario por JS. -->
<a class="support-method"
   href="https://buy.stripe.com/ENLACE_REAL_GENERADO"
   target="_blank" rel="noopener noreferrer"
   aria-label="Aportar con tarjeta u otros métodos; se abre Stripe en otra pestaña">
  <strong>Tarjeta y otros medios</strong>
  <span>Elige el importe y paga de forma segura con Stripe</span>
</a>
```

Reemplazar por URL íntegra copiada del dashboard; no inventar `?amount=` ni parámetros ocultos. El importe lo introducen en el checkout Stripe, que controla validación, SCA/3DS, métodos disponibles, moneda y recibo. No garantizar Apple Pay/Google Pay sin verificar su aparición real en dispositivos compatibles.

**No agregar** `stripe.js`, librerías, iframe de Checkout ni worker de creación de sesiones. En web estática, Payment Links evita gestión de claves y el requisito de backend. Nunca poner `sk_live_...` en frontend, repositorio, CSS, data o URL.

## Tarifas 22/10/2026

https://stripe.com/es/pricing — **1,5 % + 0,25 €** para tarjetas estándar EEE en pagos online (referencia, confirmar país/tipo de tarjeta y método), **2,8 % + 0,25 €** tarjetas premium EEE, **2,5 % + 0,25 €** UK, **3,15 % + 0,25 €** internacionales y posible +2 % por conversión. No afirmar que **todas** las donaciones cuestan solo 1,5 %. El pago recibido pasa al saldo Stripe y se liquida mediante el banco privado de la cuenta.

Stripe es compatible con España: https://stripe.com/global .

## Privacidad y comprobación real

1. Abrir cuenta y completar KYC con Stripe **privadamente**, aportar banco solo allí.
2. Nombre comercial y `statement descriptor` deben apuntar a marca pública: comprobar pantallas de checkout, recibo y extracto bancario de pagador. La información legal obligatoria puede variar.
3. Desactivar campos de dirección de envío, marketing opcional o recogida adicional no necesaria cuando Stripe lo permita. El visitante no tiene que facilitar datos en `davidportodiaz.com`.
4. Si hay mensaje de finalización, evitar página «Gracias por donar» que implique pago confirmado únicamente por redirección. Conciliar pagos en Stripe Dashboard; webhooks solo si se necesitara lógica posterior y se implementase backend.
5. No forzar redirección dentro de iframe; evitar popups y scripts de pago de terceros.

## Código reutilizable — evaluación, no importación innecesaria

Repositorio oficial https://github.com/stripe-samples/checkout-one-time-payments ; licencia **MIT**, archivo https://github.com/stripe-samples/checkout-one-time-payments/blob/main/LICENSE . Incluye múltiples servidores para construir sesiones Checkout. **No copiar a esta web** porque introduce backend, secretos y superficie de mantenimiento sin ventaja frente a Payment Links. Para la V1, el fragmento de arriba es HTML original equivalente al uso oficial de enlaces; no existe dependencia de fuente externa que adaptar.

Si más adelante se necesita importe personalizado **dentro** del propio dominio, reevaluar un checkout oficial alojado por Stripe con backend mínimo y con su test sandbox, no un formulario de tarjetas casero. Esa ampliación queda fuera de alcance.

## Aceptación de Claude

- [ ] Payment Link live real en EUR con importe voluntario y pago único.
- [ ] Checkout real en móvil y PC, medio tarjeta sin cuenta Stripe de visitante, 3DS cuando aplique.
- [ ] Validación de enlace `https://buy.stripe.com/...`; rechazar dominios parecidos o `javascript:`.
- [ ] Comprobar nombre del beneficiario/descriptor visible y justificante; ningún dato privado expuesto inesperadamente.
- [ ] Confirmación por Dashboard, no por URL de retorno ni tracking local.
- [ ] Pausar/habilitar Stripe desde configuración sin tocar páginas generadas una a una.
