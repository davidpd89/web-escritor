# E5 · Integración sin segundos publicadores (22/10/2026)

**Solo investigación / PR #692 en DRAFT. No se ha ejecutado ni integrado este código.** Fuente única del índice: [#691](https://github.com/davidpd89/web-escritor/pull/691). Dependencia funcional inmediata: [#687](https://github.com/davidpd89/web-escritor/pull/687) (todavía abierta al redactar este informe).

## 1. Diagnóstico contra código real, no suposiciones

| Ubicación revisada | Comportamiento actual | Consecuencia para la integración |
|---|---|---|
| [`.github/workflows/reading-catalogue-sync.yml`](https://github.com/davidpd89/web-escritor/blob/main/.github/workflows/reading-catalogue-sync.yml) | Programado 06:30 **UTC**, `workflow_dispatch` y `concurrency.group=reading-catalogue-intake`, `cancel-in-progress=false`; ejecución condicionada por `vars.READING_INTAKE_ENABLED` | No crear segundo cron ni asumir que el job está habilitado solo por el JSON. Verificar el estado de esa variable al integrar |
| [`scripts/refresh-reading-catalogue.py`](https://github.com/davidpd89/web-escritor/blob/main/scripts/refresh-reading-catalogue.py) | Reanuda o inspecciona la única PR `automation/reading-catalogue-*`; corre controles de libros y actualiza mercado; solo crea PR con cambios de tipos conocidos | Las mejoras de **contactos por sí solas no disparan una PR**; no forzar un ISBN artificial para hacerlo |
| [`scripts/publish-reading-refresh.py` en #687](https://github.com/davidpd89/web-escritor/blob/data/carga-sellos-pendientes/scripts/publish-reading-refresh.py) | Lista permitida incluye `data/reading-publishers.json` y páginas `/recomendaciones/editoriales/`; **no** `data/editoriales.json` | Buen límite de seguridad. NO abrir automáticamente la allowlist a cambios del estado de manuscritos |
| [`scripts/reading_intake_pipeline.py` en #687](https://github.com/davidpd89/web-escritor/blob/data/carga-sellos-pendientes/scripts/reading_intake_pipeline.py) | Fuente Penguin verifica ISBN/sello; los sellos que faltan crean ficha bibliográfica separada con fuente | Mantener la creación bibliográfica de sellos en #687. No activar enriquecimiento de contactos como efecto secundario |
| [`scripts/publish-radar-refresh.py`](https://github.com/davidpd89/web-escritor/blob/main/scripts/publish-radar-refresh.py) | El bot despacha CI real, valida SHA y reglas de `main` y fusiona el contenido generado | Un cambio editorial con contacto **no** debe llegar a esta ruta automática sin revisión humana previa |

**Cuidado adicional sobre concurrencia:** [GitHub Actions documenta `queue: max`](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency), introducido en mayo de 2026: permite hasta 100 ejecuciones pendientes; con `cancel-in-progress=false` actual, por defecto solo puede quedar una ejecución pendiente y las nuevas la sustituyen. **No activar `queue: max` de forma automática:** para un job diario de 135 minutos podría acumular trabajos obsoletos. La PR bot pendiente y el bloqueo Actions solucionan problemas distintos; revisar necesidad antes de cambiar YAML.

## 2. Diseño concreto acordado: dos carriles, un solo orquestador

```text
Semillas admitidas (ISBN/sello #687; Wikidata CC0 opcional)
   │
   ▼
Identidad + procedencia  ──►  Ambigua/histórica/no verificada ──► cola humana
   │
   ├── CARRIL A: bibliografía verificada (ISBN+fuente+licencia)
   │     └── publicador actual de libros → PR de artefactos permitidos
   │          → CI real de SHA → reglas de main → Pages
   │
   └── CARRIL B: contacto/recepción (prueba explícita y actual)
         └── observación sin correo en cola de revisión
               → aprobación humana por campo y entidad
               → PR humana separada de datos editoriales + HTML generado
               → CI de main; merge MANUAL sujeto a revisión
               → regeneración determinista mediante builders existentes
```

«Un solo orquestador» **no** significa publicar sin permiso datos variables; no crear procesos paralelos ni desbloquear el autoboletín de libros para `data/editoriales.json`. El carril B podrá usar el mismo horario **solo como etapa de descubrimiento y reporte**, no como auto-merge. La PR de revisión humana puede crearse **solo después de preparar una propuesta acotada**, comprobada por el autor/revisor; el **primer piloto** debe terminar en JSON de artefacto/issue de revisión, sin crear PR automática.

## 3. E5 — Módulo preparado en esta PR, no ejecutado

`scripts/research/gpt_editoriales_review_plan.py` recibe tres JSON **del mismo día**: directorio original `data/editoriales.json` y **salidas**, no simples entradas, de E3 (`gpt_editoriales_reconcile.py`) y E4 (`gpt_editoriales_contact_evidence.py`). No contacta webs ni modifica disco; devuelve JSON ordenado, estable y con huellas de tareas reproducibles. Ninguna tarea declara autorización de publicación.

Criterios del plan:
- **Sin libros relacionados:** ficha de sello no activa una nueva indexación (se difiere).
- **Colisión de nombre/slug o Bruguera histórico:** conflicto de identidad; no normalizar como la empresa actual.
- **Declaración por grupo (PRH, Planeta):** **no** heredar `open` a todos los sellos.
- **Declaración expresa reciente por sello y fuente oficial:** proponer revisión de `open/closed` si difiere del directorio, pero **no aplicarlo** sin aprobación.
- **Afirmaciones contradictorias o caducadas:** llevar a revisión, conservar la situación anterior hasta que se verifique, pero mostrar «última comprobación» y «estado por verificar» cuando no haya evidencia reciente. «Sin página/contacto» no significa `closed`.
- **Directorio antiguo:** añadir revalidación, sin modificar su `status`. Umbral provisional 45 días para estado conocido y 90 para `unknown`; se calibrará con volumen real.
- **Enlaces rotos/identidades repetidas:** impedir que un integrador posterior se apoye en el plan para publicar; las propuestas son para corregir datos fuente.
- **Presupuesto del piloto:** `http_requests_budget=0` en el módulo. Integración futura: máximo **5 webs/ejecución**, un mismo presupuesto total compartido con ingesta de libros y cache, no 5 peticiones adicionales sin límite. Parar por 429/403, respetar robots, errores 5xx y `Retry-After`. Registrar tasa de bloqueo y cancelación, no reintentar sistemáticamente sitios restringidos.

**Control de fuentes:** [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html) establece el estándar `robots.txt`, incluido *fail closed* cuando está inalcanzable; cumplir además términos de uso, límites y permiso de reutilización. Robots no equivale a permiso legal de copia. Excluir rutas autenticadas y cualquier extracción de datos privados o personales.

### Archivos de E5

- `scripts/research/gpt_editoriales_review_plan.py` — productor **offline** de tareas con IDs deterministas, prioridades y límites, sin red, credenciales, correos, escritura ni GitHub CLI.
- `tests/test_gpt_editoriales_review_plan.py` — **21 pruebas sintéticas escritas y no ejecutadas**: colisiones, evidencia caducada, estado de grupo, idempotencia, coste cero, errores de datos, cola limitada y privacidad.

El estudio completo #692 suma **57 pruebas escritas y no ejecutadas** entre cuatro módulos (11 conciliación + 10 Wikidata + 15 contactos + 21 plan). Se desconoce si pasan; ninguna afirmación de «apto para merge».

## 4. Qué NO se debe hacer en esta fase

1. Añadir `data/editoriales.json` a `allowed_path` del autocommit de libros: abre cambios no revisados a la fusión automática.
2. Crear un cron nuevo para contactos o habilitar procesamiento de feeds ISBN sin autorización de sus titulares.
3. Reescribir `#687` antes de su merge: cambia 683 ficheros y ya tiene su propio recorrido de validación. La integración real ha de hacerse desde un `main` actualizado, con PR específica de ingeniería.
4. Permitir que Wikidata P856 o un correo general implique recepción de manuscritos; heredar estados entre grupo y sello.
5. Usar `[skip ci]` en la eventual PR productiva: aquí solo es válido en investigación; la integración deberá **ejecutar** pruebas y controles exigidos.

## 5. Pendientes con criterio de cierre y siguiente paso E6

**E5 concluida como diseño + código experimental, sin ejecutar.** Los pendientes de mayor valor son:
- **E6.1, revisión del plan E5:** comparar la salida del conciliador y del clasificador con una misma instantánea de #687 y fechas concordantes; revisar compatibilidad de esquemas/errores, especialmente datos desactualizados y fuentes sin licencia.
- **E6.2, política de publicación del carril B:** definir un formato de aprobación manual por campo, diffs precisos `status/source/date`, revocación/expiración sin afirmar lo contrario y tests que impidan auto-merge.
- **E6.3, piloto controlado:** medir propuestas aceptadas, fuentes rotas, duplicados, riesgos de privacidad y tiempo de revisión con un máximo de 5 webs autorizadas. No activar proveedores ni Actions desde la PR de investigación.
- **E6.4, PR de integración** (aparte) únicamente cuando #687 sea parte de `main`, haya QA real y autorización de fuente. Antes, mantener #692 DRAFT y proponer al revisor del sitio solo las decisiones verificadas.

**Próximo «siguiente investigación de GPT»:** continuar aquí con **E6.1 y E6.2**, no abrir una quinta rama para lo mismo.
