# C.4 · Extractos descargables / imprimibles ampliados

Fecha de reconstrucción: 2026-08-29  
Fuente: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado final: `CONDITIONAL`.

## Veredicto

La idea solo avanza con **derechos explícitos y una necesidad de distribución real**. #135 rechazó tratar «PDF descargable» como mejora automática. Para el mismo texto, preferir una URL canónica accesible + CSS de impresión antes que crear versiones indexables duplicadas.

## Hipótesis original

Extender el patrón de versión imprimible visto en recomendaciones a capítulos de muestra de las obras propias.

## Evolución

### Revisión → `CONDITIONAL`

- depende de derechos;
- puede crear duplicación;
- preferir canonical + print CSS antes de otro documento indexable.

### Matriz → `CONDICIONAL AL DERECHO`

La matriz concreta:

- solo si contrato/editorial permite;
- no canibalizar lead magnet;
- mismo texto canónico, no múltiples páginas duplicadas.

### Autoridad final → `CONDITIONAL`

> «Fragmentos/printables únicamente con derechos y sin duplicar URLs canónicas ni promesas de lead magnet.»

### Revalidación independiente

Estado mantenido.

## Derechos primero

Antes de publicar cualquier descarga:

- confirmar quién controla derechos digitales/de muestra;
- alcance de la autorización;
- territorio/formato si aplica;
- si se permite redistribución/descarga;
- si el fragmento ya tiene versión aprobada;
- si existe obligación de retirada/actualización.

No deducir que ser autor equivale automáticamente a poder distribuir cualquier versión contractual del texto.

## Arquitectura preferida

### Caso A · Solo necesidad de imprimir

Mantener la URL HTML canónica y añadir/usar `@media print`.

Ventajas:

- una única fuente editorial;
- menos drift;
- mejor accesibilidad web;
- no duplica señales/indexación;
- cambios se reflejan en la misma URL.

### Caso B · Archivo descargable realmente necesario

Puede existir PDF/EPUB/otro asset cuando haya caso de uso y derechos. Debe quedar claro:

- URL canónica del contenido;
- versión/fecha;
- accesibilidad del archivo;
- relación con la versión web;
- política de indexación adecuada;
- retirada cuando quede obsoleto.

## Estado de Manecillas relevante

`CONTENT-PARITY-MANECILLAS-V1.md` documenta tres fragmentos públicos aprobados con IDs canónicos y QA de navegación/deep links. C.4 no autoriza a duplicarlos en PDFs por defecto.

La misma documentación mantiene otros materiales/descargas bajo gates de derechos y clearance. Ese patrón debe conservarse.

## Lead magnets

No afirmar «descarga exclusiva» o «capítulo gratis por email» si:

- el fragmento ya es público;
- no existe la automatización real;
- derechos no permiten ese uso;
- el journey de entrega no está verificado.

C.4 no redefine H/email ni los gates del newsletter.

## SEO/indexación

Evitar:

- HTML y PDF compitiendo por el mismo texto sin intención;
- múltiples URLs imprimibles indexables;
- query `?print=1` indexable;
- canonicals inconsistentes;
- sitemaps con duplicados;
- `dateModified` artificial por regenerar PDF.

## Accesibilidad

Si se publica un PDF:

- estructura/tagging razonable;
- orden de lectura;
- idioma;
- títulos/enlaces identificables;
- contraste y tamaño;
- texto seleccionable cuando proceda;
- no depender de una imagen escaneada del capítulo.

Si no puede mantenerse accesible, la versión HTML debe seguir siendo la vía principal.

## Analytics/privacidad

Medir descargas solo si responde una pregunta real. No añadir tracker nuevo para C.4. Reutilizar taxonomía actual si existe un evento aprobado.

## Qué NO hacer

- generar PDFs porque «parece profesional»;
- inventar derechos;
- duplicar todos los fragmentos;
- crear una URL SEO por cada formato;
- usar descarga como dark pattern de email;
- publicar manuscritos/borradores no autorizados;
- mantener versiones desincronizadas;
- degradar accesibilidad respecto al HTML.

## Trigger válido

```text
rights verified
AND user/distribution need
AND canonical strategy clear
AND maintenance owner
AND accessible delivery
```

## Pasadas posteriores revisadas

Cuarta–decimoquinta: ninguna cambia C.4. Las políticas de publicación, privacidad, media y factualidad refuerzan sus gates, pero no convierten la idea en obligatoria.

## Trazabilidad

- idea original;
- revisión `CONDITIONAL`;
- matriz `CONDICIONAL AL DERECHO`;
- evidencia de fragmentos/gates Manecillas;
- autoridad final `CONDITIONAL`;
- revalidación independiente.

## Recomendación

Mantener C.4 en espera hasta un caso real. Si la necesidad es «imprimir», resolver primero con CSS print sobre la URL canónica. Solo crear descarga separada cuando derechos y experiencia de usuario lo justifiquen.