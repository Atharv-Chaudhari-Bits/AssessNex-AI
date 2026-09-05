@echo off
setlocal
cd /d "%~dp0"
call venv\Scripts\activate.bat 2>nul
if errorlevel 1 echo Create a virtual environment first: python -m venv venv
python smart_launcher.py
endlocal
