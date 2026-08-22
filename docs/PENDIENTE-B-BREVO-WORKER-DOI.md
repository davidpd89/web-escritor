# Pendiente B — Completar el flujo de doble confirmación de Brevo

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-b-brevo-worker-doi`

> **Alcance de esta PR y solo esta.** Toca `cloudflare-worker-subscribe.js`,
> `scripts/test-worker-subscribe.mjs` y una página nueva
> `/gracias-suscripcion/`. No toques `script.js` salvo la única línea que se
> indica abajo (ya existe y solo hay que confirmarla, no reescribirla) — el
> resto de `script.js` lo tocan otras PRs (C) y no deben pisarse.
>
> **No requiere claves reales de Brevo/Cloudflare.** Todo esto se escribe y se
> prueba con los tests existentes del Worker, que no llaman a la API real
> (`scripts/test-worker-subscribe.mjs` ya tiene 16 casos sin red). El
> **despliegue** del Worker con las variables de entorno reales queda fuera de
> esta PR — eso lo hace David con sus propias claves, aquí después.
>
> **No es diseño final.** La página `/gracias-suscripcion/` es funcional (un
> mensaje de confirmación + reintento), no necesita acabado visual — usa los
> componentes/clases que ya existen en `styles.css` para mensajes de estado.
> Si el resultado no encaja visualmente, se retoca aquí con David delante;
> lo importante es que la lógica y el contrato funcionen.

---

## B.1 — Falta la página de retorno del DOI

### El problema

```bash
$ ls gracias-suscripcion/
ls: cannot access 'gracias-suscripcion/': No such file or directory

$ grep -n "gracias-suscripcion" script.js
645:  if (path.startsWith("/empieza-aqui/") || path.startsWith("/gracias-suscripcion/")) return false;
```

`script.js` ya tiene lógica que reconoce la ruta `/gracias-suscripcion/` (para
no reabrir el popup de newsletter en esa página), pero la página nunca se
construyó. Sin ella, cualquier lector que confirme su email desde Brevo cae en
un 404 real.

El dossier de propuestas ya documentaba el orden exacto en
`WEB DAVID PORTO nuevas ideas/22_BREVO_GUIA_TECNICA_API_Y_OPERACION.md`
(sección "Actualización 16/08/2026 — página de retorno DOI"):

1. crear `/gracias-suscripcion/index.html` — **esta PR**;
2. desplegar el Worker con `BREVO_DOI_REDIRECT_URL` apuntando a esa URL —
   **fuera de esta PR**, requiere claves reales;
3. probar el recorrido completo con una dirección de prueba — **fuera de esta
   PR**, requiere el Worker desplegado.

### Qué hacer

Crear `/gracias-suscripcion/index.html`:

- `<meta name="robots" content="noindex, follow">` — no es una página que deba
  indexarse.
- Antes de cargar `script.js`, fija el estado local igual que ya hace el
  propio `script.js` en los otros puntos de confirmación (busca
  `localStorage.setItem("nl-subscribed", "1")` en `script.js` líneas ~429,
  435, 510, 514 y replica el mismo patrón inline en el `<head>` de esta
  página, para que el estado quede fijado antes de que el runtime global
  decida si reabre el popup).
- Mensaje claro: confirmación recibida, ya está suscrito. Un enlace de vuelta
  a inicio y, si tiene sentido, a la ficha de Las manecillas.
- Reutiliza el shell del sitio (usa `scripts/site_shell.py` /
  `build-site-shell.py` como el resto de páginas generadas, o el patrón HTML a
  mano si esta página se mantiene simple y fuera del generador — revisa cómo
  están hechas páginas equivalentes como `/gracias/` si existe alguna, o si
  no, sigue el patrón de `empieza-aqui/index.html` como referencia de
  estructura mínima con shell).
- No necesita GoatCounter especial más allá de lo que ya carga el shell común.

### Criterio de aceptación

- `/gracias-suscripcion/index.html` existe, es `noindex,follow`, pasa por
  `scripts/build-site-shell.py --check` si aplica al patrón que sigas.
- Visitarla en local con `nl-subscribed` sin fijar previamente hace que quede
  fijado (compruébalo con el propio flujo del popup: tras visitar esta
  página, recarga otra página del sitio y confirma que el popup no aparece).

---

## B.2 — El Worker no tiene honeypot

### El problema

```bash
$ grep -n "honeypot" cloudflare-worker-subscribe.js
(sin resultados)
```

El contrato de cliente documentado en el dossier incluye un campo `website`
que actúa de honeypot (formulario invisible que un humano nunca rellena, pero
un bot sí). No existe ni el campo ni la validación en el Worker actual.

### Qué hacer

1. En `cloudflare-worker-subscribe.js`, añadir al contrato de entrada un campo
   opcional `website` (string).
2. Si `website` llega con cualquier contenido no vacío, el Worker debe
   responder **igual que un alta legítima** (mismo código de estado, mismo
   cuerpo de respuesta genérico) pero **no debe llamar a la API de Brevo ni
   crear ningún contacto**. No reveles al llamante que fue detectado como bot
   — eso es lo que hace útil al honeypot.
3. En el frontend (probablemente en el formulario de newsletter dentro de
   `index.html` / donde esté el `<form>` que llama al Worker), añade el campo
   oculto `website` si no existe ya, con las técnicas habituales para que sea
   invisible a un humano pero visible a un bot simple (`position: absolute;
   left: -9999px` o `tabindex="-1" aria-hidden="true"` + `autocomplete="off"`
   — no uses `display:none` ni `type="hidden"`, algunos bots los ignoran a
   propósito).
4. Añade casos de prueba en `scripts/test-worker-subscribe.mjs`:
   - `website` vacío o ausente → comportamiento normal, sin cambios.
   - `website` con contenido → respuesta idéntica a un alta válida en forma,
     pero verificable (con un mock/spy) que no se llamó a la API de Brevo.

### Criterio de aceptación

- Test nuevo en `scripts/test-worker-subscribe.mjs` cubre ambos casos y pasa.
- La respuesta HTTP a un intento con honeypot relleno es indistinguible de un
  alta exitosa desde fuera (mismo status, mismo cuerpo).

---

## B.3 — Sin rate limiting

### El problema

El propio Worker lo admite en un comentario:

```js
// cross-site browser requests, but they are NOT rate limiting or bot
// ...
// add Turnstile and/or a KV-backed rate limit; neither is implemented here
```

Confirmado repetidamente en el dossier como puerta de publicación pendiente.

### Qué hacer

No hace falta activar Turnstile (necesita clave/sitekey de Cloudflare, fuera
de esta PR). Sí puedes dejar preparado un **rate limit básico KV-backed**:

1. Define un límite razonable (por ejemplo, N intentos por IP por ventana de
   tiempo — decide un valor conservador y documéntalo, p. ej. 5 intentos/10
   minutos).
2. Si el Worker no tiene ya un binding de KV en `wrangler.toml`/config
   equivalente, añade el binding necesario (nombre descriptivo,
   `RATE_LIMIT_KV` o similar) y documenta en la PR que hace falta crear el
   namespace real en Cloudflare antes de desplegar — eso es responsabilidad
   de quien tenga las claves, no tuya aquí.
3. Implementa la lógica: leer contador por IP, incrementar, expirar por TTL,
   devolver un 429 genérico si se supera el límite (sin dar detalles que
   ayuden a un atacante a calibrar el límite exacto).
4. Test: como no hay KV real en local, escribe el test con un mock/stub de KV
   (objeto en memoria con `get`/`put` compatibles) para verificar la lógica de
   conteo y expiración sin depender de Cloudflare real.

### Criterio de aceptación

- Código de rate limiting existe, con su propio test usando un KV simulado.
- La PR documenta explícitamente qué falta configurar en Cloudflare
  (namespace KV real) antes de que esto funcione en producción — no lo dejes
  implícito.

---

## Reglas de la casa

1. No se toca `main` ni se despliega el Worker.
2. No pongas ni menciones ninguna clave real en el código, tests, ni en la
   descripción de la PR.
3. Si un test necesita simular la API de Brevo, usa un mock — nunca apuntes a
   la API real, ni siquiera con una clave de prueba.
4. No debilites ningún test existente de `scripts/test-worker-subscribe.mjs`
   para que pasen los nuevos casos — deben sumar, no reemplazar cobertura.
5. No inventes un PASS: pega en la PR la salida real de
   `node scripts/test-worker-subscribe.mjs`.

## Test plan

- [x] `node scripts/test-worker-subscribe.mjs` — todos los casos anteriores + los nuevos de honeypot y rate limit, en verde
- [x] `/gracias-suscripcion/` responde 200 en local (`python -m http.server 4173`), `noindex,follow` confirmado en el HTML
- [x] Documentado en la PR qué falta configurar en Cloudflare (KV namespace, `BREVO_DOI_REDIRECT_URL`) antes del despliegue real

---

## Estado de implementación (revisión externa 2026-08-22)

- [x] B.1: `/gracias-suscripcion/index.html` existe, `noindex,follow`, fija
  `nl-subscribed` antes de cargar `script.js`, pasa `build-site-shell.py --check`
  y no aparece en `sitemap.xml` (correcto, al ser noindex).
- [x] B.2: honeypot `website` implementado en `cloudflare-worker-subscribe.js`
  (devuelve `{ ok: true }` sin llamar a Brevo) e inyectado en los tres flujos
  del frontend (`quiz`, popup, `submitNewsletter` genérico) vía
  `honeypotValue()` en `script.js`.
- [x] B.3: rate limit KV-backed (`RATE_LIMIT_KV`, 5 intentos/10 min) con
  degradación segura a "sin límite" si el binding no existe todavía en
  Cloudflare. Documentado en el propio Worker (deploy steps 15-21) y en
  `docs/BREVO-WORKER-DEPLOY.md`.

### Evidencia de ejecución (verificado en revisión externa)

```text
$ node tests/test-cloudflare-worker-subscribe.mjs
test-cloudflare-worker-subscribe: all assertions passed

$ node tests/test-newsletter-client-contract.mjs
test-newsletter-client-contract: all assertions passed

$ python scripts/build-sitemap.py --check
SITEMAP OK: 54 URLs

$ python scripts/check-global-discoverability.py
PASS: global discoverability (89 tracked HTML artifacts; 54 indexable; search=POSPUESTO; map=60 human destinations)
```
