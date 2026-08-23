# Pendiente P — Auditoría GPT líneas 1601–1800

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente: `pendiente funcionalidad gpt.txt`, exactamente líneas 1601–1800.

## Regla de alcance

Este documento registra únicamente deuda que sigue siendo real después de contrastar el TXT con el código, datos, tests, CI y PR abiertas. No convierte en tarea una descripción antigua, una funcionalidad ya implementada, una publicación deliberadamente gated ni trabajo ya asignado a otra PR.

No tocar `main`, no desplegar producción y no activar auto-merge desde esta rama.

---

## 1. Continuación del documento 58 — Distribución de POV

**Clasificación: YA DETECTADO — #72 O.2.**

Las líneas 1601–1623 continúan exactamente el problema ya abierto en la PR #72. No justifican una PR nueva.

El cierre de O.2 debe incluir:

- detección robusta del formato de entrada;
- soporte explícito de `POV | palabras` como segundo contrato real;
- preservación de `escena | POV | palabras opcionales`;
- no reinterpretar silenciosamente dos columnas con semántica distinta;
- warnings claros para orden/tipo de columnas ambiguo o incoherente;
- orden de salida explícito y determinista;
- tests para ambos formatos y sus casos ambiguos.

No ampliar el alcance a inferir POV desde la prosa ni a construir un sistema estadístico general.

Se ha dejado comentario de coordinación en #72.

---

## 2. Documento 59 — «¿Qué tipo de lector eres?»

**Clasificación: DEUDA NUEVA — P.1.**

El TXT define una herramienta pública/local en `/herramientas/que-tipo-de-lector-eres/` y la considera un hueco de producto real.

### Estado verificado

En `implementacion-web-2026`:

- no existe la ruta `/herramientas/que-tipo-de-lector-eres/`;
- no existe un motor o fichero registrado para este quiz;
- `data/tools-hub.json` no contiene esta herramienta;
- las búsquedas de código no encuentran implementación equivalente;
- ninguna PR abierta #54–#72 cubre este producto.

### Contrato mínimo de implementación

Construir una herramienta que funcione completamente en navegador y sin cuenta.

Perfiles previstos por el documento, manteniendo un conjunto compacto de 5–7 resultados mutuamente distinguibles:

- detector de pistas;
- explorador de mundos;
- lector de personajes;
- lector de ritmo;
- lector emocional;
- lector de estilo.

El nombre final y la microcopy pueden ajustarse, pero no debe convertirse en un test psicológico, diagnóstico ni segmentación remota.

### Requisitos técnicos

- procesamiento local;
- sin enviar respuestas individuales a servidor/analytics;
- resultado reproducible para las mismas respuestas;
- preguntas y puntuación separadas de la capa de presentación;
- tie-break determinista y documentado;
- controles accesibles por teclado y lector de pantalla;
- resultado comprensible sin depender solo de color;
- integración en `data/tools-hub.json` y generación vigente del hub;
- CSP/privacidad coherentes con el contrato de herramientas locales;
- test unitario del scoring + smoke de UI;
- si se mide uso, solo evento agregado de apertura/completado conforme a la taxonomía de #63, nunca respuestas ni perfil obtenido.

### No hacer

- no almacenar un perfil de usuario;
- no pedir email para ver el resultado;
- no crear recomendaciones comerciales disfrazadas del resultado;
- no afirmar rasgos personales fuera de la preferencia de lectura que mide el propio cuestionario.

---

## 3. Documento 60 — «Esta web, en cifras»

**Clasificación: HECHO / GATED.**

La infraestructura existe:

- `scripts/build-human-site-stats.py`;
- `data/site-human-stats.generated.html`;
- `data/site-human-stats.generated.json`;
- gate de reproducibilidad en CI ya existente.

La decisión de no crear aún `/estadisticas/` con solo tres métricas humanas útiles es coherente con el propio TXT. Crear la página ahora sería inflar una superficie sin masa suficiente.

No abrir deuda nueva.

---

## 4. Documento 61 — Listas de lectura curadas

**Clasificación: PARCIAL / GATED / YA CUBIERTO POR #66 K.1.**

La infraestructura existe actualmente:

- `data/reading-list.json`;
- `data/reading-list-template.json`;
- `scripts/build-reading-list.py`.

El bloqueo real es editorial/evidencial: listas pequeñas, criterio explícito, fuente/evidencia y no atribuir lecturas personales no demostradas. Esa política pertenece al contrato de recomendaciones verificables de #66 K.1.

No abrir una segunda PR para lo mismo ni publicar `/listas-de-lectura/` por cumplir una ruta vacía.

---

## 5. Documento 62 — Web Lab

**Clasificación: HECHO / GATED.**

El TXT usa un nombre de fichero que ya no coincide con HEAD, pero la infraestructura sí existe.

Fuente vigente:

- `data/web-lab-entries.json`;
- `scripts/build-web-lab-index.py`;
- `scripts/validate-web-lab-entry.py`.

`data/web-lab-entries.json` contiene dos candidatos y ambos siguen `publish:false`.

El builder solo permite generar el hub público cuando hay al menos dos piezas publicables válidas. Eso coincide con el gate descrito: no publicar un laboratorio vacío ni convertir observaciones de un único sitio en leyes generales.

No abrir deuda nueva.

---

## 6. Documento 63 — Export de resultados / transparencia de método y licencia

**Clasificación: PARCIAL + DEUDA NUEVA — P.2.**

Existe una infraestructura de export open-source:

- `data/open-source-tools.json`;
- `scripts/build-open-source-export.py`.

La licencia raíz está deliberadamente en `null`. El builder lo trata correctamente como bloqueo y genera `LICENSE-REQUIRED.txt`; **elegir MIT o Apache-2.0 es una decisión humana y no forma parte de esta PR**.

### Gap técnico verificable

La entrada de Legibilidad declara:

- `files: ["legibilidad-engine.js"]`;
- `third_party: []`.

Pero el grafo real es:

`legibilidad-espanol.js` → `legibilidad-engine.js` → `silabajs-lite-2.1.0.js`.

`silabajs-lite-2.1.0.js` declara expresamente que es una adaptación de `silabajs 2.1.0`, upstream Nicolás Cofré Méndez, licencia MIT.

El exportador actual valida que cada fichero **declarado** exista, pero no analiza/importa el cierre transitivo del módulo. Tampoco verifica que una dependencia third-party real esté reflejada en `third_party` y en `THIRD_PARTY_NOTICES.md`.

Por tanto, activar `export:true` para Legibilidad en el estado actual puede producir un paquete incompleto: `legibilidad-engine.js` importaría un módulo que no viaja en el export. Además, el aviso «Sin dependencias de terceros declaradas» sería falso por omisión.

### Contrato de cierre P.2

Antes de habilitar cualquier `export:true`:

1. El manifiesto debe declarar el conjunto de ficheros necesario para ejecutar cada herramienta exportada.
2. El validador debe detectar imports locales estáticos y fallar si un import requerido queda fuera del paquete, o existir una alternativa equivalente que garantice closure de forma determinista.
3. Dependencias de terceros/adaptaciones deben quedar declaradas con nombre, origen y licencia.
4. `THIRD_PARTY_NOTICES.md` debe generarse a partir de esa autoridad, no de una lista opcional que puede quedar vacía incorrectamente.
5. Debe existir test de fixture que demuestre que un import transitivo omitido falla.
6. Debe existir test específico de Legibilidad que compruebe que el staging exportado puede resolver su grafo de módulos.
7. `--check` debe validar no solo hashes ya listados, sino también que el manifest actual y el staging siguen correspondiéndose con el contrato de fuentes.
8. Mantener `license: null` y `export:false` mientras no exista decisión humana de licencia/publicación.

### Fuera de alcance

- no crear un repositorio externo;
- no publicar código automáticamente;
- no elegir licencia por el propietario;
- no cambiar la licencia upstream de `silabajs`;
- no asumir que toda la web queda bajo la licencia futura del paquete de herramientas.

---

## Resultado del bloque 1601–1800

Deuda nueva real:

- **P.1** — construir «¿Qué tipo de lector eres?» como herramienta local, accesible y testeada;
- **P.2** — cerrar el grafo de dependencias y los avisos/licencias de terceros del export antes de habilitarlo.

Reutilizado, sin duplicar:

- POV → #72 O.2;
- evidencia de recomendaciones/listas → #66 K.1.

Gated correctamente:

- página dedicada de estadísticas;
- publicación de listas de lectura hasta tener evidencia;
- Web Lab hasta que existan dos casos publicables;
- elección/publicación de licencia open-source.

**STOP exacto: línea 1800.** No se interpreta la continuación del documento 63 desde la línea 1801 en esta ronda.

---

# Estado de implementación (2026-08-23)

## P.1 — «¿Qué tipo de lector eres?»

- **Ruta**: `/herramientas/que-tipo-de-lector-eres/`, `noscript` explicativo, CSP local-only (`connect-src 'none'`, sin `/script.js`).
- **6 perfiles** (`assets/tipo-lector-engine.js`: `PROFILES`): detector de pistas, explorador de mundos, lector de personajes, lector de ritmo, lector emocional, lector de estilo — el conjunto compacto de 5–7 que pedía el documento 59, ninguno presentado como rasgo de personalidad ni diagnóstico.
- **6 preguntas × 6 opciones** (una opción por perfil y pregunta, simetría exacta): preguntas y puntuación (`QUESTIONS`, `score()`) completamente separadas de la capa de presentación (`assets/tipo-lector.js` solo renderiza y lee el DOM).
- **Reproducibilidad y desempate deterministas**: `score()` es una función pura de las respuestas; en empate exacto gana el perfil que aparece antes en el array `PROFILES` (regla fija, documentada en el propio código y visible en la página: «un empate se resuelve mostrando el que aparece primero en esta lista, siempre en el mismo orden»), nunca `Math.random` ni orden de inserción.
- **Sin envío de datos**: sin `fetch`/`XHR`, sin `localStorage`/`sessionStorage`, sin email para ver el resultado, sin perfil guardado; verificado con `scripts/audit-private-tools.py` y con un QA de navegador que confirma **cero peticiones de red externas**.
- **Accesible**: preguntas como `<fieldset>`/`<legend>` con radios reales (foco y lector de pantalla nativos, no un widget custom), resultado anunciado vía `role="status"`/`aria-live`, sin depender solo del color.
- **Integrado sin segunda fuente de verdad**: nueva categoría `lectores` en `data/tools-hub.json`/`scripts/build-tools-hub.py` (las categorías existentes son todas para escritores; forzar este quiz en una de ellas habría sido una mala categorización) + `data/content-registry.json`; hub regenerado (18 herramientas, antes 17); sitemap regenerado (55 URLs).
- **Tests**: `tests/test-tipo-lector.mjs` (estructura 6+6, elegir siempre el mismo perfil da la puntuación máxima a ese perfil y 0 al resto, reproducibilidad exacta, desempate determinista construido explícitamente, respuestas incompletas y opción desconocida fallan con error en vez de puntuar a medias en silencio).
- **QA de navegador real**: `qa/tipo-lector-browser.mjs` — envío incompleto no muestra resultado, responder todo sí, perfil calculado correcto, desglose de 6 perfiles, «Repetir el test» limpia respuestas, 0 peticiones externas, 0 excepciones JS. Wireado en `tools-browser-qa.yml` (ya cubre el resto de herramientas de texto de `/herramientas/`).

## P.2 — Cierre de dependencias y avisos de terceros en el export open-source

- **Bug real confirmado y corregido**: `data/open-source-tools.json` → `legibilidad` declaraba `files: ["legibilidad-engine.js"]` y `third_party: []`, pero `legibilidad-engine.js` importa `silabajs-lite-2.1.0.js` (adaptación MIT de `silabajs` de Nicolás Cofré Méndez) que no viajaba en el paquete y cuya licencia no se avisaba. Corregido: `files` ahora incluye `silabajs-lite-2.1.0.js` y `third_party` declara la adaptación con origen y licencia. `license: null` y `export: false` **sin tocar** (la elección de licencia sigue siendo una decisión humana fuera de esta PR).
- **Cierre de dependencias real, no solo declarativo** (`scripts/build-open-source-export.py`): `closure_files()` sigue imports relativos estáticos (`import ... from './x.js'`, `import './x.js'`, `require('./x.js')`) de forma transitiva a partir de los ficheros declarados. Si el cierre real encuentra un fichero que no está en `files`, `validate()` falla con un mensaje que nombra el fichero que falta — no se auto-incluye en silencio, se exige declaración humana explícita en el manifest (punto 2 del contrato).
- **Detección de adaptaciones de terceros no declaradas**: `looks_like_adaptation()` detecta cabeceras tipo «Adaptación…Upstream:…Licencia upstream:» (el patrón real que ya usa `silabajs-lite-2.1.0.js`); si un fichero del cierre las tiene y no aparece mencionado en `third_party`, `validate()` falla explicando por qué (puntos 3–4 del contrato).
- **`THIRD_PARTY_NOTICES.md`** se sigue generando desde `third_party` (ya era la autoridad correcta); con el cierre y la detección de adaptaciones, ahora ese campo no puede quedar vacío por omisión para una herramienta que sí tiene una adaptación real (punto 4).
- **`--check` ampliado** (punto 7): además de la integridad de hashes ya existente (detecta ficheros alterados tras generar), ahora también compara el conjunto de slugs `export:true` del manifest **actual** contra los slugs realmente presentes en el `EXPORT-MANIFEST.json` del staging, y falla si difieren (por ejemplo, si alguien activa `export:true` en una herramienta nueva y olvida regenerar el staging).
- **`license: null` y `export: false` se mantienen** en todo `data/open-source-tools.json` (punto 8): esta PR construye la red de seguridad, no activa ninguna publicación.
- **Tests deterministas** (`tests/test-build-open-source-export.py`, ampliado de 8 a 13 casos, todos los anteriores siguen en verde):
  - **caso 9**: import local transitivo no declarado en `files` → rechazado, nombrando el fichero que falta;
  - **caso 10**: import declarado pero adaptación de terceros no reflejada en `third_party` → rechazado;
  - **caso 11**: con `files` y `third_party` completos → valida sin error;
  - **caso 12**: `--check` detecta que el manifest actual (herramientas `export:true` ahora mismo) ya no corresponde al staging generado previamente;
  - **caso 13**: ejecuta `validate()` contra el **grafo real** de `assets/legibilidad-engine.js` en el propio repo (activando `export:true` solo en memoria para la prueba, nunca escrito a disco) y confirma que el cierre resuelve exactamente `{legibilidad-engine.js, silabajs-lite-2.1.0.js}` sin error — la prueba que demuestra que el fix real funciona, no solo el fixture sintético.

## Evidencia de ejecución (real)

```
$ node tests/test-tipo-lector.mjs
tests/test-tipo-lector: OK

$ QA_CHROMIUM_EXECUTABLE_PATH=... node qa/tipo-lector-browser.mjs
tipo-lector-browser: PASS

$ python scripts/audit-private-tools.py herramientas/*/index.html ...
PASS — 20 file(s) satisfy the static private-tool preflight

$ python scripts/build-tools-hub.py data/tools-hub.json herramientas/index.html --check
OK: 18 herramientas, 2 directorios

$ python scripts/check-navigation-coverage.py
PASS: navigation coverage (61 registry routes, 55 sitemap routes, 18 interactive tools)

$ python scripts/check-internal-graph.py
Summary: 0 error(s), 0 warning(s)

$ python scripts/check-heading-structure.py
Heading/skip-link structure: 69 ficheros HTML revisados; 0 problema(s).

$ python scripts/check-local-assets.py
Local asset check: 89 HTML files scanned; 0 broken local reference(s).

$ python scripts/build-sitemap.py --check
SITEMAP OK: 55 URLs

$ python scripts/check-secrets.py
No obvious secrets found in tracked files.

$ node qa/sitewide-reflow-browser.mjs
sitewide-reflow-browser: OK (68 routes, 2 viewports, 136 checks)

$ python tests/test-build-open-source-export.py
tests/test-build-open-source-export: OK   [13/13 casos, antes 8/8]
```

**Pruebas en rojo reales**: caso 9 y 10 de `test-build-open-source-export.py` confirmaron que, ANTES de este fix, el manifest real de `legibilidad` habría producido exactamente el paquete incompleto que describe el documento 63 (motor sin su dependencia MIT, aviso de terceros falso por omisión) si alguien hubiera activado `export:true` sin las correcciones de este PR.

## CI

`qa/tipo-lector-browser.mjs` wireado en `tools-browser-qa.yml` (nuevas rutas `herramientas/que-tipo-de-lector-eres/**`, `assets/tipo-lector*`). `tests/test-tipo-lector.mjs` y `tests/test-build-open-source-export.py` ya cubiertos por el barrido genérico de `tool-tests.yml` (`tests/*.mjs` / `tests/test-*.py`), sin necesidad de tocar su trigger.
