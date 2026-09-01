# D.10 · Revalidación de producción — compartir texto seleccionado

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **REJECT · EXPLICIT_SHARE_ALREADY_SOLVES_TASK · NO_SELECTION_LAYER · NO_CODE**.

## 1. Resultado

D.10 sigue rechazada. La web ya ofrece una acción de compartir deliberada y accesible en artículos; no existe una fricción demostrada que justifique acoplar una toolbar al motor de selección del navegador.

## 2. Evidencia directa

`assets/v1-editorial.js` gestiona los controles `[data-share-url]` de forma progresiva:

1. el artículo sigue completo sin JavaScript;
2. el botón se activa cuando el enhancement está disponible;
3. usa `navigator.share({ title, url })` cuando existe;
4. si no puede compartir, intenta `navigator.clipboard.writeText(url)`;
5. comunica `Compartido.`, `Enlace copiado.` o `No se pudo copiar el enlace.` en la región de estado asociada;
6. un `AbortError` de Web Share se interpreta como cancelación, no como fallo que haya que castigar.

El patrón actual resuelve la tarea real:

```text
quiero compartir esta pieza
→ acción explícita
→ share nativo o copiar URL
→ feedback perceptible
```

## 3. Lo que D.10 añadiría innecesariamente

La propuesta histórica era distinta:

```text
seleccionar texto
→ detectar rango
→ posicionar UI flotante
→ decidir longitud/contexto/atribución
→ resolver mouse/touch/keyboard/zoom/reflow
→ compartir cita
```

Eso multiplica estados sin sustituir una necesidad actualmente mal resuelta.

## 4. Fragmentos literarios y contexto

La existencia de fragmentos públicos no convierte cualquier rango seleccionado en unidad promocional autorizada o útil. Una selección puede:

- cortar una frase a mitad;
- perder contexto;
- incluir varias secciones;
- ser demasiado larga;
- incluir texto que el usuario seleccionó con otra intención.

No se automatiza la transformación de selección en cita social.

## 5. Gate extraordinario de reapertura

Solo reconsiderar si existe evidencia repetida de que los lectores quieren compartir **citas concretas**, no simplemente la URL, y si un piloto está editorialmente delimitado.

El piloto debería empezar por citas explícitamente seleccionadas por el autor, no por una toolbar global de `selectionchange`.

## 6. Qué no hacer

- no listener global de selección;
- no popover flotante sitewide;
- no tracking del texto seleccionado;
- no crear imágenes dinámicas de una selección arbitraria;
- no mantener destinos sociales propios cuando Web Share cubre el caso;
- no añadir librería de posicionamiento;
- no tratar shares como SEO;
- no reemplazar el patrón actual estable.

## 7. Definition of Done

- [x] share actual inspeccionado directamente;
- [x] Web Share + clipboard fallback verificados;
- [x] estados de éxito/error identificados;
- [x] tarea actual diferenciada de share-selection;
- [x] rechazo histórico revalidado con la solución de producción;
- [x] sin runtime nuevo.

## Estado para Claude

Mantener D.10 rechazada. El share explícito actual ya resuelve la tarea con menos coste y mejor equivalencia entre dispositivos; no añadir una capa contextual de selección sin un caso de uso nuevo demostrado.