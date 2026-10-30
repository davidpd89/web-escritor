# Auditoría de mantenimiento — 30/10/2026

Base examinada: `c63bf1eede0e133e43de1c0c7b78952fccad3177`.
Actualización local por fast-forward desde una rama obsoleta sin cambios locales.
`main` está protegido; publicación mediante PR y Pages.

## Hallazgos corregidos

1. El gate universal ejecutaba 318 archivos Python `test-*.py`, pero omitía 225
   archivos `test_*.py`. Añadida su carga por unittest en los dos workflows
   generales, con regresión de cobertura y revisión de funciones anidadas.
2. El preflight usaba `python` de PATH, distinto del entorno que lo había
   iniciado. Ahora usa `sys.executable`, argumentos separados y sin shell.
   Reproducción anterior: falso bloqueo por Pillow 12.2 frente al pin 12.3.
3. El lector social publicado difería del que validaban las pruebas y podía
   aceptar una observación antigua con una expiración plausible. Sincronizados
   los módulos; la regresión prueba explícitamente ambas copias.
4. `tasklist` localizado rompía el bloqueo de instancia única en Windows con
   Python UTF-8. Lectura binaria, PID exacto en CSV y fallo conservador si el
   sistema no puede determinar su estado. Sin cambiar programaciones ni proveedores.
5. Dos pruebas sociales dependían de la fecha real o del snapshot vivo. Ahora
   usan datos y reloj deterministas, sin relajar las reglas de caducidad.
6. La confirmación del popup borraba su título/descripción ARIA y todos los
   botones, con cierre automático a los cinco segundos. Conserva referencias,
   cierre por teclado, foco en el resultado y tiempo de lectura libre.
   Prueba Playwright con suscripción simulada integrada en CI.
7. README e inventario pendiente describían una web inicial y donaciones aún
   inactivas. Actualizados según implementación actual.

## Evidencia y límites

- Regresiones del lector público, intérprete y popup reproducidas en rojo antes del arreglo.
- 99 archivos Node de motores/contratos: sin fallos tras las correcciones.
- Suite omitida: 740 pruebas unittest, sin fallos (16 exclusiones declaradas).
- 319 archivos Python con guion: 318 pasaron en el barrido; el restante, de
   integridad de Pagefind, pasó tras regenerar el buscador con el lockfile vigente.
- Preflight: `STATIC_CHECKS_PASSED` tras corregir el intérprete.
- Paridad de shell (439 páginas), sitemap (432 URLs) y versiones/hashes comprobadas.
- Newsletter: flujos inline, portada, Explore, popup inválido y confirmación
   probados en Chromium; confirmación también en Edge. Sin envío real a Brevo.
- Artefacto de 1371 archivos construido y verificado por la allowlist pública.
- La evidencia final de CI/despliegue corresponde al SHA de la PR, no al preflight local.

No se garantiza ausencia total de errores ni se simulan pagos, entregabilidad de
correo o pruebas físicas en iOS. Los avisos npm transitivos de desarrollo siguen
inventariados; no son dependencias enviadas al navegador y no se ha forzado una
actualización incompatible de Lighthouse. La revisión editorial del Atlas sigue
requiriendo al titular. No se han alterado bots ni tareas programadas.