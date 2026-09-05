@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo AssessNex AI - FastAPI + React + Gemini
echo ============================================================

echo [1/2] Checking Python...
python --version || exit /b 1

echo [2/2] Checking Node.js...
node --version || exit /b 1

if not exist "ANAI_platform\.venv" (
  echo Creating virtual environment...
  python -m venv ANAI_platform\.venv || exit /b 1
)
call "ANAI_platform\.venv\Scripts\activate.bat"
python -m pip install -r ANAI_platform\backend\requirements.txt

cd ANAI_reactapp
if not exist node_modules npm install
cd ..

python ANAI_platform\smart_launcher.py
endlocal
