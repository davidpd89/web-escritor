@echo off
chcp 65001 >nul
setlocal
set "QA=%~dp0"
set "PY=python"
where python >nul 2>&1 || set "PY=C:\Users\pblac\AppData\Local\Programs\Python311\python.exe"
echo.
echo  EJECUTAR-ACTIONS-QA-GPT: valida en local y envia a GitHub Actions TODOS los tests preparados ahora.
echo  Es seguro cerrar esta ventana o pulsar de nuevo: el lote se reanuda sin duplicar nada.
echo.
"%PY%" "%QA%scripts\qa-gpt\qa_gpt.py" ejecutar-actions
echo.
"%PY%" "%QA%scripts\qa-gpt\qa_gpt.py" estado | findstr /B /C:"Tests preparados" /C:"Lote Actions" /C:"  - " /C:"Ultimo lote" /C:"Ultima ejecucion" /C:"    " /C:"Proximo pendiente"
echo.
pause
