# Contrato de integración con el orquestador local existente

## Lo que YA funciona en esta PR

`rotacion.py` prepara y reserva **una** investigación JSON. Mantiene estado atómico fuera del repositorio bajo `LOCALAPPDATA/web-escritor-mejoras/<hash_worktree>/rotacion.json`; no comparte cola, perfil, puerto ni contadores con QA. Ofrece selección automática o explícita, recupera pendientes y permite cerrarlos o reabrirlos. No usa API, navegador, Claude, Actions o GitHub; funciona sin red.

```powershell
python experimentos/mejoras-web/rotacion.py --vista
python experimentos/mejoras-web/rotacion.py --siguiente
python experimentos/mejoras-web/rotacion.py --siguiente
python experimentos/mejoras-web/rotacion.py --resultado sin_evidencia
python experimentos/mejoras-web/rotacion.py --siguiente --canal github
python experimentos/mejoras-web/rotacion.py --elegir SEO-01
python experimentos/mejoras-web/rotacion.py --ver-estado
```

La segunda llamada --siguiente recupera exactamente la misma tarea pendiente; no registra dos turnos. Para elegir otra primero `--liberar` o cerrar con `--resultado`. `--vista` no reserva ni escribe archivo.

**Nota:** `--vista` muestra la próxima reserva si no existe pendiente; no simula una consulta a Internet.

## Puente mínimo GPT -> Claude

El adaptador local existente debe llamar `rotacion.py --siguiente` y leer `tarea` del JSON. La tarea incluye ID, familia, canal, hipótesis, antiduplciados, criterio de medición, rama base y rutas de prompts de GPT/Claude. Después:
1. GPT documenta baseline real, búsqueda nueva y repositorio candidato; 0 o 1 hallazgo útil es suficiente.
2. Claude evalúa independientemente `ENVIAR_A_PR`, `MÁS_INVESTIGACIÓN` o `DESCARTAR`.
3. El orquestador registra el expediente fuera de main; **solo** si Claude autoriza y se cumplen criterios, crea una PR hija con base lab. Ningún merge/despliegue.
4. El adaptador cierra la reserva con `--resultado investigada|descartada|sin_evidencia|pendiente_revision`.
5. El siguiente ciclo cambia de canal/familia conforme a historial. Mantener máximo dos investigaciones en ejecución simultánea hasta comprobar coste.
6. Para novedades espontáneas de Internet/repositorios: generar archivo candidato con ID único, evidencia, categoría/canal, y revisión humana/Claude de duplicados antes de meterlo en catalogo.json.

## Lo que falta del otro sistema (sin inventarlo)

No se ha localizado en el repo el script local completo de `EJECUTAR-ACTIONS-QA-GPT` que maneja conversaciones CDP, bloqueos, cola, secuencias GPT/Claude, teclas Q y Ctrl+C, ni lanzamiento de PR. Sí consta el ejecutor de QA en `scripts/qa-gpt/ci_grupo.py` y su clasificadora `qa_clases.py`. **No copiar código que no se ha inspeccionado**. Claude deberá localizar esos ficheros en el equipo, copiar los componentes reutilizables y adaptar únicamente transporte, mensajes y destino `lab/mejoras-web-20261024`, sin tocar el circuito actual.

## Contrato de continuidad

- Reinicio: primero `--ver-estado`, luego `--siguiente`, que recupera el mismo ID pendiente.
- Respuesta no válida, tiempo agotado, Edge 9331 caído: conservar reserva y registrar error sin reportar un estudio como terminado.
- Dos lanzadores simultáneos: la carpeta `.lock` impide doble escritura; ante parada abrupta investigar el lock antes de retirarlo.
- Una propuesta nueva no significa PR automáticamente; los rechazos y conclusiones sin evidencia son resultados útiles.
- No lanzar `deploy-pages.yml`, ni usar `main` como base de PR hijas.
- No colocar tokens, correos ni valores de configuración personal en los expedientes.
- QA del selector: `python -m unittest discover -s experimentos/mejoras-web -p 'test_*.py' -v`.

## Actualización: origen recuperado

El director original sí se ha localizado en la rama Git `automation/qa-gpt`. Se han adaptado sus clientes de GPT/Claude y el patrón de PR en `motor/`; la integración del circuito ya existe en código. Siguen sin validar el arranque real en Windows, los permisos de cuentas y la ejecución completa con PR hija. El laboratorio no comparte puerto, Project ChatGPT (debe configurarse), estado ni rama base de QA.
