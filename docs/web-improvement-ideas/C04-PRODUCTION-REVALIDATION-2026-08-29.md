# C.4 · Revalidación de producción — extractos imprimibles / descargables

Fecha: 2026-08-29  
Base inspeccionada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #179

## Veredicto final

**CONDITIONAL · HTML_CANONICAL_EXISTS · RIGHTS_NOT_VERIFIED_FOR_DOWNLOAD · NO_PDF · NO_CODE**

La necesidad original ya está cubierta en su parte esencial por una única superficie HTML pública: `/las-manecillas-del-recuerdo/fragmentos/`, con tres fragmentos aprobados, canonical propio, navegación interna y structured data que identifica la muestra y sus tres piezas.

No se ha demostrado una necesidad actual de distribuir ese mismo contenido como PDF/EPUB/archivo independiente, ni se ha localizado una autorización explícita que amplíe el uso público actual a una descarga redistribuible. Por ello C.4 no debe convertir automáticamente una muestra web en un nuevo artefacto.

## 1. Superficie existente verificada

La URL actual:

`https://davidportodiaz.com/las-manecillas-del-recuerdo/fragmentos/`

expone:

- canonical propio;
- tres fragmentos con IDs `#fragmento-1`, `#fragmento-2`, `#fragmento-3`;
- `WebPage` + `Collection` + tres `CreativeWork`;
- `isAccessibleForFree:true` para la muestra;
- portada y metadata del libro;
- navegación entre fragmentos y regreso a la ficha.

Conclusión: **no falta una superficie de muestra**.

## 2. Estado de impresión

Se inspeccionaron directamente:

- `las-manecillas-del-recuerdo/fragmentos/index.html`;
- `assets/v1-base.css`;
- `assets/v1-book.css`;
- `assets/v1-fragments.css`.

La hoja local `v1-fragments.css` gobierna índice/pager/lectura responsive y no contiene un modo de impresión dedicado. Las capas base/book inspeccionadas tampoco introducen en sus reglas observadas una experiencia específica para la impresión de esta muestra.

Esto **no basta para implementar**. C.4 exige además una necesidad real. El navegador ya permite imprimir una página aunque no exista una UI específica; añadir un diseño print solo debe hacerse cuando haya un caso de uso que justifique decidir qué elementos conservar/ocultar y mantener ese contrato.

Trigger preferente si aparece esa necesidad:

`print need → mejorar CSS de la URL HTML existente → probar salida → solo después considerar archivo separado`

## 3. Derechos / clearance

Se revisó Drive mediante búsquedas específicas de derechos/fragmentos/descarga y materiales de Manecillas.

Se localizó `28_MANECILLAS_FRAGMENTOS_POSTS_Y_PAGINAS_2026-08-16.md`, que:

- identifica los tres pasajes contra la maqueta;
- fija cortes y riesgo de spoilers;
- autoriza/proyecta usos concretos como página de fragmentos, newsletter y piezas sociales dentro del plan editorial.

No se localizó en esa revisión una autorización explícita para convertir la muestra en PDF/EPUB descargable o permitir redistribución autónoma del archivo.

Estado correcto: **RIGHTS_NOT_VERIFIED_FOR_DOWNLOAD**.

No equivale a afirmar que el contrato lo prohíbe; significa que C.4 no dispone de evidencia para afirmar que lo permite.

## 4. PDF no es una mejora SEO automática

Google Search Central mantiene la canonicalización como mecanismo para agrupar contenido duplicado o muy similar:

- https://developers.google.com/search/docs/crawling-indexing/canonicalization
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls

Si en el futuro se publica un PDF con el mismo contenido que el HTML, el elemento HTML `<link rel="canonical">` no puede insertarse dentro del PDF. Google documenta el encabezado HTTP `Link: <URL>; rel="canonical"` como mecanismo aplicable a documentos no HTML, incluidos PDF.

Por tanto, una futura descarga necesita como mínimo:

- propósito de usuario/distribución claro;
- rights/clearance verificable;
- owner de mantenimiento;
- estrategia de indexación/canonical HTTP;
- versión/fecha coherente;
- accesibilidad razonable;
- QA de que no compite accidentalmente con el HTML canónico.

## 5. Accesibilidad

La versión HTML sigue siendo la vía principal porque ya participa en los QA del sitio y puede adaptarse a viewport, tamaño de texto y navegación.

Un PDF futuro no debe rebajar ese nivel mediante:

- páginas escaneadas como imagen;
- texto no seleccionable sin motivo;
- orden de lectura defectuoso;
- ausencia de idioma/títulos;
- enlaces sin semántica;
- contraste/tamaño insuficiente.

El PDF sería un complemento, no sustituto de la página accesible.

## 6. No crear un nuevo evento analytics ahora

La taxonomía actual ya mide consumo de muestra con:

- `leer-fragmento-manecillas`;
- `sample-start-manecillas`;
- `sample-complete-manecillas`.

No existe una necesidad de negocio demostrada para medir `download_excerpt` porque no existe descarga. No reservar nombres de evento para features inexistentes.

Si se activa una descarga real, el evento debe registrarse primero en la autoridad analytics existente, no emitirse ad hoc.

## 7. Triggers exactos

### Activar print CSS

Solo cuando exista necesidad real de impresión/uso offline y se defina la salida esperada. Entonces:

1. conservar contenido literario + título/autor/contexto mínimo;
2. ocultar navegación/dialog/newsletter/CTAs no útiles en papel;
3. evitar cortes pobres dentro de bloques;
4. mantener URL/fuente visibles de forma razonable;
5. probar navegador y tamaño de papel objetivo.

### Activar archivo descargable

Solo si se cumplen simultáneamente:

```text
rights verified
AND user/distribution need verified
AND HTML remains canonical source
AND HTTP canonical/index strategy defined
AND accessibility acceptable
AND maintenance owner assigned
```

## 8. Qué no hacer

- crear un PDF porque “parece más profesional”;
- duplicar los tres fragmentos en varias URLs;
- abrir `?print=1` indexable;
- usar un archivo como lead magnet fingidamente exclusivo cuando el texto ya es público;
- inferir permisos de redistribución por el hecho de que la página web esté autorizada;
- meter el PDF en sitemap sin una estrategia;
- añadir tracking antes de existir la feature;
- reemplazar el HTML por el PDF.

## 9. Definition of Done de C.4

- [x] reconstrucción histórica preservada;
- [x] página HTML de tres fragmentos verificada directamente;
- [x] canonical/structured data/IDs verificados;
- [x] CSS local/base/book inspeccionado;
- [x] materiales de fragmentos en Drive contrastados;
- [x] ausencia de clearance explícito para descarga tratada como `not verified`, no como prohibición inventada;
- [x] canonicalización PDF revalidada con Google 2026;
- [x] trigger de print CSS separado del trigger de archivo descargable;
- [x] sin PDF, URL o evento analytics inventado;
- [ ] CI del HEAD final verde;
- [ ] revisión de Claude antes de merge.

## Estado para revisión

**CONDITIONAL · HTML_CANONICAL_EXISTS · RIGHTS_NOT_VERIFIED_FOR_DOWNLOAD · NO_PDF · NO_CODE**

No hay una mejora obligatoria que ejecutar hoy. Si aparece una necesidad real de impresión, el primer paso técnico es mejorar la misma URL HTML; un archivo separado queda detrás de un gate adicional de derechos, accesibilidad, canonicalización y mantenimiento.
