# PENDIENTE O — Auditoría GPT líneas 1401–1600

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente auditada: `pendiente funcionalidad gpt.txt`, líneas **1401–1600 exactas**.

> Esta rama registra únicamente deuda técnica nueva que sigue viva en el HEAD comprobado. No implementa todavía las soluciones. No tocar `main`, no desplegar producción y no activar auto-merge.

## Resumen

El tramo mezcla conclusiones antiguas con una auditoría posterior más precisa. Al contrastarlo con el repositorio actual, varias de las deudas que el propio TXT daba por pendientes ya están resueltas y no deben reabrirse.

La deuda nueva no cubierta por las PR abiertas queda concentrada en:

1. dos herramientas que el documento 57 marca expresamente como «IMPLEMENTAR YA» y que siguen sin existir en el sistema productivo;
2. una incompatibilidad real entre el formato V1 documentado para Distribución de POV y el parser vigente.

## O.1 — Completar las dos herramientas base pendientes del hub

### O.1a — Contador de palabras

El documento 57 exige la ruta canónica:

- `/herramientas/contador-palabras/`

Estado real del HEAD:

- la ruta no existe;
- no aparece en `data/tools-hub.json`;
- no existe referencia alternativa con ese slug;
- el hub actual contiene 17 herramientas, pero ninguna expone este producto independiente.

`/herramientas/manuscrito/` sí calcula palabras como parte de un análisis de capítulos más amplio. Eso no satisface por sí solo la ruta/producto específico exigido por el documento 57, aunque debe reutilizarse lógica existente cuando sea razonable para evitar duplicación técnica.

### O.1b — Limpiador de manuscritos

El documento 57 exige la ruta canónica:

- `/herramientas/limpiador-manuscritos/`

Estado real del HEAD:

- la ruta no existe;
- no aparece en `data/tools-hub.json`;
- no existe una herramienta registrada equivalente bajo ese slug;
- no debe resolverse con un placeholder.

### Contrato de implementación de O.1

Para ambas herramientas:

- construir una utilidad funcional, no una landing vacía;
- mantener procesamiento local cuando el input sea texto/manuscrito;
- cumplir el contrato existente de herramientas privadas/local-only (`connect-src 'none'`, sin envío ni almacenamiento persistente del texto);
- quedar cubiertas por `scripts/audit-private-tools.py`;
- incorporarlas a `data/tools-hub.json` y al registro/navegación que corresponda sin crear una segunda fuente de verdad;
- añadir tests deterministas de motor y QA suficiente para las rutas públicas;
- conservar accesibilidad, no-JS explicativo, responsive y estilos V1;
- reutilizar utilidades/motores existentes cuando encajen, en lugar de copiar contadores o normalizadores.

La implementación concreta del «limpiador» debe seguir el contrato funcional autoritativo del documento 57; esta auditoría no inventa transformaciones nuevas.

## O.2 — Compatibilidad del formato V1 en Distribución de POV

El documento 58, dentro de las líneas auditadas, establece como entrada V1:

```text
POV | palabras
```

El motor actual (`assets/pov-distribucion-engine.js`) interpreta:

```text
escena | POV | palabras opcionales
```

Y, con exactamente dos columnas, interpreta:

```text
escena | POV
```

Esto no es una diferencia de copy: es una incompatibilidad de formato. El test vigente `tests/test-pov-distribucion.mjs` fija expresamente el comportamiento actual con ejemplos como `A | Ana`, de modo que el formato documentado `Ana | 1200` sería interpretado como escena=`Ana`, POV=`1200`, no como POV=`Ana`, palabras=`1200`.

### Contrato de implementación de O.2

- preservar el formato actual de escenas, porque ya es funcional y está testeado;
- añadir compatibilidad real con `POV | palabras` sin reinterpretar silenciosamente entradas actuales;
- la selección/detección del formato debe ser determinista y comprensible para el usuario;
- si existe ambigüedad, resolverla mediante un modo explícito o una regla inequívoca documentada, no mediante heurísticas opacas;
- añadir tests que prueben ambos contratos y eviten regresiones;
- mantener procesamiento local y el contrato de privacidad vigente;
- no modificar todavía requisitos del documento 58 que aparezcan después de la línea 1600: esta ronda se detiene exactamente ahí.

## Hallazgos del tramo que NO deben convertirse en otra deuda

### Documento 49 — privacidad de herramientas

**SUPERADO / HECHO.**

El TXT afirmaba que `scripts/audit-private-tools.py` existía pero no estaba conectado a CI. El HEAD actual ya lo ejecuta desde `.github/workflows/content-index-check.yml` en todas las PR. El workflow además documenta por qué ese gate protege la promesa local-only.

No abrir otra PR para ello.

### Documentos 47 y 48

**HECHO.** Tiempo de lectura en voz alta y Variedad léxica ya cuentan con implementación local y tests. Sin deuda nueva en este tramo.

### Documento 50 — decisiones de escritura

**HECHO en su fase actual.**

`tests/test-validate-writing-decision.py` confirma que el contrato autoritativo es interno: plantilla + validador, y que el propio documento indica «No crear todavía» el hub público. Por tanto, la ausencia de `/decisiones/` o `/cuaderno/decisiones-de-escritura/` no es un fallo.

### Documento 51

**GATED-INTENCIONAL.** El propio tramo lo condiciona temporalmente a diciembre de 2026. No convertirlo en deuda de agosto.

### Documentos 52–56

Sin deuda nueva obligatoria:

- 52 — research-log: pipeline interno implementado; `research-notes.component.html` sigue siendo progresivo/opcional mientras no haya una publicación seleccionada que lo necesite;
- 53 — preguntas de lectores: pipeline interno, sin crear `/preguntas/`;
- 54 — vídeo → activo editorial: test y componente faltantes ya pertenecen a **PR #59**;
- 55 — colecciones: sistema implementado; colecciones sin densidad permanecen correctamente en draft;
- 56 — directorio externo de herramientas: implementado y complementario al hub propio.

### Atlas literario

Tests faltantes → **YA DETECTADO en PR #59**. No duplicar.

### Analítica

Cualquier instrumentación adicional de estas nuevas herramientas debe consumir la taxonomía sitewide de **PR #63** si finalmente se instrumenta; no crear una convención paralela.

### Redes sociales / Metricool

**OUT OF SCOPE** por decisión del propietario del proyecto web.

## Criterios de aceptación de esta PR de auditoría

Esta PR documental se considera correctamente cerrada cuando el trabajo posterior demuestre, como mínimo:

- las dos rutas de O.1 existen como productos funcionales o existe una decisión autoritativa posterior que las sustituye explícitamente;
- el hub/registry/checkers permanecen sincronizados;
- privacidad local-only y tests pasan para ambas;
- Distribución de POV acepta de forma no ambigua el contrato `POV | palabras` además del formato actual, con tests para los dos;
- no se reabren 49, 50, 52–56 ni Atlas como deudas nuevas duplicadas.

## Límite de auditoría

La revisión termina exactamente en la línea **1600**. El documento 58 continúa después; cualquier requisito adicional deberá contrastarse en la ronda **1601–1800** y, si pertenece a esta misma inconsistencia POV, se incorporará a esta PR O en vez de crear una duplicidad.

---

# Estado de implementación (2026-08-23)

## O.1 — Dos herramientas base nuevas

- **`/herramientas/contador-palabras/`**: motor propio (`assets/contador-palabras-engine.js`) — palabras (Unicode, incluye acentos y apóstrofos), caracteres con/sin espacios, frases, párrafos, medias por frase/párrafo y tiempo de lectura estimado (200 ppm). Cálculo en vivo mientras se escribe, sin necesidad de pulsar un botón.
- **`/herramientas/limpiador-manuscritos/`**: motor propio (`assets/limpiador-manuscritos-engine.js`) con **9 correcciones independientes y togglables** (todas activas por defecto): espacios al final de línea, espacios dobles, tabulaciones, espacio no separable, líneas en blanco de más, espacio antes de puntuación, comillas rectas → «», guion de diálogo → raya, puntos suspensivos. Cada corrección informa cuántas veces se aplicó; el usuario puede desactivar cualquiera y volver a generar. Salida en un `<textarea readonly>` con copiar/descargar `.txt`.
- **No se ha inventado ninguna transformación agresiva de reescritura**: las 9 reglas son higiene de formato ampliamente reconocida (limpiar artefactos de pegar desde Word/Docs/móvil), no decisiones de estilo. Las dos heurísticas con más margen de error (comillas alternadas y guion de diálogo solo al inicio de línea) están explícitamente señaladas como tal en la propia página («revisa el resultado antes de darlo por bueno»), en vez de presentarse como automáticas y perfectas.
- **Privacidad local-only real**: ambas páginas pasan `scripts/audit-private-tools.py` (CSP `connect-src 'none'`, sin `/script.js`, sin `fetch`/`XHR`/almacenamiento persistente); `navigator.clipboard` y la descarga vía `Blob`+`URL.createObjectURL` no son red, no están prohibidos por el contrato.
- **Sin segunda fuente de verdad**: registradas en `data/tools-hub.json` (19 herramientas, antes 17) y `data/content-registry.json`; `herramientas/index.html` se **regenera** con `scripts/build-tools-hub.py` (no se editó a mano); `scripts/build-sitemap.py` regenerado (56 URLs, antes 54).
- **Tests deterministas**: `tests/test-contador-palabras.mjs` (8 casos: texto vacío, solo espacios, acentos/apóstrofos, tiempo de lectura, formato de horas) y `tests/test-limpiador-manuscritos.mjs` (9 casos: cada regla por separado, selección vacía, combinación, `RULES` expone id+label para la UI).
- **QA de navegador real**: `qa/o1-new-tools-browser.mjs` — recuento en vivo, ejemplo, borrar, checkboxes activos por defecto, desactivar una regla cambia el resultado, cero excepciones JS.

## O.2 — Compatibilidad del formato V1 en Distribución de POV

- **Modo explícito, no heurística**: el documento pedía evitar reinterpretar en silencio. `escena | POV` (2 o 3 columnas) y `POV | palabras` (2 columnas) son ambiguos entre sí a nivel de conteo de columnas, así que en vez de adivinar por contenido se añadió un `<select data-pov-format-mode>` con dos opciones claramente descritas; el usuario elige, la página cambia de campo de entrada y de interpretación.
- **Motor**: `parse()`/`analyze()` (escenas) **sin tocar** — mismo comportamiento, mismos tests previos en verde. Nuevas funciones separadas `parseTotals()`/`analyzeTotals()` para el formato `POV | palabras` (totales ya agregados, sin orden de escena, por lo que no calculan racha/hueco/secuencia — no existen en ese formato).
- **UI coherente con la ausencia de datos**: en modo "Totales", la Secuencia de lectura y los Carriles de POV se ocultan (no tiene sentido mostrarlos sin orden), la cabecera de la tabla resumen cambia (sin columnas de Escenas/Racha/Hueco) y hay una nota explicando por qué.
- **Tests**: `tests/test-pov-distribucion.mjs` ampliado (formato de escenas intacto + 5 casos nuevos: totales válidos, `wordShare`, rechazo de segunda columna no numérica, rechazo de POV duplicado). `qa/pov-distribucion-format-browser.mjs` (navegador real): modo escenas sigue funcionando, modo totales carga su propio ejemplo (no reutiliza el campo de escenas), oculta secuencia/carriles, cabecera correcta, y un formato incorrecto da un error específico sin reinterpretar.

## Evidencia de ejecución (real)

```
$ node tests/test-contador-palabras.mjs
tests/test-contador-palabras: OK

$ node tests/test-limpiador-manuscritos.mjs
tests/test-limpiador-manuscritos: OK

$ node tests/test-pov-distribucion.mjs
tests/test-pov-distribucion: OK

$ QA_CHROMIUM_EXECUTABLE_PATH=... node qa/o1-new-tools-browser.mjs
o1-new-tools-browser: PASS

$ QA_CHROMIUM_EXECUTABLE_PATH=... node qa/pov-distribucion-format-browser.mjs
pov-distribucion-format-browser: PASS

$ python scripts/audit-private-tools.py herramientas/*/index.html clubes-de-lectura/preparar-sesion/index.html convocatorias-escritores/index.html recursos/ficha-historia-objeto-heredado/index.html
PASS — 21 file(s) satisfy the static private-tool preflight

$ python scripts/build-tools-hub.py data/tools-hub.json herramientas/index.html --check
OK: 19 herramientas, 2 directorios

$ python scripts/check-navigation-coverage.py
PASS: navigation coverage (62 registry routes, 56 sitemap routes, 19 interactive tools)

$ python scripts/check-internal-graph.py
Summary: 0 error(s), 0 warning(s)

$ python scripts/check-heading-structure.py
Heading/skip-link structure: 70 ficheros HTML revisados; 0 problema(s).

$ python scripts/check-local-assets.py
Local asset check: 90 HTML files scanned; 0 broken local reference(s).

$ python scripts/build-sitemap.py --check
SITEMAP OK: 56 URLs

$ python scripts/check-secrets.py
No obvious secrets found in tracked files.

$ node qa/sitewide-reflow-browser.mjs
sitewide-reflow-browser: OK (69 routes, 2 viewports, 138 checks)
```

## CI

`qa/o1-new-tools-browser.mjs` y `qa/pov-distribucion-format-browser.mjs` (autocontenidos, levantan su propio servidor) wireados en `sitewide-reflow-qa.yml`, que ya corre en cada PR sin filtro de rutas. `assets/**`/`tests/**` ya disparan `tool-tests.yml`; `content-index-check.yml` no tiene filtro de rutas y ya cubre `audit-private-tools.py` (glob `herramientas/*/index.html`) y el `--check` de `build-tools-hub.py`. No hizo falta tocar sus triggers.
