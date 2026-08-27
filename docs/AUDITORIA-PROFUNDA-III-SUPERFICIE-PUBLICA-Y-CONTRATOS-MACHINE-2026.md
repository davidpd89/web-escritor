# Auditoría profunda III — superficie pública, contratos machine-readable y resiliencia

**Proyecto:** davidportodiaz.com  
**Repositorio:** `davidpd89/web-escritor`  
**Base auditada:** `main` @ `85dc4f2f6650ad818faf317cb6d6714bc97cb616`  
**Fecha:** 27 de agosto de 2026  
**Tipo de PR:** documentación y especificación; no modifica producción, no despliega y no mergea.

---

## 0. Propósito de esta tercera pasada

Esta auditoría no repite la revisión visual/UX general, la homogeneización del sistema editorial, la arquitectura de Obras/Lectores beta ni los puntos ya recogidos en la auditoría postlaunch/producción. Tampoco reabre el ajuste tipográfico integrado en la PR #105.

La pregunta de esta pasada es distinta:

> **¿Qué puede seguir fallando aunque las páginas se vean bien y los gates actuales estén verdes?**

Se ha revisado especialmente:

- qué ficheros terminan realmente en el árbol servido al navegador;
- separación entre fuentes internas de build y superficies públicas;
- artefactos para prensa, buscadores y sistemas de IA;
- duplicación de hechos editoriales mutables;
- coherencia entre `editorial-facts.json`, `/ai/`, `llms*.txt`, press-kit y asistente;
- alcance real de `build-public-dist.py` y `.assetsignore`;
- QA que valida el código fuente pero no necesariamente el artefacto final;
- PWA/service worker, robots y otros candidatos a falsos positivos.

El resultado cambia la prioridad de una parte de la deuda: **el mayor hueco nuevo no está en el diseño, sino en la frontera entre repositorio y publicación**.

---

## 1. Resumen ejecutivo

### Veredicto

El sistema de QA es amplio y la fuente editorial central está bastante mejor gobernada de lo que parecía a primera vista. Sin embargo, existe una debilidad estructural importante: el builder público trabaja con un modelo **include-by-default** y la exclusión actual no cubre clases enteras de artefactos internos.

Eso permite que una build considerada «segura» pueda contener documentación operativa, scripts de QA, prototipos de laboratorio, migraciones SQL y configuración real del Worker del asistente. No se ha encontrado una clave secreta expuesta en los ficheros revisados y **no debe describirse como filtración de credenciales**. El problema es de minimización de superficie pública, exposición innecesaria de topología/implementación y ausencia de un contrato fuerte sobre qué artefactos son publicables.

A la vez, varias superficies públicas machine-readable mezclan hechos destinados a prensa/IA con detalles internos de implementación o de gates editoriales. Esto reduce la calidad semántica de las fuentes que precisamente se anuncian como autoridad factual.

### Prioridad propuesta

| ID | Prioridad | Hallazgo | Estado |
|---|---|---|---|
| AIII-01 | **P0** | El `public-dist` permite publicar directorios internos completos (`docs/`, `qa/`, `lab/`, `migrations/`) | Confirmado |
| AIII-02 | **P0** | Configuración real del asistente y Worker quedan fuera de la lista de exclusión | Confirmado |
| AIII-03 | **P1** | Configuración/dependencias de build (`package*.json`, Lighthouse Pro) pueden formar parte del output público | Confirmado |
| AIII-04 | **P1** | El check del `dist` solo comprueba lo que ya está en la denylist; no detecta una clase nueva de fichero interno | Confirmado |
| AIII-05 | **P1** | JSON público de Manecillas mezcla datos para prensa con nomenclatura de incidente/gate interno | Confirmado |
| AIII-06 | **P1** | `press-kit/package-manifest.json` es un manifiesto de build almacenado en un namespace público | Confirmado |
| AIII-07 | **P1** | `llms-full.txt` publica decisiones de implementación, no solo hechos verificables | Confirmado |
| AIII-08 | **P1** | El asistente mantiene hechos mutables duplicados a mano fuera del contrato editorial | Confirmado |
| AIII-09 | **P2** | `/ai/` duplica manualmente la fecha de revisión factual | Confirmado |
| AIII-10 | **P1** | Falta una proyección pública explícita del contrato editorial interno | Arquitectura recomendada |

---

## 2. Hallazgos confirmados

## AIII-01 — P0 — El árbol público admite directorios internos completos

### Evidencia

`scripts/build-public-dist.py` declara explícitamente:

- «default-INCLUDE every git-tracked file»;
- después resta `EXCLUDE_DIR_PREFIXES` y `EXCLUDE_FILES`.

La lista actual de directorios excluidos contiene `.claude/`, `.github/`, `scripts/`, `tests/`, `data/`, fuentes de Manecillas, `publicar-web/` y `lecturas/`, entre otros.

**No contiene:**

- `docs/`
- `qa/`
- `lab/`
- `migrations/`

La omisión de `docs/` contradice además la propia cabecera del builder, que afirma que el output seguro debe evitar «internal docs».

El repositorio confirma que esos directorios contienen material inequívocamente interno:

- `docs/ASSISTANT-ARCHITECTURE-RESEARCH-V3.md`
- `docs/CLOUDFLARE-ZONE-CDN-SECURITY-RUNBOOK.md`
- `docs/BREVO-WORKER-DEPLOY.md`
- múltiples auditorías y runbooks;
- `qa/assistant-browser.mjs`, `qa/cross-engine-smoke.mjs`, `qa/csp-public-shell-browser.mjs`, etc.;
- `lab/diseno-home-v1/`;
- `migrations/assistant-quota.sql`.

`.assetsignore` se genera desde esas mismas constantes, por lo que reproduce la omisión.

### Riesgo

No es necesario que un fichero contenga un secreto para que no deba ser servido. Publicar documentación operativa, pruebas y migraciones:

- aumenta superficie de reconocimiento;
- expone estructura, decisiones técnicas y rutas internas;
- ensucia el namespace público;
- permite que crawlers/indexadores descubran material que no representa contenido editorial;
- hace más probable que un futuro documento realmente sensible llegue a producción por omisión.

### Implementación exacta

1. Añadir inmediatamente a `EXCLUDE_DIR_PREFIXES`:
   - `docs/`
   - `qa/`
   - `lab/`
   - `migrations/`
2. Regenerar `.assetsignore` con `--emit-assetsignore`.
3. Añadir una prueba que construya el output y compruebe que esas rutas no existen.
4. No depender exclusivamente de esta lista manual: aplicar también el gate por clase descrito en AIII-04.

### Aceptación

- `.preview-dist/docs/` inexistente.
- `.preview-dist/qa/` inexistente.
- `.preview-dist/lab/` inexistente.
- `.preview-dist/migrations/` inexistente.
- Las mismas rutas quedan excluidas por `.assetsignore`.
- `release-readiness` falla si cualquiera reaparece.

---

## AIII-02 — P0 — El despliegue de assets puede incluir configuración real y código del asistente

### Evidencia

En el root existen:

- `cloudflare-worker-assistant.js`
- `wrangler.assistant.example.jsonc`
- `wrangler.assistant.jsonc`

Ninguno figura actualmente en `EXCLUDE_FILES`.

`cloudflare-worker-subscribe.js` sí está excluido expresamente, lo que evidencia una asimetría de política.

`wrangler.assistant.jsonc` contiene configuración real de despliegue del asistente: ruta de producción, binding D1, nombre e identificador de base de datos, namespaces y límites de rate limiting, modelo y valores operativos. La clave pública de Turnstile es pública por naturaleza; el identificador D1 tampoco es una credencial. El problema no es que esos valores sean secretos, sino que **el sitio estático no necesita servir el fichero de infraestructura completo**.

`cloudflare-worker-assistant.js` documenta además bindings, cadena de proveedores, cuotas y funcionamiento del endpoint.

### Riesgo

- exposición innecesaria de topología y controles antiabuso;
- duplicación pública de código que ya se despliega como Worker separado;
- futura posibilidad de añadir por error un valor operativo más sensible al mismo fichero;
- incumplimiento del principio que ya se aplica correctamente al Worker de suscripción.

### Implementación exacta

Añadir a la política pública:

- `cloudflare-worker-assistant.js`
- `wrangler.assistant.jsonc`
- `wrangler.assistant.example.jsonc`

Y añadir regla de clase:

- `wrangler*.jsonc` no publicable salvo excepción explícita;
- `cloudflare-worker-*.js` no publicable salvo excepción explícita de runtime demostrada.

### Aceptación

Los tres recursos no están presentes en `.preview-dist` ni en el despliegue estático, mientras `/api/assistant*` sigue funcionando desde su Worker independiente.

---

## AIII-03 — P1 — Dependencias y configuración de QA se publican por defecto

### Evidencia

El root contiene, entre otros:

- `package.json`
- `package-lock.json`
- `lighthouserc-pro-resources.json`
- `lighthouserc.json`

La exclusión actual cubre `lighthouserc.json`, pero **no** `lighthouserc-pro-resources.json`; tampoco cubre `package.json` ni `package-lock.json`.

`lighthouserc-pro-resources.json` es inequívocamente configuración CI: URLs localhost, scores mínimos, número de runs, flags de Chrome y destino de subida temporal.

### Implementación exacta

- excluir `package.json` y `package-lock.json` del output estático;
- excluir `lighthouserc-pro-resources.json`;
- añadir gate por patrones para:
  - `lighthouserc*.json`
  - `package*.json`
  - ficheros de configuración de tooling que no sean requeridos por runtime.

No excluir avisos de licencia a ciegas: `THIRD_PARTY_NOTICE_SILABAJS.md` debe tratarse según su obligación de licencia, no como basura técnica.

### Aceptación

Los ficheros de tooling/dependencias no aparecen en el manifiesto público y la aplicación sigue funcionando sin ellos.

---

## AIII-04 — P1 — `check_contents()` solo puede detectar errores que ya conoce

### Evidencia

`check_contents()` recorre:

- `EXCLUDE_DIR_PREFIXES`;
- `EXCLUDE_FILES`;
- assets sociales;
- rutas gated derivadas del content registry.

Es decir: si aparece mañana `terraform.tfstate`, `new-worker.js`, `internal-runbook.md` o un nuevo directorio `benchmarks/`, el gate será verde mientras nadie lo añada previamente a la denylist.

El comportamiento es coherente con el diseño documentado del builder, pero insuficiente para una frontera de publicación.

### Solución compatible con la arquitectura existente

No hace falta invertir de golpe todo el sitio a una allowlist estricta —el propio builder explica el riesgo de olvidar recursos runtime—. La opción más segura para este repositorio es una política en capas:

1. **Denylist explícita** para directorios/ficheros conocidos.
2. **Forbidden classes** para extensiones/nombres normalmente internos (`*.sql`, `wrangler*.jsonc`, `package*.json`, `lighthouserc*.json`, directorios QA/lab/docs/migrations).
3. **Allow-exceptions explícitas** para casos legítimos.
4. **Inspección del output final**, no solo de las fuentes.
5. Un manifiesto del dist que clasifique cada artefacto como `page`, `runtime-asset`, `machine-readable`, `verification`, `license` o excepción documentada.

### Aceptación

Un fixture nuevo `migrations/example.sql` o `internal/new-config.jsonc` hace fallar CI aunque nadie haya añadido su nombre exacto a `EXCLUDE_FILES`.

---

## AIII-05 — P1 — El press-kit público mezcla semántica de prensa con un incidente interno

### Evidencia

`press-kit/las-manecillas-del-recuerdo.json` es enlazado públicamente desde `/ai/` como JSON para reutilización editorial.

Dentro de `press` contiene:

- `coverReleaseStatus: "blocked-pending-editorial-clearance"`
- una nota que menciona literalmente `knownEditorialIncident`;
- instrucciones sobre no generar/publicar el ZIP saltándose el gate.

Son datos útiles para el proceso de build, pero no son una formulación adecuada para periodistas, librerías, crawlers o modelos.

### Cambio propuesto

Proyectar el estado público a algo editorial y autocontenido, por ejemplo:

- `coverHighRes: null`
- `coverAvailability: "on_request"` o `"not_yet_available"`
- `contact` para solicitarla.

El nombre del incidente, su gate y la instrucción de build permanecen únicamente en la fuente interna.

### Aceptación

El JSON público puede entregarse a un periodista sin exponer nombres de variables internas, incidentes ni instrucciones de pipeline.

---

## AIII-06 — P1 — `press-kit/package-manifest.json` es un artefacto de build dentro de una ruta pública

### Evidencia

`press-kit/package-manifest.json` describe:

- output ZIP;
- `editorialFacts: "editorial-facts.json"`;
- fuentes y paths de archivo;
- `required`;
- estados de release como `blocked-pending-editorial-clearance`.

Eso es un manifiesto de empaquetado, no una pieza de prensa. Al vivir dentro de `press-kit/` y no existir una exclusión específica, el builder lo trata como publicable.

### Cambio propuesto

Mover el manifiesto operativo a un espacio interno (`data/`, `docs/` o directorio de build excluido) y generar, solo si aporta valor, un índice público distinto con URLs finales y etiquetas legibles por prensa.

### Aceptación

- el pipeline sigue pudiendo generar el ZIP;
- el manifiesto operativo no forma parte del output web;
- los JSON públicos de autor/libros siguen disponibles.

---

## AIII-07 — P1 — `llms-full.txt` mezcla autoridad factual con decisiones de implementación

### Evidencia

`llms-full.txt` explica públicamente que:

- se decidió mantener una redacción editorial concreta antes de la fecha de publicación;
- no existe transición automática basada en reloj del cliente/runner;
- la disponibilidad comercial se gobierna mediante otro contrato.

La separación conceptual publicación/retailer es correcta. Lo que sobra en una fuente pública es el relato de **cómo está implementado el sistema** y por qué se tomó una decisión interna.

### Problema

La página `/ai/` presenta `llms-full.txt` como contexto ampliado de hechos y rutas de comprobación. Incluir proceso interno diluye la señal que se pretende hacer reutilizable por sistemas automáticos.

### Cambio propuesto

Mantener en `llms-full.txt` únicamente la formulación pública:

- fecha/estado editorial autorizado;
- ausencia de URL comercial verificada;
- no inferir retailer u oferta.

Mover el razonamiento y la mecánica de transición a documentación interna.

### Aceptación

`llms-full.txt` se puede leer como una ficha de autoridad, no como un runbook.

---

## AIII-08 — P1 — El asistente duplica hechos editoriales mutables a mano

### Evidencia

`assets/assistant-local-knowledge.mjs` contiene respuestas literales como:

- fecha de publicación de Manecillas;
- editorial;
- descripciones de las obras;
- inventario de Obras.

`editorial-facts.json` ya es la fuente central para hechos mutables, pero estas respuestas locales son código mantenido manualmente.

La fecha coincide ahora. El hallazgo no es una inconsistencia presente, sino un **camino de drift** que se vuelve especialmente relevante el día de un cambio editorial/comercial.

### Cambio propuesto

Una de estas dos estrategias:

**Preferida:** generar un pequeño módulo público seguro durante build a partir de una proyección autorizada de `editorial-facts.json` y hacer que `assistant-local-knowledge.mjs` componga sus respuestas desde ese módulo.

**Mínimo aceptable:** ampliar `check-assistant-contract.py` / `check-editorial-facts.py` para comprobar cada literal mutable (fecha, editorial, ISBN, páginas, estado comercial) contra la fuente canónica.

### Aceptación

Modificar el hecho canónico en un fixture provoca o bien regeneración automática del asistente o un fallo de CI por drift.

---

## AIII-09 — P2 — `/ai/` puede mostrar una fecha de revisión factual obsoleta

### Evidencia

`/ai/index.html` publica:

`Revisión factual: 22 de agosto de 2026`

`editorial-facts.json` mantiene su propia `meta.lastReviewed`.

Actualmente coinciden. La preocupación es que la primera es HTML literal y no se ha identificado un contrato que obligue a mantenerla sincronizada.

### Cambio propuesto

- generar el sello desde la fuente canónica; o
- añadir un assertion explícito en `test-machine-authority.py`.

### Aceptación

Cambiar `meta.lastReviewed` sin actualizar `/ai/` debe romper CI.

---

## AIII-10 — P1 — Falta una frontera de esquema entre contrato interno y proyección pública

Los hallazgos AIII-05, 06, 07 y 08 tienen la misma causa: el repositorio dispone de una fuente central rica, pero no de una **proyección pública tipada y mínima**.

### Arquitectura propuesta

```text
editorial-facts.json             # build-time, rico, puede contener incidentes/rationale
        │
        ├── validadores internos
        │
        └── public editorial projection
                ├── press-kit/*.json
                ├── llms.txt / llms-full.txt
                ├── /ai/
                ├── JSON-LD
                └── assistant facts module
```

La proyección pública debe permitir solo campos autorizados. Campos internos como incidentes, paths fuente, razones de implementación, comandos y gates de release no deben existir en el schema público.

### Aceptación

Un campo interno nuevo añadido a `editorial-facts.json` no aparece en ninguna salida pública salvo que el schema/proyector lo autorice expresamente.

---

## 3. Falsos positivos descartados durante la auditoría

Esta sección es deliberada: evita que la siguiente persona repita comprobaciones ya resueltas.

### ISBN de Manecillas

**Correcto en `main`:** `979-8-90514-935-1`.

Se contrastó `editorial-facts.json`, `/ai/`, ficha y press-kit. No hay discrepancia actual.

### Redacción «publicada el 3 de septiembre de 2026» antes del 3/09

**No se registra como bug.** Es una decisión editorial explícita del contrato actual y está testeada. Puede reconsiderarse editorialmente, pero esta auditoría no la trata como error técnico.

### Compra de Manecillas antes del lanzamiento

El enlace/preestado comercial se gobierna separadamente de la fecha de publicación. No se marca como bug el placeholder prelaunch ya acordado.

### Crawlers de IA

`robots.txt` ya contempla OAI-SearchBot, ChatGPT-User, GPTBot, Claude y Perplexity. No se recomienda otra modificación genérica de robots.

### PWA / API

`service-worker.js` excluye explícitamente `/api/*` de su caché y usa network-first para páginas/código mutable. No se ha encontrado aquí un problema nuevo que justifique reabrir la PWA.

### Guía imprimible de Samuel

Una copia indexada externamente mostraba datos antiguos, pero el `main` auditado ya muestra publicación 2025 y público «lectores juveniles y adultos». No se incorpora como defecto del código actual.

---

## 4. Plan de implementación recomendado

### PR de implementación A — cerrar superficie pública (P0)

Archivos:

- `scripts/build-public-dist.py`
- `.assetsignore` generado
- tests del builder
- `scripts/release-readiness.py`

Cambios:

1. excluir `docs/`, `qa/`, `lab/`, `migrations/`;
2. excluir Worker/config del asistente;
3. excluir package/Lighthouse de tooling;
4. añadir forbidden classes + excepciones documentadas;
5. construir e inspeccionar output final en CI.

### PR de implementación B — separar público/interno en machine-readable

Archivos principales:

- `editorial-facts.json`
- nuevo generador/proyector;
- `press-kit/*.json`
- `press-kit/package-manifest.json` (mover/excluir);
- `llms.txt`
- `llms-full.txt`
- `ai/index.html`
- tests de machine authority.

### PR de implementación C — bind del asistente a hechos canónicos

Archivos:

- `assets/assistant-local-knowledge.mjs`
- módulo factual generado o validator;
- `scripts/check-assistant-contract.py`
- tests/QA correspondientes.

### Orden

A → B → C.

Cerrar primero la superficie de publicación evita que los propios documentos y herramientas de implementación de B/C se conviertan en nuevos artefactos públicos.

---

## 5. Gate nuevo obligatorio: `public-artifact-contract`

Debe ejecutarse sobre el output construido.

### Debe fallar si encuentra

- `docs/**`
- `qa/**`
- `lab/**`
- `migrations/**`
- `scripts/**`
- `tests/**`
- `data/**`
- `wrangler*.jsonc`
- `cloudflare-worker-*.js`
- `package.json`
- `package-lock.json`
- `lighthouserc*.json`
- `*.sql`
- fuentes/editorial facts internos;
- cualquier ruta `status != public` del content registry.

### Excepciones

Toda excepción debe tener una razón explícita de runtime/licencia/verificación. No basta con «estaba en el repo».

### Además

Generar un `dist-manifest` con categoría por artefacto:

- `page`
- `runtime-asset`
- `machine-readable`
- `verification`
- `license`
- `explicit-exception`

No debe existir la categoría implícita «other» en una release.

---

## 6. Gate nuevo: `public-machine-schema`

Validar `press-kit/*.json`, `llms*.txt`, `/ai/` y el módulo factual del asistente.

### Prohibiciones recomendadas en salida pública

- nombres de variables internas como `knownEditorialIncident`;
- paths de fuente/build;
- instrucciones de pipeline;
- comandos de release;
- identificadores internos de incidentes;
- razonamientos sobre runner/cliente/CI cuando no sean un hecho editorial útil al público.

No implementar solo un grep de palabras: el mecanismo principal debe ser schema/proyección. El lint textual es una segunda defensa.

---

## 7. Matriz de ficheros: público vs interno

| Recurso | Clasificación correcta | Acción |
|---|---|---|
| `index.html`, páginas y rutas públicas | Público | Mantener |
| `assets/*` usados por runtime | Público | Mantener |
| `manifest.json`, `service-worker.js`, `offline.html` | Público runtime | Mantener |
| `robots.txt`, `sitemap.xml`, `llms*.txt` | Público machine-readable | Mantener, depurar contenido |
| `press-kit/david-porto-diaz.json` | Público editorial | Mantener |
| `press-kit/las-manecillas-del-recuerdo.json` | Público editorial | Sanitizar/proyectar |
| `press-kit/samuel-entre-mundos.json` | Público editorial | Mantener bajo mismo schema |
| `press-kit/package-manifest.json` | Build interno | Mover/excluir |
| `editorial-facts.json` | Build interno | Ya excluido; mantener |
| `docs/**` | Interno | Excluir |
| `qa/**` | Interno | Excluir |
| `lab/**` | Interno | Excluir |
| `migrations/**` | Infraestructura | Excluir |
| `cloudflare-worker-assistant.js` | Infraestructura | Excluir del sitio estático |
| `wrangler.assistant*.jsonc` | Infraestructura | Excluir |
| `package*.json` | Tooling | Excluir |
| `lighthouserc*.json` | QA | Excluir |
| `THIRD_PARTY_NOTICE_SILABAJS.md` | Licencia | Revisar obligación; no borrar automáticamente |

---

## 8. Definition of Done

Esta auditoría se considera implementada cuando:

1. `docs/`, `qa/`, `lab/` y `migrations/` no llegan al output público.
2. Ningún `wrangler.assistant*.jsonc` ni Worker fuente del asistente se sirve como asset estático.
3. `package*.json` y configuraciones Lighthouse no forman parte del dist.
4. El gate inspecciona el output real y detecta clases nuevas de artefactos internos.
5. `.assetsignore` y el builder siguen compartiendo una única política y CI comprueba paridad.
6. El press-kit público no contiene nombres de incidentes ni instrucciones de pipeline.
7. `package-manifest.json` deja de ser un recurso público.
8. `llms-full.txt` contiene hechos/contexto editorial, no implementación interna.
9. Los hechos mutables del asistente derivan de la fuente canónica o están contract-tested contra ella.
10. La fecha «Revisión factual» de `/ai/` está generada o validada contra `meta.lastReviewed`.
11. El ISBN de Manecillas sigue siendo `979-8-90514-935-1` en todas las superficies.
12. Los gates ya existentes —release readiness, accesibilidad, Lighthouse, cross-engine, reflow, navegación, enlaces/activos, structured data, machine authority, PWA y asistente— continúan verdes.
13. No se modifica la política editorial intencionada de prepublicación ni el placeholder comercial sin decisión explícita.
14. No se despliega ni se mergea automáticamente como consecuencia de esta auditoría.

---

## 9. Conclusión

Las dos primeras capas de trabajo han fortalecido diseño, arquitectura, findability y QA. El hueco que queda aquí es más de ingeniería de publicación: **el repositorio distingue bien bastantes fuentes internas, pero el artefacto público todavía no tiene una frontera suficientemente estricta**.

La mejora de mayor retorno consiste en convertir «lo que no hemos excluido» en «lo que hemos clasificado como publicable», sin romper el runtime existente. La estrategia propuesta mantiene la denylist actual para compatibilidad, añade clases prohibidas y exige una inspección del output final. Después, una proyección pública del contrato editorial evita que prensa, `llms`, `/ai/` y asistente hereden detalles de implementación.

Esta PR deja el trabajo especificado para implementación directa, con prioridades, archivos, arquitectura, pruebas y criterios de aceptación. No incluye cambios funcionales para no mezclar diagnóstico y corrección antes de revisar el diff técnico correspondiente.
