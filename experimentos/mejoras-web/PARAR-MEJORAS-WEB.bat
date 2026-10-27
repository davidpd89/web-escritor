@echo off
chcp 65001 >nul
setlocal
set "LAB=%~dp0"
call "%LAB%motor\buscar-python.cmd"
if not defined PY goto :sinpython
echo.
echo  PARAR-MEJORAS-WEB: parada limpia del investigador y del ejecutor. NO cancela los runs remotos en curso.
echo.
"%PY%" "%LAB%motor\mw.py" parar
echo.
choice /c SN /n /m "  Cerrar tambien el Edge del laboratorio (pulsa S antes de arrancar el QA, que comparte su perfil) o N para dejarlo abierto [S/N]: "
if errorlevel 2 goto :fin
"%PY%" "%LAB%motor\mw.py" parar --cerrar-edge
:fin
echo.
pause
exit /b 0

:sinpython
echo.
echo  No se encontro Python 3.10 o superior que funcione.
echo  Instala Python 3.11+ desde python.org (marca "Add python.exe to PATH") o define la variable
echo  MEJORAS_WEB_PYTHON con la ruta completa de python.exe, y vuelve a pulsar este archivo.
echo.
pause
exit /b 2
