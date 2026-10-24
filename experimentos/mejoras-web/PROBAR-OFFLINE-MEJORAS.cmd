@echo off
setlocal
cd /d "%~dp0\..\.."
set "LAB=experimentos\mejoras-web"
echo [1/4] Catalogo
python "%LAB%\verificar.py"
if errorlevel 1 goto :error
echo [2/4] Preflight local (no llama a servicios)
python "%LAB%\motor\preflight.py" --offline
if errorlevel 1 goto :error
echo [3/4] Tests offline (no lanza Actions)
python -m unittest discover -s "%LAB%" -p "test_*.py" -v
if errorlevel 1 goto :error
echo [4/4] Simulacion (no usa IA ni PR)
python "%LAB%\motor\ciclo.py" --simular
if errorlevel 1 goto :error
echo OK: comprobaciones locales terminadas.
exit /b 0
:error
echo ERROR: revisar el paso anterior; no se ha lanzado CI.
exit /b 2
