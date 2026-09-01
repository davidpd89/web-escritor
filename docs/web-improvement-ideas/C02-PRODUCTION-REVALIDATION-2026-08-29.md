# C.2 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #177  
Decisión operativa: **CONDITIONAL · MATERIAL_EXISTS · EDITORIAL_GATE_NOT_MET · HUB_GATED · NO_CODE**

## Resultado

C.2 no está bloqueada por falta de material. La revalidación de Drive encuentra un conjunto real de borradores y scaffolds de Manecillas. Sin embargo, **material existente no equivale a publicación autorizada** y el trigger técnico del hub sigue sin cumplirse.

No se activa `/las-manecillas-del-recuerdo/como-se-escribio/` ni se importan artículos automáticamente desde Drive.

## Evidencia del repo

Inspección directa de `main`:

- `data/content-registry.json` no contiene `/las-manecillas-del-recuerdo/como-se-escribio/`;
- la ruta `las-manecillas-del-recuerdo/como-se-escribio/index.html` no existe;
- las URLs proyectadas del hub no están publicadas como cuatro notas indexables del Cuaderno;
- `docs/CONTENT-PARITY-MANECILLAS-V1.md` mantiene el hub como `GATED_CON_CONDICIÓN` y exige al menos cuatro notas reales, indexables, en sitemap y enlazadas desde `/cuaderno/` antes de activarlo.

Por tanto, el gate técnico de publicación es inequívoco: **no cumplido**.

## Evidencia de Drive

Drive sí contiene:

- `como-se-escribio-manecillas-index.example.html`: scaffold de un `CollectionPage` noindex con nueve tarjetas proyectadas;
- `manecillas-process-hub-integration.txt`: regla explícita de activación por cuatro notas publicadas/indexables;
- borradores individuales, entre ellos:
  - `01_POR_QUE_LOS_OBJETOS_GUARDAN_MEMORIA.md`;
  - `02_QUE_ES_UNA_NOVELA_CORAL.md`;
  - `03_ABUELOS_NIETOS_Y_MEMORIA_FAMILIAR.md`;
  - `05_CUANDO_TECNOLOGIA_TRANSFORMA_HISTORIA.md`;
  - `06_COMO_DAR_BIOGRAFIA_A_UN_OBJETO_PROCEDENCIA.md`;
  - `07_CAMBIAR_EPOCA_REGISTRO_NOVELA_CORAL.md`;
- ejemplos HTML derivados para varias de esas piezas.

El propio material marca repetidamente `listo para revisión editorial`, `sin destripes` y **`No publicar automáticamente`**.

## Revisión editorial de muestra

Se leyeron directamente cuatro piezas representativas.

### 01 · Objetos que guardan memoria

Tiene sustancia, buena relación con el eje del reloj y un bloque específico sobre Manecillas. Pero la mayor parte funciona como ensayo general sobre memoria material. Antes de presentarlo como “detrás del libro” necesita reforzar qué decisión real tomó David, qué alternativa descartó o qué problema narrativo resolvió.

Estado C.2: **READY_FOR_EDITORIAL_REVIEW**, no publicación automática.

### 02 · Qué es una novela coral

Es útil y explica bien estructura, hilo conductor y orden. También contiene una aplicación concreta a Manecillas. Su framing principal sigue siendo definicional/general, por lo que encaja mejor como pieza de Cuaderno sobre técnica narrativa que como testimonio de proceso si no se añade experiencia de primera mano.

Estado C.2: **READY_FOR_EDITORIAL_REVIEW**.

### 03 · Abuelos, nietos y memoria familiar

Tiene buena coherencia temática y control de spoilers. La sección Manuel/Tomás conecta con la obra, pero el texto generaliza sobre memoria familiar. Requiere una capa autoral verificable para que “cómo se escribió” no sea solo una etiqueta de distribución.

Estado C.2: **READY_FOR_EDITORIAL_REVIEW**.

### 06 · Biografía/procedencia de un objeto

Es la pieza más claramente diferenciada de la muestra revisada porque combina una técnica concreta con investigación documental y fuentes externas identificadas (Smithsonian, Getty, Met). Aun así, para C.2 debe quedar claro qué parte de ese método se utilizó realmente durante la escritura de Manecillas y qué parte es extrapolación didáctica posterior.

Estado C.2: **STRONG_PILOT_CANDIDATE · EDITORIAL_REVIEW_REQUIRED**.

## Por qué no se publican cuatro piezas desde esta PR

Hacerlo solo para cumplir el gate numérico invertiría la causalidad correcta:

1. primero la pieza debe ser auténtica, útil, spoiler-safe y editorialmente aprobada;
2. después puede publicarse como URL individual del Cuaderno;
3. solo cuando existan al menos cuatro URLs reales y enlazadas se reconsidera el hub.

El hub no debe crear la necesidad de artículos. Los artículos deben justificar el hub.

Además, los borradores son materiales del usuario en Drive y declaran expresamente que no deben publicarse automáticamente. Esta PR de revalidación no transforma `ready for review` en consentimiento de publicación.

## Revalidación Google 2026

La documentación actual de Google continúa centrada en contenido útil, fiable y people-first; su política de spam define como scaled content abuse la creación de muchas páginas poco originales o con poco valor, independientemente de cómo se generen.

C.2 tiene valor precisamente cuando la ventaja es irrepetible: experiencia real del autor, decisiones propias, materiales y trade-offs. Convertir seis/nueve borradores en URLs solo para llenar una arquitectura sería el anti-patrón opuesto.

Fuentes primarias:

- `https://developers.google.com/search/docs/fundamentals/creating-helpful-content`
- `https://developers.google.com/search/docs/essentials/spam-policies`

## Trigger exacto de publicación de una pieza C.2

Una pieza puede pasar de Drive a Cuaderno cuando:

1. David confirma que el proceso/decisión descrito ocurrió realmente o autoriza el framing didáctico;
2. se distinguen hechos de proceso de inferencias/consejos posteriores;
3. no revela spoilers no aprobados;
4. fuentes externas están verificadas cuando se usan;
5. no duplica una URL existente;
6. tiene suficiente valor independiente para justificar URL propia;
7. CTA/copy factual se sincroniza con `editorial-facts.json` actual, no con wording prelaunch antiguo;
8. pasa los builders/checks actuales de Cuaderno, sitemap, navegación y accesibilidad.

## Trigger exacto del hub

Mantener el contrato existente de Drive/Content Parity:

- ≥4 notas publicadas;
- las cuatro `index,follow`;
- presentes en sitemap;
- enlazadas desde `/cuaderno/`;
- cada una con enlace entrante contextual;
- entonces crear/activar hub con enlaces HTML rastreables, `dateModified` real y enlace descriptivo desde Manecillas.

Antes de eso, no crear ni siquiera una página pública `noindex` vacía: el scaffold de Drive ya preserva el diseño futuro sin ensuciar producción.

## Relación con C.1

C.1 puede usar una pieza C.2 si ya ha pasado su gate editorial. No puede convertir una fecha del calendario en autorización para publicar un borrador.

El calendario social existente en Drive es además un plan operativo, no prueba de que un contenido C.2 concreto haya sido aprobado o ejecutado.

## Definition of Done

- [x] reconstrucción histórica preservada;
- [x] `main` inspeccionado directamente;
- [x] ausencia del hub público comprobada sin depender de code search;
- [x] Drive inspeccionado para comprobar material real;
- [x] scaffold y contrato de activación leídos directamente;
- [x] cuatro borradores representativos revisados;
- [x] existencia de material separada de autorización de publicación;
- [x] candidato de piloto identificado sin publicarlo automáticamente;
- [x] trigger de pieza y trigger de hub fijados;
- [ ] CI del HEAD final completamente verde;
- [ ] revisión de Claude antes de merge.

## Conclusión

C.2 permanece **condicionada**, pero ya no por falta de material: hay un corpus de borradores real. El bloqueo actual es editorial y de publicación. La siguiente acción correcta no es generar más contenido ni activar un hub vacío, sino revisar/autorizar una primera pieza —con `06_COMO_DAR_BIOGRAFIA_A_UN_OBJETO_PROCEDENCIA.md` como candidato fuerte— y demostrar valor antes de escalar la serie.
