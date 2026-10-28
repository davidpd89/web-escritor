@echo off
chcp 65001 >nul
setlocal
set "LAB=%~dp0"
call "%LAB%motor\buscar-python.cmd"
if not defined PY goto :sinpython
echo.
echo  EJECUTAR-ACTIONS-MEJORAS-WEB: proceso CONTINUO y MANUAL. Valida en local cada mejora preparada (worktree separado)
echo  y mantiene hasta 3 grupos a la vez en GitHub Actions (workflow dedicado, solo workflow_dispatch).
echo  Al terminar uno recoge sus resultados y envia el siguiente. NO abre PR y NO fusiona nada.
echo  Q = parar tras guardar ^| Ctrl+C = parada controlada ^| cerrar la ventana = dejar de lanzar grupos nuevos.
echo  Los runs ya enviados a GitHub NO se cancelan: al abrirlo de nuevo se recogen sus resultados sin duplicar envios.
echo.
"%PY%" "%LAB%motor\preflight.py" --offline
if errorlevel 1 goto :fallo
"%PY%" "%LAB%motor\supervisor.py" ejecutar-actions --continuo
echo.
"%PY%" "%LAB%motor\mw.py" estado
echo.
pause
exit /b 0
:fallo
echo.
echo  El preflight encontro problemas. Arreglalos y vuelve a pulsar. No se ha enviado nada a GitHub.
echo.
pause
exit /b 2

:sinpython
echo.
echo  No se encontro Python 3.10 o superior que funcione.
echo  Instala Python 3.11+ desde python.org (marca "Add python.exe to PATH") o define la variable
echo  MEJORAS_WEB_PYTHON con la ruta completa de python.exe, y vuelve a pulsar este archivo.
echo.
pause
exit /b 2
