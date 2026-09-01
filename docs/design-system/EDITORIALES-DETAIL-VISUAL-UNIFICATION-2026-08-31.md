# Editoriales · fichas verificadas individuales — contrato de unificación visual · 2026-08-31

## Trazabilidad

Continúa la cadena `DISEÑO -` después de la PR de Herramientas individuales.

La PR #272 (`DISEÑO - Editoriales · unificación visual del directorio verificado`) cerró únicamente `/editoriales/` como registro/directorio y protegió explícitamente el aislamiento frente a las fichas individuales. Esta intervención completa esas fichas sin reabrir el hub.

Mantener Draft y no mergear fuera de orden.

## Superficies

- `/editoriales/minotauro/`
- `/editoriales/nocturna-ediciones/`
- `/editoriales/duermevela-ediciones/`

Antes de producción, reconciliar sitemap, robots, canonical y estado factual de las tres fichas en el HEAD heredado.

## Objetivo

Convertir las fichas en **expedientes editoriales verificados** coherentes con el sistema azul/negro/dorado y con el directorio #272, sin convertirlas en landing pages promocionales ni en cards ampliadas.

La jerarquía debe ayudar a responder rápidamente:

1. qué editorial es;
2. si acepta manuscritos y en qué estado;
3. qué vías de envío existen;
4. qué géneros/condiciones están documentados;
5. cuándo se verificó;
6. qué fuente oficial sostiene cada dato;
7. qué cautelas o límites de evidencia existen.

## Principio editorial

La ficha no debe aparentar más certeza que la evidencia disponible. El diseño debe diferenciar visualmente estado, evidencia, fuente, fecha de verificación y recomendaciones prácticas sin transformar esos elementos en badges celebratorios o métricas de dashboard.

## Preservar estrictamente

Por editorial:

- nombre y descripción factual;
- estado real de recepción de manuscritos (`open`/`closed` o equivalente);
- existencia o ausencia de envío directo;
- géneros y condiciones verificadas;
- vías de contacto/envío;
- enlaces a fuente oficial;
- fecha de verificación;
- notas de cautela;
- canonical y robots;
- JSON-LD/schema existente;
- navegación por hash si existe;
- breadcrumbs/context nav;
- enlaces de vuelta al directorio;
- funcionamiento sin JavaScript.

No actualizar hechos durante esta PR visual salvo que se haga una verificación factual independiente, trazable y documentada. Un cambio factual no debe esconderse dentro de un cambio de CSS.

## Dirección visual

### Masthead / apertura

- continuidad con #272 mediante azul `#1d4f96`, azul profundo `#0d2c57`, dorado `#b8860b` y neutros;
- título claro y dominante, pero no hero publicitario;
- estado de verificación como metadato documental;
- Yellowtail, si se usa, solo en una apertura/acción selectiva y nunca en datos críticos.

### Estado de manuscritos

- distinguir `abierto`, `cerrado`, `sin envío directo` u otros estados con texto inequívoco además del color;
- no usar verde/rojo como única señal;
- no presentar `cerrado` como error ni `abierto` como promoción;
- evitar pills/badges excesivos: preferir ficha/ledger editorial.

### Evidencia y fuentes

- fuentes oficiales como bloque probatorio legible;
- fecha de verificación visible pero subordinada;
- cautelas con rail o superficie documental, no alertas agresivas salvo riesgo real;
- URLs largas deben romper correctamente en móvil/zoom.

### Estructura

- usar ledgers, reglas, rails y secciones abiertas;
- evitar card soup;
- lectura lineal en móvil;
- acciones claras y accesibles;
- separar hechos de orientación práctica.

## Ownership

Reutilizar la arquitectura y owners existentes de las fichas. Evitar contaminar el directorio `/editoriales/` o Convocatorias/Metodología. Si `assets/editoriales.css` contiene reglas compartidas, introducir scope explícito de detalle o una capa local única para las tres fichas, no una hoja por editorial.

## QA requerido

Crear contrato browser específico para las tres fichas y mantener las autoridades funcionales/profesionales existentes.

### Cobertura

- las 3 rutas, no solo una representante, porque el estado factual difiere;
- 1440, 1280, 1024, 768, seams reales, 390, 360, 320;
- zoom 200 %;
- text spacing WCAG;
- teclado/focus;
- no-JS;
- cero overflow;
- fuentes oficiales y enlaces seguros;
- long URLs/wrapping;
- carga/estabilidad tipográfica antes de snapshots.

### Contratos factuales mínimos

- identidad exacta de cada editorial;
- estado exacto visible;
- número/estructura de fuentes según el HTML heredado;
- fechas de verificación;
- CTAs/vías de envío sin inventar opciones;
- canonical/schema intactos.

### Aislamiento

Verificar expresamente que los tokens/reglas de detalle no se filtren a:

- `/editoriales/`;
- `/convocatorias-escritores/`;
- `/metodologia-editorial/`.

No relajar tests ni ocultar overflow.

## Revisión humana

Revisar las tres fichas en desktop y móvil, especialmente:

- que abierto/cerrado se entienda de un vistazo sin parecer un semáforo de app;
- jerarquía entre estado, instrucciones y fuente;
- densidad de información;
- URLs y acciones;
- ritmo vertical;
- coherencia con #272 sin convertir el detalle en copia del directorio.

Seguir `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md` antes del merge.

## Definition of Done

- las tres fichas unificadas;
- hechos y fuentes preservados;
- estados accesibles y no ambiguos;
- directorio #272 aislado;
- Convocatorias/Metodología aisladas;
- responsive/zoom/text-spacing/teclado/no-JS verdes;
- evidencia visual revisada;
- CI verde;
- Draft y sin merge automático hasta revisión física.
