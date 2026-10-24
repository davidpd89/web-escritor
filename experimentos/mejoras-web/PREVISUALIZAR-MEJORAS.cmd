@echo off
chcp 65001 >nul
cd /d "%~dp0"
python "%~dp0motor\preview.py" %*
if errorlevel 1 pause
