# P.1 · Exportar resultados de herramientas — reconstrucción completa desde PR #135

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: snapshot `8e72321d047c0445c5ac411ebe242af8a0386929` de PR #135.  
Estado final histórico: `CONDITIONAL`.

## 1. Hipótesis original

La idea P.1 proponía permitir que las herramientas de `/herramientas/` exportasen su resultado a PDF o imagen compartible, buscando aumentar utilidad fuera de la página y compartibilidad.

La hipótesis inicial era razonable como mejora de producto, pero demasiado amplia: no todos los resultados tienen valor fuera del navegador y un export universal podía introducir dependencias de PDF/canvas, peso JS, problemas de accesibilidad y riesgo de subir texto privado a un servidor.

## 2. Evolución dentro de #135

### Revisión exhaustiva 27/08

Decisión: `CONDITIONAL`.

La revisión redujo el alcance a 1–2 herramientas donde el resultado sea realmente útil fuera de la página. Condiciones explícitas:

- export client-side;
- nunca subir manuscritos para fabricar PDF/imagen;
- no convertir el export en feature transversal por checklist.

### Matriz final intermedia 28/08

Decisión: `PILOTAR SELECTIVO`.

Se añadió una preferencia técnica importante: antes de incorporar librerías PDF pesadas, usar capacidades nativas y formatos simples —print stylesheet, descarga de texto/HTML/Markdown/JSON/ICS/ZIP cuando encajen— y medir si el formato adicional resuelve una necesidad real.

### Autoridad final humana + machine-readable

Estado final: `CONDITIONAL`.

Regla final:

> Export solo donde el resultado tenga valor fuera de la página; preferir print/download nativo antes que PDF libs pesadas.

No existe autorización para añadir export global a todas las herramientas.

## 3. Revalidación independiente y pasadas posteriores

La revalidación independiente mantiene P.1 sin corrección material de estado. No aparece en las pasadas tardías ninguna evidencia que convierta el export universal en prioridad ni que justifique introducir un servicio externo.

La regla privacy-first de las herramientas privadas refuerza la decisión: el texto/manuscrito no debe salir del navegador para generar un archivo.

## 4. Evidencia actual de `main`

`data/tools-hub.json` muestra que el ecosistema ya tiene múltiples herramientas con resultados de naturaleza distinta. Además, existen precedentes selectivos de exportación:

- generador de kit de prensa → ZIP;
- tarjeta «Estoy leyendo» → HTML/Markdown portable;
- generador de eventos → `.ics`;
- preparador de entrevista familiar → salida imprimible;
- otras herramientas trabajan con texto/manuscritos locales y no necesitan export adicional por defecto.

Esto demuestra que el patrón correcto ya es **exportar solo cuando el artefacto final forma parte del trabajo de la herramienta**.

`data/private-tools-privacy-manifest.json` exige para herramientas de manuscrito:

- análisis en navegador;
- ningún envío del manuscrito al servidor;
- sin terceros;
- sin conexiones programáticas de red;
- sin almacenamiento persistente del manuscrito.

Por tanto un futuro export debe respetar ese contrato.

## 5. Decisión efectiva para revisión futura

Mantener `CONDITIONAL`.

No crear:

- botón “Exportar PDF” sitewide;
- librería PDF global cargada en todas las herramientas;
- servicio cloud de render;
- subida temporal del manuscrito;
- imagen rasterizada si un HTML/Markdown/print stylesheet conserva mejor accesibilidad.

Sí puede pilotarse cuando una herramienta concreta cumpla todos estos triggers:

1. el resultado tiene valor después de abandonar la página;
2. existe un caso real de guardar, imprimir, entregar o compartir;
3. el formato elegido conserva legibilidad y accesibilidad;
4. puede generarse localmente;
5. el coste de bytes/mantenimiento es proporcional;
6. no rompe el contrato de privacidad de herramientas sensibles.

## 6. Escalera de implementación preferida

Por orden de menor coste/riesgo:

1. copiar al portapapeles;
2. descarga de texto/Markdown/JSON/CSV/ICS según semántica;
3. HTML imprimible + `@media print`;
4. Blob/download local;
5. ZIP si el producto exige varios archivos;
6. PDF client-side solo si los pasos anteriores no satisfacen el uso;
7. imagen/canvas únicamente cuando la naturaleza visual lo requiera.

Nunca usar un backend para procesar manuscritos solo para obtener un PDF.

## 7. QA / Definition of Done si se activa

- export funciona sin red después de cargar la herramienta;
- ningún contenido introducido aparece en requests;
- CSP de herramientas privadas se mantiene;
- archivo tiene nombre determinista y extensión correcta;
- caracteres españoles/Unicode se preservan;
- salida accesible o existe alternativa textual equivalente;
- funciona con teclado y 200% de texto;
- no introduce CLS ni una dependencia global;
- se prueba con contenido vacío, largo y caracteres especiales;
- se documenta por qué ese formato aporta valor fuera de la página.

## 8. Relaciones con otras ideas

- **P.2:** no usar persistencia local como requisito del export.
- **P.4:** un resultado exportable puede enlazar a contenido relacionado, pero son problemas separados.
- **E.5:** una librería pesada de PDF debe entrar en presupuestos de artifact.
- **I.5:** no introducir datos persistentes o terceros sin inventario.

## 9. Conclusión

P.1 no significa «añadir exportación a todas las herramientas». #135 terminó correctamente en `CONDITIONAL`: el sitio ya demuestra que los exports selectivos funcionan cuando son parte natural del producto. La implementación futura debe ser herramienta por herramienta, local-first y con el formato más simple que resuelva el trabajo real.