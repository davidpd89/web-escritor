# D.2 · Revalidación de producción — modo lectura dedicado

Fecha: 2026-08-30  
Base comprobada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.

## Veredicto

**REJECT · BASE_READING_QA_STRONG · NATIVE_CAPABILITIES_PREFERRED · NO_CODE**

La revalidación no encuentra una necesidad que justifique crear un Reader Mode propio. La experiencia editorial base ya tiene una matriz de QA suficientemente amplia como para que los problemas de lectura se corrijan en la página canónica, no mediante un segundo modo.

## Evidencia directa del repo

`.github/workflows/cuaderno-browser-qa.yml` valida el Cuaderno y artículos representativos con:

- navegador real headless;
- WCAG2AA/Pa11y;
- Lighthouse;
- outputs generados;
- presupuesto de CLS;
- múltiples superficies editoriales.

`qa/cuaderno-browser.mjs` mantiene además escenarios explícitos para:

- responsive;
- teclado;
- zoom;
- Text Spacing;
- no-JS;
- reduced motion;
- share;
- impresión;
- canonical/schema/enlaces/imágenes;
- overflow y CLS.

Los viewports de esa suite cubren 320, 390, 768, 1024, 1440, 1728 y landscape estrecho.

## Implicación

Si una pieza larga falla en:

- ancho de línea;
- interlineado;
- jerarquía;
- foco;
- reflow;
- zoom;
- sticky UI;
- reduced motion;

el defecto pertenece al sistema editorial base y debe corregirse allí.

Crear un Reader Mode escondería ese fallo y duplicaría estados, CSS, impresión, imágenes, anchors, navegación y QA.

## Capacidades nativas

La web debe conservar HTML semántico y una composición suficientemente limpia para convivir con:

- zoom del navegador;
- preferencias del sistema;
- tecnologías de asistencia;
- modos de lectura nativos cuando el navegador los ofrezca.

No se crea una copia paralela de los artículos para perseguir una uniformidad que ya puede resolverse sobre la URL canónica.

## Gate extraordinario

D.2 solo se reabriría con investigación real que demuestre simultáneamente:

```text
necesidad repetida de lectores
AND experiencia base no puede resolverla
AND browsers objetivo no cubren el caso
AND solución no duplica contenido/URLs
AND owner de QA para estados adicionales
AND beneficio medido > coste
```

No se reabre por tendencia estética ni por la mera existencia de Reader Mode en otros productos.

## Decisión final

La evidencia actual refuerza el rechazo histórico. El sitio ya invierte en robustez de lectura base; esa es la autoridad correcta.

**Estado final: `REJECT · BASE_READING_QA_STRONG · NATIVE_CAPABILITIES_PREFERRED · NO_CODE`.**
