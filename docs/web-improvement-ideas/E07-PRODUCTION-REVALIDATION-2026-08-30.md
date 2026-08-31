# E.7 · Revalidación de producción — compresión HTTP del origen

Fecha inicial: 2026-08-30  
Revalidación live cerrada: 2026-08-31  
Base de código contrastada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
HEAD de implementación live: `a4fda2cfa799cc762a41b8d5e1e8b39df608ebdf`.  
Decisión efectiva: **IMPLEMENTED_IN_PR · LIVE_REPORT_ONLY · ORIGIN_GZIP_VERIFIED · VARY_ACCEPT_ENCODING_VERIFIED · NO_INFRA_CHANGE**.

## 1. Resolución de la contradicción histórica

Se conserva la secuencia de #135:

- la autoridad final/machine-readable llegó a `NOT_APPLICABLE` porque Cloudflare estaba DNS-only;
- la revalidación independiente corrigió el estado efectivo a `PARTIAL_AUDIT` porque DNS-only solo demuestra que Cloudflare edge no gobierna la respuesta, no qué compresión aplica el hosting/origen real;
- el 30/08 el runtime de trabajo no podía resolver `davidportodiaz.com`, por lo que se mantuvo correctamente `LIVE_HEADER_NOT_OBSERVED`;
- #244/M.1 demostró después que GitHub Actions sí puede observar la producción real desde una red adecuada;
- E.7 reutiliza ese patrón de observación, pero con un auditor propio de negociación HTTP porque M.1 no registra `Content-Encoding` ni `Vary`.

La falta de DNS del runtime local deja de ser el bloqueo de E.7. La respuesta live ya está observada de forma reproducible.

## 2. Pregunta que resuelve E.7

La pregunta no es «¿Cloudflare tiene Brotli activado?», sino:

> ¿Qué `Content-Encoding` recibe realmente un cliente para HTML/CSS/JS textuales cuando anuncia distintos valores de `Accept-Encoding`, y el servidor declara correctamente la variación cacheable?

La documentación HTTP vigente confirma que:

- `Accept-Encoding` anuncia los encodings aceptados por el cliente;
- `Content-Encoding` comunica la representación seleccionada;
- `Vary: Accept-Encoding` diferencia correctamente las variantes cacheables negociadas.

Fuentes de referencia preservadas:

- MDN · HTTP compression;
- MDN · `Accept-Encoding`;
- MDN · `Content-Encoding`.

## 3. Implementación añadida en esta PR

### `qa/live-compression-origin.mjs`

Auditor Node 22 sin dependencias externas que observa producción mediante GET y genera evidencia JSON machine-readable.

Muestra tres assets textuales representativos:

- HOME HTML: `/`;
- shell CSS: `/assets/v1-shell.css`;
- runtime JS: `/script.js`.

Para cada uno ejecuta tres negociaciones separadas:

```text
Accept-Encoding: br, gzip
Accept-Encoding: gzip
Accept-Encoding: identity
```

Registra:

- status y URL final;
- `Content-Encoding`;
- `Vary`;
- `Content-Type`;
- `Content-Length`;
- `Cache-Control`;
- `ETag`;
- `Server`;
- clasificación de tipo y negociación.

Semántica deliberada: **REPORT_ONLY**. Falta de Brotli o ausencia de compresión no son por sí mismas un fallo de CI; un fallo de observación sí lo es.

### `.github/workflows/live-compression-origin-audit.yml`

- ejecuta el auditor cuando cambia su contrato;
- permite `workflow_dispatch`;
- usa Node 22;
- sube siempre `artifacts/compression/live-compression-origin.json` como `live-compression-origin-report`;
- no modifica hosting, proxy, DNS ni headers.

## 4. Primera observación live reproducible

Workflow: `Live compression origin audit`  
Run: `33371081813`  
HEAD: `a4fda2cfa799cc762a41b8d5e1e8b39df608ebdf`  
Resultado: `success`  
Artefacto: `live-compression-origin-report` · ID `9750073305`  
Digest: `sha256:92e4503391b115ede0b738763221420e846cf561552d65cf0c4a547eb8333b5f`

Resumen machine-readable:

```text
9 observaciones
9 success
0 fallos de observación
6 respuestas textuales con negociación de compresión
6/6 comprimidas
6/6 con Vary: Accept-Encoding
```

## 5. Resultado por recurso

### HOME HTML

Con `br, gzip`:

```text
200
server: GitHub.com
content-encoding: gzip
vary: Accept-Encoding
content-type: text/html; charset=utf-8
content-length: 12037
```

Con `gzip`: mismo resultado gzip.

Con `identity`:

```text
content-encoding: (ausente)
vary: Accept-Encoding
content-length: 49344
```

Reducción observada de longitud de representación al negociar gzip frente a identity: aproximadamente **75,6 %**.

### `assets/v1-shell.css`

Con `br, gzip` y con `gzip`:

```text
content-encoding: gzip
vary: Accept-Encoding
content-type: text/css; charset=utf-8
content-length: 170
```

Con `identity`:

```text
content-encoding: (ausente)
content-length: 503
```

Reducción observada: aproximadamente **66,2 %**.

### `script.js`

Con `br, gzip` y con `gzip`:

```text
content-encoding: gzip
vary: Accept-Encoding
content-type: application/javascript; charset=utf-8
content-length: 8526
```

Con `identity`:

```text
content-encoding: (ausente)
content-length: 25194
```

Reducción observada: aproximadamente **66,2 %**.

## 6. Interpretación

La producción actual sí comprime las tres clases textuales comprobadas y negocia correctamente la variante cacheable mediante `Vary: Accept-Encoding`.

Cuando el cliente anuncia `br, gzip`, el servidor GitHub Pages observado elige **gzip**, no Brotli. Esto no se clasifica automáticamente como defecto:

- gzip está activo en HTML/CSS/JS relevantes;
- la reducción observada es material;
- la respuesta identifica `server: GitHub.com`;
- no existe evidencia de que una migración/proxy solo para obtener Brotli compense su coste, complejidad y superficie operativa;
- E.7 no autoriza activar Cloudflare proxy, añadir Workers de compresión ni migrar hosting para perseguir un encoding concreto.

Por tanto el resultado operativo es **NO_ACTION sobre infraestructura mientras no exista evidencia cuantificada de un cuello de botella real atribuible a gzip**.

## 7. Qué queda gobernado

E.7 deja ahora una capacidad reproducible para volver a comprobar la negociación si cambia hosting/origen o aparece una regresión de serving.

Una futura revalidación debe distinguir:

- `gzip`/`br`/otro encoding presente y `Vary` correcto → observar y comparar, no cambiar por checklist;
- texto relevante sin compresión → reproducir, identificar ownership y cuantificar impacto;
- respuesta `identity` pese a aceptar compresión → investigar si el asset/tamaño/hosting lo justifica;
- cambio de infraestructura → volver a ejecutar esta auditoría antes/después.

## 8. No hacer

- activar proxy naranja de Cloudflare solo para E.7;
- añadir Worker de compresión por defecto;
- migrar hosting por un supuesto ahorro no medido;
- versionar `.br`/`.gz` sin garantía de negociación del servidor;
- tratar Brotli como requisito universal de calidad;
- confundir el resultado de GitHub Pages con una configuración versionada dentro del repo;
- convertir ausencia futura de un encoding concreto en hard fail sin owner estable.

## 9. Taxonomía de verdad

```text
DOCUMENTED = true
IMPLEMENTED_IN_PR(E.7) = true
LIVE_OBSERVATION = true
ORIGIN_SERVER_OBSERVED = GitHub.com
HTML_GZIP = verified
CSS_GZIP = verified
JS_GZIP = verified
VARY_ACCEPT_ENCODING = verified
BROTLI_SELECTED_FOR_BR_GZIP_REQUEST = false
INFRA_CHANGE_AUTHORIZED = false
MERGED_MAIN = false
```

## 10. Estado para integración

La auditoría que faltaba queda implementada y ejecutada con evidencia live. El hallazgo no justifica un cambio de infraestructura: producción ya comprime el contenido textual representativo con gzip y declara correctamente `Vary: Accept-Encoding`.

Antes de merge, revisar código/workflow y CI del HEAD final. Mantener DRAFT; no mergear automáticamente desde esta conversación.
