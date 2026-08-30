# E.7 · Revalidación de producción — compresión HTTP del origen

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **PARTIAL_AUDIT · CLOUDFLARE_DNS_ONLY_DOES_NOT_ANSWER_ORIGIN_ENCODING · LIVE_HEADER_NOT_OBSERVED · NO_INFRA_CHANGE**.

## 1. Resolución de la contradicción histórica

Se conserva la secuencia de #135:

- la autoridad final/machine-readable llegó a `NOT_APPLICABLE` porque Cloudflare estaba DNS-only;
- la revalidación independiente corrigió el estado efectivo a `PARTIAL_AUDIT` porque DNS-only solo demuestra que Cloudflare edge no gobierna la respuesta, no qué compresión aplica el hosting/origen real.

La segunda es la interpretación operativa vigente.

## 2. Qué debe verificarse

La pregunta no es «¿Cloudflare tiene Brotli activado?», sino:

> ¿Qué `Content-Encoding` recibe realmente un cliente para HTML/CSS/JS textuales cuando anuncia `Accept-Encoding`?

La documentación HTTP vigente confirma que `Accept-Encoding` negocia los encodings aceptados y el servidor comunica la elección mediante `Content-Encoding`; cuando se cachean variantes negociadas, `Vary: Accept-Encoding` evita servir una representación equivocada.

Fuentes consultadas el 30/08/2026:
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Compression
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-Encoding
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Encoding

## 3. Verificación live en esta revalidación

Se volvió a intentar una petición directa desde el runtime de trabajo:

```text
curl -sSIL --compressed https://davidportodiaz.com/
→ Could not resolve host: davidportodiaz.com
```

Por tanto este entorno sigue sin poder observar de forma fiable los headers live.

No se afirma:

- Brotli activo;
- Zstd activo;
- gzip únicamente;
- respuesta sin compresión.

Cualquiera de esas frases sería evidencia inventada.

## 4. Auditoría mínima futura

Desde una red normal comprobar al menos:

```bash
curl -sSI -H 'Accept-Encoding: br, zstd, gzip' https://davidportodiaz.com/
curl -sSI -H 'Accept-Encoding: br, zstd, gzip' https://davidportodiaz.com/assets/v1-base.css
curl -sSI -H 'Accept-Encoding: br, zstd, gzip' https://davidportodiaz.com/assets/v1-shell.js
```

Registrar `Content-Type`, `Content-Encoding`, `Vary`, status y cualquier header útil para identificar el origen efectivo.

## 5. Decisión según resultado

- `br`/`zstd` correcto: documentar y cerrar sin cambio.
- `gzip`: no tratarlo automáticamente como fallo; cuantificar diferencia y coste de cambiar infraestructura.
- sin compresión en texto relevante: confirmar varias veces, identificar el origen y buscar la solución mínima en ese hosting.

## 6. No hacer

- activar proxy naranja de Cloudflare solo para E.7;
- añadir Worker de compresión por defecto;
- migrar hosting por un supuesto ahorro no medido;
- versionar `.br`/`.gz` sin garantía de que el servidor negocie correctamente;
- declarar `CONFIGURED_LIVE` desde datos de repo.

## 7. Estado para integración

No hay cambio de infraestructura ni código. E.7 queda como live-check pendiente y bien delimitado; el bloqueo es de observabilidad del entorno, no una deuda demostrada de la aplicación.