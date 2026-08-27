# 03 — Catálogo de herramientas, MCP y APIs para diseño/UX

**Corte:** 27/08/2026.  
**Regla:** instalar una herramienta solo cuando responde a una pregunta concreta. Las credenciales se crean fuera del repositorio y con mínimo privilegio.

## 1. Matriz ejecutiva

| Herramienta | Prioridad | Rol principal | Tipo de acceso | Estado recomendado |
|---|---:|---|---|---|
| Chrome DevTools for agents | P0 | observar navegador real, CSS, DOM, performance | local/plugin, sin key | CONFIGURAR |
| Playwright MCP/CLI | P0 | flujos y capturas reproducibles | local, sin key | CONFIGURAR |
| Figma MCP remoto | P0 | prototipos y contexto de diseño estructurado | OAuth | CONFIGURAR |
| BrowserStack MCP | P0/P1 | dispositivos/navegadores reales | OAuth remoto o credenciales | CONFIGURAR antes del merge visual grande |
| Percy | P1 | visual regression | token | ELEGIR si se usa BrowserStack |
| Chromatic | P1 | visual regression Playwright | project token | ALTERNATIVA a Percy |
| Stark MCP | P1 | accesibilidad + governance de diseño | OAuth | ELEGIR Stark o axe según prueba |
| axe MCP | P1 | auditoría a11y/render + remediación | OAuth/API | ELEGIR Stark o axe según prueba |
| Maze | P1 | estudios de prototipo/live website | cuenta | USAR para decisiones de comprensión |
| CrUX API / History | P1 | rendimiento real de campo | Google Cloud API key | CONFIGURAR si se automatiza |
| PageSpeed Insights API | P1/P2 | diagnóstico remoto puntual | API key recomendada | COMPLEMENTO |
| Canva MCP | P1 | moodboards/media/campaign assets | OAuth | USAR SOLO PARA MEDIA |
| Microsoft Clarity | condicional | heatmaps/session recordings | project config | NO ACTIVAR sin gate privacidad |
| Storybook MCP | defer | component docs/context | depende de stack | NO MIGRAR a React por esto |
| WebPageTest | opcional | waterfall/performance externo | cuenta/API según uso | MANUAL/CONDICIONAL |

## 2. Chrome DevTools for agents

### Para qué sirve aquí

Es la herramienta principal para impedir que Claude opine sobre una captura sin entender la implementación.

Debe utilizarse para:

- abrir producción/preview;
- inspeccionar DOM y accessibility tree;
- leer computed styles;
- localizar qué regla CSS produce un efecto;
- medir bounding boxes;
- detectar overflow;
- capturar viewport/full-page;
- revisar network;
- ejecutar performance traces;
- observar LCP/CLS/layout shifts;
- probar estados hover/focus;
- comparar mobile/desktop;
- verificar que un cambio visual existe realmente en navegador.

### Setup recomendado en Claude Code

Preferencia: plugin oficial con MCP + Skills, para que Claude tenga además procedimientos de uso.

```text
/plugin marketplace add ChromeDevTools/chrome-devtools-mcp
/plugin install chrome-devtools-mcp@chrome-devtools-plugins
```

Reiniciar Claude Code y comprobar `/skills`.

Alternativa MCP-only:

```bash
claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
```

### Credenciales

Ninguna.

### Privacidad/telemetría

Documentar en setup si se desea desactivar estadísticas de uso:

```text
--no-usage-statistics
```

Y si una sesión no debe consultar CrUX desde el tooling de performance:

```text
--no-performance-crux
```

### Qué no hacer

- no usarlo para «autodiseñar»;
- no aceptar una recomendación de DevTools como decisión artística;
- no sustituir dispositivos reales por emulación;
- no editar producción mediante DevTools y considerar eso implementación.

## 3. Playwright MCP + Playwright tests

### Doble rol

**MCP:** exploración interactiva por el agente.  
**Tests/CLI:** evidencia repetible y CI.

Setup MCP para Claude:

```bash
claude mcp add playwright npx @playwright/mcp@latest
```

### Casos de uso

- screenshot matrix;
- long-scroll captures;
- abrir/cerrar `Explorar`;
- keyboard/focus flows;
- resize sin reload;
- reduced motion;
- text spacing stylesheet;
- forms;
- tests de media/crop;
- geometry report;
- guardar evidencia antes/después.

### Regla

Una inspección MCP que descubre un bug repetible debe terminar convertida, cuando sea razonable, en test/script estable.

### Credenciales

Ninguna para browsers locales.

## 4. Figma MCP remoto

### Papel

Figma debe ser el **laboratorio estructurado de composición**, no el generador que dicta el sitio.

Endpoint remoto oficial:

```text
https://mcp.figma.com/mcp
```

Setup recomendado en Claude Code:

```text
claude plugin install figma@claude-plugins-official
```

Alternativa manual:

```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

Autenticación: OAuth.

### Para qué usarlo

- leer frames/reference designs;
- crear exploraciones estructuradas;
- colocar capturas actuales junto a hipótesis;
- inspeccionar propiedades/tokens del diseño;
- comparar 390/768/1440;
- documentar decisiones por familia;
- pasar contexto de diseño a Claude;
- producir variants A/B/C que luego se prueban en navegador.

### Agent Skills

Si el plugin aporta Skills oficiales, priorizarlos frente a prompts gigantes improvisados.

### Code Connect

Evaluar solo si aporta mapping estable entre diseño y componentes reales. El sitio es principalmente HTML/CSS estático; no crear una arquitectura React únicamente para poder utilizar Code Connect/Storybook.

### Credenciales

OAuth; no guardar tokens manuales en el repo.

## 5. BrowserStack MCP

### Por qué es importante

El contrato mobile existente exige realidad que la emulación no reproduce bien:

- Safari iOS;
- Chrome Android;
- barras dinámicas;
- teclado virtual;
- cutouts/safe areas;
- orientación;
- gestures;
- render/font differences;
- devices con densidades distintas.

### Acceso

Preferencia: MCP remoto/OAuth si la cuenta/flujo disponible lo permite.

Para integración local tradicional, las credenciales esperables son:

```text
BROWSERSTACK_USERNAME
BROWSERSTACK_ACCESS_KEY
```

Nunca versionarlas.

### Casos de uso

- smoke visual de familias;
- rotación;
- teclado;
- sticky header;
- dialogs;
- touch;
- screenshot evidence;
- comparación Safari/Chrome;
- confirmar bugs antes de introducir hacks de navegador.

### Gate de coste

No contratar un plan superior por adelantado. Primero:

1. comprobar acceso actual;
2. usar trial/capacidad existente si procede;
3. definir device matrix mínima;
4. medir cuántas sesiones reales necesitamos al mes.

## 6. Percy

### Rol

Visual regression en el ecosistema BrowserStack.

Puede:

- capturar baselines;
- producir diffs;
- revisar cambios;
- integrarse con Playwright;
- convertir una PR visual en evidencia comparable.

### Credencial

Token del proyecto Percy, almacenado como secret en CI si se autoriza.

Nombre habitual de entorno:

```text
PERCY_TOKEN
```

### Recomendación

Si BrowserStack se adopta como plataforma de device QA, Percy es la opción natural a probar primero.

No aprobar automáticamente diffs. Un cambio intencionado puede ser malo; un diff «cero» puede preservar un problema existente.

## 7. Chromatic

### Rol

Alternativa de visual testing, incluyendo flujos Playwright.

### Cuándo elegirlo

- si su revisión/UX encaja mejor con el equipo;
- si Playwright es la base y BrowserStack/Percy no compensa;
- si se adopta Storybook en un futuro por razones arquitectónicas reales.

### Credencial

Project token, guardado en GitHub Secrets si se automatiza.

### Regla

**Elegir Percy o Chromatic como baseline principal**, no pagar/mantener dos sistemas equivalentes sin un motivo.

## 8. Stark MCP

### Rol

Accesibilidad como parte de diseño y governance, no solo test al final.

Servidor remoto documentado:

```text
https://mcp.getstark.ai/mcp
```

Autenticación: OAuth en los clientes compatibles.

### Para qué usarlo

- análisis de diseño;
- contraste;
- problemas de accesibilidad;
- remediación;
- governance/project assets según capacidades de cuenta;
- revisión antes de que el diseño llegue a código.

### Valor añadido sobre Pa11y

Pa11y del repo ayuda en código. Stark puede aportar una capa de diseño/proceso y revisión anterior a implementación.

## 9. axe MCP

### Rol

Alternativa/complemento profesional para revisar una página renderizada y obtener orientación de remediación.

### Autenticación

Según el producto/configuración disponible: OAuth o API key.

Si se usa una key, una convención local posible es:

```text
AXE_API_KEY
```

pero debe seguirse el setup oficial de la cuenta elegida.

### Casos de uso

- scan por viewport;
- componentes/estados;
- problemas WCAG;
- revisión de código;
- remediación guiada.

### Decisión Stark vs axe

Hacer un piloto con la misma página problemática y comparar:

- calidad de hallazgos;
- capacidad de integrarse en Claude;
- ruido/falsos positivos;
- acciones de remediación;
- coste;
- facilidad de governance.

No instalar ambos permanentemente por inercia.

## 10. Maze

### Rol

Responder preguntas que ni Figma ni un test automatizado pueden resolver:

- ¿se entiende la jerarquía?;
- ¿la gente distingue dónde acaba una sección?;
- ¿encuentran fragmento/compra/prensa?;
- ¿qué interpreta un lector de la portada y el descriptor?;
- ¿una reorganización móvil mejora first-choice/task success?;

### Superficies

- prototypes;
- live website tests;
- mobile testing;
- comparación de variantes cuando sea útil.

### Uso correcto

No preguntar simplemente «¿cuál te gusta más?».

Diseñar tareas observables:

> «Quieres saber de qué trata Las manecillas y leer una muestra. ¿Qué harías?»

> «Has llegado a la página Autor. ¿Dónde buscarías la información para entrevistarle?»

> «Recorre esta página durante 20 segundos. Dime qué bloques principales recuerdas.»

### Credenciales

Cuenta de Maze; no se requiere guardar una key en el repo para un uso manual normal.

## 11. CrUX API / CrUX History

### Papel

Campo real, no laboratorio.

Sirve para saber si una mejora visual que parece correcta convive con experiencia real aceptable en Chrome UX Report.

### Métricas relevantes

- LCP;
- INP;
- CLS;
- distribución por periodos/estado según API vigente.

### Configuración

Proyecto Google Cloud + Chrome UX Report API habilitada + API key restringida.

Secret sugerido internamente:

```text
CRUX_API_KEY
```

El nombre es decisión del proyecto, no requisito de Google.

### Gate de disponibilidad

CrUX solo devuelve datos si la URL/origin tiene muestra suficiente. Tratar ausencia de datos como «no data», no como cero.

## 12. PageSpeed Insights API

### Papel

Diagnóstico remoto puntual complementario a Lighthouse CI.

No debe convertirse en otro workflow que duplique Lighthouse en cada commit.

Usos:

- producción después de un cambio importante;
- análisis externo de una URL concreta;
- contraste con lab local;
- auditoría periódica.

Para automatización frecuente, usar API key restringida.

## 13. Canva MCP

### Endpoint

```text
https://mcp.canva.com/mcp
```

Autenticación: OAuth.

### Papel correcto

- moodboards;
- social/campaign assets;
- composiciones promocionales;
- variaciones de crop;
- press materials;
- exploración de tratamiento gráfico;
- trabajo con Brand Kit si existe en el plan.

### Papel incorrecto

No usar Canva como autoridad para:

- grid web;
- responsive;
- semantic DOM;
- component behavior;
- CSS tokens;
- browser states.

Figma/navegador gobiernan esos aspectos.

## 14. Microsoft Clarity — condicional

### Valor potencial

- heatmaps;
- recordings;
- comportamiento real;
- clicks/dead clicks/scroll según producto vigente.

### Motivo de no activación automática

El repositorio ha mantenido una política sin grabación de sesiones. En EEA además el uso completo está sujeto a consentimiento válido según la configuración/funciones utilizadas.

Antes de activar:

1. revisar audiencia;
2. revisar privacidad y base legal;
3. implementar consentimiento válido si corresponde;
4. actualizar política;
5. minimizar datos;
6. definir periodo y pregunta de investigación;
7. apagarlo si no aporta.

No activar «porque es gratis».

## 15. Storybook MCP — defer

Storybook tiene tooling MCP/AI, pero la situación actual no justifica migrar la web a React ni crear una component architecture paralela solo para obtenerlo.

Reabrir si:

- el sitio adopta un sistema real de componentes reutilizables;
- existe Storybook por necesidades de desarrollo independientes del MCP;
- la herramienta deja de estar limitada por el stack que utilizamos.

## 16. WebPageTest — opcional

Útil cuando necesitamos profundizar en:

- waterfall;
- filmstrip;
- repeat view;
- render milestones;
- third parties;
- diferencias regionales/dispositivos.

Usarlo como herramienta de diagnóstico puntual antes de añadir otra automatización permanente.

## 17. Herramientas que NO recomiendo como núcleo

### Generadores «prompt → landing»

Pueden servir para sketches desechables, pero no para gobernar la dirección de arte del sitio.

Riesgos:

- patrones repetitivos;
- React/component scaffolding innecesario;
- cards/bentos;
- tipografía/paleta inventadas;
- pérdida de HTML/SEO existente;
- falsa sensación de velocidad.

### Librerías de inspiración sin procedencia

Pinterest/Dribbble pueden mostrar formas, pero no explican:

- task;
- constraints;
- responsive;
- accessibility;
- performance;
- results.

No deben ser autoridad.

### Page builders como fuente del sistema

No introducir Webflow/Framer solo para que Claude «diseñe visualmente» si después el sitio sigue implementándose en el repo. Duplicaría la fuente de verdad.

## 18. Orden recomendado de configuración

### Fase A — sin coste/secretos

1. Chrome DevTools plugin;
2. Playwright MCP;
3. scripts de capture/geometry;
4. evidencia actual.

### Fase B — diseño

5. conectar Figma MCP por OAuth;
6. crear laboratorio de familias;
7. importar screenshots baselines;
8. producir variantes.

### Fase C — calidad cross-device

9. BrowserStack;
10. Percy **o** Chromatic;
11. Stark **o** axe.

### Fase D — investigación

12. Maze;
13. CrUX/PSI API;
14. Clarity solo si pasa privacidad.

### Fase E — media

15. Canva MCP según necesidades concretas.

## 19. Regla de cierre

Una herramienta solo permanece en el stack si, tras un piloto, demuestra que mejora al menos una de estas capacidades:

- observación;
- decisión;
- reproducción;
- validación;
- investigación;
- calidad del handoff;
- prevención de regresiones.

Si solo genera más dashboards, prompts o screenshots sin cambiar decisiones, se retira.