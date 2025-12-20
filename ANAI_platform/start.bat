@echo off
setlocal enabledelayedexpansion

echo.
echo ======================================================
echo   AssessNex AI - Smart Start
echo ======================================================
echo.

echo [*] Cleaning up existing Python processes...
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }"
echo [OK] Cleanup complete
echo.

echo [*] Finding available ports...
REM Use Python to find free ports (more reliable)
for /f "tokens=1,2" %%a in ('python find_ports.py') do (
    set BACKEND_PORT=%%a
    set FRONTEND_PORT=%%b
)

echo [DEBUG] Backend: !BACKEND_PORT!, Frontend: !FRONTEND_PORT!

REM Check if port detection failed
if "!BACKEND_PORT!"=="" (
    echo [ERROR] Could not find available backend port
    pause
    exit /b 1
)

if "!FRONTEND_PORT!"=="" (
    echo [ERROR] Could not find available frontend port
    pause
    exit /b 1
)

echo [OK] Backend port: !BACKEND_PORT!
echo [OK] Frontend port: !FRONTEND_PORT!

REM Skip killing processes - just create Procfile
echo [*] Creating Procfile with detected ports...
(
    echo backend: python -m uvicorn backend.app.main:app --host 127.0.0.1 --port !BACKEND_PORT! --reload
    echo frontend: python frontend_wrapper.py
) > Procfile

echo [OK] Procfile created

REM Set environment for frontend
set API_BASE_URL=http://localhost:!BACKEND_PORT!
set STREAMLIT_SERVER_PORT=!FRONTEND_PORT!
set STREAMLIT_SERVER_ADDRESS=127.0.0.1

echo.
echo ======================================================
echo   STARTING SERVICES
echo ======================================================
echo.
echo Backend:  http://localhost:!BACKEND_PORT!
echo Frontend: http://localhost:!FRONTEND_PORT!
echo API URL:  !API_BASE_URL!
echo.
echo Press Ctrl+C to stop
echo ======================================================
echo.

REM Start honcho
honcho start

endlocal

