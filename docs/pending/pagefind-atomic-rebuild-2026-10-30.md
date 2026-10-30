# Encargo: conservar el índice Pagefind si falla su reconstrucción

Estado: **PENDIENTE DE IMPLEMENTACIÓN — PR EN BORRADOR**.
Prioridad: P1 de mantenimiento; no es una caída confirmada de producción.
Base examinada: `85a335e8309b10f10961f58029810f7c50e3dbc6`.

## Qué se ha demostrado

`scripts/build-pagefind-index.py`, `run_pagefind()` (líneas 173–189), ejecuta
`shutil.rmtree(out_dir)` antes de lanzar `npx --no-install pagefind`.
Si falta la dependencia o falla el proceso, desaparece la salida anterior.
`build()` (líneas 249–257) solo limpia `src_dir` en su `finally`; no recupera
la salida y no llega a escribir el manifiesto.

En la auditoría anterior ocurrió realmente al reconstruir sin Pagefind instalado:
el proceso falló y faltó `pagefind/pagefind.js` hasta instalar el lockfile y
reconstruir. No se publicó ese estado.

Confirmación adicional del 30/10, aislada del repositorio:

1. Directorio temporal de salida con `sentinel.txt = last good index`.
2. Invocar la función real `run_pagefind(src, output)` parcheando únicamente
   `subprocess.run` para lanzar `CalledProcessError(1, ['npx'])`.
3. Capturar la excepción y consultar el centinela.

Resultado literal: `PAGEFIND failure: previous output preserved = False`.
No se ejecutó npx, no se borró el índice real y no se cambió código funcional.

## Encargo a la IA implementadora

- Reproducir primero con una prueba de regresión sobre temporales.
- Generar la nueva salida en un directorio temporal hermano y validarla,
  incluyendo manifiesto e integridad, antes de sustituir el índice anterior.
- Diseñar promoción/rollback seguro en Windows y Linux. No asumir que renombrar
  sobre un directorio no vacío funciona igual en ambos sistemas.
- Ante fallo de subprocess, manifiesto o validación, conservar byte a byte la
  salida anterior y devolver error. No silenciarlo ni declarar éxito con datos viejos.
- Limpiar temporales propios; nunca borrar rutas ajenas ni ampliar la allowlist pública.
- Mantener CLI, política de publicación, corpus, etiquetas y normalización CRLF/LF.
- Considerar invocaciones concurrentes: impedir que una limpie la salida de otra,
  o documentar una exclusión explícita y comprobarla.

## Archivos de partida

- `scripts/build-pagefind-index.py`.
- `tests/test-build-pagefind-index.py`.
- `tests/test-pagefind-artifact-corruption.py` y pruebas de manifiesto/source hashes.
- `qa/` de buscador/findability y contrato del artefacto público.

Los hashes de texto ya normalizan CRLF/LF: no confundirlo con una incidencia nueva.
No atribuir otros incidentes históricos a esta causa sin correlación.

## Criterios de aceptación y evidencia requerida

- [ ] Prueba roja que reproduzca la pérdida de salida con subprocess fallido.
- [ ] Dependencia ausente, proceso fallido, salida incompleta y fallo de manifiesto
      dejan intacto el índice anterior y retornan fallo.
- [ ] Reconstrucción correcta promueve salida y manifiesto coherentes; `--check` pasa.
- [ ] Sin temporales huérfanos ni rutas de trabajo dentro del artefacto publicado.
- [ ] Pruebas existentes y de búsqueda pasan en CI; validar semántica Windows.
- [ ] Probar búsqueda real de una consulta conocida en la vista previa y tras deploy.
- [ ] Registrar SHA y evidencia antes/después; solo fusionar y desplegar tras gates verdes.

## Estado de esta PR

Contiene solo el encargo. No implementa, prueba extensamente, fusiona ni despliega
la solución. No marcar lista ni fusionar este borrador como si el problema estuviera
resuelto. La IA implementadora debe continuar en esta misma rama y añadir el código.