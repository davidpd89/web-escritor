# Contrato de integración del laboratorio con la cadena QA existente

**La cadena original se ha localizado** en `automation/qa-gpt`, concretamente `qa_gpt.py`, `qa_lote.py`, `qa_cobertura.py`, `qa_claude.py`, `qa_pr.py`, `gpt_browser.py` y `edge_launcher.py`. Se han adaptado los módulos relevantes a `motor/`. El servicio QA conserva sus propios procesos, estado, conversaciones y PR hacia main; el laboratorio usa CDP 9331 y solo ramas `feature/mejoras-web/*` con destino `lab/mejoras-web-20261024`.

## Contrato estable por ciclo

- **Seleccionar** tema general: `rotacion.py --vista | --siguiente | --elegir ID | --resultado investigada|descartada|sin_evidencia|pendiente_revision`. Fichero de estado separado en `ciclo/rotacion.json`.
- **Descubrir**: `motor/descubrimiento.py --canal github|web|api|sector|auditoria_local --familia AREA`. Devuelve URL, fecha, descripción y origen. Sin resultados no hay PR. Tras 68 semillas, `motor/ciclo.py` genera sondeos y sigue buscando fuentes nuevas.
- **Investigar GPT** con `motor/gpt_browser.ask`, usando Project configurado; persistir chat_id antes de esperar respuesta para no duplicar. El expediente exige objetivo, baseline, fuente real, código original, SHA, licencia, alternativas A/B, pruebas y riesgo.
- **Contrastar** para GitHub con `motor/verificar_upstream.py`, contra blob y licencia reales. Sin verificación se queda en la fase y no pasa a Claude.
- **Revisar Claude** mediante `motor/claude_cli.py` con salida JSON de decisión, esquema, justificación, criterio y riesgo; `investigar_mas` no pasa a implementación.
- **Desarrollar** solo si Claude aprueba. GPT emite parche declarativo y tests. Nunca se ejecutan comandos arbitrarios redactados por GPT.
- **Validar** en nuevo worktree derivado de lab. Se ejecutan tests indicados y comprobaciones complementarias. Cualquier fallo conserva worktree y error sin PR publicada.
- **Publicar PR draft** únicamente en `lab/mejoras-web-20261024`, recuperar la ya existente si estaba abierta. **Nunca fusionar**, desplegar ni desproteger main. Como máximo dos PR hijas abiertas pendientes de revisión.

## Pruebas y herramientas

```powershell
python experimentos/mejoras-web/verificar.py
python -m unittest discover -s experimentos/mejoras-web -p 'test_*.py' -v
python experimentos/mejoras-web/motor/ciclo.py --simular
python experimentos/mejoras-web/motor/ciclo.py --estado
python experimentos/mejoras-web/rotacion.py --vista
```

Para ejecución real: configurar `LAB_MEJORAS_PROJECT_ID`, Edge/Playwright, Claude y GitHub CLI; iniciar desde el BAT en el worktree independiente. `Q` y `Ctrl+C` conservan las etapas ya persistidas. No se necesita ni debe detenerse `qa-gpt` para ejecutar el laboratorio.

## Estado de validación

Implementación del circuito real presente en la rama, con pruebas offline creadas. Falta confirmar CI verde y ejecutar una ronda real Windows/Edge/Claude/GitHub que llegue a PR hija revisable. No presumir éxitos antes de observarlos.
