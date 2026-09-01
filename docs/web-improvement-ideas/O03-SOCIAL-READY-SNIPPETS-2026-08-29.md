# O.3 · Extractos “listos para redes” dentro de cada artículo

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `REJECT`.

## Veredicto

#135 terminó rechazando la idea de insertar al final de cada artículo bloques promocionales preformateados para copiar/pegar en redes. El beneficio es bajo frente al coste editorial, la repetición y el riesgo de convertir el Cuaderno en una superficie de promoción constante.

La alternativa válida es generar social copy **fuera del contenido público**, como parte del workflow editorial/Metricool, usando citas reales del artículo y revisión humana.

## Hipótesis original

Añadir al final de cada artículo un fragmento breve ya preparado para compartir, reduciendo la fricción de republicación social.

## Evolución

### Revisión

La revisión detectó que el patrón podía añadir ruido y copy duplicado.

### Matriz → `PILOTAR COMO WORKFLOW`

La matriz rescató la parte útil:

> extraer citas/social copy desde contenido; no meter bloques de relleno “tweet this” en cada artículo.

### Autoridad final → `REJECT`

La autoridad final cerró:

> no añadir bloques públicos “listos para tuitear” como relleno. Social copy puede generarse como workflow editorial externo.

### Revalidación independiente

O.1–O.4 se mantienen.

## Qué se rechaza exactamente

- componente fijo al final de cada artículo;
- texto promocional repetitivo;
- bloques indexables que no aportan al lector;
- “tweet this” como patrón visual obligado;
- generación automática sin revisión;
- CTA social en todas las piezas por sistema.

## Qué sí es válido

En la capa editorial externa:

```text
article canonical
candidate quote
platform
copy variant
utm/source
status = DRAFT | APPROVED | SCHEDULED | PUBLISHED
```

El copy puede derivarse de frases reales, pero debe revisarse para:

- no sacar citas de contexto;
- no inventar claims;
- no romper derechos/embargos;
- no repetir exactamente el mismo mensaje en todas las redes;
- adaptar longitud/formato al canal.

## Relación con D.10

D.10 rechazó igualmente el botón flotante para compartir texto seleccionado. Ambas decisiones siguen la misma regla: no introducir UI de sharing invasiva sin necesidad demostrada.

## Relación con O.4

O.4 es la vía correcta para reutilizar evergreen: programación editorial en Metricool u otra herramienta ya autorizada. O.3 no necesita convertirse en HTML para alimentar O.4.

## Relación con C.2/C.3

Piezas originales de proceso o respuestas a lectores pueden generar buenos snippets, pero el snippet es un derivado de distribución, no una sección obligatoria del contenido.

## Riesgos

- contenido promocional duplicado;
- degradación del tono editorial;
- mantenimiento de copy obsoleto;
- fragmentos que sobreviven a una edición del artículo;
- incentivo a escribir para redes en vez de para el lector;
- UI añadida sin mejora de lectura.

## Qué NO hacer

- `<blockquote class="tweet-this">` en todos los artículos;
- botones “copiar para X/Twitter” sitewide;
- hashtags hardcoded que envejecen;
- snippets generados por IA publicados sin revisión;
- guardar variants sociales en la misma fuente de verdad del artículo si no son contenido canónico.

## Trazabilidad

- backlog original O.3;
- revisión 108/108;
- matriz `PILOTAR COMO WORKFLOW`;
- autoridad final `REJECT`;
- revalidación independiente.

## Recomendación

No implementar O.3 en la web. Cuando una pieza merezca promoción, generar y revisar sus snippets en la capa editorial/Metricool.