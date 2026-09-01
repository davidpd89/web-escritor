# Herramientas individuales — contrato de unificación visual · 2026-08-31

## Trazabilidad

Continúa la cadena `DISEÑO -` después de la PR de Cuaderno artículos/temas.

La PR #270 (`DISEÑO - Herramientas · unificación visual del hub`) cerró deliberadamente solo `/herramientas/` y dejó fuera las herramientas individuales. Su QA usa `/herramientas/manuscrito/` como control de aislamiento. Esta intervención completa la familia instrumental sin reabrir el hub.

Mantener Draft y no mergear fuera de orden.

## Objetivo

Unificar el chrome visual de las herramientas individuales con el sistema editorial azul/negro/dorado, preservando íntegramente cada motor funcional y su visualización específica.

La interfaz debe seguir pareciendo una herramienta útil, pero integrada en la web editorial: evitar tanto el aspecto SaaS genérico como convertir formularios/resultados en decoración editorial que reduzca claridad o eficiencia.

## Arquitectura existente favorable

La familia ya está bien preparada para una intervención centralizada:

- `assets/v1-tools.css` define hero, formularios, acciones, status, resultados, findings, tablas, workspace y trust.
- Los CSS específicos de cada motor consumen en gran parte variables semánticas (`--color-*`, `--surface-*`, etc.).
- Ejemplo verificado: `assets/analizador-capitulos.css` usa variables del sistema para barras, tablas y superficies.

Por tanto, la solución preferida es una capa/firma de familia y ajustes puntuales por arquetipo, NO editar veinte herramientas una por una ni duplicar CSS.

## Superficies

Antes de producción, inventariar todas las rutas públicas/indexables que usan `data-family="tool"` o `v1-tools.css`.

El inventario actual incluye numerosas rutas bajo `/herramientas/`, entre ellas contador, diálogo, manuscrito, distribución POV, entrevista, eventos ICS, JSON-LD, metadatos, kit de prensa y otras utilidades.

Además, comprobar explícitamente dos rutas fuera de `/herramientas/` que ya usan la misma familia instrumental:

- `/clubes-de-lectura/preparar-sesion/`
- `/recursos/ficha-historia-objeto-heredado/`

No asumir que toda carpeta existente es pública: reconciliar sitemap + robots + canonical.

## Fuera de alcance

- `/herramientas/` hub — #270.
- `/asistente/` — interfaz conversacional propia; PR separada.
- Editoriales, Convocatorias y Metodología — ya tienen PRs propias.
- `/recursos/herramientas-para-escritores/` mientras siga noindex, salvo decisión posterior explícita.
- motores JS, algoritmos, fórmulas y resultados, salvo bug funcional demostrado.

## Dirección visual

### Chrome compartido

- hero con continuidad azul/dorado sin convertir cada utilidad en landing promocional;
- labels, hints y metadatos principalmente neutros;
- inputs/selects/textareas limpios, con focus claramente accesible y coherente con la nueva identidad;
- acciones primarias/secundarias diferenciadas sin exceso de botones azules;
- status/error/success con semántica clara: no usar dorado como sustituto de estados de error;
- resultados como instrumentos/ledgers, no dashboards de KPIs genéricos;
- findings, tablas y comparativas con rails/reglas y densidad suficiente;
- trust/source lists documentales;
- continuidad final con el hub sin repetir cards innecesarias.

### Azul/dorado

Referencia:

- azul editorial `#1d4f96`
- azul profundo `#0d2c57`
- dorado `#b8860b`
- pale blue `#eefaff`

Preferir tokens scopeados a hardcodes. No recolorear métricas/estados que necesiten otra semántica.

### Yellowtail

Uso muy limitado: posible apertura o acción editorial, nunca labels de formulario, valores numéricos, tablas ni resultados técnicos.

## Estrategia para reducir trabajo

No validar cada herramienta en cada viewport si comparten exactamente estructura. Primero clasificar arquetipos y seleccionar representantes.

Arquetipos mínimos esperados:

1. textarea/análisis simple;
2. workspace lateral + resultados complejos (`/herramientas/manuscrito/`);
3. formulario con múltiples campos/opciones;
4. tabla o exportación;
5. recurso/constructor fuera de `/herramientas/`;
6. herramienta con visualización propia (barras/métricas).

Solo añadir representantes si el inventario revela otra arquitectura real.

## Contrato funcional a preservar

Por representante, proteger:

- canonical/robots/schema WebApplication cuando exista;
- inputs, labels, `aria-*` y asociaciones;
- procesamiento local cuando sea contractual;
- botones/estados/errores;
- exportación/copia/descarga cuando exista;
- persistencia local si existe;
- resultados y fórmulas;
- no-JS/fallback según diseño de cada herramienta;
- navegación contextual y enlaces al hub;
- privacidad y mensajes de tratamiento local;
- impresión si la herramienta la soporta.

No cambiar data-* usados por motores JS.

## QA requerido

Crear contrato browser de familia basado en arquetipos y mantener `Tool engine tests` como autoridad funcional.

Cobertura:

- desktop 1440/1280;
- tablet 1024/768;
- seams reales;
- 390/360/320;
- landscape móvil si workspaces complejos lo justifican;
- zoom 200 %;
- text spacing;
- teclado/focus;
- cero overflow;
- estados vacío/con resultados/error cuando sean reproducibles;
- tablas responsivas;
- textarea/select/file input;
- carga de fuentes estable;
- aislamiento hacia `/herramientas/` hub, Asistente, Editoriales y Convocatorias.

No usar `overflow:hidden` para esconder tablas/formularios que no refluencian. No relajar engine tests.

## Revisión humana

Revisar especialmente:

- densidad y claridad frente a estética;
- legibilidad de resultados;
- orden de tabulación;
- teclado móvil y safe areas en formularios;
- botones que no se desplacen o envuelvan de forma torpe;
- estados de espera/error;
- diferencia perceptiva entre herramienta y artículo editorial;
- consistencia del chrome sin borrar la identidad funcional de cada motor.

Seguir `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md` antes del merge.

## Definition of Done

- inventario real de herramientas reconciliado;
- arquetipos documentados;
- familia visual coherente mediante owners/tokens compartidos;
- mínimos cambios puntuales por motor;
- hub #270 sin contaminación;
- Asistente sin contaminación;
- motores y Tool engine tests verdes;
- responsive/zoom/text-spacing/teclado verdes;
- evidencia visual representativa revisada;
- CI verde;
- Draft y sin merge automático hasta revisión física.
