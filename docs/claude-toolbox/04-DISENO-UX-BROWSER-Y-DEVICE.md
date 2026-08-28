# 04 — Diseño, UX, browser y device tooling

Este capítulo no define cómo debe verse la web. Define qué herramientas pueden aportar evidencia o capacidad real al proceso de diseño.

## 1. Frontend Design — generador de hipótesis, no director de arte

```bash
/plugin install frontend-design@claude-plugins-official
```

Anthropic lo presenta como un plugin para producir frontends con carácter y evitar estética genérica de IA. Eso lo hace relevante para este proyecto, pero también peligroso si se usa como “hazme algo bonito”.

### Uso correcto

Dar antes:

- captura del estado actual tomada con Chrome DevTools;
- ancho/alto exacto;
- contenido real;
- contratos V1 de diseño;
- problema observable (“no se distinguen escenas en 390 px”);
- constraints de DOM/SEO/a11y;
- prohibición de cambiar paleta/tipografía solo para crear novedad.

Pedir:

1. máximo 2–3 hipótesis;
2. explicar qué variable compositiva cambia;
3. no codificar todavía;
4. señalar riesgos en 320/390/768/1440;
5. pasar después por critic.

### Uso incorrecto

`/frontend-design Rediseña mi web de escritor para que sea premium.`

Eso produce exactamente la pérdida de identidad que esta estrategia quiere evitar.

## 2. Chrome DevTools MCP — observador primario

Instalación: ver P0.

### Capacidades que sí nos importan

- emulación de viewport/dispositivo;
- screenshots;
- computed styles y DOM snapshots;
- medir bounding boxes y distancia entre regiones;
- console/network;
- performance trace;
- Lighthouse/CrUX cuando aplique;
- memory/profile si aparece un problema real.

### Protocolos de diseño

#### Jerarquía mobile

Para una página:

1. 390×844;
2. screenshot full page y above-the-fold;
3. listar headings, landmarks, imágenes y grandes regiones;
4. medir tamaños H1/H2/body y gaps de sección;
5. contar transiciones visuales distinguibles sin leer el copy;
6. comparar con la misma página a 1440;
7. emitir **evidencia**, no solución.

#### Imágenes “meh”

No preguntar “¿qué imagen pondrías?”. Medir primero:

- ratio intrínseco vs renderizado;
- crop/object-position;
- superficie ocupada;
- nitidez/densidad real;
- relación con texto vecino;
- si es contenido, documento, portada, retrato o decoración;
- si el mismo asset se usa en contextos incompatibles.

## 3. Playwright MCP — comportamiento y journeys

### Casos

- abrir/cerrar Explorar;
- navegación por teclado;
- formulario newsletter;
- share/print;
- volver atrás y conservar contexto;
- resize continuo;
- reduced motion;
- enlaces de una herramienta;
- screenshot states después de una interacción.

### Regla

Una prueba exploratoria que encuentra una regresión repetible debe convertirse en test Playwright dentro del repo cuando su importancia justifique CI.

## 4. Figma plugin + MCP — laboratorio estructurado

Instalación preferida actual según Figma:

```bash
/plugin install figma@claude-plugins-official
```

Alternativa MCP remoto:

```bash
claude mcp add --scope user --transport http figma https://mcp.figma.com/mcp
```

Después:

```text
/mcp
```

y autenticar por OAuth.

### Qué aporta

- lectura de components, variables, layout y canvas;
- Design/FigJam/Make context;
- Code Connect;
- generar código desde selección;
- enviar interfaces web a Figma como capas editables;
- lectura/escritura de contenido nativo según capacidades actuales.

### Qué no aporta

Figma no conoce por sí solo:

- browser bars iOS;
- teclado real;
- DOM/semántica final;
- LCP/CLS/INP;
- CSS cascade real;
- todo el contenido dinámico/edge state.

Por eso nunca se aprueba una familia porque “se ve bien en Figma”.

### Flujo recomendado

`Chrome current state → Figma hypotheses → critic → implementation branch → Chrome/Playwright → visual diff → device`.

## 5. Canva plugin — media, no layout web

```bash
/plugin install canva@claude-plugins-official
```

El plugin actual de Canva integra su MCP y skills para editar, resize, bulk create, brand check, design feedback e implementar comments con preview/approve.

### Usos válidos

- creatividades de Manecillas;
- press/social assets;
- variantes de formatos;
- moodboards/referencia de material;
- revisión de consistencia de marca;
- crop studies que después se traducen a `picture`/manifest.

### No usar para

- decidir grid responsive del sitio;
- generar HTML/CSS;
- reemplazar Figma/Chrome;
- convertir toda la web en templates de Canva.

## 6. Playground — prototipo aislado

```bash
/plugin install playground@claude-plugins-official
```

Útil para explorar en un HTML autocontenido:

- ritmo de secciones;
- comportamiento de una ruta/filete;
- microinteraction;
- estados de un componente;
- comparación de dos hipótesis;
- visualización de un token scale.

Nada del playground pasa a producción por copy/paste sin adaptar al sistema V1 y tests.

## 7. BrowserStack MCP — el cierre de real device

### Preferencia: remoto OAuth

Endpoint actual:

```text
https://mcp.browserstack.com/mcp
```

BrowserStack documenta OAuth para su servidor remoto, evitando pasar access keys al cliente.

Para un cliente compatible con HTTP MCP, configurar ese endpoint y autenticar.

### Alternativa local

Paquete:

```text
@browserstack/mcp-server@latest
```

Credenciales si se usa local:

```text
BROWSERSTACK_USERNAME
BROWSERSTACK_ACCESS_KEY
```

Nunca escribirlas en `.mcp.json` versionado.

### Qué probar para este proyecto

Matriz mínima:

- Safari iOS actual: 390-ish portrait + landscape;
- Safari iOS pantalla estrecha si disponible;
- Chrome Android actual;
- Chrome/Edge desktop;
- Firefox como motor secundario;
- al menos una sesión con teclado/inputs;
- rotación caliente;
- browser chrome dinámico;
- safe area/notch;
- touch y scroll.

### Pilot gate

No pagar/expandir plan por “tener BrowserStack”. Primero ejecutar 10 escenarios del doc Mobile Runtime y comprobar que encuentra issues que no detectamos con Playwright/Chrome local.

## 8. Visual regression: Percy o Chromatic, no ambos de entrada

No se ha verificado un plugin Claude imprescindible para estas suites; su valor está en CLI/CI.

### Percy

Preferente si BrowserStack se adopta y queremos un stack integrado.

### Chromatic + Playwright

Alternativa sólida si queremos snapshots Playwright versionados y review cloud.

### Política

- baseline consciente, no “accept all”;
- viewport por familia, no miles de screenshots;
- tolerancias solo para contenido realmente variable;
- cada diff visual rechazado/aceptado debe tener razón;
- artifacts no se convierten en fuente de diseño.

## 9. axe Accessibility plugin/MCP — piloto profesional

Marketplace Deque:

```text
/plugin marketplace add dequelabs/axe-accessibility
/plugin install axe-accessibility
```

Setup:

```text
/axe-accessibility:mcp-setup
```

Deque documenta ciclo:

`analyze → remediate → verify`.

Auth:

- OAuth 2.0 (Node 22+) preferible;
- o `AXE_API_KEY` en entorno/keychain.

Requiere actualmente una suscripción axe DevTools for Web Bundle para el MCP.

### Cómo encaja con Pa11y

Pa11y sigue en CI. Axe añade:

- motor/knowledge Deque;
- explicación/remediation agentic;
- una segunda perspectiva especializada.

Pilot durante una familia. Si no encuentra/ayuda a resolver nada relevante adicional, no se paga por redundancia.

## 10. Stark — monitor/pilot

Stark anunció en agosto de 2026 una integración/connector para Claude capaz de trabajar con Figma, live URLs, source y otras superficies de accesibilidad.

No se asume aquí que tenga exactamente la misma disponibilidad/instalación que un plugin de `claude-plugins-official`. Antes de usar:

1. confirmar compatibilidad actual con Claude Code/VS Code;
2. confirmar plan/coste;
3. delimitar datos que recibe;
4. ejecutar mismo piloto que axe;
5. elegir el que aporte más valor. No mantener dos suites pagadas por defecto.

## 11. Adobe for Creativity — media profesional opcional

Plugin presente en el marketplace oficial de Claude, de Adobe.

Caso de uso si existe licencia/flujo Adobe:

- background removal;
- vectorización;
- retoque;
- procesamiento de assets reales;
- automatización creativa controlada.

No sustituye dirección de arte, ni justifica crear “material documental” falso.

## 12. Web references como herramienta, no como Pinterest

Claude puede investigar referencias reales, pero cada consulta debe tener una pregunta:

- ¿cómo resuelve esta publicación la jerarquía mobile?
- ¿cómo presenta un libro sin ecommerce-card?
- ¿cómo separa escenas sin alternar fondos arbitrariamente?
- ¿cómo trata fotografía editorial en 390 px?
- ¿qué ocurre con el TOC al perder columnas?

Fuentes útiles:

- Awwwards/CSS Design Awards/Webby → candidatos y criterios, no reglas universales;
- Pentagram/AREA 17/estudios → case studies con razonamiento;
- Fonts In Use → precedentes tipográficos reales;
- Typewolf → observación tipográfica, no copiar combinación;
- Mobbin/Page Flows → patrones de interacción; menos autoridad para una publicación literaria;
- Nielsen Norman Group/Baymard → investigación UX; usar lo que aplique, no convertir una web editorial en ecommerce.

## 13. Cadena de evidencia para un cambio visual

Un cambio significativo no se aprueba con una captura bonita.

```text
problema real
→ Chrome evidence
→ contrato V1
→ 2–3 hipótesis
→ Figma/Playground si ayuda
→ critic
→ implementación aislada
→ Playwright journeys
→ accessibility
→ visual diff
→ BrowserStack real device
→ performance
→ revisión humana
```

Si la hipótesis no supera esta cadena, se descarta aunque la haya generado un plugin “de diseño”.