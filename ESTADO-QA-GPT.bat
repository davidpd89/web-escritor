@echo off
chcp 65001 >nul
setlocal
set "QA=%~dp0"
set "PY=python"
where python >nul 2>&1 || set "PY=C:\Users\pblac\AppData\Local\Programs\Python311\python.exe"
echo.
"%PY%" "%QA%scripts\qa-gpt\qa_gpt.py" estado
:menu
echo.
choice /c CS /n /m "  Pulsa C para copiar el informe completo (listo para pegar en ChatGPT) o S para salir: "
if errorlevel 2 goto fin
echo.
"%PY%" "%QA%scripts\qa-gpt\qa_gpt.py" informe --copiar
goto menu
:fin
