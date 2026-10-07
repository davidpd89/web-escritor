# Evidencia de cierre del issue #555

Fecha: 2026-10-07, Europe/Madrid.
Owner de la decision: David Porto Diaz.
Ejecucion tecnica: Codex, sobre produccion y servicios reales.
Version de produccion revisada: `49f66a66b6a469b97fb701552d5339e2f3dff385`.

Este registro separa resultados observados de exenciones. `WAIVED` no significa
que una prueba fisica haya pasado y `NOT_APPLICABLE` no afirma compatibilidad
con un canal que no se usa.

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

- Alcance: Safari en iPhone/iPad, safe areas, teclado virtual, zoom de texto,
  rotacion y ciclo de vida de la PWA instalada.
- Resultado: `WAIVED` por decision explicita del owner; no dispone de iPhone,
  iPad ni Mac y no se presenta esta exencion como `PASS`.
- Evidencia compensatoria: matriz CI verde del despliegue, Lighthouse, Pa11y,
  reflow, PWA/offline automatizado y auditoria responsive en Edge real.
- Riesgo residual: diferencias propias de WebKit, VoiceOver y PWA iOS.
- Reevaluacion: ejecutar la matriz fisica si se dispone de hardware Apple o si
  una incidencia de usuario apunta a WebKit, VoiceOver o instalacion iOS.

## Android con TalkBack - WAIVED

- Resultado: `WAIVED` por decision explicita del owner; no hay dispositivo y
  lector real disponibles para esta ejecucion.
- Evidencia compensatoria: Pa11y, Lighthouse, contratos de accesibilidad,
  navegacion de teclado y viewports moviles en Edge real.
- Riesgo residual: gestos, anuncios y orden de exploracion propios de TalkBack.
- Reevaluacion: al disponer de Android/TalkBack o ante una incidencia real.

## Windows con NVDA o JAWS - WAIVED

- Resultado: `WAIVED` por decision explicita del owner; no se ejecutaron NVDA
  ni JAWS y no se declara una prueba de lector de pantalla superada.
- Evidencia compensatoria: Pa11y, nombres accesibles, foco de teclado,
  live-regions y flujos criticos comprobados en Edge real.
- Riesgo residual: diferencias de anuncio e interaccion propias de NVDA/JAWS.
- Reevaluacion: al incorporar un lector real al entorno de QA o ante una
  incidencia de accesibilidad.

## macOS con VoiceOver y Safari - WAIVED

- Resultado: `WAIVED` por decision explicita del owner; no hay Mac disponible.
- Evidencia compensatoria y riesgo: los mismos del bloque Apple, sin afirmar
  equivalencia entre las pruebas automatizadas y VoiceOver/Safari.
- Reevaluacion: al disponer de un Mac o ante una incidencia WebKit/VoiceOver.

## Previews externos

- Telegram, Discord, Slack, LinkedIn y X: `NOT_APPLICABLE`; el owner confirma
  que esos canales no forman parte de la estrategia actual.
- WhatsApp y Facebook: `WAIVED`; no se hizo envio real a terceros. Como
  evidencia compensatoria, `scripts/check-social-cards.py --strict` valido 384
  paginas indexables con 0 errores y 0 warnings, y se inspeccionaron en
  produccion las etiquetas Open Graph de las rutas criticas.
- Riesgo residual: cache o recorte especifico de cada cliente externo.
- Reevaluacion: antes de activar uno de esos canales o ante una tarjeta rota.

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
