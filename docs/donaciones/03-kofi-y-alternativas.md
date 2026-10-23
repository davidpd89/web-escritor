# Ko-fi y alternativas — comparación enfocada a cobrar sin fricción

**Investigación 22/10/2026, sin cuentas ni enlaces activos.**

## Ko-fi Free: opción complementaria viable

Fuentes oficiales:
- https://help.ko-fi.com/hc/en-us/articles/360002506494-Does-Ko-fi-take-a-fee
- https://help.ko-fi.com/hc/en-us/articles/115004001294-What-personal-information-is-shared-on-Ko-fi-as-a-creator
- https://help.ko-fi.com/hc/en-us/articles/360013140633-Supporter-payments-FAQ

**Modelo:** aportaciones puntuales dirigidas directamente a la cuenta PayPal o Stripe enlazada. Los simpatizantes no necesitan abrir cuenta Ko-fi para dar una aportación. En modalidad **Free** configurada sin el modo Standard, Ko-fi declara **0 % de comisión propia en tips de una vez**; PayPal/Stripe sí cobran procesamiento. Las aportaciones mensuales, tienda y membresía tienen otras comisiones. **Standard** aplica 5 % también a propinas; nuevas cuentas pueden venir con funciones del modo de pago activadas por defecto: hay que revisar `Settings → Payment` y su elección real antes de comunicar 0 %.

**No publicar un perfil hasta confirmar** nombre público, PayPal Business vs personal, dirección/email visible, mensajes y privacidad del donante. Ko-fi no anula lo que PayPal o Stripe revelen: su documentación afirma que una cuenta PayPal personal suele enseñar nombre legal/email; Business ayuda a controlar la identidad comercial. Se puede optar por ocultar los mensajes públicos y mostrar solo el botón.

HTML propuesto (sin widget JS ni cookies externas):

```html
<a class="support-method"
   href="https://ko-fi.com/USUARIO_PUBLICO_VALIDADO"
   target="_blank" rel="noopener noreferrer"
   aria-label="Apoyar en Ko-fi; se abre otra pestaña">
  <strong>Ko-fi</strong>
  <span>Una aportación puntual mediante PayPal o tarjeta</span>
</a>
```

El `USUARIO_PUBLICO_VALIDADO` se sustituye exclusivamente con la URL entregada por Ko-fi. No crear `iframe` ni cargar widget flotante automático: sería más invasivo y no añade capacidad de pago.

## Buy Me a Coffee: alternativa B, no prioridad

- España sí figura entre países con pagos a creadores: https://help.buymeacoffee.com/en/articles/6258038-supported-countries-for-payouts-on-buy-me-a-coffee
- Comisión de plataforma declarada del **5 %**, además de procesamiento, según https://buymeacoffee.com/terms .
- Permite aportaciones sin crear cuenta, tarjetas/Apple Pay/Google Pay en regiones/dispositivos compatibles. https://help.buymeacoffee.com/en/articles/10182730-what-is-buy-me-a-coffee-and-how-does-it-work
- Cobro por Stripe y liquidación posterior a banco verificado; **no** es un método «dinero a PayPal» para el autor.

Código condicional si se comprueba que atrae público adicional:

```html
<a class="support-method" href="https://buymeacoffee.com/PERFIL_REAL"
   target="_blank" rel="noopener noreferrer">
  <strong>Buy Me a Coffee</strong>
  <span>Continuar en la plataforma de apoyo</span>
</a>
```

No recomendar simultáneamente 5 plataformas: produce fatiga de elección y fragmenta conciliación. Elegir 2 vías primarias, tercera solo si aporta ventajas de pago demostradas.

## Klarna: descartar por ahora

Klarna es modalidad de pago aplazado/financiación, no cuenta receptora independiente. Su soporte depende de país, plataforma y objeto del checkout, y puede generar coste alto; la tarifa orientativa de Stripe España comienza en **4,99 % + 0,40 €** para Klarna: https://stripe.com/es/pricing . No impulsar endeudamiento para contribuciones voluntarias ni ofrecerlo como plataforma de recepción.

## Otras rutas que NO merece la pena implementar en V1

- **Bizum por teléfono personal**: descartado por requisito expreso de no publicar móvil. Una integración comercial exige entidad/proveedor compatible y puede involucrar identificación/comisiones; no se añade sin caso de uso.
- **Transferencia bancaria pública**: descartada (expondría IBAN).
- **Cripto**: innecesario para público general, conciliación fiscal/operativa compleja, ruido UX.
- **Patreon/membresías**: sería un producto de suscripción y probablemente prometería ventajas; fuera de alcance de aportación puntual.
- **Liberapay/otras**: solo considerar tras verificar actualidad, payouts España, privacidad, cuenta receptora y comisiones; no inventar compatibilidad.

## Recomendación

**V1 — decisión vigente tras #700 y #698 (22/10/2026): probar primero un único PayPal Business Payment Link con importe libre; puede admitir PayPal y tarjeta en el mismo checkout según cuenta, comprador y región.** Añadir Stripe *solo* si el checkout real revela una carencia verificable de pago con tarjeta, privacidad, coste o experiencia. **Ko-fi Free** y BMC quedan como alternativas documentadas, no como botones por defecto. No desplegar una segunda pasarela solo para llenar la página: cada método adicional necesita una ventaja comprobada y sus pruebas de recepción/identidad.

## Lista de QA

- [ ] No aparecen opciones sin configuración real y consentida.
- [ ] Probar destinatario, comisiones efectivas, domicilio/nombre/correo visible y recibo.
- [ ] Verificar una aportación **única** con pago de invitado cuando el proveedor lo ofrezca.
- [ ] Comprobar si Ko-fi aplica 0 % o 5 % en la cuenta (no confiar solo en la página de precios).
- [ ] No superponer widgets, no añadir trackers a la página propia.
- [ ] Explicar claramente que el flujo termina fuera de la web y puede aplicar la política del proveedor.
