# Pendiente K — Auditoría de `pendiente funcionalidad gpt.txt`, líneas 401–600

Fecha de auditoría: 2026-08-23  
Rama base auditada: `implementacion-web-2026`  
HEAD auditado: `4694799edc6d9c9e729b896cadda1eef9726d083`

> Esta PR recoge únicamente deuda real encontrada al contrastar las líneas 401–600 del fichero de pendientes con el repositorio actual. No debe reabrir trabajo ya cubierto por otras PR ni convertir gates editoriales/externos en bugs de código.

## 1. Qué NO hay que duplicar

### Ya cubierto por otras PR

- **Rate limiting / honeypot / DOI del Worker de newsletter:** PR #55.
- **Runtime global / popup / imágenes responsive / funnel específico de Manecillas:** PR #61.
- **Taxonomía analítica sitewide / eventos GoatCounter:** PR #63.
- **Operativa de Search Console cuando no exista API/conector utilizable:** PR #64.
- **CSP del shell público:** PR #62.

### Gates o trabajo editorial, no bugs de esta PR

- URL comercial y retailers reales de `Las manecillas del recuerdo`.
- Clearance/typo de cubierta y material de prensa.
- Revisión jurídica de la base legal de Privacidad.
- Artículos futuros de Manecillas: memoria familiar, abuelos/nietos, objetos heredados, proceso y club/guía.
- Decisión editorial definitiva sobre el artículo 2025–2026 actualmente en cuarentena.
- Cadencia continua de publicaciones.
- Feedback «¿te resultó útil?», XSL para RSS e IndexNow: mejoras opcionales, no deuda obligatoria de esta ronda.

### Afirmaciones del TXT que ya están superadas

La línea 409 afirma que `/recomendaciones/` vuelve a enlazar el artículo 2025–2026 en cuarentena. En el HEAD auditado ya no ocurre: el hub actual solo presenta las dos listas de Recomendaciones y conexiones al Cuaderno. El propio commit base registra que ese enlace residual fue retirado. **No reabrirlo.**

---

# 2. DEUDA NUEVA REAL

## K.1 — Recomendaciones afirma evidencia verificada sin publicar el estado ni la trazabilidad exigidos

### Evidencia actual

Las dos guías públicas contienen afirmaciones como:

- «Todos tienen edición en español verificada»;
- «Edición en español verificada»;
- ISBN concretos;
- editorial/formato en algunos casos;
- clasificación editorial de la obra dentro de la lista.

Sin embargo, no existe en la superficie pública ni en un contrato canónico comprobable el estado pedido por la documentación:

- `Leído`;
- `Consultado`;
- `Verificado`;
- `Pendiente`.

Tampoco existe una fuente primaria visible por obra que permita distinguir:

1. la evidencia bibliográfica de la edición concreta;
2. la fuente utilizada para sinopsis/hechos de la obra;
3. el juicio editorial propio de David sobre por qué encaja en la lista.

El enlace de compra de Amazon —aunque identifique una edición— no debe tratarse automáticamente como fuente primaria suficiente para todos los hechos de una ficha.

El hub sí contiene transparencia de afiliación y de conflicto de interés cuando aparece `Samuel entre mundos`; eso debe conservarse.

### Objetivo

Convertir «verificado» en una afirmación auditable, sin inventar qué obras ha leído David ni transformar una selección editorial en una bibliografía académica innecesaria.

### Implementación requerida

1. Definir una autoridad de evidencia para las obras incluidas en Recomendaciones. Puede ser un JSON/estructura equivalente, pero debe ser machine-checkable y tener una única fuente de verdad.
2. Cada obra debe declarar como mínimo:
   - identificador estable —ISBN cuando proceda—;
   - `evidenceStatus`: `leido | consultado | verificado | pendiente`;
   - fecha de última verificación cuando se afirme una edición concreta;
   - fuente bibliográfica/primaria de la edición;
   - fuente principal para hechos objetivos de la obra cuando sea distinta;
   - nota editorial separada para la clasificación/encaje, que es juicio de la lista y no un hecho que la fuente «demuestre» por sí sola.
3. **No inferir `Leído`.** Si el repositorio no contiene evidencia suficiente para saber que David leyó una obra, usar un estado no más fuerte que el que pueda demostrarse o dejarlo `Pendiente` para decisión humana.
4. Mostrar el estado de evidencia de forma comprensible en cada entrada, sin convertir cada card en una ficha técnica pesada.
5. Hacer visible al menos una fuente primaria relevante por obra o un acceso claro a su trazabilidad.
6. Mantener por separado el enlace comercial/afiliado; no presentar «Comprar en Amazon» como si fuese la fuente editorial de la clasificación.
7. Añadir al hub una política de Recomendaciones que explique:
   - qué significan los cuatro estados;
   - cómo se verifican ediciones/ISBN;
   - qué parte es juicio editorial;
   - afiliación y obra propia;
   - cómo solicitar una corrección.
8. No reutilizar sin contexto la política de `/metodologia-editorial/`, porque esa política pertenece al directorio de editoriales. Se pueden compartir principios, pero Recomendaciones necesita su contrato propio.

### Tests / gate

Crear un checker determinista para las dos guías actuales y cualquier guía futura de la familia Recomendaciones:

- toda obra listada tiene entrada de evidencia;
- `evidenceStatus` pertenece al enum permitido;
- una afirmación «verificada» no existe sin fuente y fecha de verificación;
- ISBN visible/JSON-LD coincide con la autoridad de evidencia cuando exista;
- enlaces afiliados siguen declarados como tales;
- la obra propia sigue identificada;
- no se permite que el checker se ponga verde degradando silenciosamente todos los estados a `verificado`.

### Criterios de aceptación

- [ ] las 16 entradas actuales de las dos listas tienen estado explícito;
- [ ] ninguna entrada recibe `Leído` por inferencia;
- [ ] existe fuente trazable para cada edición que se publique como verificada;
- [ ] el usuario puede distinguir fuente, compra y juicio editorial;
- [ ] existe política pública de correcciones para Recomendaciones;
- [ ] test automático falla al eliminar la fuente de una entrada verificada;
- [ ] test automático falla si HTML/JSON-LD y la autoridad de evidencia discrepan en ISBN/edición.

---

## K.2 — `FAQPage` legacy sigue presente en las dos guías de Recomendaciones

### Evidencia actual

El HEAD auditado mantiene `FAQPage` JSON-LD en:

- `/recomendaciones/portal-fantasy-espanol/`;
- `/recomendaciones/magia-con-coste/`.

La documentación auditada ya había decidido dejar de dedicar mantenimiento a ese schema en estas superficies. El contenido FAQ visible puede seguir siendo útil para humanos; el problema es mantener una capa de rich-result/schema que ya no forma parte del contrato deseado.

### Implementación requerida

1. Retirar únicamente el nodo `FAQPage` de JSON-LD en ambas guías.
2. Conservar las preguntas/respuestas visibles si siguen siendo editorialmente útiles.
3. No retirar `WebPage`, `ItemList`, `Book`, breadcrumbs ni otras entidades válidas solo por simplificar.
4. Añadir un test que impida reintroducir `FAQPage` dentro de la familia `/recomendaciones/` salvo una decisión futura explícita.

### Criterios de aceptación

- [ ] cero `FAQPage` JSON-LD en las dos rutas de Recomendaciones;
- [ ] FAQ visible preservada;
- [ ] ItemList/Book/breadcrumb permanecen válidos;
- [ ] schema parsea correctamente después de la limpieza;
- [ ] test de regresión en CI.

---

## K.3 — La compatibilidad real no tiene gate cross-browser/Baseline; el gate sitewide actual es Chromium-only

### Evidencia actual

`qa/sitewide-reflow-browser.mjs` importa y lanza exclusivamente `chromium` de Playwright. Además usa CDP para parte del stress de estilos, por lo que ese test profundo no puede considerarse evidencia de Firefox/WebKit.

El repo tiene Lighthouse, Pa11y, reflow, múltiples browser QA y una batería mucho más fuerte que cuando se escribieron los documentos, pero no existe un contrato explícito que pruebe la experiencia crítica en más de un motor ni una política formal para features recientes.

Lighthouse **no sustituye** un test de compatibilidad cross-engine.

### Objetivo

Adoptar una política práctica alineada con «Baseline / ampliamente disponible» sin convertir el proyecto en una promesa irreal de soportar cualquier navegador histórico.

### Implementación requerida

1. Documentar el contrato de compatibilidad:
   - funcionalidades esenciales: APIs/features ampliamente disponibles o con fallback;
   - features recientes/experimentales: solo como progressive enhancement;
   - ausencia de una feature no puede bloquear navegación, lectura, formularios principales ni acceso a contenido.
2. Mantener el reflow profundo actual en Chromium; **no degradarlo** para hacerlo artificialmente portable.
3. Añadir un smoke cross-engine independiente con Playwright:
   - Chromium;
   - Firefox;
   - WebKit.
4. Cubrir un conjunto representativo de rutas críticas, no las ~todas las rutas × todos los motores si el coste de CI no aporta valor. Como mínimo:
   - `/`;
   - `/las-manecillas-del-recuerdo/`;
   - `/las-manecillas-del-recuerdo/fragmentos/`;
   - `/libros/samuel-entre-mundos/`;
   - `/cuaderno/`;
   - `/recomendaciones/` y una guía;
   - `/herramientas/` y una herramienta representativa;
   - `/asistente/` en modo local/inactivo seguro.
5. En cada motor verificar como mínimo:
   - HTTP/DOM cargado;
   - shell/navegación utilizable;
   - Explorar abre/cierra y gestiona foco;
   - enlaces críticos accesibles;
   - ausencia de excepciones JS no esperadas;
   - ausencia de overflow horizontal crítico en viewport móvil representativo;
   - formularios/controles esenciales no quedan inutilizados;
   - reduced-motion no provoca una dependencia funcional de la animación.
6. Auditar features modernas que ya existen —por ejemplo `scheduler.postTask`, speculation rules u otras— para asegurar feature detection o degradación inocua.
7. Si se introduce una herramienta automatizada de Baseline, usarla como señal adicional, no como sustituto del navegador real y no bloquear por APIs que sean deliberadamente progressive enhancement.

### Criterios de aceptación

- [ ] política de compatibilidad documentada;
- [ ] smoke crítico verde en Chromium + Firefox + WebKit;
- [ ] el gate se ejecuta en CI cuando cambian shell/runtime/CSS críticos;
- [ ] una regresión deliberada/fixture demuestra que el gate puede ponerse rojo;
- [ ] no se elimina el reflow Chromium/CDP existente;
- [ ] features no universales tienen detección/fallback documentado.

---

## K.4 — El artículo `noindex` del sistema de magia de Noveris sigue publicando como canon una versión expresamente en cuarentena

### Evidencia actual

Ruta:

`/cuaderno/sistema-de-magia-noveris/`

La parte técnica de cuarentena sí existe:

- `meta robots` = `noindex, follow`;
- la auditoría previa indica que no está en sitemap.

Pero el contenido sigue afirmando como hechos concretos una de las versiones incompatibles del canon. El JSON-LD `FAQPage`, por ejemplo, afirma que:

- cada canalización consume historia residual de forma irreversible;
- el coste es pérdida de memoria/historia de los objetos;
- no es energía física del canalizador.

El propio artículo contiene además wording que habla de «coste físico». Mientras esa contradicción no se resuelva con autoridad editorial, la URL no debe escoger una versión como verdad solo porque esté `noindex`.

### Implementación requerida

1. Preservar la URL y el `noindex` mientras el canon siga sin resolver.
2. Sustituir el contenido factual conflictivo por un estado editorial neutral, por ejemplo una nota clara de que el artículo está en revisión porque existen versiones incompatibles del material de trabajo.
3. No inventar una nueva explicación intermedia del sistema mágico.
4. Neutralizar también las superficies que podrían seguir difundiendo la versión conflictiva aunque la página sea `noindex`:
   - `<title>`/description si contienen claims concretos;
   - OG/Twitter copy;
   - Article description/keywords si hacen afirmaciones no autorizadas;
   - `FAQPage` factual;
   - cualquier bloque visible con la mecánica discutida.
5. Retirar `FAQPage` de esta URL mientras esté en cuarentena.
6. Mantener canonical propio y preservar la URL para recuperación futura.
7. Confirmar que no reaparece en sitemap ni en hubs/navegación prominente mientras siga en revisión.
8. Cuando el autor valide el canon, la recuperación debe hacerse en una PR separada con fuente/autorización explícita y revisión cross-surface.

### Criterios de aceptación

- [ ] la ruta sigue accesible y `noindex`;
- [ ] no publica como hecho ninguna de las mecánicas incompatibles;
- [ ] no queda `FAQPage` factual en la URL;
- [ ] title/meta/social/schema no contradicen el estado «en revisión»;
- [ ] no aparece en sitemap;
- [ ] un test busca y bloquea las afirmaciones conflictivas conocidas mientras la página esté en cuarentena;
- [ ] no se modifica `/universo/noveris/` dentro de esta tarea salvo que una evidencia posterior demuestre una contradicción del mismo canon; esta auditoría 401–600 se refiere específicamente al artículo del Cuaderno.

---

# 3. Operación externa detectada en esta ronda — NO mezclar con K.1–K.4

## Search Console

Las Platform Properties / inspecciones reales siguen siendo operación externa. Aplicar PR #64 solo si no existe API/conector autorizado que permita la acción concreta.

## Metricool

Se consultó el conector/API disponible para la marca configurada en el intervalo 27/08/2026–04/09/2026. En la consulta realizada no aparecen publicaciones programadas en ese intervalo.

Por tanto, las afirmaciones históricas de las líneas 495–497 —que todavía seguían programadas piezas evergreen concretas el 3/09 y un Google Business Profile del 27/08— **no deben darse por vigentes sin volver a verlas en el planner actual**.

A la vez, cero publicaciones devueltas tampoco demuestra que la campaña Manecillas-first esté preparada: es una tarea operativa de contenido/calendario, no una carencia del repositorio. Si se decide preparar el lanzamiento, hacerlo mediante el conector/API de Metricool, no mediante Edge mientras la API cubra la operación.

No modificar el calendario desde esta PR.

---

# 4. Orden recomendado de desarrollo

1. **K.4 — cuarentena Noveris**, porque actualmente existe contenido factual contradictorio accesible aunque sea `noindex`.
2. **K.1 — evidencia de Recomendaciones**, porque afecta credibilidad de afirmaciones públicas indexables.
3. **K.2 — FAQPage legacy**, cambio pequeño que puede hacerse junto a K.1 sin tocar el FAQ visible.
4. **K.3 — cross-browser/Baseline**, independiente y adecuado para cerrar QA antes de release.

Si K.3 genera un diff demasiado grande o CI muy costoso, puede separarse a una PR hija; esta PR debe conservar la trazabilidad y enlazarla.

# 5. QA y Definition of Done

Antes de declarar esta PR resuelta:

- rebasar sobre un HEAD fresco de `implementacion-web-2026` y comprobar qué PR previas ya entraron;
- no duplicar ni revertir #55, #61, #62, #63 o #64;
- no debilitar asserts existentes;
- ejecutar validadores de schema/SEO/content indexes;
- ejecutar Recommendations browser QA;
- ejecutar Pa11y/Lighthouse/reflow donde el cambio lo justifique;
- ejecutar el nuevo smoke cross-engine;
- revisar visualmente Recomendaciones después de añadir estados/fuentes para evitar sobrecargar las cards;
- confirmar que la cuarentena de Noveris no filtra claims conflictivos en metadata/schema;
- revisar el diff final completo.

**No tocar `main`. No desplegar producción. No auto-merge.**
