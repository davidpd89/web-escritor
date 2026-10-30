# Encargo: importación validada y transaccional del mapa de personajes

Estado: **BORRADOR, SIN IMPLEMENTAR**. Prioridad P1: pérdida de trabajo en memoria.
Base examinada: `85a335e8309b10f10961f58029810f7c50e3dbc6`.

## Fallo confirmado

`assets/mapa-personajes-core.js`, `parseProject()`, solo hace JSON.parse y llama
a `normalizeProject()`. El normalizador tolerante convierte objetos ajenos y
arrays en un proyecto vacío. Tampoco rechaza una versión desconocida.
`assets/mapa-personajes.js`, handler de `#import-file`, asigna ese resultado a
`project`, borra posiciones, renderiza y anuncia éxito sin validar el contrato.

Comprobación de función real en memoria:

```text
parseProject('{"unrelated":"data"}') -> version:1, characters:[], relations:[]
parseProject('[]') -> version:1, characters:[], relations:[]
parseProject('{"version":999,"characters":[{"id":"a","name":"Ana"}],"relations":[]}')
  -> version:1, characters:[Ana], relations:[]
```

Reproducción en producción con Chromium y archivos sintéticos en memoria:
1. Abrir `/herramientas/personajes/` e importar un proyecto v1 con Ana y Bruno
   y una relación amistad entre ellos.
2. Contador: `2 personajes · 1 relación · más conectado: Ana (1)`.
3. Abrir un JSON distinto: `{"unrelated":"not a character map"}`.
4. Contador: `0 personajes · 0 relaciones`; estado: `Mapa importado.`.

La herramienta no ha guardado un respaldo del proyecto reemplazado. La prueba
solo usó estado efímero del navegador; no se enviaron datos ni se alteró producción.
No se afirma que el fichero original en disco se borre.

## Encargo a la IA implementadora

- Separar validación de fichero externo de normalización interna tolerante.
- Definir versión/esquema admitidos y compatibilidad explícita con exportaciones
  anteriores; no aceptar silenciosamente una versión futura como v1.
- Validar tipos, personajes, IDs y referencias antes de sustituir el estado.
- Si se rechaza, conservar proyecto, título, relaciones, posiciones y filtros;
  explicar el motivo de forma accesible. No convertir errores en mapas vacíos.
- Para reparaciones que descartan relaciones o truncan texto, elegir rechazo o
  advertencia/confirmación; nunca éxito silencioso con datos perdidos.
- Conservar la posibilidad de abrir un mapa vacío legítimo del esquema admitido.
- Mantener contenido como texto; no introducir HTML ejecutable desde JSON.

## Cobertura y aceptación

`tests/test-mapa-personajes-core.mjs` solo comprueba roundtrip válido y normalización
de referencias. `qa/tools-structure-browser.mjs` prueba JSON sintácticamente roto,
pero no un JSON válido de otro tipo con un mapa existente.

- [ ] Regresión roja del escenario anterior, sin persistir datos reales.
- [ ] Objeto ajeno, array, campos mal tipados y versión desconocida no borran el mapa.
- [ ] Importación admitida y exportar/reimportar preservan datos.
- [ ] Prueba browser conserva estado anterior y anuncia error comprensible.
- [ ] Caso de mapa vacío válido separado de importación inválida.
- [ ] Tests, CSP, cache busting/hashes y paridad vigentes antes de deploy.
- [ ] Evidencia antes/después, CI y comprobación del SHA desplegado.

Continuar esta misma rama con la solución. No fusionar el documento como arreglo.
El encargo de exportación SVG es independiente: no ampliar este cambio a diseño
ni a estilos de exportación; coordinar si ambas IAs editan el mismo módulo.