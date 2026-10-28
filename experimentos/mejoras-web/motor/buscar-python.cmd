@echo off
rem Devuelve en la variable PY la ruta de un Python 3.10+ que FUNCIONE (descarta el alias vacio de la Microsoft Store).
set "PY="
if defined MEJORAS_WEB_PYTHON call :probar "%MEJORAS_WEB_PYTHON%"
if not defined PY for /f "delims=" %%P in ('where python 2^>nul') do if not defined PY call :probar "%%P"
if not defined PY for /f "delims=" %%P in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do if not defined PY call :probar "%%P"
if not defined PY for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if not defined PY call :probar "%%D\python.exe"
if not defined PY for /d %%D in ("%ProgramFiles%\Python3*") do if not defined PY call :probar "%%D\python.exe"
exit /b 0
:probar
"%~1" -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=%~1"
exit /b 0
