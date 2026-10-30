# Encargo: preservar URLs en el calendario del generador de eventos

Estado: **IMPLEMENTADO** (2026-10-30). P2: paridad de exportaciones/interoperabilidad.
Base: `c369f933e52073604adc2972f902191289992e08`.

## Reproducción sin red

Se llamó a `buildEventOutputs()` de `assets/evento-escritor-core.js` con un evento
confirmado, día completo 2026-11-02, lugar/dirección sintéticos y esta URL válida:

```text
https://example.com/eventos/uno,dos;sesion?x=a,b
```

El JSON-LD conserva la URL original. La propiedad URL del ICS, tras desplegar
líneas CRLF+espacio, produce:

```text
URL:https://example.com/eventos/uno\,dos\;sesion?x=a\,b
```

`buildIcs()` usa `escapeIcs(model.url)`, función de escape de valores TEXT que
añade barras a comas/punto y coma. Pero URL tiene tipo URI, no TEXT.
RFC 5545 §3.3.13 y §3.8.4.6 establecen la sintaxis URI, sin ese escape adicional:
https://www.rfc-editor.org/rfc/rfc5545#section-3.3.13

Se consultó la norma y se ejecutó el módulo real en memoria. No se ha importado
el archivo en Outlook/Google/Apple: su tolerancia concreta queda por probar.
No afirmar fallo universal de clientes ni que todos los calendarios publicados
estén afectados; el caso confirmado es la salida de este generador con esos caracteres.

## Encargo a la IA implementadora

- Separar serialización URI y TEXT: preservar URL del evento sin backslashes
  indebidos, manteniendo escape de SUMMARY, DESCRIPTION y LOCATION.
- Conservar plegado de 75 octetos, UTF-8 y CRLF; no quitar el plegado para arreglar la URL.
- Validar/rechazar controles y saltos de línea que puedan inyectar propiedades;
  no sustituir el escape actual por interpolación de entrada sin validar.
- Definir normalización URI coherente con HTML/JSON-LD y mantener query/fragment.
- Revisar usos de escapeIcs para propiedades URI equivalentes sin ampliación indiscriminada.

## Aceptación y pruebas

- [ ] Regresión roja del ejemplo con coma/punto y coma en path/query.
- [ ] URL leída por parser independiente coincide con el destino de HTML/JSON-LD.
- [ ] Parámetros percent-encoded, fragmentos y URL larga plegada conservan destino.
- [ ] TEXT con comas, punto y coma, barras y saltos sigue haciendo roundtrip correcto.
- [ ] Controles/inyección CRLF rechazados, sin propiedades VEVENT adicionales.
- [ ] Pruebas existentes `tests/test-evento-ics-rfc5545.mjs`,
      `tests/test-evento-escritor-core.mjs` y roundtrip independiente pasan.
- [ ] Validar archivo desde el botón real; clientes de calendario si disponibles,
      declarando explícitamente los no probados.
- [ ] Versionado/hashes, CI y SHA desplegado comprobados antes de cerrar.

Esta PR solo prepara el encargo para otra IA. Continuar aquí con implementación,
tests y publicación; no fusionar documentación como si resolviera el defecto.

## Implementación

- `assets/evento-escritor-core.js`: `URL:` se serializa con `icsUri()` (URI, sin
  escape TEXT) a partir de la misma URL recortada que usa el JSON-LD. SUMMARY,
  DESCRIPTION y LOCATION mantienen `escapeIcs`. El plegado a 75 octetos no cambia.
- `isHttps()` rechaza controles y espacios internos: `new URL()` los eliminaba en
  silencio, de modo que `https://x/a
ATTENDEE:...` se daba por válida. Afecta
  también a las URL del organizador y de la imagen, que usan el mismo validador.
- Regresiones: `tests/test-evento-ics-rfc5545.mjs` (coma/punto y coma en path y
  query, percent-encoding, fragmento, URL larga plegada, TEXT con roundtrip, CRLF,
  tabulador, espacio y NUL rechazados), roja con el código anterior. QA del botón
  real en `qa/tools-events-memory-browser.mjs`.
- No verificado: importación en Outlook, Google Calendar y Apple Calendar.
