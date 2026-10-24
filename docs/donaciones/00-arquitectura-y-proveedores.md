# Apoyar el contenido — investigación principal (22-10-2026)

> **Estado: diseño y evidencia, NO activado ni publicado como pasarela.** Esta PR se limita a preparar una implementación por piezas para revisar con Claude. No contiene cuentas receptoras, claves, teléfonos, IBAN ni URLs de cobro inventadas. No ejecutar Actions ni fusionar sin revisión.

## Decisión propuesta

Crear una página propia `/apoyar/`, legible desde móvil, que explique las aportaciones voluntarias y muestre **solo los canales que estén correctamente configurados y comprobados**. Una contribución no compra ninguna herramienta, contenido, prioridad, recompensa ni acceso. El pago se realiza en la página segura del proveedor: **nunca recoger tarjeta, CVC, credenciales de PayPal ni IBAN en nuestra web**.

Orden propuesto: (1) PayPal Business con enlace/botón alojado; (2) Stripe Payment Links con importe libre; (3) Ko-fi Free opcional como alternativa con PayPal/Stripe; (4) Buy Me a Coffee solo si aporta alcance diferencial. Klarna es «compra ahora/paga después», no una pasarela independiente para recibir dinero, y no encaja en micropagos voluntarios.

No basta con abrir «PayPal.Me» personal: podría revelar nombre o email. Usar nombre público/comercial en cuenta Business cuando PayPal lo permita y comprobar **en el checkout real y el justificante al donante** qué identidad aparece. Los proveedores pedirán datos verificables y cuenta de cobro **privadamente** para verificación y pagos; «no publicarlos en la web» no significa que se pueda cobrar sin identificarse ante el proveedor.

## Contexto verificado del repositorio

- Publicación estática HTML + CSS + JS; `package.json` es para CI, no una aplicación con servidor para pagos.
- `scripts/build-site-shell.py`: `render_footer()` (~línea 640) reproduce el pie global, y los comentarios «site-shell» de las páginas son bloques generados. **No editar 100 pies a mano**.
- `data/navigation.json`: fuente de grupos de navegación del pie y menú. Incorporar `apoyar` mediante entrada de navegación pública (y su definición en el catálogo de entidades que consuma el builder), preferentemente en «Información», no en la cabecera «Comprar» ni como elemento principal de Explorar.
- `scripts/build-tools-hub.py`, `scripts/build-reading-catalogue.py`, `scripts/build-topic-collections.py`: generators/consumidores del shell y potenciales puntos de CTA. Localizar el generador antes de modificar HTML derivado.
- `assets/v1-shell.css` y sus imports con versión son el CSS real compartido; `styles.css` es herencia y NO el punto principal para el diseño v1.
- `index.html` utiliza `assets/v1-home-editorial-v3.js` para construir el diseño visible; editar su antigua banda HTML estática puede tener efecto nulo o producir flash.
- `aviso-legal.html` ya informa de enlaces afiliados de Amazon; por tanto, **no afirmar «este sitio no monetiza nada»**. Copy más preciso: «Las herramientas y el contenido se ofrecen gratis. Si te han servido, puedes contribuir a mantenerlos y crear más».

## Recorrido UX: sin molestar

| Ubicación | Propuesta | Prioridad | Razón |
| --- | --- | --- | --- |
| Página `/apoyar/` | Título sencillo, explicación honesta, 2–3 métodos y nota de seguridad/privacidad | P0 | Un destino estable para todas las invitaciones |
| Pie global (grupo «Información») | «Apoyar el proyecto» (un único enlace) | P0 | Presencia constante sin estorbar |
| Herramientas, **después de obtener el resultado** | Frase opcional y enlace «¿Te ha servido? Apoya las herramientas gratuitas» | P1 | Petición contextual después de entregar valor, jamás antes |
| `/herramientas/` (parte baja) | CTA textual discreta | P1 | Descubrible sin competir con el buscador o filtros |
| Cuaderno / guías (después del contenido) | 1 párrafo, sin recuadro comercial | P1 | Vinculado al valor leído |
| Catálogo/recomendaciones | Solo pie o final de guía; evitar cada ficha y enlaces de afiliado | P2 | No competir con acciones de lectura/compra |
| Portada | Como máximo un enlace secundario en la zona final; nunca sobre hero ni compra de libros | P2 | No diluir el foco editorial |

**No implementar:** pop-ups, banners flotantes, bloqueo de resultados, contador de donantes, automatismos de recordatorio, tracking de importe o personas, precargas de scripts de pagos, urgencias ficticias, botones dentro de cada tarjeta. El mensaje no tiene que aparecer por cada herramienta si se vuelve intrusivo: probar en 2 superficies representativas antes de extender.

## Copy listo para usar

Título: **«Apoya este proyecto»**.
Descripción: «Las herramientas, las guías y los recursos de esta web se ofrecen gratis. Si te han resultado útiles y quieres ayudar a mantenerlos y crear otros nuevos, puedes hacer una aportación voluntaria. Gracias por leer y utilizar este espacio.»
Enlace contextual A: «¿Te ha servido? Puedes apoyar estas herramientas gratuitas».
Enlace contextual B: «Si esta guía te ha ayudado, puedes apoyar el proyecto».
Nota junto a los métodos: «El pago se completa en la plataforma elegida. Nunca te pediremos datos de tarjeta en esta web».
Pie: «Apoyar el proyecto».

No llamar a estas contribuciones «donaciones benéficas» ni prometer desgravación fiscal. No presentar importe sugerido como obligación; si se ofrecen 2 €, 5 €, 10 € deben ser orientativos y el proveedor debe permitir una cifra libre en al menos un método.

## Comparativa de proveedores — fuentes primarias revisadas 22-10-2026

| Ruta | Desde web estática | Elección importe | Dinero llega a | Coste indicativo y condición |
| --- | --- | --- | --- | --- |
| PayPal Donate/Payment link | URL oficial de botón alojado | Según configuración en PayPal | PayPal Business | PayPal ES: «donativo» nacional 2,90 % + 0,35 € (en EUR); comprobar clasificación real de la operación |
| Stripe Payment Links | URL `buy.stripe.com/...` generada en dashboard | **Sí**, «Customers choose what to pay» para pago único | Saldo Stripe -> banco verificado | Stripe España: tarjetas estándar EEE 1,5 % + 0,25 €; más si internacional, divisa o método |
| Ko-fi Free | URL de página Ko-fi o botón oficial | Según configuración Ko-fi | PayPal o Stripe vinculados | Ko-fi Free: 0 % del servicio en aportaciones puntuales; sigue habiendo tasas del procesador; modo Standard 5 % |
| Buy Me a Coffee | URL de creador | Aportación única | Stripe -> banco | 5 % plataforma + tasa de procesamiento; desembolsos disponibles para España |
| Klarna | No es receptor/cartera | No apropiado | A través de adquirente compatible | Financiación BNPL, desaconsejada para aportaciones voluntarias |

Fuentes:
- PayPal, tipos: https://www.paypal.com/es/business/paypal-business-fees
- PayPal, confirmación de uso por negocio con ánimo de lucro: https://www.paypal.com/es/cshelp/article/%C2%BFc%C3%B3mo-puedo-conseguir-asistencia-financiera-adicional-para-mi-empresa-help241
- PayPal, opción de Donate SDK y comprobación de elegibilidad: https://developer.paypal.com/sdk/donate/
- Stripe, enlace de importe libre: https://support.stripe.com/questions/how-to-accept-donations-through-stripe
- Stripe, precios España: https://stripe.com/es/pricing
- Ko-fi, comisiones: https://help.ko-fi.com/hc/en-us/articles/360002506494-Does-Ko-fi-take-a-fee
- Ko-fi, privacidad del creador: https://help.ko-fi.com/hc/en-us/articles/115004001294-What-personal-information-is-shared-on-Ko-fi-as-a-creator
- Buy Me a Coffee, comisiones: https://buymeacoffee.com/terms
- Buy Me a Coffee, países de cobro: https://help.buymeacoffee.com/en/articles/6258038-supported-countries-for-payouts-on-buy-me-a-coffee

## Arquitectura V1: enlace externo = cero dependencia de pagos

```text
/herramientas/ o herramienta individual o guía
  → CTA de texto discreta (opcional)
  → /apoyar/ (página propia, sin tarjetas ni scripts financieros)
  → PayPal / Stripe / Ko-fi (checkout alojado, validado)
  → pago confirmado por el proveedor, NO inferido por querystring de retorno
```

Configuración pública mínima (cuando exista implementación): 2–3 URLs de cobro reales validadas, no credenciales. Mantener métodos inactivos **ocultos**, no «próximamente» ni `href="#"`. Validar host `paypal.com`, `buy.stripe.com`, `ko-fi.com`, `buymeacoffee.com` de forma explícita antes de hacer visibles los enlaces. Sin `fetch`, iframe, SDK ni secretos en navegador para V1. `target="_blank" rel="noopener noreferrer"`; indicar apertura externa en nombre accesible y foco visible.

## Legal, privacidad, contabilidad y cumplimiento

- **Privacidad:** no publicaremos IBAN, teléfono ni email personales en código o página de donaciones; un proveedor de pagos puede mostrar nombre/comercio y datos fiscales o de contacto obligatorios. Hacer pago de prueba y mirar captura/recibo antes de publicar. No fingir anonimato absoluto.
- **Operación:** configurar nombre público, logo, descriptor bancario y correo comercial dentro de cada panel; verificación KYC/IBAN solo en las cuentas oficiales. Nunca guardar claves ni credenciales en el repositorio.
- **Fiscalidad:** «aportación», «apoyo» y «donativo» comercial no significan automáticamente donativo a entidad beneficiaria de mecenazgo. Las cantidades podrían tributar como ingreso de actividad o de otra naturaleza según circunstancias; verificar con asesor fiscal español antes de cobrar. No emitir certificado de deducción ni anunciarla. AEAT recuerda diferencia entre entrega voluntaria y contraprestación: https://sede.agenciatributaria.gob.es/Sede/declaraciones-informativas-otros-impuestos-tasas/campana-declaraciones-informativas-2025/notas-informativas/modelo-182-recordatorio-donativos.html
- **Documentos:** antes de lanzar, revisar `aviso-legal.html` (aportaciones no reembolsables salvo derecho aplicable, contacto para incidencias, identidad exigible) y `privacidad.html` (proveedores externos y finalidades), sin copiar declaraciones genéricas. La página debe aclarar que pagar es optativo y no hay bienes/servicios a cambio.
- **No recoger datos propios:** evitar formulario interno de nombre/correo, métricas individuales, cookies o píxeles del proveedor sin opt-in. No registrar importe, correo, IP o token de checkout en analytics.

## Reutilización de código: NO confundir «público» con «dominio público»

GitHub público **no** autoriza por sí solo copiar cualquier archivo sin condiciones. Copiar código de proyectos con licencia compatible (y mantener avisos exigidos) sí es viable; guardar URL, licencia, archivo, commit y fragmento efectivamente usado. Fuentes comprobadas:
- https://github.com/stripe-samples/checkout-one-time-payments — **MIT** (https://github.com/stripe-samples/checkout-one-time-payments/blob/main/LICENSE), trae cliente HTML/JS y servidor; **no se incorpora** porque exige backend, cuando Payment Links resuelve V1 sin servidor.
- https://github.com/paypal/paypal-js — **Apache-2.0** (https://github.com/paypal/paypal-js/blob/main/LICENSE), SDK helper válido para un futuro SDK PayPal, pero **innecesario** para URL de botón alojado y añade carga/CSP.
- Se reutiliza primero código del **propio sitio**: patrón de `<a>`, tokens de `assets/v1-*.css` y el generador `scripts/build-site-shell.py`. Los bloques nuevos de las PR hijas son adaptaciones originales de contratos oficiales, no copias atribuidas falsamente.

## PR hijas, independientes sobre esta rama

1. PayPal: configuración, privacidad y ejemplo `<a>` hospedado; alternativa Donate SDK y CSP si realmente se exige.
2. Stripe: «elige importe», enlace y precios con pruebas de aceptación.
3. Ko-fi y alternativos: modalidad gratis, visibilidad, evaluación BMC/Klarna y referencias.
4. UX/implementación: matriz de ubicaciones, contratos HTML/CSS y tests para Claude, diferenciando fuentes y generados.

En las PR hijas solo entrará documentación y/o ejemplos **no activados**. No introducir elementos de cobro en producción mientras los enlaces reales y el responsable no estén configurados.

## Criterios de aceptación del conjunto

- [ ] Proveedores y URLs reales probados en móvil y escritorio, con cuenta receptora confirmada.
- [ ] Ningún dato personal/secretos en repo, código, HTML público o analytics.
- [ ] Elección libre de importe y al menos tarjeta y PayPal mediante opciones comprobadas.
- [ ] Copy optativo, sin afirmación falsa de deducción o ausencia total de monetización.
- [ ] Pie global generado por shell; páginas derivadas no editadas a mano.
- [ ] No romper CSP existente, enlaces, navegación por teclado, contraste, responsive ni SEO.
- [ ] Revisión legal/fiscal/documental antes de lanzar; registro en la PR de cualquier licencia realmente utilizada.
- [ ] QA sintáctico y de paridad en branch de implementación; **no ejecutado en esta fase**.
