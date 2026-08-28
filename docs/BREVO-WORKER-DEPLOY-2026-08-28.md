# Brevo subscribe Worker — despliegue en producción, 2026-08-28

Registro de auditoría de la mutación real hecha hoy en producción, según lo
que exige `docs/claude-toolbox/08-CLOUDFLARE-Y-PRODUCCION.md` §13.

## Qué cambió

1. **Script del Worker `subscribe`** (cuenta `davidpd89`, id
   `77a008227d663ec8661f1e4422289c1b`) actualizado vía API
   (`PUT /accounts/{acct}/workers/scripts/subscribe`) con el contenido
   actual de `cloudflare-worker-subscribe.js` del repo. La versión que
   estaba desplegada era anterior a la reescritura DOI/`lectores-beta`
   del 23 de agosto — confirmado enviando una petición real y observando
   un mensaje de error (`"Missing required fields"`) que no existe en
   ningún punto del código fuente actual.
2. **Bindings añadidos/actualizados**:
   - `BREVO_API_KEY` (secret) — se reutilizó el valor ya guardado en
     `.env` del repo, sin mostrarlo ni preguntarlo; no se creó una clave
     nueva.
   - `BREVO_LIST_ID` = `3` (lista "Lectores web", la general).
   - `BREVO_BETA_LIST_ID` = `6` (lista "Lectores beta").
   - `BREVO_DOI_TEMPLATE_ID` = `9` (plantilla nueva, ver abajo).
   - `BREVO_DOI_REDIRECT_URL` = `https://davidportodiaz.com/gracias-suscripcion/`.
   - `RATE_LIMITER` (Cloudflare Workers Rate Limiting) — `namespace_id`
     `2001`, 5 peticiones / 60 s, siguiendo el mismo patrón que ya usa
     `wrangler.assistant.jsonc` para el Worker del asistente.
3. **Plantilla de email nueva en Brevo** (Transaccional → Plantillas,
   id `#9`, activa): asunto "Confirma tu suscripcion", cuerpo HTML propio
   (no reutiliza ninguna plantilla existente), etiqueta `optin` en
   configuración avanzada (requisito de Brevo para que la plantilla sea
   válida como confirmación de doble opt-in), botón de confirmación con
   `href="{{ doubleoptin }}"` — verificado en el email real entregado
   que Brevo sustituyó ese merge tag por una URL de tracking real y
   funcional.

## Por qué

El ledger (`data/implementation-truth-ledger.json`) marcaba
`brevo-beta-worker-routing` y `brevo-newsletter-samuel-chapter-delivery`
como `BLOCKED` desde el 27/08. El usuario autorizó explícitamente
completar todo lo pendiente aquí ("Toma decisiones y déjalo ya todo
funcionando correctamente y que podamos pasar de tema").

Se corrigió además una idea equivocada mía de un mensaje anterior: la
migración de zona Cloudflare de ayer **no** desbloqueaba nada de esto —
el Worker vive en `subscribe.davidpd89.workers.dev` (subdominio
`workers.dev`, no depende de ninguna zona DNS). Lo que faltaba era
simplemente desplegar el código actual con la configuración real.

## Verificado con una petición real (no simulada)

```
POST https://subscribe.davidpd89.workers.dev/
Origin: https://davidportodiaz.com
{"email":"davidpd89@gmail.com","source":"home","website":""}
→ 201 {"ok":true,"state":"pending_confirmation"}
```

Confirmado en el panel "Tiempo real" de Brevo: email real enviado y
entregado a `davidpd89@gmail.com`, plantilla `#9`, con un enlace de
confirmación real y funcional (se inspeccionó el HTML renderizado del
email, no solo el estado "entregado").

Se repitió la misma prueba con `source=lectores-beta` (misma dirección):
Brevo también envió un segundo email real (id de mensaje distinto, mismo
timestamp), pero el Worker devolvió `502` al cliente en vez de `201`.
Brevo sí procesó y envió el email — el fallo está en que el Worker
exige `brevoRes.status === 201` de forma estricta y Brevo, al parecer,
devuelve otro código 2xx cuando el mismo email ya tiene otra
confirmación pendiente muy reciente. **No se ha corregido a ciegas** —
queda anotado en el ledger como pendiente de diagnóstico real antes de
tocar el código, siguiendo el principio de no parchear sin entender la
causa raíz. No es bloqueante: un usuario real solo envía el formulario
una vez.

## Qué falta para poder decir "cerrado del todo"

- Que alguien (el propio David, con acceso a `davidpd89@gmail.com`) haga
  clic en los dos emails de confirmación ya enviados de verdad, y
  compruebe que aterriza en `/gracias-suscripcion/` con el enlace al
  capítulo (ver PR #136).
- Diagnosticar (no parchear a ciegas) el 502 en reenvíos rápidos del
  mismo email entre fuentes distintas.

## Rollback

Si hace falta revertir: `PUT` el script anterior (Cloudflare guarda
versiones/despliegues, `GET /accounts/{acct}/workers/scripts/subscribe/versions`
lista las anteriores) o simplemente `wrangler rollback`. No se ha tocado
nada del lado de Brevo salvo crear la plantilla `#9`, que se puede
desactivar sin afectar a nada más.
