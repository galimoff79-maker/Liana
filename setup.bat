@echo off
REM Liana Setup Script for Windows
REM This script sets up the development environment

echo ========================================
echo Liana Setup
echo ========================================
echo.

REM Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)
echo Python found.

REM Check Node.js
echo [2/6] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 20+
    pause
    exit /b 1
)
echo Node.js found.

REM Check Docker
echo [3/6] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Docker not found. You can still run locally without Docker.
) else (
    echo Docker found.
)

REM Create .env if not exists
echo [4/6] Setting up environment...
if not exist .env (
    echo Creating .env file...
    (
        echo # Database
        echo DATABASE_URL=postgresql://privatchat:privatchat@localhost:5432/privatchat
        echo DB_PASSWORD=privatchat
        echo.
        echo # Security - CHANGE THIS IN PRODUCTION
        echo SECRET_KEY=dev-secret-key-change-in-production-min-32-chars!!
        echo.
        echo # Push Notifications
        echo VAPID_PUBLIC_KEY=
        echo VAPID_PRIVATE_KEY=
        echo.
        echo # Frontend
        echo FRONTEND_URL=http://localhost:3000
        echo.
        echo # Files
        echo UPLOAD_DIR=./uploads
        echo FILE_RETENTION_DAYS=30
        echo MAX_FILE_SIZE_MB=500
    ) > .env
    echo .env created. Please edit it with your values.
) else (
    echo .env already exists.
)

REM Install backend dependencies
echo [5/6] Installing backend dependencies...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..

REM Install frontend dependencies
echo [6/6] Installing frontend dependencies...
call npm install

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env with your values
echo 2. Start PostgreSQL (or use Docker)
echo 3. Run: start.bat
echo.
pause
