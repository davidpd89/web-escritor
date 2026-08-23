# PENDIENTE N — Auditoría GPT líneas 1201–1400

Fecha de auditoría: 2026-08-23  
Base verificada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Árbol: `4322f69934a1907a8af0c715ebb26762fe3ff83c`

> Esta rama registra únicamente deuda **nueva y no absorbida por otras PR** localizada al contrastar exactamente las líneas 1201–1400 de `pendiente funcionalidad gpt.txt` contra el repositorio actual. No anticipa la línea 1401 ni documentos posteriores.
>
> No tocar `main`, no desplegar producción y no activar auto-merge.

## Resumen ejecutivo

El TXT contiene varios diagnósticos que ya no describen correctamente el HEAD actual. Tras verificarlos contra código, tests, QA y PR abiertas, esta ronda deja dos frentes reales para esta PR:

1. **N.1 — Fundación Lectores Beta V1+**: la capa funcional de adquisición/operación no existe todavía. Debe construirse como producto independiente de la newsletter general, sin publicar aún una comunidad vacía.
2. **N.2 — Cierre de validación empírica del Auditor de página de libro**: el motor y sus tests sintéticos existen; falta conservar evidencia reproducible de revisión sobre varias páginas reales/representativas para controlar falsos positivos y negativos.

La instrumentación pendiente de Metadatos Libro y del Auditor de página de libro **no se duplica aquí**: se ha añadido como alcance explícito a la PR #63, autoridad actual de la taxonomía analítica sitewide.

---

## Clasificación del tramo 1201–1400

### Documento 38 — Navegación V1

**YA DETECTADO / #68.**

La línea 1201 insiste en normalizar Explorar a los cinco territorios estables. Esa deuda ya está registrada en la PR #68 (`M — Auditoría GPT 1001–1200: territorios estables de navegación`). No se crea un segundo dueño.

### Documento 39 — Comunidad / Lectores Beta

**DEUDA NUEVA — N.1.**

Verificación actual:

- no existe `/lectores-beta/` en el árbol del HEAD;
- no aparece ninguna entrada `beta`/`lectores-beta` en `data/content-registry.json`;
- no existe una PR abierta o cerrada localizada con alcance «lectores beta»;
- la PR #55 corresponde al Worker de newsletter general y no debe absorber este propósito distinto.

La especificación auditada diferencia correctamente dos fases y esa separación debe conservarse.

#### N.1 — Fundación Lectores Beta V1+

Construir **solo la fundación funcional** necesaria para captar y operar un primer grupo de lectores beta, con propósito y consentimiento independientes de la newsletter general.

Alcance mínimo esperado:

- landing o superficie de captación de lectores beta;
- formulario y consentimiento específicos para ese propósito;
- flujo de confirmación/alta propio, sin reutilizar de forma ambigua el consentimiento de newsletter;
- listas/atributos/automatización de Brevo propios cuando corresponda;
- Worker/endpoint propio o contrato claramente separado si la arquitectura final decide reutilizar infraestructura compartida;
- mecanismo de solicitud para escritores/proyectos, si forma parte de la primera fase aprobada;
- operación privada o semi-asistida suficiente para poner en marcha el servicio sin fingir actividad pública;
- tratamiento de datos minimizado, documentación de privacidad y posibilidad de baja/retirada de consentimiento;
- QA determinista del flujo de alta y de las separaciones de propósito/lista.

#### Lo que **NO** debe publicarse todavía

La capa social pública queda **GATED** hasta existir masa crítica y actividad real. No crear ahora, solo para “rellenar” arquitectura:

- `/lectores-beta/comunidad/` vacía;
- directorios públicos sin miembros reales;
- perfiles sociales públicos;
- observatorio o estadísticas comunitarias sin muestra suficiente;
- tablero público sin actividad;
- métricas decorativas o testimonios inventados.

Este proyecto es **no bloqueante para el lanzamiento del 3 de septiembre**. Debe competir en prioridad por crecimiento posterior, no desplazar QA/release blockers actuales.

### Documento 40 — Validador de metadatos de libro

**PARCIAL / MEDICIÓN ABSORBIDA POR #63; NO DEUDA NUEVA DE TESTS.**

El TXT afirmaba que faltaba una suite dedicada, pero el HEAD actual sí contiene:

- `tests/test-metadatos-libro.mjs`;
- `qa/tools-publishing-browser.mjs`;
- CSP de la herramienta con `connect-src 'none'`.

La suite cubre generación, URLs HTTPS, warnings, sanitización de payload hostil y campos opcionales; el QA de navegador añade un guard de red/exfiltración para la familia de herramientas de publicación.

Sí sigue faltando instrumentación `dp:analytics` en `assets/metadatos-libro.js`, pero ese hueco pertenece a #63. Se ha dejado allí un comentario explícito que exige medir generación/copia sin enviar título, autor, URL, ISBN, description, imagen, handles ni contenido del usuario.

No abrir N.3 por ello.

### Documento 41 — Radar de convocatorias

**HECHO / operación editorial continua.**

No aparece deuda nueva en este tramo. La ausencia de un cron activo no se reabre porque la especificación auditada lo declara preparado pero no activado.

### Documento 42 — Preparador de entrevista familiar

**SUPERADO.**

La afirmación de las líneas 1291–1299 de que falta `test-entrevista-familiar-core.mjs` es incorrecta frente al HEAD actual. Existe:

- `tests/test-entrevista-familiar-core.mjs`;
- `assets/entrevista-familiar-core.js` con RNG inyectable;
- `assets/entrevista-familiar.js` con `dp:analytics` limitado a duración, número de temas y `object_mode`, sin nombre, parentesco, preguntas ni contenido personal.

No crear tarea ni PR adicional.

### Documento 43 — Auditor de página de libro

**PARCIAL — N.2 + medición absorbida por #63.**

El motor y la QA están más avanzados de lo que afirma el TXT:

- existe `tests/test-book-page-audit-rules.mjs`;
- cubre página rica, mínimos, JSON-LD inválido, mismatch de ISBN, mismatch de autor, schema-only ISBN, entrada hostil y HTML vacío;
- `qa/tools-publishing-browser.mjs` ejecuta el auditor en navegador, prueba varios casos sintéticos y verifica que el contenido pegado no se exfiltra;
- `herramientas/auditor-pagina-libro/index.html` mantiene CSP `connect-src 'none'`.

La arquitectura con landing propia queda **SUPERADA/SUSTITUIDA** respecto a la instrucción histórica que pedía integrarlo exclusivamente en otro auditor. No revertir.

#### N.2 — Validación empírica y falsos positivos

Lo que no aparece conservado en el repositorio es la evidencia exigida por el documento de probar el motor contra **3–5 páginas de libro reales o fixtures representativos derivados de estructuras reales** y revisar falsos positivos/negativos.

Criterio de cierre:

1. seleccionar 3–5 estructuras de página suficientemente distintas;
2. documentar para cada una qué debería detectar el auditor y qué no;
3. congelar fixtures sanitizados o un corpus reproducible que no dependa de red en CI;
4. comprobar esenciales, metadatos, JSON-LD e inconsistencias;
5. registrar cualquier falso positivo/negativo descubierto y corregir regla o excepción cuando esté justificado;
6. añadir el conjunto al QA automatizado o, si alguna comprobación debe seguir siendo humana, documentar evidencia y criterio de aceptación claros.

No convertir ISBN, editorial, páginas, formato u otros campos opcionales en requisitos para “hacer pasar” las muestras.

La medición anónima de uso que también pide el documento no se implementa aquí: se ha delegado explícitamente a #63 para evitar una segunda taxonomía. Allí debe quedar prohibido enviar HTML, URL, dominio, título esperado/detectado, ISBN o evidencias extraídas.

### Documento 44 — Ficha de historia de un objeto heredado

**HECHO / 0 deuda nueva.**

La utilidad existe y el HEAD además contiene `tests/test-objeto-heredado-core.mjs`. No aparece una desviación independiente en este tramo que justifique otro owner.

### Documento 45 — Constructor de sesión de club de lectura

**HECHO / 0 deuda nueva.**

La infraestructura existente tiene además `tests/test-club-session-engine.mjs`. No reabrir arquitectura ni descubrimiento desde este bloque.

### Documento 46 — Atlas literario

**YA DETECTADO / #59.**

La ausencia de tests específicos del Atlas sigue siendo deuda real en la base, pero ya está expresamente absorbida por la PR #59 (`F — Herramientas: bugs y gaps de código`), cuyo alcance F.3 dice: «Atlas literario sin tests (scaffolding y validación ya funcionan)».

No duplicar.

La línea 1400 termina a mitad de la separación «motor/infraestructura del Atlas → debe ser verificable». Esta ronda se detiene aquí y **no interpreta ni anticipa** lo que sigue desde 1401.

---

## Coordinación con PR existentes

- **#68 / M** — dueño de los cinco territorios de Explorar.
- **#63 / I** — dueño de la taxonomía analítica sitewide; se ha comentado explícitamente el alcance de Metadatos Libro y Auditor de página de libro con restricciones de privacidad.
- **#59 / F** — dueño del test ausente del Atlas.
- **#55 / B** — newsletter general/DOI; no debe convertirse en dueño de Lectores Beta ni mezclar consentimientos.
- **#58 / E** — smoke test post-deploy general; no sustituye la validación empírica específica del motor del Auditor.

## Aceptación de esta PR

Esta PR es un **brief de deuda**, no la implementación final. Para cerrarla como resuelta deberán existir implementaciones/PR derivadas o commits que acrediten:

### N.1

- fundación funcional de Lectores Beta construida con consentimiento y propósito independientes;
- flujo de alta/baja y pruebas deterministas;
- sin comunidad pública vacía ni datos ficticios;
- integración con Brevo/Worker resuelta de forma programática y documentada;
- privacidad/minimización revisadas antes de activar producción.

### N.2

- corpus reproducible de 3–5 estructuras reales/representativas;
- expectativas explícitas por fixture;
- falsos positivos/negativos revisados;
- QA automatizada o evidencia humana preservada;
- sin relajar la distinción entre esenciales, opcionales y enriquecimientos.

## Fuera de alcance

- Metricool, calendario social y programación de publicaciones;
- merge a `main`;
- despliegue en producción;
- auto-merge;
- publicación de una comunidad beta vacía;
- duplicar la taxonomía analítica de #63;
- duplicar Atlas (#59) o navegación (#68).

---

# Estado de implementación (2026-08-23)

## N.2 — Validación empírica del Auditor de página de libro (hecho primero)

- Corpus reproducible de **5 estructuras suficientemente distintas** en
  `tests/fixtures/book-page-audit-corpus/`: 2 páginas **reales y
  publicadas** del propio sitio (leídas directamente de
  `libros/samuel-entre-mundos/index.html` y
  `las-manecillas-del-recuerdo/index.html` — si la página real cambia,
  este test lo nota) + 3 fixtures representativos derivados de patrones
  reales (autopublicación mínima, editorial tradicional rica, y un bug de
  CMS real y frecuente: JSON-LD desactualizado tras un cambio de título de
  última hora).
- `expectations.json` documenta, por cada estructura, qué debería y qué
  NO debería detectar el motor — no se ha convertido ningún campo
  opcional (ISBN, editorial, páginas, formato) en requisito para que un
  fixture "pase".
- **Hallazgo real durante la validación** (no un fallo, un comportamiento
  correcto documentado): sin `expectedTitle` explícito, el motor usa el
  título del `Book` JSON-LD como referencia, así que un caso de schema
  desactualizado produce una señal doble (`book_title` en `review` +
  `book_title_mismatch`) en vez de una sola — reforzado, no roto.
- **0 falsos positivos, 0 falsos negativos** en las 5 estructuras: la
  inconsistencia real (`book_title_mismatch`/`book_author_mismatch`) se
  detecta; la que no existe (`book_isbn_mismatch`, ISBN idéntico en ambos
  sitios) no se marca.
- `tests/test-book-page-audit-corpus.mjs` (nuevo) ejecuta el motor real
  contra las 5 estructuras y compara con `expectations.json`. Cubierto
  automáticamente por `tool-tests.yml` (`for f in tests/*.mjs`), sin
  necesidad de tocar ningún workflow.
- La medición anónima de uso (`dp:analytics`) sigue delegada a #63, tal y
  como pedía esta misma PR; no se ha implementado aquí.

## N.1 — Fundación Lectores Beta V1+

- **Landing propia**: `/lectores-beta/` (`noindex, follow` — operación
  privada/semi-asistida, no promocionada en Explorar/header/footer;
  registrada en `data/content-registry.json` como `status: "noindex"`,
  mismo patrón que `work-jaula-staging`). Enlazada de forma discreta desde
  la sección de contacto de `/autor.html` («Programa de lectores beta»).
- **Consentimiento propio**, textualmente distinto de "recibir novedades
  del autor": explica que implica recibir material sin publicar y que se
  puede pedir opinión, y que es una lista separada de la newsletter
  general.
- **Lista de Brevo separada**: `cloudflare-worker-subscribe.js` añade
  `source: "lectores-beta"` al whitelist y lo enruta a
  `env.BREVO_BETA_LIST_ID` (nunca a `env.BREVO_LIST_ID`) — si esa
  variable no está configurada, falla cerrado con 500, nunca cae a la
  lista general. El Worker sigue siendo el mismo endpoint compartido, con
  un contrato de fuente/lista claramente separado (explícitamente
  permitido por el propio criterio de aceptación de esta PR).
- **Flujo de alta propio en `script.js`**: mismo mecanismo de envío que el
  resto de formularios, pero copy de éxito propio («programa de lectores
  beta», nunca «novedades de David Porto Díaz»).
- **Privacidad**: nueva finalidad específica en `privacidad.html`
  (`#finalidad`), separada de la newsletter general, con enlace a
  `/lectores-beta/`; base legal y derechos sin cambios; fecha de
  actualización y changelog de la página revisados.
- **Sin comunidad pública**: no se ha creado `/lectores-beta/comunidad/`,
  ni directorios, ni perfiles, ni métricas decorativas — exactamente lo
  que esta PR prohíbe explícitamente.
- **QA determinista**:
  - `tests/test-cloudflare-worker-subscribe.mjs` — 3 casos nuevos: lista
    separada correcta, fallo cerrado sin `BREVO_BETA_LIST_ID`, fuentes
    generales no afectadas.
  - `qa/lectores-beta-browser.mjs` (navegador real) — sin consentimiento
    no se envía nada; con consentimiento se envía exactamente
    `{ email, source: "lectores-beta" }` y el copy de éxito no reutiliza
    el de la newsletter general.
  - Ambos wireados en `privacy-legal-browser-qa.yml` (ya cubría
    `cloudflare-worker-subscribe.js`/`privacidad.html`, tema correcto para
    esta pieza).

## Hallazgo colateral corregido: email de contacto obsoleto

Mientras se auditaba `autor.html` para N.1 se encontró que el documento
1201–1400 daba por resuelto un bug que en realidad seguía vivo en **7
sitios reales**, en dos formas que el grep literal de auditorías previas
no atrapaba:

- texto visible codificado con la entidad HTML `&#64;` (`samuelentremundos&#64;gmail.com`)
  en `index.html` (×3), `libros/samuel-entre-mundos/index.html` (×2),
  `autor.html` (×1) y `prensa.html` (×1) — el `href` real ya era correcto,
  pero el texto copiable/legible no lo era;
- `data-n="samuelentremundos"` en `clubes-de-lectura/samuel-entre-mundos/index.html`
  — este SÍ era un bug funcional real: `script.js` reconstruye `href` en
  tiempo de ejecución a partir de `data-n`, así que el enlace "Contactar
  al autor" abría un `mailto:` a la dirección equivocada.

Corregidas las 7 instancias a `davidportodiaz@gmail.com` (la dirección
que ya usaban todos los `href` hardcodeados). **Gate nuevo**:
`scripts/check-no-stale-contact-email.py` (+
`tests/test-check-no-stale-contact-email.py`, 3 casos) impide que
reaparezca, wireado en el mismo workflow.

## Evidencia de ejecución (real)

```
$ node tests/test-book-page-audit-corpus.mjs
[5/5 estructuras, 0 fallos]
tests/test-book-page-audit-corpus: OK

$ node tests/test-book-page-audit-rules.mjs
tests/test-book-page-audit-rules: OK

$ node tests/test-cloudflare-worker-subscribe.mjs
test-cloudflare-worker-subscribe: all assertions passed

$ node qa/newsletter-worker-contract.mjs
newsletter Worker contract: PASS

$ node tests/test-newsletter-client-contract.mjs
test-newsletter-client-contract: all assertions passed

$ QA_CHROMIUM_EXECUTABLE_PATH=... node qa/lectores-beta-browser.mjs
lectores-beta-browser: PASS

$ python scripts/check-no-stale-contact-email.py --check
Stale contact email check: 0 incumplimiento(s).

$ python tests/test-check-no-stale-contact-email.py
[3/3 OK]

$ python scripts/check-navigation-coverage.py
PASS: navigation coverage (61 registry routes, 54 sitemap routes, 17 interactive tools)

$ python scripts/check-internal-graph.py
Summary: 0 error(s), 0 warning(s)   (lectores-beta/index.html correctamente excluido como noindex, no huérfano)

$ python scripts/check-heading-structure.py
Heading/skip-link structure: 69 ficheros HTML revisados; 0 problema(s).

$ python scripts/check-local-assets.py
Local asset check: 89 HTML files scanned; 0 broken local reference(s).

$ python scripts/build-sitemap.py --check
SITEMAP OK: 54 URLs

$ python scripts/check-secrets.py
No obvious secrets found in tracked files.

$ node qa/sitewide-reflow-browser.mjs
sitewide-reflow-browser: OK (68 routes, 2 viewports, 136 checks)
```

**Pruebas en rojo reales**: `check-no-stale-contact-email.py` detectó una
reinyección de texto de prueba en `autor.html` (restaurado); el Worker
real (`test-cloudflare-worker-subscribe.mjs`) confirma que
`source: "lectores-beta"` sin `BREVO_BETA_LIST_ID` falla con 500 en vez
de caer silenciosamente a la lista general.
