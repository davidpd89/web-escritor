# Pendiente R — Auditoría Claude, líneas 201–400

Fecha de auditoría: 2026-08-23  
Fuente auditada: `claude pending.txt`, **exactamente líneas 201–400**  
Base contrastada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Estado: **DRAFT / no merge / no producción**

## Regla de esta ronda

El TXT es un informe histórico de pendientes, no una autoridad superior al estado vivo del repositorio. Cada afirmación se ha contrastado contra:

1. HEAD real de `implementacion-web-2026`;
2. todas las PR abiertas contra esa rama;
3. código, datos y workflows actuales cuando el hallazgo era comprobable;
4. el material de especificación de Drive cuando el propio TXT remitía a una propuesta aún no integrada.

No se abre trabajo nuevo si otra PR ya posee la deuda.

---

## Resumen ejecutivo

Este tramo deja **una sola deuda nueva independiente**:

### R.1 — Hub de proceso de «Las manecillas del recuerdo» sin estado ejecutable

La ruta prevista:

`/las-manecillas-del-recuerdo/como-se-escribio/`

no existe en el repositorio, no figura en `data/content-registry.json`, no tiene builder/checker y ninguna PR abierta la posee.

Sin embargo, **no debe publicarse todavía como una página indexable vacía**. La especificación histórica conservada en Drive establece un gate editorial claro: activar el hub únicamente cuando existan al menos cuatro notas reales del Cuaderno que puedan sostenerlo.

Por tanto, esta deuda no significa «crear ya una landing con enlaces ficticios». Significa convertir una propuesta olvidada en un contrato explícito, medible y seguro de activación.

---

# R.1 — Contrato del hub «Cómo se escribió»

## Problema actual

El proyecto ya había decidido que el lanzamiento de Manecillas debía tener una capa de proceso editorial que conectase la ficha del libro con artículos reales del Cuaderno. La propuesta llegó a disponer de:

- una maqueta HTML de ejemplo;
- un documento de integración;
- una ruta futura definida.

Nada de eso pasó al repositorio vivo.

Resultado actual:

- no existe `/las-manecillas-del-recuerdo/como-se-escribio/`;
- no existe una entrada equivalente en `data/content-registry.json`;
- no existe un estado `publish:false`, `noindex` o contrato equivalente que haga visible que la idea está deliberadamente gated;
- no existe QA que impida publicar un hub vacío o con enlaces a artículos inexistentes;
- la ficha de Manecillas no tiene un destino estable «Cómo se escribió la novela» que pueda activarse cuando el contenido exista.

El riesgo no es solo que falte una página. El riesgo es que la decisión quede indefinidamente en tierra de nadie: ni construida ni descartada ni gated de forma reproducible.

## Estado correcto ahora

**GATED — contenido insuficiente.**

No crear una página pública/indexable solo para “cerrar” el pendiente.

El gate mínimo para activarla es:

1. disponer de **al menos cuatro notas de proceso reales** publicadas en `/cuaderno/`;
2. esas cuatro URLs deben ser indexables, canónicas, estar en sitemap y enlazadas desde el Cuaderno;
3. el hub debe enlazarlas con `<a href>` HTML real y texto descriptivo;
4. el hub debe recibir un enlace contextual desde la ficha de Manecillas con copy del tipo «Cómo se escribió la novela», no un CTA ambiguo «Más»;
5. solo al cumplirse lo anterior se permite `index,follow` y sitemap;
6. `dateModified` debe corresponder a una modificación real del hub, no a una fecha de build inventada.

## Implementación propuesta

La implementación final debe integrarse en las autoridades actuales del proyecto, no recuperar sin más el HTML de ejemplo de agosto.

### 1. Fuente de datos / estado

Crear un contrato pequeño y explícito para el hub. Puede resolverse de una de estas dos maneras, eligiendo la que mejor encaje con la arquitectura existente:

- entrada staged en el registro de contenidos; o
- fichero de datos específico consumido por un builder/checker.

Debe poder expresar al menos:

- `id` estable;
- URL canónica futura;
- `status` o `publish`;
- lista de piezas de proceso relacionadas por IDs estables del registry, no por HTML copiado;
- fecha real de modificación cuando sea publicable.

Mientras no se cumpla el umbral editorial, el estado debe impedir sitemap/indexación y no debe añadir navegación pública engañosa.

### 2. Construcción del hub

Cuando el gate se abra:

- usar shell V1 actual;
- reutilizar tokens/componentes actuales;
- generar tarjetas/enlaces desde datos o IDs del registry, evitando una segunda lista manual de URLs;
- no crear filtros ni taxonomías nuevas para cuatro o pocas piezas;
- no depender de JavaScript para que los enlaces sean rastreables;
- no duplicar artículos con intención editorial solapada solo para alcanzar el mínimo numérico.

### 3. Integración con la ficha de Manecillas

El enlace desde `/las-manecillas-del-recuerdo/` debe aparecer únicamente cuando el destino sea válido según el contrato de publicación.

No debe existir un enlace roto, un CTA deshabilitado permanente ni una tarjeta que prometa contenido aún inexistente.

### 4. Registry, sitemap y grafo interno

Cuando pase a público:

- añadirlo al `content-registry` con `parentId: work-manecillas` y la territorialidad de Obras;
- permitir que el generador vigente determine sitemap/indexación según el estado declarado;
- el checker de grafo interno debe detectar artículos sin enlace entrante y el hub sin enlace desde la obra;
- cualquier relación con las notas debe usar IDs/URLs canónicas ya existentes, no rutas inventadas.

### 5. QA mínimo

Añadir pruebas deterministas para estos casos:

- **gate cerrado:** menos de cuatro piezas válidas → el hub no puede quedar indexable ni entrar en sitemap;
- **enlace inexistente/no público:** una pieza referenciada no existe o está `noindex` → fallo de validación;
- **gate abierto:** cuatro o más piezas válidas → se puede generar/publicar;
- todos los enlaces de tarjeta son `<a href>` rastreables;
- el enlace contextual desde la ficha de Manecillas aparece solo cuando el hub está publicable;
- canonical, robots y `dateModified` son coherentes con el estado;
- no se introducen URLs/filtros de categoría innecesarios.

## Lo que esta PR NO autoriza

- No inventar cuatro artículos para desbloquear el gate.
- No publicar una landing vacía.
- No marcar `index,follow` antes de cumplir el contrato.
- No copiar literalmente la maqueta histórica si contradice el shell/diseño V1 actual.
- No añadir datos editoriales no verificados.
- No tocar `main` ni producción.

---

# Hallazgos del bloque que ya tienen owner

## Protocolo de correcciones editoriales — YA DETECTADO / #66 K.1

El tramo confirma que la antigua propuesta de correcciones públicas (`article-correction.template.md`, componente visual y validador) nunca llegó al repo.

No se abre una PR nueva porque #66 K.1 ya es propietario de evidencia/procedencia y política de correcciones. Se ha añadido a esa PR el contrato detallado para que la solución sea reutilizable en Recomendaciones/Cuaderno:

- ID, estado, URL, fecha de corrección, `significant_update`, `public_note` y fuente;
- nota pública accesible con «qué cambió / por qué / fuente»;
- coherencia con `dateModified` y fecha visible;
- validación de placeholders, URLs y fechas;
- tests de corrección sustancial/menor/fuente no publicable.

Coordinación necesaria con #57 D.1 para la fecha visible de artículos.

## `update-dates.yml` — YA DETECTADO / #54

El TXT vuelve a confirmar que `.github/workflows/update-dates.yml` contradice la autoridad única de `build-sitemap.py` y autoescribe sitemap desde un workflow paralelo.

Esto es exactamente #54. No duplicar.

## Popup / runtime global — YA DETECTADO / #61 H.1

La inyección de estilos del popup y el acoplamiento de responsabilidades globales en `script.js` pertenecen a #61 H.1.

## FAQ legacy — YA DETECTADO / #66 K.2

Cualquier residuo `FAQPage` que deba retirarse sigue siendo responsabilidad de #66 K.2.

---

# Hallazgos corregidos o no accionables

## `broken-links.yml` con fallo silencioso — SUPERADO

El informe dejaba pendiente comprobar si el workflow seguía tolerando enlaces rotos mediante `fail:false`.

El HEAD auditado usa:

- `fail: true`;
- `failIfEmpty: true`;
- reintentos y timeout;
- artefacto de informe.

No hay deuda nueva aquí.

## Backlog de artículos / calendario / reutilización social — OUT OF SCOPE o editorial

El TXT distingue correctamente estos elementos del trabajo de código. Además, publicación social/Metricool está explícitamente fuera del alcance del proyecto web.

No generar PR técnica para piezas que requieren redacción, fuentes o decisión editorial real.

## Guía de despliegue antigua — SUPERADA como autoridad

Las instrucciones antiguas de DOI/deploy no sustituyen el Worker actual, #55, #58 ni el protocolo de readiness vivo de #1/#74.

No recuperar runbooks históricos de forma literal.

---

# Matriz final 201–400

| Área | Clasificación | Owner / acción |
|---|---|---|
| Backlog editorial y calendario de artículos | OUT OF SCOPE / editorial | sin PR de código |
| Protocolo de correcciones públicas | YA DETECTADO | ampliar #66 K.1; coordinar #57 |
| `update-dates.yml` | YA DETECTADO | #54 |
| `broken-links.yml` / `fail:false` | SUPERADO | HEAD ya usa `fail:true` |
| Diseño/identidad histórica | SUPERADO / editorial | no restaurar specs antiguas |
| FAQ legacy | YA DETECTADO | #66 K.2 |
| Runtime/popup | YA DETECTADO | #61 H.1 |
| Guía deploy/DOI histórica | SUPERADA | #55 + #58 + #1/#74 |
| `/las-manecillas-del-recuerdo/como-se-escribio/` | **DEUDA NUEVA / GATED** | **R.1** |
| Search Console / Brevo / Cloudflare live | GATED / externo | operativa separada |
| ampliación de bio del autor | editorial | no código |

---

## Definition of Done de R.1

R.1 solo puede cerrarse de una de estas dos formas explícitas:

### A. Activación

- existen ≥4 notas reales y publicables;
- contrato/registry resuelve todas sus URLs;
- hub generado con shell V1 y enlaces rastreables;
- enlace contextual desde la ficha de Manecillas;
- robots/canonical/sitemap/dateModified correctos;
- QA de gate y grafo en verde.

### B. Aplazamiento formal

Si todavía no existen las cuatro piezas, debe quedar un estado gated reproducible y documentado, sin página pública vacía, de manera que el proyecto pueda distinguir «pendiente deliberadamente» de «olvidado».

---

Auditoría detenida exactamente en la línea **400** de `claude pending.txt`. No se han usado líneas 401+ para esta clasificación.
