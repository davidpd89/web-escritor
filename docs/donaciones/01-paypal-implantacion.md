# PayPal — implementación mínima, sin cuenta personal visible

**Fecha de revisión 22/10/2026.** Requiere una cuenta receptora propia en PayPal; no se pueden inventar enlaces ni recibir pagos sin configurarla. Documento de integración, **no activación**.

## Camino preferente: enlace oficial alojado

1. En PayPal, configurar una cuenta Business y la presentación pública (nombre comercial del escritor/proyecto, logo y correo comercial, si lo permite el producto); la verificación legal y bancaria se hace solo dentro del proveedor.
2. Comprobar si el producto **Donar** está disponible en la cuenta desde https://www.paypal.com/donate/buttons . El SDK vigente indica expresamente que la posibilidad de iniciar ese flujo en la cuenta es la prueba de elegibilidad (https://developer.paypal.com/sdk/donate/, actualizado 14/09/2026).
3. Crear botón/link, elegir EUR e importe libre cuando el panel lo permita, copiar URL emitida por PayPal y comprobar dominio, destinatario y checkout.
4. Si «Donar» no está disponible, estudiar los **enlaces/botones de pago oficiales** (https://pep.paypal.com/es/cshelp/article/%C2%BFc%C3%B3mo-puedo-crear-un-enlace-y-un-bot%C3%B3n-de-pago-help262), etiquetando la transacción correctamente. No camuflar pagos comerciales como transferencias entre amigos.
5. Probar con un pago pequeño en vivo o sandbox cuando lo soporte la integración y revisar en incógnito el **nombre, email y datos que ve el pagador** y el recibo. No publicar hasta validarlo.

## Bloque completo listo para adaptar

El enlace debe pegarse **literalmente desde el panel PayPal**, no construirlo con correo o teléfono en HTML. Ejemplo de UI nativa (original, sin SDK, se integra en `/apoyar/`):

```html
<!-- Reemplazar SOLO con URL oficial comprobada; ocultar todo el enlace si no existe. -->
<a class="support-method"
   href="URL_OFICIAL_DE_PAYPAL_GENERADA_EN_EL_PANEL"
   target="_blank"
   rel="noopener noreferrer"
   aria-label="Aportar con PayPal; se abre PayPal en otra pestaña">
  <strong>PayPal</strong>
  <span>Continuar en PayPal para elegir la aportación</span>
</a>
```

**Condición de publicación:** no usar este placeholder en el HTML desplegado. Validación `URL`: protocolo HTTPS y `hostname` exactamente `paypal.com` o subdominio verificado terminado en `.paypal.com` (no `paypal.com.ejemplo.net`). No almacenar identificador personal del receptor en el código; `hosted_button_id` es un identificador de botón **público**, no una clave secreta, pero evita publicarlo antes de verificar identidad y destino.

## Alternativa B: SDK Donate en ventana superpuesta (no V1)

Documentación actualizada 14/09/2026: https://developer.paypal.com/sdk/donate/ .
Permite popup sin abandonar la página, pero añade `https://www.paypalobjects.com/donate/sdk/donate-sdk.js`, imágenes externas, potenciales frames/popup y requiere cambios puntuales de CSP y pruebas de bloqueadores, móvil y accesibilidad. Si el enlazado de V1 funciona, **no incorporar SDK**.

Ejemplo de invocación de API (reescritura mínima del contrato documentado, no un botón funcional hasta disponer de ID):

```js
// SOLO si la cuenta es elegible y el script oficial ya se cargó.
if (window.PayPal?.Donation && typeof window.PayPal.Donation.Button === 'function') {
  window.PayPal.Donation.Button({
    env: 'production',
    hosted_button_id: 'ID_DE_BOTON_REAL_CONFIRMADO'
  }).render('#paypal-donate-container');
}
```

No marcar transacción como exitosa desde `onComplete` o redirección: conciliar en el panel de PayPal. La capa SDK **no** se autoriza en la primera fase; no relajar CSP con comodines.

## Tarifas reales España

https://www.paypal.com/es/business/paypal-business-fees (publicado con actualización 07/09/2026). La recepción de donativos nacionales clasificados como tales: **2,90 % + 0,35 €** en EUR. La operación podría clasificarse como otro pago comercial si usa otro producto y tendría otras tarifas. Recibir desde fuera del EEE y cambios de divisa puede aumentar comisiones. Las tasas reducidas para **organizaciones benéficas** requieren acreditación y aprobación previa: **no aplicarlas** por ser página de autor.

PayPal afirma que empresas con ánimo de lucro pueden aceptar donativos; no se presume condición benéfica: https://www.paypal.com/es/cshelp/article/%C2%BFc%C3%B3mo-puedo-conseguir-asistencia-financiera-adicional-para-mi-empresa-help241 .

## Privacidad del titular

Evitar PayPal.Me asociado a cuenta personal si muestra datos personales. Los visores del pago pueden ver nombre o nombre comercial, imagen y determinados datos de la cuenta en función del producto y ajustes. Ver explicación oficial: https://www.paypal.com/us/privacy-center/privacy-practices y https://help.ko-fi.com/hc/en-us/articles/115004001294-What-personal-information-is-shared-on-Ko-fi-as-a-creator . **No prometer anonimato** ni exención de obligaciones de identificación legal.

## Criterios para Claude

- [ ] Cuenta habilitada y botón legítimo; URL copiada del panel.
- [ ] Nombre, correo, datos visibles y descriptor revisados con un donante de prueba y justificante.
- [ ] Vista móvil escritorio, ventana emergente no bloqueada porque se usa enlace externo V1.
- [ ] Botón solo visible cuando esté configurado, sin callback de «éxito» inventado.
- [ ] Sin scripts PayPal inyectados ni cambios CSP en V1.
- [ ] Estado del cobro se concilia en panel y no con `?success`.
