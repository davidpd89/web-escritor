# Evidencia final del issue #555

Fecha: 2026-10-07, Europe/Madrid.
Owner de exenciones: decision explicita de David Porto Diaz registrada el 2026-10-07 en #555.
Ejecucion tecnica: Codex, sobre produccion y servicios reales.
Version de produccion revisada: `49f66a66b6a469b97fb701552d5339e2f3dff385`.

Este registro separa resultados observados de pruebas no ejecutadas. El owner
acepta cerrar las comprobaciones que requieren hardware o clientes no disponibles
como `WAIVED`, sin convertirlas en `PASS` y conservando su riesgo residual.

## Edge real en Windows - PASS

- Dispositivo/servicio: Windows y Microsoft Edge estable, sesion real.
- URLs: `/`, `/libros/`, `/editoriales/`, ficha de Ediciones Hic Sic,
  `/convocatorias-escritores/`, `/metodologia-editorial/` y `/cuaderno/`.
- Viewports: escritorio, `390x844` y `844x390`.
- Resultado: `PASS`.
- Evidencia: navegacion, filtros, busqueda, foco de teclado, consola, recursos,
  metadatos Open Graph y limites de viewport revisados en produccion. Sin
  errores de consola, requests fallidas, scroll horizontal ni controles fuera
  del viewport. Las busquedas de Hic Sic y Santa Olalla devolvieron su ficha.

## Dispositivos Apple fisicos y PWA iOS - WAIVED

- Resultado: `WAIVED`, no `PASS`. No hubo iPhone, iPad ni Mac disponibles.
- Decision del owner: cerrar esta comprobacion con la evidencia automatizada y de
  Edge disponible, aceptando expresamente el riesgo residual el 2026-10-07.
- Evidencia compensatoria: Lighthouse, Pa11y, reflow, PWA/offline automatizado,
  safe-area CSS, rotacion y viewports moviles/landscape en Edge real.
- Riesgo residual: diferencias propias de WebKit, VoiceOver, teclado virtual y
  ciclo de vida de una PWA instalada en iOS. Revalidar cuando haya hardware.

## Android con TalkBack - WAIVED

- Resultado: `WAIVED`, no `PASS`; no se dispuso de un dispositivo Android
  con TalkBack dentro de esta ejecucion.
- Decision del owner: se acepta el cierre con Pa11y, Lighthouse, contratos de
  accesibilidad, foco de teclado y viewports moviles como evidencia compensatoria.
- Riesgo residual: gestos, anuncios y orden de exploracion propios de TalkBack.

## Windows con NVDA o JAWS - WAIVED

- Resultado: `WAIVED`, no `PASS`; NVDA/JAWS no se ejecutaron.
- Evidencia compensatoria: nombres accesibles, landmarks, orden de foco,
  live-regions, teclado y flujos criticos comprobados en Edge real.
- Riesgo residual aceptado por el owner: diferencias de anuncio e interaccion
  propias de lectores de pantalla de escritorio.

## macOS con VoiceOver y Safari - WAIVED

- Resultado: `WAIVED`, no `PASS`; no hubo Mac disponible.
- Decision del owner: cierre aceptado con evidencia compensatoria, sin afirmar
  equivalencia entre automatizacion y VoiceOver/Safari.
- Riesgo residual: interaccion y anuncios propios de VoiceOver/WebKit.

## Previews externos - WAIVED

- Resultado: `WAIVED`, no `PASS`; no se crearon comunidades ni cuentas
  adicionales para forzar previews en clientes externos.
- Evidencia compensatoria: `scripts/check-social-cards.py --strict` valido 384
  paginas indexables con 0 errores y 0 warnings; tambien se inspeccionaron en
  produccion las etiquetas Open Graph de las rutas criticas.
- Decision del owner: cerrar sin pruebas manuales en WhatsApp, Telegram, Discord,
  Slack, LinkedIn, X y Facebook, manteniendo como riesgo residual sus caches,
  recortes e interpretaciones especificas.

## Google Search Console - PASS

- Servicio: propiedad de dominio `davidportodiaz.com` en sesion real.
- Resultado: `PASS` operativo.
- Evidencia: `/editoriales/`, `/convocatorias-escritores/` y
  `/metodologia-editorial/` constan indexadas. La ficha de Ediciones Hic Sic no
  estaba aun en Google y se solicito su indexacion con confirmacion del panel.
  `https://davidportodiaz.com/sitemap.xml` se reenvio correctamente el
  2026-10-07. La indexacion final de una URL nueva depende del crawler.

## Bing Webmaster Tools - PASS

- Servicio: propiedad `davidportodiaz.com` en sesion real.
- Resultado: `PASS` operativo.
- Evidencia: las tres rutas de indice anteriores constan indexadas sin errores
  SEO/GEO. Ediciones Hic Sic figuraba descubierta pero no rastreada; se solicito
  indexacion y el panel confirmo el envio. El sitemap canonico se reenvio con
  confirmacion de procesamiento.

## Brevo/newsletter - PASS

- Cuenta de prueba: alias controlado del owner; no se usaron terceros.
- Resultado: `PASS` end-to-end.
- Alta: el formulario de produccion y el Worker devolvieron `201` con estado
  `pending_confirmation`; el contacto aterrizo una sola vez en la lista 3
  `Lectores web`, con `SOURCE=home` y sin mezclarse con `Lectores beta`.
- DOI: Gmail recibio el mensaje real, el enlace fue servido por Brevo y
  redirigio a `/gracias-suscripcion/`, que mostro la confirmacion esperada.
- Idempotencia: Brevo devuelve `204` para un contacto ya confirmado. El Worker
  se corrigio para aceptar `201` y `204` con la misma respuesta publica, sin
  revelar pertenencia a la lista. El formulario real quedo operativo.
- Error de proveedor: se observo un 502 real con recuperacion visible y boton
  reutilizable. La causa adicional fue la plantilla DOI 9 desactivada; se
  valido como `doiTemplate=true`, se reactivo sin cambiar claves ni listas y
  se repitio el flujo correctamente.
- Baja y limpieza: se verifico `emailBlacklisted=true` exclusivamente en el
  alias de QA; despues se elimino ese contacto. La lista general regreso a 5
  suscriptores totales y 5 unicos.
- Seguridad: la restriccion por IP y todas las claves permanecieron activas.
  El despliegue `/content` conservo el secreto, ambas listas, plantilla,
  redireccion y rate limiter.
