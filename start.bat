@echo off
REM Liana Start Script for Windows
REM This script starts the development servers

echo ========================================
echo Starting Liana
echo ========================================
echo.

REM Check .env
if not exist .env (
    echo ERROR: .env not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Start backend
echo [1/2] Starting backend...
cd backend
start "Liana Backend" cmd /k "call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd ..

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

REM Start frontend
echo [2/2] Starting frontend...
start "Liana Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo Liana is starting...
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C in each window to stop.
echo.
pause
