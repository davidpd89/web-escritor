# QA pendiente de dispositivo/servicio real

Estas pruebas quedan fuera de los navegadores headless y de los contratos estáticos del repositorio. No deben darse por superadas por equivalencia con Playwright: requieren hardware, SO, lector de pantalla, diálogo de impresión o buzón real.

## 1. iPhone / Safari real — home e intro

**Dispositivo mínimo:** iPhone con iOS/Safari actual.

1. Abrir una pestaña privada nueva en `https://davidportodiaz.com/`.
2. Confirmar que la intro de tinta se reproduce o, si el sistema bloquea autoplay, que aparece «Entrar» sin quedar una pantalla congelada.
3. Pulsar «Entrar» y comprobar acceso completo a la home.
4. Rotar vertical → horizontal → vertical.
5. Repetir con Modo de bajo consumo activado.
6. Repetir con Reducir movimiento activado.

**PASS:** no hay bloqueo, clipping horizontal, salto permanente de foco ni control fuera de safe-area; la home queda utilizable en todos los estados.

## 2. iOS Safari / Android Chrome — teclado virtual y formularios

Rutas: `/`, `/lectores-beta/`, herramientas con inputs y newsletter visible.

1. Enfocar cada input situado cerca de la mitad/inferior de la pantalla.
2. Abrir teclado virtual.
3. Tabular/usar «Siguiente» entre controles.
4. Cerrar teclado y rotar dispositivo.

**PASS:** el control enfocado y mensajes de error permanecen visibles; ninguna CTA fija tapa el campo; no queda scroll lateral tras cerrar teclado.

## 3. VoiceOver iOS/macOS y TalkBack Android

Muestra mínima: home, Obras, una página de libro, Cuaderno, Herramientas, Editoriales, Convocatorias, Metodología, 404.

Comprobar:
- navegación por landmarks;
- navegación por encabezados;
- nombre/estado de botones de menú y diálogos;
- foco al abrir/cerrar Explorar;
- labels de formularios y errores;
- orden de lectura de tarjetas;
- enlaces externos/compra comprensibles sin contexto visual.

**PASS:** no hay focos perdidos, controles sin nombre, landmarks ambiguos ni contenido esencial inaccesible.

## 4. Impresión real / Guardar como PDF

Navegadores: Chrome y Safari/Edge del sistema.

Rutas: home, `/las-manecillas-del-recuerdo/`, `/editoriales/`, `/convocatorias-escritores/`, `/metodologia-editorial/`, `/prensa.html`.

1. Abrir vista previa de impresión.
2. Revisar primera página y salto entre páginas.
3. Guardar PDF.

**PASS:** no aparece la intro cinematográfica, banners/overlays fijos ni navegación superpuesta; contenido principal no queda cortado; texto y enlaces esenciales son legibles.

## 5. Newsletter DOI con buzón real

Usar una dirección de prueba controlada, nunca una dirección de terceros.

1. Suscribirse desde home.
2. Confirmar estado «revisa tu correo».
3. Comprobar recepción del correo DOI.
4. Confirmar.
5. Verificar que no se produce doble alta ni doble envío al reenviar/refrescar.
6. Repetir en Lectores beta con su flujo/lista específica.

**PASS:** consentimiento, DOI, mensajes de estado y segmentación funcionan sin duplicados.

## 6. Compartir social real

Probar una URL de libro, un artículo de Cuaderno y la home en WhatsApp/Telegram/LinkedIn/X o sus depuradores oficiales.

**PASS:** título, imagen, descripción y URL corresponden a la página compartida; no se hereda por error la tarjeta genérica de otra ruta.

## 7. Search Console / render de buscador

Tras el despliegue estable:
- inspeccionar home, Editoriales, Convocatorias, Metodología y una ficha editorial;
- comprobar URL canónica declarada vs seleccionada;
- renderizado/indexabilidad;
- sitemap aceptado y sin rutas excluidas inesperadas.

**PASS:** no hay canonical alternativo inesperado, bloqueo de recursos ni exclusión por noindex/soft-404.

## 8. Headers HTTP dependientes del hosting

El audit automático observa HSTS, compresión y los headers de respuesta disponibles. GitHub Pages no permite controlar desde este repositorio todos los headers HTTP deseables.

Pendiente si se migra/antepone Cloudflare u otro edge configurable:
- CSP como header HTTP;
- X-Content-Type-Options: nosniff;
- Referrer-Policy;
- Permissions-Policy;
- frame-ancestors / política de framing;
- COOP/CORP según compatibilidad real del sitio.

**PASS:** endurecimiento añadido sin romper embeds, analítica, fuentes, workers ni navegación.

---

No cerrar estos casos por inferencia a partir de tests headless: registrar dispositivo/SO/navegador, fecha, resultado y evidencia al ejecutarlos.
