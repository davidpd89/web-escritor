@echo off
chcp 65001 >nul
setlocal
set "QA=%~dp0"
set "PY=python"
where python >nul 2>&1 || set "PY=C:\Users\pblac\AppData\Local\Programs\Python311\python.exe"
echo.
"%PY%" "%QA%scripts\qa-gpt\qa_gpt.py" estado
echo.
pause
