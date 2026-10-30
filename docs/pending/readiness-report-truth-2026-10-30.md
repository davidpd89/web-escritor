# Encargo: informe de preflight sin certificación contradictoria

Estado: **PENDIENTE DE IMPLEMENTACIÓN — PR EN BORRADOR**.
Prioridad: P2, exactitud de evidencia de release; no es un bypass del gate.
Base examinada: `85a335e8309b10f10961f58029810f7c50e3dbc6`.

## Hallazgo reproducido

En `scripts/release-readiness.py`, `build_report()` calcula correctamente
`summary = 'STATIC_CHECKS_PASSED' if failures == 0 else 'BLOCKED'`, pero añade
incondicionalmente esta frase bajo el estado:

> Este informe certifica el estado STATIC_CHECKS_PASSED.

Por tanto, un informe que detecta fallos se titula `Status: BLOCKED` y, debajo,
afirma certificar éxito. El código de salida sigue siendo 1: **no se ha
demostrado que CI permita publicar un fallo**. El defecto afecta al documento
que leen humanos y otras IAs, no al exit code.

## Reproducción segura realizada

Se importó el módulo real y se llamó a `build_report()` con:

- `CHECKS = [('synthetic failing check', 'python bad.py')]` mediante mock.
- `run()` devolviendo `(1, 'synthetic failure')`, sin ejecutar ese comando.
- `ROUTE_CHECKS = []` y `git_output()` simulado.
- Informe de salida dentro de `TemporaryDirectory`, no dentro del repositorio.

Resultado literal:

```text
REPORT exit = 1
REPORT BLOCKED = True
REPORT also asserts certification = True
```

No se modificaron comprobaciones reales ni documentos de release existentes.

## Encargo a la IA implementadora

- Añadir regresión para informes con check fallido, ruta faltante y todo correcto.
- Hacer que la explicación concuerde con el estado calculado. En `BLOCKED`, no
  afirmar certificación de éxito y resumir qué bloquea la validación.
- Conservar la distinción entre preflight estático, gates de CI y producción
  verificada; ningún resultado local debe presentarse como autorización de deploy.
- Mantener códigos de salida, comandos, inventario de rutas e identidad del SHA.
- Revisar si otros resúmenes consumen este documento y necesitan expectativas
  actualizadas. No arreglarlo sustituyendo a mano los informes generados.

## Archivos de partida y aceptación

- `scripts/release-readiness.py`, `build_report()` y `main()`.
- `tests/test-release-readiness-interpreter.py` y referencias a release-readiness
  en pruebas y workflows; crear regresión enfocada si no existe una adecuada.

- [ ] Evidencia roja del texto contradictorio antes del cambio.
- [ ] Check fallido: estado bloqueado, código no cero y sin certificación positiva.
- [ ] Ruta requerida faltante: mismo resultado, fallo identificado.
- [ ] Todo correcto: `STATIC_CHECKS_PASSED`, código cero y límites explícitos.
- [ ] Ningún mock modifica archivos reales ni requiere servicios externos.
- [ ] CI y consumidores del informe siguen funcionando sin relajar validaciones.
- [ ] Registrar resultados antes/después antes de marcar la PR como lista.

Esta PR solo prepara el encargo. Otra IA implementa, prueba y gestiona su entrega
en esta misma rama. No fusionar este documento como si solucionara el defecto.