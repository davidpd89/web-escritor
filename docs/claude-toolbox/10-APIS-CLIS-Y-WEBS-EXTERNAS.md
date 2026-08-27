# 10 — APIs, CLIs, validadores y webs externas útiles

No todo lo útil para Claude debe convertirse en plugin. Muchas veces una CLI o una API determinista da una señal más fiable y con menos superficie de ataque/contexto.

## 1. W3C Nu HTML Checker — alto valor, sin “IA”

Interfaz programática oficial:

```text
https://validator.w3.org/nu/
```

El W3C documenta salida `json`, `xml` y `gnu` mediante la API del HTML Checker moderno.

### Para qué

- HTML inválido;
- nesting imposible;
- atributos/roles conflictivos;
- errores estructurales que un screenshot no muestra.

### Propuesta

Antes de añadir otra dependencia npm, pilotar un script de QA que valide el **artefacto público generado**, no solo source HTML.

### Importante

Valid HTML no significa buen UX/a11y. Es una capa estructural.

## 2. HTML-Validate — alternativa/local complementaria

Versión 11.x está activa en 2026. CLI:

```bash
npm exec html-validate "**/*.html"
```

Puede usar presets `recommended`/`a11y` y existe extensión VS Code.

### ¿Añadir al repo?

Solo después de comparar contra W3C + Pa11y + tests actuales:

- findings únicos;
- falsos positivos con nuestro HTML;
- capacidad de correr offline;
- coste CI.

No añadir ambos por reflejo.

## 3. Stylelint — candidato para CSS guardrails, no estilo de diseño

Setup oficial actual:

```bash
npm create stylelint@latest
```

O:

```bash
npm add -D stylelint stylelint-config-standard
npx stylelint "**/*.css"
```

### Lo que puede aportar

- errores CSS;
- sintaxis;
- prácticas problemáticas;
- custom properties;
- consistencia estructural.

### Lo que NO debe hacer

- ordenar propiedades o imponer reglas cosméticas generando diffs enormes;
- prohibir modern CSS que Modern Web Guidance ha validado;
- “simplificar” excepciones responsive deliberadas;
- decidir diseño.

### Pilot

Ejecutar Stylelint sin auto-fix sobre `assets/v1-*.css`, clasificar findings. Solo adoptar reglas de error/robustez que tengan beneficio real.

## 4. CrUX API

Fuente oficial de experiencia agregada de usuarios Chrome.

Endpoint diario:

```text
POST https://chromeuxreport.googleapis.com/v1/records:queryRecord
```

Requiere Google Cloud API key habilitada para Chrome UX Report API.

### Datos relevantes

- LCP;
- CLS;
- INP;
- FCP/TTFB experimental según disponibilidad;
- `PHONE`, `DESKTOP` o agregado;
- URL u origin cuando existe suficiente muestra.

Datos diarios representan ventana agregada; no comparar como si fueran telemetry instantánea.

## 5. CrUX History API

Endpoint:

```text
POST https://chromeuxreport.googleapis.com/v1/records:queryHistoryRecord
```

La documentación oficial actual ofrece histórico de seis meses y actualización semanal de series.

### Uso real

Antes/después de un rediseño significativo:

- no esperar causalidad instantánea;
- anotar release;
- observar tendencia varias semanas;
- comparar origin + URLs con señal;
- controlar cambios externos.

## 6. PageSpeed Insights API

Endpoint oficial v5:

```text
GET https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed
```

Puede llamarse sin key para uso puntual; Google recomienda key para queries frecuentes/automatizadas.

### Advertencia 2026

Google avisa que planea dejar de incluir datos CrUX field dentro de PSI API y recomienda CrUX/CrUX History para datos reales. Por eso:

- LHCI → lab CI;
- PSI → diagnóstico externo puntual;
- CrUX → field data.

No construir una nueva infraestructura que dependa de PSI para field metrics.

## 7. WebPageTest — PILOT

WebPageTest aporta análisis de waterfall, filmstrip, múltiples ubicaciones/dispositivos y scripting más profundo.

### Cuándo merece API key

- una regresión de LCP que Lighthouse no explica;
- analizar carga de fuentes/imágenes/third parties;
- comparar cold/warm cache;
- filmstrip visual del loading;
- probar network profiles.

No meterlo en cada PR si LHCI + Chrome trace ya responden la pregunta.

Si se automatiza: `WEBPAGETEST_API_KEY` como secret.

## 8. WAVE

### Browser extension

WAVE ofrece extensiones Chrome/Firefox/Edge que ejecutan evaluación en el navegador; WebAIM indica que la extensión no envía la página al servidor. Muy útil para revisión humana de una build local.

### API

WAVE API es de pago por créditos y devuelve JSON/XML sobre páginas renderizadas.

### Decisión

- extensión manual: recomendada como segunda mirada humana;
- API: DEFER mientras Pa11y + posible axe no dejen un gap demostrable.

No sumar Pa11y + axe + WAVE API permanentemente sin saber qué finding único aporta cada uno.

## 9. Chrome Accessibility / DevTools

Antes de pagar una suite nueva, utilizar:

- accessibility tree;
- contrast info;
- focus inspection;
- performance/accessibility audits disponibles;
- Rendering tools cuando sean útiles.

Claude DevTools puede acceder a buena parte de este contexto mediante MCP.

## 10. ImageMagick + cwebp — ya presentes en el entorno local histórico

El `settings.local.json` actual contiene comprobaciones para `magick` y `cwebp`, señal de que ya se han usado/previsto localmente.

### Uso

- resize/crop deterministic;
- generar WebP;
- comparar dimensiones/peso;
- preparar variants para `<picture>`;
- generar contact sheets para revisión.

### Regla

No automatizar crops de retrato/portada solo por algoritmo. Los crops importantes requieren art direction/manifest.

## 11. Sharp — no añadir por reflejo

Node Sharp es excelente, pero si ImageMagick/cwebp + scripts actuales resuelven pipeline, no introducir otra librería binaria. Reabrir si un pipeline programático exige AVIF/crops/metadata con más reproducibilidad.

## 12. FontTools / fonttools subset — solo si aparece necesidad real

Puede ser útil para inspección/subsetting de fuentes. Antes de modificar fuentes:

- licencia;
- glyph coverage español;
- ligaduras/features;
- fallback metrics;
- CLS;
- calidad tipográfica.

No subsetear una fuente artística hasta romper caracteres poco frecuentes.

## 13. Lighthouse CI — ya existe

`@lhci/cli@0.15.1` está fijado. No instalar “Lighthouse plugin para Claude” como reemplazo.

Claude puede:

- ejecutar workflow/script actual;
- abrir reports;
- usar Chrome trace para investigar.

La fuente reproducible sigue siendo el lockfile/CI.

## 14. Pa11y — ya existe

`pa11y-ci@4.1.1` está fijado.

Antes de meter axe/WAVE, usar Pa11y como baseline para detectar valor incremental.

## 15. Lychee — ya existe broken-links workflow

No añadir otro link checker genérico. Mejorar configuración existente si hay falsos positivos/gaps.

## 16. Pagefind — ya existe

No añadir Algolia/Meilisearch/local search SaaS por “mejor tooling” salvo necesidad funcional nueva. Pagefind es consistente con sitio estático y privacidad.

## 17. Web platform sources

### MDN

Primera referencia general de APIs/HTML/CSS y compatibilidad.

### web.dev / Chrome Developers

Performance, Baseline, modern platform, CrUX.

### W3C/WAI/WCAG

Normativa y técnicas de accesibilidad.

### WHATWG

Especificación viva HTML cuando se necesita resolver una duda normativa precisa.

Claude debe citar/guardar la fuente primaria en decisiones no obvias.

## 18. Diseño/referencia

### Webby / CSS Design Awards / Awwwards

Útiles para:

- observar ejecución actual;
- criterios de jurado;
- generar muestra de soluciones.

No son evidencia de usabilidad por sí mismos.

### Pentagram / AREA 17 / estudios

Mejor cuando publican case study/proceso: entender por qué, no copiar forma.

### Fonts In Use

Útil para precedentes tipográficos reales, especialmente editorial/cultural.

### Mobbin / Page Flows

Útil para interactions/product patterns. Menos autoridad estética para una web literaria.

### NN/g

Research UX y heurísticas con contexto.

### Baymard

Especialmente ecommerce; aplicar solo si una superficie de compra realmente se comporta como commerce.

## 19. Visual diff local simple

Antes de SaaS puede existir un script Playwright que capture viewports y use pixel diff/SSIM. Pero no reinventar una plataforma si Percy/Chromatic resuelve review/histórico mejor cuando se necesite.

## 20. APIs que NO necesitamos ahora

- generadores de paleta por IA;
- “AI UX score” opaco;
- API de stock photography para rellenar huecos;
- icon generators;
- logo generators;
- random design inspiration APIs;
- scraping masivo de Awwwards;
- screenshot SaaS redundante si Chrome/Playwright ya captura;
- múltiples PageSpeed wrappers de terceros.

## 21. Criterio de incorporación

Una CLI/API entra en dependencia o CI solo si:

- encuentra un fallo relevante que hoy escapa;
- la salida es reproducible;
- el coste de mantenimiento es bajo/justificado;
- no crea conflicto con modern CSS/HTML válido;
- no genera un score vanity;
- podemos fijar versión/config;
- existe owner y procedimiento de actualización.