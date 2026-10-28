@echo off
chcp 65001 >nul
setlocal
set "LAB=%~dp0"
call "%LAB%motor\buscar-python.cmd"
if not defined PY goto :sinpython
echo.
echo  INICIAR-MEJORAS-WEB: investigador de mejoras web (GPT investiga, Claude contrasta, GPT desarrolla, Claude revisa).
echo  Trabaja en segundo plano hasta que pulses PARAR-MEJORAS-WEB.bat. Con autoejecutar=true (config.json) tambien arranca el ejecutor automatico:
echo  valida cada mejora en local, la prueba en GitHub Actions (max 3 a la vez) y la integra en la rama de laboratorio. NUNCA toca main.
echo  Si se cerro de golpe, vuelve a pulsarlo: reanuda las conversaciones y la cola sin duplicar nada.
echo.
"%PY%" "%LAB%motor\preflight.py" --real
if errorlevel 1 goto :fallo
echo.
"%PY%" "%LAB%motor\mw.py" iniciar
echo.
pause
exit /b 0
:fallo
echo.
echo  El preflight encontro problemas (lineas FALLA). Arreglalos y vuelve a pulsar. No se ha iniciado nada.
echo.
pause
exit /b 2

:sinpython
echo.
echo  No se encontro Python 3.10 o superior que funcione.
echo  Instala Python 3.11+ desde python.org (marca "Add python.exe to PATH") o define la variable
echo  MEJORAS_WEB_PYTHON con la ruta completa de python.exe, y vuelve a pulsar este archivo.
echo.
pause
exit /b 2
