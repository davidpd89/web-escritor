# Material heredado de la PR #819 (conservado como evidencia, no forma parte del motor)

Estos documentos son de la fase documental de la #819 (24/10/2026). El motor que los sustituye esta en `../motor/` y se describe en `../README.md` y `../PROCEDENCIA.md`.
Se conservan por trazabilidad; nada de aqui se ejecuta.

| Archivo | Contenido | Estado |
|---|---|---|
| `catalogo.json` | 68 hipotesis iniciales en 25 familias | **Ya no se usa**: el laboratorio descubre sin catalogo fijo (rotacion area × lente por epocas, memoria de lo investigado y deduplicacion por necesidad). Sirve como lectura de ideas ya pensadas |
| `AUDITORIA-2026-10-24.md`, `FUENTES-2026-10-24.md` | Auditoria del sitio y fuentes consultadas ese dia | Historico; una fuente caducada se vuelve a comprobar en cada ronda |
| `investigaciones/01-web-vitals.md`, `02-pagefind.md` | Dos investigaciones de ejemplo | Historico |
| `contratos/`, `CONTRATO-ORQUESTADOR.md` | Contratos del orquestador JSON (`ciclo.py`) | Sustituidos por los prompts de `../prompts/` y los esquemas de `investigar.py` |
| `TRASPASO-CLAUDE.md`, `README-819.md` | Traspaso y README de la #819 | Sustituidos por `../README.md`; sus avisos siguen vigentes: #819 cerrada, sin `gh workflow run`, sin fusion a main |

## Decision modulo a modulo

| Modulo de la #819 | Decision | Motivo |
|---|---|---|
| `motor/ciclo.py` (504 lineas, orquestador JSON) | **Retirado** | Segundo orquestador paralelo; sustituido por `investigar.py` + `actions.py` sobre SQLite, como el QA |
| `motor/gpt_browser.py` | **Reemplazado** por la version actual del QA (fe131c8c) | La de la #819 era de un blob anterior (`4fda7332`) sin las correcciones posteriores del QA |
| `motor/claude_cli.py` | **Reemplazado** por `qa_claude.py` adaptado | Mismo origen; el del QA tiene cuentas, cache validada y registro de coste |
| `motor/pr_laboratorio.py` | **Reemplazado** por `parches.py` + `actions.py` + `pr_hija.py` | Mismo patron de `qa_pr.py`, con linea base, cola y PR solo por accion explicita |
| `motor/verificar_upstream.py` | **Conservado** | Verifica blob/commit/ruta/licencia contra GitHub REST; no existia en el QA |
| `motor/descubrimiento.py` | **Conservado** (pistas opcionales) | Util y sin equivalente; un fallo de red nunca bloquea |
| `motor/preflight.py`, `motor/preview.py` | **Reescritos** | Nuevo estado, aislamiento del QA y vista previa por SHA |
| `rotacion.py`, `verificar.py`, `catalogo.json` | **Retirados** | Catalogo finito |
| `test_motor.py`, `test_rotacion.py` | **Retirados** | Probaban el orquestador retirado; los sustituyen los `tests/test_*.py` nuevos |
| `test_upstream.py` | **Conservado** | Sigue probando `verificar_upstream.py` |
| `INICIAR-MEJORAS.ps1/.cmd`, `PREVISUALIZAR-MEJORAS.cmd`, `PROBAR-OFFLINE-MEJORAS.cmd` | **Reemplazados** por los cuatro `.bat` | Misma experiencia que los BAT del QA |
