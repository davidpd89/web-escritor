@echo off
chcp 65001 >nul
setlocal
set "LAB=%~dp0"
call "%LAB%motor\buscar-python.cmd"
if not defined PY goto :sinpython
echo.
"%PY%" "%LAB%motor\mw.py" estado
:menu
echo.
choice /c CS /n /m "  Pulsa C para copiar el informe completo al portapapeles o S para salir: "
if errorlevel 2 goto :fin
"%PY%" "%LAB%motor\mw.py" estado --completo | clip
echo  Informe copiado.
goto :menu
:fin
exit /b 0

:sinpython
echo.
echo  No se encontro Python 3.10 o superior que funcione.
echo  Instala Python 3.11+ desde python.org (marca "Add python.exe to PATH") o define la variable
echo  MEJORAS_WEB_PYTHON con la ruta completa de python.exe, y vuelve a pulsar este archivo.
echo.
pause
exit /b 2
