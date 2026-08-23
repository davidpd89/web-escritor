# WEB 2026 — HANDOFF VIVO: AUTORIDAD Y PROTOCOLO

> Este fichero es deliberadamente **corto y estable**. No intenta copiar el estado vivo de GitHub ni mantener una cola manual de PR, porque eso se vuelve falso en cuanto otra sesión abre, cierra o integra trabajo.
>
> La versión extensa anterior se conserva íntegra, como fotografía histórica, en `docs/archive/WEB-2026-HANDOFF-REMAINING-WORK-2026-08-22.md`.

## 0. Qué manda realmente

La autoridad operativa, en este orden, es:

1. HEAD **actual** de `origin/implementacion-web-2026`;
2. **todas** las PR abiertas cuyo `base` sea `implementacion-web-2026`;
3. CI/QA ejecutado sobre el SHA concreto que se está evaluando;
4. código, builders, fuentes de datos y tests presentes en ese SHA;
5. documentación de Drive/repo como especificación, contexto e historial, nunca como sustituto de 1–4.

Un SHA, una lista de PR o un «siguiente orden» escritos en un documento son siempre un **snapshot fechado**, no estado vivo.

Snapshot de procedencia de esta corrección: PR #74 nació desde `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`. No reutilizar ese SHA como base fija.

## 1. Antes de decidir qué sigue

Ejecutar siempre:

```bash
git fetch origin --prune
git switch implementacion-web-2026
git pull --ff-only origin implementacion-web-2026
git status
git rev-parse HEAD
```

Y, además, consultar GitHub para enumerar **todas** las PR abiertas con base `implementacion-web-2026`.

Si el worktree no está limpio:

- no `reset --hard`;
- no borrar archivos;
- no descartar trabajo automáticamente;
- detener esa vía de escritura y explicar qué cambios locales existen.

## 2. Cómo interpretar cualquier tarea antigua

Antes de programar, clasificarla contra HEAD + PR abiertas como una de:

- `HECHO`;
- `YA DETECTADO`;
- `DEUDA NUEVA`;
- `PARCIAL`;
- `GATED`;
- `SUPERADO`;
- `OUT OF SCOPE`.

Reglas:

- que exista una URL, script o documento con nombre parecido **no demuestra** cumplimiento funcional;
- que Drive diga `ADOPTAR`, `P0`, `P1`, `pendiente`, `código preparado` o `COMPLETADO` **no demuestra** el estado actual;
- si una PR abierta ya posee la deuda, ampliar/comentar/reutilizar esa PR; no abrir un duplicado;
- si una decisión posterior sustituyó el contrato histórico, documentar la sustitución en vez de implementar literalmente una receta antigua;
- una feature gated por contenido, fecha, licencia, proveedor o decisión humana no se «completa» inventando datos.

## 3. Protocolo de implementación

Una deuda independiente = una rama/PR coherente, salvo que ya tenga owner abierto.

Para cada cambio:

1. partir del HEAD actual de `implementacion-web-2026`;
2. localizar ownership real: fuente → template/builder → output → tests/workflow;
3. reproducir el problema o demostrar el gap contractual;
4. implementar solo el scope;
5. ejecutar QA real;
6. revisar el diff completo;
7. abrir/actualizar PR contra `implementacion-web-2026`;
8. mantenerla `DRAFT` mientras queden bugs/gates de scope;
9. no integrar la propia PR automáticamente.

No apilar una tarea nueva sobre una PR sin integrar salvo que exista una razón explícita y documentada.

## 4. Estados de QA

Usar lenguaje verificable:

- `PASS`: ejecutado y correcto;
- `FAIL`: ejecutado y falla;
- `NO HECHO`: no se ejecutó;
- `INCOMPLETO`: comenzó pero no terminó.

No inferir `PASS` por inspección estática ni por un check verde que no haya ejecutado realmente el contrato.

No «arreglar» el gate para esconder el producto: no bajar Lighthouse, a11y, CSP, seguridad ni tolerancias sin evidencia.

## 5. Invariantes del proyecto

- No tocar `main` salvo autorización humana explícita.
- No desplegar producción salvo autorización humana explícita.
- No activar auto-merge.
- GitHub Pages publica desde `main`: promover la rama de integración a `main` es una decisión de release.
- Preservar la dirección visual V1 y la topología editorial ya cerrada salvo scope explícito.
- Preservar accesibilidad, no-JS, responsive, reduced motion, canonical/robots/schema y facts editoriales cuando no sean el scope.
- Fuente antes que output generado; builders reproducibles e idempotentes.
- No borrar assets/contenido por ausencia de referencias sin evidencia y decisión correspondiente.
- Metricool y la operativa/publicación social están **OUT OF SCOPE** del proyecto web. Las referencias históricas pueden conservarse como investigación, pero no abren tareas de publicación.

## 6. Herramientas externas

Prioridad:

1. conector/API/CLI autorizado;
2. navegador solo cuando no exista una vía programática usable para la acción concreta.

Brevo y Cloudflare: API-first.

Search Console: navegador solo si no hay API/connector autorizado usable para esa acción concreta.

No enviar emails, cambiar automatizaciones externas ni desplegar Workers de producción sin autorización específica.

## 7. Qué hacer con la documentación histórica

La documentación extensa anterior sigue siendo útil para:

- decisiones visuales/editoriales;
- causas de bugs ya encontrados;
- contratos de QA;
- contexto de builders y arquitectura;
- razonamiento de por qué ciertas soluciones se rechazaron.

Pero sus frases como «SIGUIENTE», «ACTIVA», «la única PR viva», «ninguna rama abierta», números de rutas, tamaños, HEAD o listas de blockers deben leerse únicamente como **snapshot histórico**.

Cuando una afirmación histórica choque con GitHub vivo, manda GitHub vivo.

## 8. Auditoría documental GPT

La auditoría estricta de `pendiente funcionalidad gpt.txt` quedó cerrada hasta su EOF real, línea 1969.

No existe un bloque 1970–2000.

Los briefs/owners resultantes están registrados en las PR y en `docs/PENDIENTE-*-GPT-*.md`. Antes de reutilizarlos, volver a consultar su estado actual; un brief abierto no implica que siga pendiente y uno cerrado no demuestra por sí solo que su resultado esté integrado en el HEAD que estés mirando.

## 9. PR #1 — staging hacia `main`

La PR #1 debe permanecer `DRAFT / DO NOT MERGE` hasta revisión humana final.

Su body tampoco es un tracker permanente: antes de plantear release hay que volver a:

1. obtener HEAD final de `implementacion-web-2026`;
2. enumerar todas las PR abiertas aplicables;
3. resolver/integrar/descartar explícitamente cada una;
4. regenerar la evidencia de release desde ese HEAD;
5. comprobar CI y QA reales del SHA final;
6. revisar el diff completo `main...implementacion-web-2026`;
7. ejecutar los gates de staging/post-deploy aplicables;
8. requerir decisión humana explícita para mergear.

Un informe de readiness de un SHA anterior nunca autoriza el merge de otro SHA.

## 10. Definition of Done para cualquier bloque

Un bloque solo puede considerarse cerrado cuando:

- se leyó su contrato vigente completo;
- cada requisito tiene evidencia o una sustitución explícita;
- la implementación cumple comportamiento, no solo naming/rutas;
- tests relevantes se ejecutaron;
- browser QA se hizo cuando aplica;
- privacidad/analytics/CSP coinciden con el comportamiento real;
- builders no regeneran una versión anterior;
- navegación/sitemap/hub se integraron cuando el contrato los exige;
- gates humanos/externos pendientes están declarados como `GATED`, no maquillados como `PASS`;
- el resultado y los comandos/evidencias quedan registrados en la PR.

## 11. Handoff a otra sesión/agente

No copiar una lista manual de «lo siguiente» desde este fichero.

El handoff correcto es:

1. leer este protocolo;
2. refrescar HEAD y PR abiertas;
3. inspeccionar los owners abiertos y su diff/estado real;
4. elegir la primera deuda independiente no cubierta que siga siendo aplicable;
5. continuar desde ahí sin reabrir investigación cerrada.

Si no existe deuda aplicable después del refresco, el siguiente paso no es inventar trabajo: es preparar/repetir la evidencia de revisión o release que corresponda al HEAD real.
