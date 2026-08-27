# Pendiente de código puro — 2026-08-27

Este documento es para terminar desde VS Code / Claude Desktop (no requiere
MCPs, navegador ni herramientas externas — son ediciones de archivo directas).
Todo lo que sí necesitaba navegador/Figma/generación de imágenes ya se hizo
en esta sesión (avatar del header regenerado y subido a `main` en `ee4b032`,
mockups de dirección visual en el artifact que te pasé por chat).

---

## 1. CRÍTICO: el vídeo de la intro nunca se sirve cuando el Service Worker ya controla la pestaña

**Esto es el bug del punto 4** ("solo sale la imagen inicial, no salta la
tinta ni mi foto, luego aparece Entrar"). Causa raíz confirmada con
evidencia real (no es una suposición):

- `<video preload="auto">` hace su primera petición con cabecera
  `Range: bytes=0-`. El servidor (GitHub Pages/Fastly) responde **206
  Partial Content** — esto es normal y correcto.
- El Service Worker (`service-worker.js`) intercepta esa petición en
  `cacheFirstAsset()` y llama a `putIfCacheable()`, que hace
  `cache.put(request, response.clone())` sin comprobar el status.
- **La Cache API de los navegadores prohíbe cachear respuestas 206**:
  `cache.put()` lanza un `TypeError` para cualquier respuesta con
  `status === 206`. Esa excepción no está controlada dentro de
  `putIfCacheable`, así que sube hasta el `catch` de `cacheFirstAsset` y
  se devuelve `offlineResponse()` — una respuesta sintética con
  **status 504** — en vez del vídeo real.
- El `<video>` recibe un 504, nunca reproduce, se queda en el poster, y a
  los 9.6s el timeout de `initIntro()` muestra "Entrar" igual que si el
  usuario hubiera decidido saltárselo.

**Por qué funciona en incógnito / la primera vez y falla después:** la
primera navegación de una pestaña nueva normalmente NO está todavía
controlada por el Service Worker (`clients.claim()` tarda un instante en
tomar el control), así que esa primera petición del vídeo va directa a
red y nunca pasa por `cacheFirstAsset`. En cualquier navegación
posterior — pestaña nueva, recarga, reabrir el navegador — el SW ya
controla desde el primer byte, así que el bug se dispara siempre.
Reproducido y verificado en vivo contra producción con Chrome DevTools
(petición 206 real → cache.match vacío tras el intento fallido →
network request muestra 504 en la recarga siguiente).

**Fix (una línea, en el helper compartido — corrige los 4 handlers a la vez):**

```js
// service-worker.js
async function putIfCacheable(cache, request, response) {
  if (response && response.ok && response.status !== 206) {
    await cache.put(request, response.clone());
  }
  return response;
}
```

Con este cambio, `cacheFirstAsset` sigue devolviendo el vídeo real (206)
al `<video>` tal cual llega de red — simplemente deja de intentar
guardarlo en Cache Storage. El vídeo no queda cacheado por el SW (se
apoya en el `Cache-Control: max-age=600` normal del navegador), pero
deja de romperse. Es la única vía sana: cachear rangos manualmente
(trocear y reensamblar respuestas) sería mucho más código para un
archivo que ya cachea razonablemente bien vía HTTP.

**Además, sube la versión de caché** para limpiar cualquier estado roto
que ya tengan los visitantes actuales:

```js
const CACHE_VERSION = `${CACHE_NAMESPACE}-v13`;
```

**Verificación sugerida tras aplicar el fix:** con DevTools abierto,
Network filtrado a "media", recarga la home dos veces seguidas — la
segunda petición al `.webm`/`.mp4` debe seguir devolviendo 206 (no 504),
y el vídeo debe reproducirse.

---

## 2. Punto 1 (resto): centrar mejor la foto del header junto al nombre

Ya regeneré y subí a `main` una versión más limpia de la foto (sin el
fleco oscuro del fondo del estudio pegado a la mano, encuadre más
cerrado a cabeza+hombros) — commit `ee4b032`. Lo que queda es puro ajuste
de CSS, en `assets/v1-shell-lrb-v2.css`:

```css
html.v1[data-lrb-home="true"] .masthead__brand-row{
  display:flex;
  align-items:center;
  justify-content:center;
  gap:clamp(.6rem,1.6vw,1.1rem)  /* ← prueba bajarlo, ej. clamp(.35rem,1vw,.7rem) */
}
html.v1[data-lrb-home="true"] .masthead__avatar{
  width:clamp(52px,7vw,92px);   /* ← el tamaño ya está en proporción con el texto */
  height:clamp(52px,7vw,92px);
  ...
}
```

Medí el logo (`assets/david-porto-diaz-escritor-banner-cropped.png`): el
padding interno arriba/abajo es casi simétrico (10.5% / 10.8%), así que
el `align-items:center` no está mal calculado — la sensación de
"separado" es sobre todo el **gap** (bájalo) y quizá el propio tamaño del
avatar en el rango más pequeño del clamp (52px puede sentirse chico
frente al script grande en pantallas estrechas — prueba subiendo el
mínimo a 60-64px). Ajusta ambos números a ojo en el navegador hasta que
lo veas "pegado" — es un cambio de 2 valores, no hace falta más.

---

## 3. Punto 2: imagen al compartir por WhatsApp

Verificado: `og-david-porto-sol.jpg` en producción **está bien** — es la
foto del sol, nítida, con el texto correcto (lo comprobé descargando el
archivo real servido por `davidportodiaz.com`, no hay mezcla ni
pixelado). Lo que viste mezclado/pixelado es la **caché propia de
WhatsApp** de la vista previa anterior (antes de que este fix estuviera
desplegado) — WhatsApp cachea por URL durante días y no hay forma de
forzar su refresco desde aquí sin iniciar sesión en una cuenta.

Dos vías, ninguna la puedo hacer yo sin tus credenciales:
- Esperar — su caché expira sola en unos días.
- Entrar tú en https://developers.facebook.com/tools/debug/ (Meta y
  WhatsApp comparten el mismo crawler), pegar `https://davidportodiaz.com/`
  y pulsar "Depurar" / "Scrape Again" — eso fuerza el refresco al
  instante. Pide iniciar sesión con Facebook, por eso no lo hice yo.

Si quieres una vía 100% en tu control sin depender de su caché, se puede
añadir un `?v=2` al final de la URL del `og:image` en `index.html` en
cada cambio de foto — truco simple, dímelo si lo quieres y lo dejo
anotado con el valor exacto.

---

## 4. Punto 7: CLS de `que-es-el-portal-fantasy`

Sigue documentado y con el estado real en
[`docs/PENDIENTE-CLS-FERIA-MADRID-2026-08-27.md`](./PENDIENTE-CLS-FERIA-MADRID-2026-08-27.md) —
no hay nada nuevo que investigar desde el navegador; el siguiente paso
(correr `lhci` de verdad en Linux/WSL para leer el trace crudo de
`LayoutShift`) es puro entorno/herramientas, no algo que MCPs puedan
resolver. Se dejó bajado a `warn` en CI mientras tanto, documentado, no
oculto.
