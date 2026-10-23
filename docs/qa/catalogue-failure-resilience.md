# Catálogo: fallos controlados de red y JavaScript

Complemento de `reading-commerce-browser.mjs`, que comprueba reglas de precios y
valoraciones, y de `reading-type-selector-browser.mjs`, que prueba el selector de
tipos. Las suites generales de sesión/entrega de scripts no incluían esta ruta.
Este lote cubre específicamente la dependencia opcional `reading-market.json` y
el estado que introduce el lector mientras su respuesta aún está pendiente.

## Casos

Cada escenario se ejecuta con un contexto nuevo en 390 y 1280 píxeles:

1. La conexión al JSON comercial falla.
2. El endpoint devuelve HTTP 503.
3. Responde 200 con JSON truncado.
4. Responde con estructura incompatible (`offers: null`, `ratings: {}`).
5. La respuesta válida y vacía llega después de filtrar.
6. No se puede descargar `reading-catalogue.js`.

Se sirven el HTML y los recursos reales del repositorio en un servidor local.
No se modifican libros ni datos publicados. Cada fallo inyectado se comprueba:
un cambio de URL que deje de interceptar la petición causa un fallo de la
prueba, no un aprobado sin cobertura. No se consulta Amazon ni Goodreads.

Para los cinco casos comerciales, se busca un ISBN real y se cambia el orden
antes de liberar la respuesta. Se comprueban los resultados, los valores de los
controles, el hash compartible, el parámetro de origen y una recarga completa.
No deben aparecer precios o estrellas inventados ni filtros de precio activos.
En la caída del script, todas las fichas deben permanecer visibles y los
controles que no pueden funcionar deben permanecer desactivados. En todos los
casos se conservan enlaces de compra y afiliación y no hay errores JS sin capturar.
El PVP editorial existente se conserva, porque es independiente de las ofertas
comerciales opcionales. Con conexión fallida se comprueba además restablecer
filtros y pasar a la segunda página cuando existe.

## Ejecutar y analizar

```sh
python -m http.server 4175 --bind 127.0.0.1
# En otra terminal, desde la raíz del mismo checkout:
node qa/reading-failure-resilience-browser.mjs
```

Se puede usar otro servidor con `QA_BASE_URL`. El resultado está en
`.ci/reading-resilience/results.json` y `report.md`, con modo, tamaño, commit,
URL y error. Los casos fallidos añaden captura completa y resultados visibles.
Se ejecutan todos los casos aunque uno falle. Código de salida 1 significa que
al menos un escenario falló; no se silencia con `continue-on-error`.

El workflow informativo se ejecuta en PR pertinentes, cambios pertinentes de
main, cada miércoles a las 07:41 UTC y manualmente. Conserva los informes durante
30 días incluso si falla. No modifica los checks obligatorios ni cambia producto.

Los servicios externos se bloquean deliberadamente para evitar que una caída de
analítica falsee esta prueba de la dependencia comercial local. Esto no verifica
la disponibilidad real de proveedores, lectores de pantalla ni otros motores.
Los casos se sincronizan con la petición retenida y el fin de la actividad de
red, sin esperas fijas para adivinar cuándo respondió el proveedor.

## Validación inicial, 22/10/2026

Los doce escenarios pasan en local sobre los 55 libros de `72ab6be7`. Un control
negativo separado sirvió una variante en memoria que lanzaba un error en vez de
recuperarse del fallo del fetch comercial: los cuatro casos de conexión y JSON
truncado detectaron ese error, con informes y capturas. No se guardó ni publicó
esa variante como código del sitio. Un resultado negativo inducido no se
presenta como fallo del producto actual.
