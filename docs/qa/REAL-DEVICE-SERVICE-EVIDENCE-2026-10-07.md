# Evidencia parcial del issue #555

Fecha: 2026-10-07, Europe/Madrid.
Owner de exenciones: no consta una decision explicita registrada en #555.
Ejecucion tecnica: Codex, sobre produccion y servicios reales.
Version de produccion revisada: `49f66a66b6a469b97fb701552d5339e2f3dff385`.

Este registro separa resultados observados de pruebas no ejecutadas. Mientras
#555 no registre una decision explicita del owner, ninguna prueba pendiente se
marca como `WAIVED` o `NOT_APPLICABLE`: permanece `BLOCKED` y conserva su riesgo.

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

## Dispositivos Apple fisicos y PWA iOS - BLOCKED

- Alcance: Safari en iPhone/iPad, safe areas, teclado virtual, zoom de texto,
  rotacion y ciclo de vida de la PWA instalada.
- Resultado: `BLOCKED`; no se dispuso de iPhone, iPad ni Mac para esta ejecucion
  y no existe en #555 una decision explicita que permita convertirlo en `WAIVED`.
- Evidencia compensatoria: matriz CI verde del despliegue, Lighthouse, Pa11y,
  reflow, PWA/offline automatizado y auditoria responsive en Edge real.
- Riesgo residual: diferencias propias de WebKit, VoiceOver y PWA iOS.
- Siguiente paso: ejecutar la matriz fisica cuando haya hardware Apple disponible
  o registrar en #555 una decision explicita del owner sobre el riesgo residual.

## Android con TalkBack - BLOCKED

- Resultado: `BLOCKED`; no hubo dispositivo Android con TalkBack disponible y
  no existe una decision explicita registrada que permita marcarlo `WAIVED`.
- Evidencia compensatoria: Pa11y, Lighthouse, contratos de accesibilidad,
  navegacion de teclado y viewports moviles en Edge real.
- Riesgo residual: gestos, anuncios y orden de exploracion propios de TalkBack.
- Siguiente paso: ejecutar con Android/TalkBack real o registrar explicitamente
  en #555 la decision del owner y el riesgo aceptado.

## Windows con NVDA o JAWS - BLOCKED

- Resultado: `BLOCKED`; no se ejecutaron NVDA ni JAWS y no existe una decision
  explicita registrada que permita renunciar a esa prueba.
- Evidencia compensatoria: Pa11y, nombres accesibles, foco de teclado,
  live-regions y flujos criticos comprobados en Edge real.
- Riesgo residual: diferencias de anuncio e interaccion propias de NVDA/JAWS.
- Siguiente paso: ejecutar NVDA/JAWS real o registrar explicitamente en #555
  la decision del owner y el riesgo aceptado.

## macOS con VoiceOver y Safari - BLOCKED

- Resultado: `BLOCKED`; no hubo Mac disponible y no existe una decision
  explicita registrada que permita marcar la prueba como `WAIVED`.
- Evidencia compensatoria y riesgo: los mismos del bloque Apple, sin afirmar
  equivalencia entre las pruebas automatizadas y VoiceOver/Safari.
- Siguiente paso: ejecutar en Mac/VoiceOver/Safari o registrar explicitamente
  en #555 la decision del owner y el riesgo aceptado.

## Previews externos - BLOCKED

- Resultado: `BLOCKED`; no se ejecutaron previews reales en WhatsApp, Telegram,
  Discord, Slack, LinkedIn, X ni Facebook durante esta ejecucion.
- No se usa `NOT_APPLICABLE` ni `WAIVED` porque #555 no contiene una decision
  explicita del owner sobre esos canales.
- Evidencia compensatoria: `scripts/check-social-cards.py --strict` valido 384
  paginas indexables con 0 errores y 0 warnings, y se inspeccionaron en
  produccion las etiquetas Open Graph de las rutas criticas.
- Riesgo residual: cache, recorte o interpretacion especifica de cada cliente.
- Siguiente paso: ejecutar previews reales o registrar explicitamente en #555 la
  decision del owner y la condicion de reevaluacion.

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
