# Encargo: URL del catálogo coherente con la página realmente mostrada

Estado: **BORRADOR, SIN IMPLEMENTAR**. Prioridad P3: coherencia de enlaces/estado.
Base examinada: `c369f933e52073604adc2972f902191289992e08`.

## Reproducción confirmada en producción

Abrir `/recomendaciones/#pagina=99` con JS y esperar carga completa. Chromium,
service worker bloqueado y peticiones fuera del origen bloqueadas:

```text
hash: #pagina=99
count: 88 libros · página 4 de 4
nav: ← ANTERIOR / Página 4 de 4 / SIGUIENTE →
```

El runtime evita un resultado vacío al limitar correctamente la página al máximo,
pero no refleja esa normalización en la URL inicial. No es una caída del catálogo,
un error de canonical SEO ni una vulnerabilidad: es estado compartible ambiguo.
La URL obsoleta puede volver a indicar otra página si crece el catálogo.

## Causa localizada

En `assets/reading-catalogue.js`, `restore()` lee pagina y llama a `apply(false)`.
`apply()` limita `currentPage` al número real de páginas, pero solo serializa la
URL cuando `save=true`. La restauración y actualizaciones de datos conservan por
ello una página fuera de rango en el hash hasta otra interacción del usuario.

## Encargo a la IA implementadora

- Definir normalización canónica del estado cliente para páginas no existentes.
- Tras limitar la página, actualizar el hash sin recargar ni añadir entradas
  innecesarias al historial, preservando filtros válidos y parámetros de búsqueda.
- Mantener selección visible, paginación, contador y URL en el mismo estado.
- Tratar explícitamente vacíos, negativos, valores no numéricos/extremos y
  cambios del número de coincidencias tras filtros/datos.
- Evitar bucles hashchange/restore o perder parámetros repetidos de facetas.
- No modificar el canonical SEO ni indexación por un hash de interacción.

## Aceptación y pruebas

- [ ] Regresión roja del deep link reproducido y prueba de restauración normalizada.
- [ ] Casos página 1, válida intermedia, última y fuera de rango.
- [ ] Cero resultados y páginas que disminuyen al filtrar o refrescar datos.
- [ ] URL sigue representando filtros múltiples; recargar reproduce la misma vista.
- [ ] Botones Anterior/Siguiente, foco y navegación por historial sin regresiones.
- [ ] Sin JS permanece disponible el catálogo estático.
- [ ] Versionado/hashes, índice y tests afectados al día antes del deploy.
- [ ] Evidencia antes/después y comprobación del SHA desplegado.

Buscar QA y pruebas de catálogo/paginación existentes para ampliar un recorrido
real; no validar únicamente cadenas del código. No confundir esta ruta con
`/recomendaciones/autores/`, que no es el caso reproducido.

Esta PR solo prepara el encargo para otra IA. Continuar aquí con implementación,
pruebas y publicación; no fusionar documentación como solución terminada.