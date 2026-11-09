@echo off
rem Turno de noche: ejecuta la version de night-autorepair.py que hay en origin/main, sobre el repo vivo.
setlocal
set "AUTOREPAIR_REPO=C:\GIT\web-escritor"
set "DIR=%LOCALAPPDATA%\web-escritor-autorepair"
if not exist "%DIR%" mkdir "%DIR%"
git -C "%AUTOREPAIR_REPO%" fetch -q origin main || exit /b 1
git -C "%AUTOREPAIR_REPO%" show origin/main:scripts/night-autorepair.py > "%DIR%\night-autorepair.py" || exit /b 1
python "%DIR%\night-autorepair.py" %* >> "%DIR%\salida.log" 2>&1
