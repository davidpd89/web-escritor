# Pendiente C — Popup de newsletter: código vs. spec documentada

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-c-popup-newsletter`

> **Alcance de esta PR y solo esta.** Toca únicamente el bloque de triggers
> del popup en `script.js` (líneas ~778-790, ver abajo) y, si hace falta, un
> test nuevo en `qa/`. No toques el resto de `script.js` — otras PRs (B) tocan
> otras zonas del mismo fichero; si al hacer `git pull` hay conflicto porque
> alguien más ya mergeó algo ahí, resuélvelo conservando ambos cambios, no
> descartando el ajeno.
>
> **No requiere claves ni acceso externo.** Es JS puro, verificable en local.
>
> **No es diseño final.** Esto es lógica de disparo (cuándo aparece el
> popup), no su aspecto visual. No toques CSS del popup salvo que el fix lo
> exija de forma trivial.

---

## El problema

Un agente de verificación (revisión file-by-file del dossier de propuestas)
detectó que `16_IMPLEMENTACION_CODIGO_LISTA.md` fija una spec más específica
en su sección final que el código actual no cumple:

| | Spec documentada en el dossier | Código actual (`script.js`) |
|---|---|---|
| Scroll trigger | 70% de la página | **60%** (línea 781: `ratio >= 0.6`) |
| Temporizador de fallback | **no debe existir** | **sí existe**, 30 segundos (línea 790: `setTimeout(showPopup, 30000)`) |
| Exit-intent (`mouseleave`) | solo con `hover:hover` + `pointer:fine` | sin filtro de puntero (líneas 785-787) — puede dispararse en móvil por un scroll/touch que el navegador interprete como salida |

Código actual completo (`script.js:778-790`):

```js
// Trigger 1: 60% scroll depth
window.addEventListener("scroll", function onScroll() {
  const ratio = window.scrollY / Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
  if (ratio >= 0.6) { window.removeEventListener("scroll", onScroll); showPopup(); }
}, { passive: true });

// Trigger 2: exit-intent — mouse leaves from top of viewport
document.addEventListener("mouseleave", function onLeave(e) {
  if (e.clientY <= 0) { document.removeEventListener("mouseleave", onLeave); showPopup(); }
});

// Trigger 3: 30-second fallback for passive readers
setTimeout(showPopup, 30000);
```

## Qué hacer

**Paso 0 — decide cuál versión es la vigente antes de tocar nada.** Puede que
el 60%/30s sea una iteración posterior deliberada (menos agresiva la spec
original, más permisiva el código) que la documentación del dossier no llegó
a actualizar. O puede que el código se haya desalineado sin querer. No hay
forma de saberlo solo con el repo — si tienes forma de preguntar, pregunta.
Si no, aplica este criterio por defecto: **el código de producción manda**
salvo que exista una razón de UX documentada para preferir la spec del
dossier (menos intrusivo en móvil suele ser la razón real detrás de "no
timer" y "solo hover real"). Sea cual sea la decisión, documenta el motivo en
la PR — no lo cambies en silencio.

Si decides aplicar la spec documentada (recomendado, salvo que encuentres una
razón para no hacerlo):

1. **Scroll trigger a 70%:** cambiar `ratio >= 0.6` por `ratio >= 0.7`.
2. **Eliminar el temporizador de 30s:** borrar la línea
   `setTimeout(showPopup, 30000);` y su comentario.
3. **Gatear el exit-intent a puntero real:** el evento `mouseleave` no debe
   registrarse (o no debe disparar `showPopup`) en dispositivos táctiles.
   Usa `window.matchMedia("(hover: hover) and (pointer: fine)").matches`
   antes de añadir el listener, o compruébalo dentro de `onLeave` antes de
   llamar a `showPopup()`. Ejemplo:
   ```js
   if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
     document.addEventListener("mouseleave", function onLeave(e) {
       if (e.clientY <= 0) { document.removeEventListener("mouseleave", onLeave); showPopup(); }
     });
   }
   ```

## Qué NO hacer

- No inventes un valor intermedio (p. ej. "65%, 15s") como compromiso sin
  justificarlo — o aplicas una versión completa o documentas por qué te
  quedas con la otra.
- No toques `showPopup()` en sí ni la lógica de supresión por
  `nl-subscribed`/rutas excluidas (eso ya funciona y no es parte de este
  hallazgo).

## Criterio de aceptación

- Los tres triggers quedan alineados entre sí y con lo que documenta la PR.
- Un test nuevo (o una prueba manual documentada con pasos exactos si no hay
  infraestructura de test para esto en `qa/`) verifica:
  - el popup no se dispara antes del umbral de scroll elegido;
  - el popup se dispara al alcanzar el umbral;
  - si se elimina el timer, que no se dispare a los 30s sin scroll ni
    exit-intent;
  - si se gatea el exit-intent, que un evento `mouseleave` sintético no
    dispare el popup cuando `matchMedia("(hover: hover) and (pointer: fine)")`
    devuelve `false` (puedes forzarlo en el test, no hace falta un dispositivo
    táctil real).

## Reglas de la casa

1. No se toca `main`.
2. No debilites ningún test existente para que pase este cambio.
3. No inventes un PASS: si añades test en `qa/`, pega su salida real en la
   PR. Si documentas verificación manual, sé específico (pasos + resultado
   observado), no "probado y funciona".

## Test plan

- [ ] Decisión documentada en la PR: código manda o spec del dossier manda, y por qué
- [ ] Los tres triggers alineados con la decisión
- [ ] Verificación (test o pasos manuales) de los tres puntos de la tabla, con evidencia pegada en la PR
