# AF — Asistente · búsqueda local Pagefind

Hallazgo durante el cruce final de `DISEÑO Y DEMÁS`, especialmente docs 38 y 40, contra `implementacion-web-2026`.

Base auditada: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

## Estado real

El asistente actual YA contiene degradación correcta:

- `assets/assistant.js` define `pagefindFallback(query)`;
- primero intenta `import('/pagefind/pagefind.js')`;
- si Pagefind no existe/falla, usa `data/assistant-source-registry` + `rankLocalSources()`;
- por tanto el asistente no queda roto sin Pagefind.

Pero la capa Pagefind del contrato canónico NO se materializa hoy:

- no existe `/pagefind/` en la rama;
- no existe `package.json` en la base actual (la autoridad de dependencias Node está siendo creada por #65);
- no se encontró builder/script Pagefind bajo `scripts/`;
- no se encontró workflow que instale/genere el índice;
- `assistant-hardening-qa.yml` prueba registry/core/worker/browser pero no genera Pagefind;
- `build-public-dist.py` copia lo trackeado, no construye un índice Pagefind.

Resultado actual: el `import('/pagefind/pagefind.js')` cae al fallback local de forma sistemática salvo que un pipeline externo no versionado lo genere, del que no hay evidencia en el repo auditado.

## Por qué importa

Doc 40 define una arquitectura híbrida donde la búsqueda local gratuita es una capa de primer orden y Pagefind es el motor cliente previsto. El fallback local actual es valioso y debe mantenerse, pero no sustituye silenciosamente la capacidad diseñada si queremos declarar el contrato 40 implementado.

Esto es una deuda funcional/findability, NO una nueva PR de estética.

## Owner

Materializar una búsqueda local Pagefind reproducible para contenido público elegible, conservando el fallback actual.

### AF.1 — Fuente de verdad

El corpus indexable debe derivar de la autoridad viva:

- `data/content-registry.json`;
- solo entries públicas/elegibles;
- respetar `searchIndex:false`, gated/noindex y publication gate;
- no indexar datos privados, drafts, herramientas internas, solicitudes beta, scripts/data administrativos ni contenido excluido del artefacto público.

No crear una segunda lista manual de rutas Pagefind.

### AF.2 — Build reproducible

Implementar una única vía reproducible que genere `/pagefind/` desde el artefacto público/corpus elegible.

Requisitos:

- integrarse con la autoridad de dependencias Node de **#65** después de su integración/rebase; no crear otro `package.json` o lockfile paralelo;
- versión Pagefind fijada/reproducible;
- build determinista en la medida compatible con Pagefind;
- no commitear binarios/artefactos efímeros sin decidir explícitamente si el repo sirve source o build output;
- si `/pagefind/` se genera en CI/deploy, documentar exactamente dónde y garantizar que staging/producción lo sirven;
- si se versiona el output, añadir checker de stale/parity.

### AF.3 — Integración con Asistente

Mantener el orden de degradación:

1. resolución determinista/intent cuando aplique;
2. Pagefind local;
3. ranking local/registry como fallback robusto;
4. IA solo según contrato actual y acción/condición autorizada.

No hacer que una caída de Pagefind rompa el asistente.

Resultados locales deben usar URLs internas seguras y títulos/fragmentos procedentes del contenido público, no del modelo.

### AF.4 — UX/findability

No crear automáticamente una segunda caja de búsqueda global en header.

El doc 40 integra la búsqueda dentro de `/asistente/`/Explorar. Cualquier launcher adicional en shell queda condicionado a pruebas de utilidad y a #68; no se introduce por esta PR.

### AF.5 — QA

Añadir pruebas que demuestren:

- el índice se genera;
- una página pública indexable aparece;
- una entry `searchIndex:false` no aparece;
- contenido gated/noindex/publication-excluded no aparece;
- consulta simple devuelve destino real;
- si se elimina/rompe `/pagefind/`, el ranking local sigue funcionando;
- no hay requests externos para búsqueda local;
- teclado y resultados siguen siendo utilizables;
- staging sirve `/pagefind/pagefind.js` y recursos necesarios cuando la integración llegue a ese gate.

## Coordinación

- **#65**: autoridad package.json/package-lock/Node QA; AF debe rebase después, no competir.
- **#67**: microcopy del Asistente; AF no decide wording.
- **#68**: navegación/findability global; AF no añade territorio/menu/launcher sin coordinación.
- **#79**: publication gate; el índice no puede re-publicar contenido gated.
- **#58**: smoke de staging debe comprobar Pagefind una vez integrado.
- **#62**: CSP final debe admitir únicamente los recursos locales necesarios; Pagefind no justifica orígenes externos.
- **#89/#88**: diseño final del Asistente/herramientas consume el comportamiento, no lo reimplementa.

## No hacer

- no eliminar el fallback local actual;
- no indexar el repo completo;
- no indexar `data/` o fuentes privadas por comodidad;
- no crear una taxonomía de búsqueda paralela a content-registry;
- no introducir búsqueda externa/Google custom search;
- no usar Pagefind para justificar un segundo overlay/menu;
- no absorber #65 creando otra autoridad Node.

## Definition of Done

- Pagefind deja de ser un import que falla sistemáticamente;
- build/index source está documentado y reproducible;
- elegibilidad deriva de authorities actuales;
- exclusiones de privacidad/publicación tienen regresiones;
- fallback local sigue probado;
- staging evidencia recursos Pagefind 200 + búsqueda real;
- no se altera `main`, no deploy de producción y no auto-merge.

PR DRAFT / owner técnico. No es bloque de diseño visual.