@echo off
REM AssessNex AI - Complete Stack Starter
REM This script creates/activates venv and starts all three services using honcho

echo.
echo ============================================================================
echo  AssessNex AI - Complete Stack Launcher
echo ============================================================================
echo.
echo Services to start:
echo   1. Backend API     (FastAPI)     - http://localhost:8000
echo   2. Streamlit App   (Frontend)    - http://localhost:8501
echo   3. React App       (Dashboard)   - http://localhost:5173
echo.

REM Check Python version
python --version
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo.
echo Checking virtual environment in parent directory...
echo.

REM Create venv if it doesn't exist
if not exist venv (
    echo [!] Virtual environment not found. Creating venv...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists, skipping creation
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

echo.
echo Checking and installing root dependencies if needed...
python -m pip show honcho > nul 2>&1
if errorlevel 1 (
    echo [!] Installing root dependencies from ANAI_platform/requirements.txt...
    python -m pip install -r ANAI_platform/requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install root requirements
        pause
        exit /b 1
    )
    echo [OK] Root requirements installed
) else (
    echo [OK] All root dependencies already installed, skipping
)

echo.
echo Checking and installing backend requirements if needed...
cd ANAI_platform
python -c "import uvicorn; import fastapi; import langchain; import python_dotenv" > nul 2>&1
if errorlevel 1 (
    echo [!] Installing backend dependencies from ./requirements.txt...
    python -m pip install -r ./requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install backend requirements
        cd ..
        pause
        exit /b 1
    )
    echo [OK] Backend requirements installed
) else (
    echo [OK] Backend dependencies already installed, skipping
)
cd ..

echo.
echo Checking and installing React dependencies if needed...
cd ANAI_reactapp
if not exist node_modules (
    echo [!] Installing React dependencies from ./package.json...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install npm dependencies
        cd ..
        pause
        exit /b 1
    )
    echo [OK] React dependencies installed
) else (
    echo [OK] React dependencies already installed, skipping
)
cd ..

echo.
echo ============================================================================
echo  Starting AssessNex AI Stack with honcho...
echo ============================================================================
echo.
echo Press Ctrl+C to stop all services
echo.

honcho start
