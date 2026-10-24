@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INICIAR-MEJORAS.ps1" %*
if errorlevel 1 (
  echo.
  echo Inicio no completado. Lee el error anterior.
  pause
)
