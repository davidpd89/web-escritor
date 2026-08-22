# Pendiente E — QA/CI: smoke test post-deploy y verificación del dist público

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-e-qa-smoke-test`

> **Prioridad más alta de las seis PRs.** Quedan ~12 días para el lanzamiento
> del 3/09. Esto es lo único que detectaría un despliegue roto ese día.
>
> **Alcance de esta PR y solo esta.** Añade tests/workflows nuevos en
> `tests/` y `.github/workflows/`. No toca `script.js`,
> `cloudflare-worker-subscribe.js` ni contenido — otras PRs cubren eso.
>
> **No requiere claves.** El smoke test hace peticiones HTTP normales (GET)
> contra una URL pública de staging que ya existe y no necesita
> autenticación: `https://david-porto-preview.davidpd89.workers.dev`
> (confirmado en `script.js:72`, es la misma que usa el propio frontend para
> distinguir staging de producción). No se despliega nada nuevo — solo se
> consulta lo que ya está desplegado.

---

## E.1 — `build-public-dist.py --check-contents` no está en ningún workflow (prioridad media)

### El problema

```bash
$ grep -rln "check-contents" .github/workflows/*.yml
(sin resultados)
```

`scripts/build-public-dist.py` ya tiene el flag `--check-contents` (líneas
156 en adelante, función `check_contents()`) que verifica que un dist ya
construido no incluye rutas internas (`scripts/`, `tests/`, `data/`,
`.env.example`, `lecturas/`, `publicar-web/`, `editorial-facts.json`,
`cloudflare-worker-subscribe.js`). El script existe y funciona; solo falta
ejecutarlo en CI.

### Qué hacer

1. Añade un paso en `.github/workflows/content-index-check.yml` (o un
   workflow nuevo si el existente no encaja bien temáticamente — decide tú
   cuál es más limpio) que ejecute:
   ```bash
   python scripts/build-public-dist.py
   python scripts/build-public-dist.py --check-contents
   ```
2. Verifica en local primero que el comando pasa limpio antes de wireearlo.
3. Rómpelo a propósito una vez: añade temporalmente un fichero de la denylist
   dentro de `.preview-dist/` a mano, confirma que `--check-contents` falla,
   revierte, y dilo en la PR.

### Criterio de aceptación

- El paso existe en CI y pasa.
- La PR documenta la prueba en rojo (paso 3) con la salida real del comando.

---

## E.2/E.3 — Sin smoke test HTTP contra staging, sin regresión visual (prioridad alta)

### El problema

Nada en `tests/` ni `qa/` hace una petición HTTP real contra el despliegue de
staging para confirmar que sigue vivo después de un cambio. Ambos huecos
estaban señalados como P0 en su día en el dossier
(`WEB DAVID PORTO nuevas ideas/16_IMPLEMENTACION_CODIGO_LISTA.md` y
`64_AUDITORIA_COMPLETITUD_REAL_Y_ORDEN_DE_EJECUCION_2026-08-20.md`, ítem M) y
ninguno de los dos se construyó:

- No hay ninguna suite de regresión visual (comparación de capturas
  antes/después).
- No hay ningún test/workflow que confirme que, tras un deploy, las rutas
  clave siguen respondiendo y el HTML sigue siendo válido.

### Qué hacer — prioriza esto sobre E.1 y sobre regresión visual completa

Con el tiempo que queda, un smoke test HTTP mínimo vale más que una suite
completa de Playwright. Construye:

1. **`tests/test-staging-smoke.mjs`** (o `.py`, sigue la convención que uses
   ya en `tests/` — revisa si predominan `.mjs` o `.py` para mantener
   consistencia):
   - Contra `https://david-porto-preview.davidpd89.workers.dev`, haz `GET` a
     un conjunto de rutas públicas clave: `/`, `/las-manecillas-del-recuerdo/`,
     `/libros/samuel-entre-mundos/`, `/cuaderno/`, `/herramientas/`.
   - Cada una debe responder `200` y contener al menos un `<title>` no vacío.
   - Contra las mismas rutas internas que verifica `--check-contents`
     (`/scripts/`, `/tests/`, `/data/`, `/.env.example`, `/lecturas/`,
     `/publicar-web/`, `/editorial-facts.json`,
     `/cloudflare-worker-subscribe.js`), confirma que responden **404**, no
     200. Esto es la verificación end-to-end de lo que E.1 solo comprueba
     localmente antes de subir — aquí se comprueba contra el sitio real ya
     desplegado.
   - Valida que el JSON-LD de `/` y de `/las-manecillas-del-recuerdo/` parsea
     como JSON válido (no hace falta validar el schema completo, solo que no
     esté roto).
   - El test debe poder ejecutarse manualmente (`node tests/test-staging-smoke.mjs`)
     y también estar preparado para un workflow (paso siguiente). Debe fallar
     con una salida clara de qué ruta/comprobación falló, no un timeout mudo.
   - Usa timeouts razonables (p. ej. 10s por petición) y no reintentos
     infinitos — si staging está caído, el test debe fallar rápido y con
     claridad.

2. **`.github/workflows/staging-smoke-test.yml`**:
   - `workflow_dispatch` (manual) como mínimo, para poder lanzarlo a mano
     justo después de un deploy real.
   - Si tiene sentido, añade también un trigger programado (`schedule`) diario
     o cada pocas horas durante la ventana de lanzamiento — pero no lo hagas
     obligatorio en cada PR, porque depende de un servicio externo (staging)
     que puede estar temporalmente caído por razones ajenas al código.
   - El job simplemente ejecuta el test de E.2.

3. **Regresión visual (si hay tiempo después de lo anterior):** un scaffold
   mínimo con capturas de las mismas rutas clave, comparando contra una
   captura baseline guardada en el repo o en un artifact. No hace falta que
   sea Playwright completo con reporting — puede ser tan simple como una
   captura + diff de imagen con una librería ligera. Si no da tiempo, déjalo
   fuera y dilo explícitamente en la PR: esto es lo más prescindible de las
   tres tareas de esta PR si hay que recortar.

### Criterio de aceptación

- `tests/test-staging-smoke.mjs` (o equivalente) ejecutado manualmente contra
  staging real, con salida pegada en la PR (verde).
- Workflow `workflow_dispatch` que ejecuta ese test, probado al menos una vez
  manualmente desde la pestaña Actions (o documentado que no se pudo probar
  por falta de permisos, sin fingir que sí se hizo).
- Si la regresión visual no se aborda, la PR lo dice explícitamente en vez de
  callarlo.

---

## Reglas de la casa

1. No se toca `main` ni se despliega nada — el smoke test **consulta** un
   staging que ya existe, no lo modifica.
2. No inventes un PASS: pega salidas reales de los comandos, no descripciones
   de lo que "debería" pasar.
3. Si staging está caído o inaccesible al probar, dilo en la PR en vez de
   simular una ejecución exitosa.
4. No debilites `build-public-dist.py --check-contents` para que pase en CI —
   si detecta algo real (una ruta interna filtrándose), es un hallazgo, no un
   fallo del test a silenciar.

## Test plan

- [ ] E.1: `--check-contents` wireado en CI, probado en rojo una vez, salida pegada
- [ ] E.2: smoke test ejecutado manualmente contra staging real, salida pegada
- [ ] E.2: workflow `workflow_dispatch` creado y, si es posible, disparado una vez para confirmar que funciona
- [ ] E.3 (regresión visual): abordada o marcada explícitamente como fuera de esta PR

---

## Estado de implementación (rama `pendiente-e-qa-smoke-test`)

- [x] E.1 wireado en CI: `content-index-check.yml` ejecuta
  `build-public-dist.py` + `build-public-dist.py --check-contents`.
- [x] E.1 probado en rojo una vez (inyección deliberada de `scripts/` en
  `.preview-dist/`) y revertido.
- [x] E.2 implementado: `tests/test-staging-smoke.mjs` + workflow
  `.github/workflows/staging-smoke-test.yml` con `workflow_dispatch` (y
  `schedule` diario).
- [ ] E.2 ejecución verde local contra staging: **no reproducible en esta red**
  por TLS interceptado (`self-signed certificate in certificate chain`) y
  respuestas `403` del endpoint desde este entorno. El test mantiene criterios
  estrictos (200 públicas / 404 internas) y falla con diagnóstico explícito.
- [x] E.3 marcada fuera de alcance en esta PR (scaffold visual no implementado
  en esta rama).

### Evidencia de comandos (real)

Rojo deliberado de E.1:

```text
FAIL — 1 issue(s) in C:\GIT\web-escritor\.preview-dist:
- excluded directory present in dist: scripts/
```

Verde de E.1 tras revertir la inyección:

```text
OK: C:\GIT\web-escritor\.preview-dist contains none of the excluded categories.
```

Ejecución local de E.2 en este entorno (fallo de conectividad/TLS real, no
simulado):

```text
FAIL public /: /: request failed (Error: self-signed certificate in certificate chain)
...
STAGING SMOKE FAIL (15 issue(s))
```
