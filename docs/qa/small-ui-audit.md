# Auditoría ligera de huecos de interfaz

Complementa las pruebas de navegador existentes con siete familias de controles
offline sobre el HTML público versionado. No necesita servicios, claves,
dependencias nuevas ni llamadas a modelos.

1. Desplegables nativos: un único `summary`, primero y con nombre legible.
2. Selectores: valores no vacíos duplicados y varias opciones `selected` en
   selectores de elección única. Se respetan grupos desactivados y etiquetas
   `option` con cierre omitido.
3. Listas de sugerencias: `input[list]` debe apuntar a un `datalist` real.
4. Descargas: archivo local versionado, ruta sensible a mayúsculas incluso en
   Windows, y advertencia cuando `download` apunta a otro origen. Los destinos
   `blob:` y `data:` se reconocen como descargas generadas.
5. Entradas numéricas: mínimo superior al máximo y pasos no positivos.
6. Asociación de formularios: `form=` debe apuntar a un elemento `form` real.
7. JSON de `assets/` y `data/`: claves duplicadas —también mediante escapes—,
   errores de sintaxis y tokens `NaN`/`Infinity` que Python acepta por defecto
   pero no son JSON válido para el navegador. No imprime valores de los datos.

## Ejecución

```sh
python tests/test-small-ui-audit.py
python scripts/audit-small-ui-contracts.py
```

La segunda orden genera `.ci/small-ui-audit/results.json` y `report.md` y termina
con código 1 si encuentra incidencias. El workflow **Small UI gaps audit
(advisory)** se ejecuta en PR pertinentes, los lunes a las 07:17 UTC y de forma
manual. Conserva el informe durante 30 días y lo muestra en el resumen de la
ejecución, también si falla. No oculta hallazgos con `continue-on-error` ni cambia
los controles obligatorios de publicación. Las pruebas del propio auditor sí
entran en el bucle universal existente de `tests/test-*.py`.

## Primera medición: 22/10/2026

Sobre `72ab6be7`, con 32 pruebas del auditor aprobadas:

| Cobertura | Cantidad |
| --- | ---: |
| Páginas HTML | 348 |
| Desplegables | 320 |
| Selectores | 36 |
| Descargas | 5 |
| Entradas numéricas | 6 |
| Referencias explícitas a formularios | 2 |
| Listas de sugerencias | 0 |
| Fuentes JSON | 42 |
| Hallazgos | 0 |

Cero listas de sugerencias significa que esa regla no encuentra componentes
reales que comprobar todavía; sus casos positivos y negativos están probados
con fixtures. Los contadores permiten distinguir ausencia de uso de cobertura
real. Cero hallazgos no demuestra que toda la web esté libre de errores.

El análisis es de fuente: no ejecuta controles creados o modificados por JS, no
calcula estilos ni sustituye pruebas de teclado, lectores de pantalla o red.
Los futuros hallazgos deben revisarse en contexto; los cambios de producto se
pueden abordar por separado sin modificar umbrales ni silenciar las reglas.
