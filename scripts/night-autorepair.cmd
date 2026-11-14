@echo off
rem Turno de noche: ejecuta la version de night-autorepair.py que hay en origin/main, sobre el repo vivo.
setlocal
set "AUTOREPAIR_REPO=C:\GIT\web-escritor"
set "DIR=%LOCALAPPDATA%\web-escritor-autorepair"
if not exist "%DIR%" mkdir "%DIR%"
git -C "%AUTOREPAIR_REPO%" fetch -q origin main || exit /b 1
rem Se copian el script y todos los modulos locales que importa (tests/test_night_autorepair.py lo exige).
for %%M in (night-autorepair estado_local ci_checks) do (
  git -C "%AUTOREPAIR_REPO%" show origin/main:scripts/%%M.py > "%DIR%\%%M.py" || exit /b 1
)
python "%DIR%\night-autorepair.py" %* >> "%DIR%\salida.log" 2>&1
