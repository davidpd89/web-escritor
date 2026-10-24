@echo off
chcp 65001 >nul
setlocal
set "QA=%~dp0"
set "PY=python"
where python >nul 2>&1 || set "PY=C:\Users\pblac\AppData\Local\Programs\Python311\python.exe"
echo.
echo  EJECUTAR-ACTIONS-QA-GPT: proceso CONTINUO. Valida en local y mantiene hasta 3 grupos a la vez en GitHub Actions;
echo  al terminar uno recoge sus resultados y envia el siguiente. Sin trabajo, espera propuestas nuevas.
echo  Q = parar tras guardar estado ^| Ctrl+C = parada controlada ^| cerrar la ventana = dejar de lanzar grupos nuevos.
echo  Los runs ya enviados a GitHub NO se cancelan: al abrirlo de nuevo se recogen sus resultados sin duplicar nada.
echo.

"%PY%" "%QA%scripts\qa-gpt\qa_gpt.py" ejecutar-actions --continuo
echo.
"%PY%" "%QA%scripts\qa-gpt\qa_gpt.py" estado | findstr /B /C:"Tests preparados" /C:"Lote Actions" /C:"  - " /C:"Ultimo lote" /C:"Ultima ejecucion" /C:"    " /C:"Proximo pendiente"
echo.
pause
