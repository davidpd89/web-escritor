@echo off
chcp 65001 >nul
setlocal
set "QA=%~dp0"
set "PY=python"
where python >nul 2>&1 || set "PY=C:\Users\pblac\AppData\Local\Programs\Python311\python.exe"
echo.
echo  EJECUTAR-ACTIONS-QA-GPT: valida en local y envia a GitHub Actions como MAXIMO 3 grupos a la vez.
echo  Q = parar tras guardar estado ^| Ctrl+C = parada controlada ^| cerrar la ventana = dejar de lanzar grupos nuevos.
echo  Los runs ya enviados a GitHub NO se cancelan. Pulsar de nuevo reanuda sin duplicar nada.
echo.

"%PY%" "%QA%scripts\qa-gpt\qa_gpt.py" ejecutar-actions
echo.
"%PY%" "%QA%scripts\qa-gpt\qa_gpt.py" estado | findstr /B /C:"Tests preparados" /C:"Lote Actions" /C:"  - " /C:"Ultimo lote" /C:"Ultima ejecucion" /C:"    " /C:"Proximo pendiente"
echo.
pause
