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
