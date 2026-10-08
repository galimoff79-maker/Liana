@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title Liana — Остановка

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║          LIANA — Остановка мессенджера           ║
echo ╚══════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ============================================
REM Остановка Backend
REM ============================================
echo [1/3] Остановка Backend...

if exist "backend.pid" (
    set /p BACKEND_PID=<backend.pid
    echo    Остановка процесса PID: !BACKEND_PID!
    
    REM Убиваем процесс по PID
    taskkill /PID !BACKEND_PID! /F >nul 2>&1
    
    REM Также убиваем все процессы с окном "Liana Backend"
    taskkill /FI "WINDOWTITLE eq Liana Backend" /F >nul 2>&1
    
    REM Удаляем PID файл
    del backend.pid >nul 2>&1
    
    echo    Backend остановлен.
) else (
    echo    Backend не запущен.
)

REM ============================================
REM Остановка Frontend
REM ============================================
echo [2/3] Остановка Frontend...

if exist "frontend.pid" (
    set /p FRONTEND_PID=<frontend.pid
    echo    Остановка процесса PID: !FRONTEND_PID!
    
    REM Убиваем процесс по PID
    taskkill /PID !FRONTEND_PID! /F >nul 2>&1
    
    REM Также убиваем все процессы с окном "Liana Frontend"
    taskkill /FI "WINDOWTITLE eq Liana Frontend" /F >nul 2>&1
    
    REM Удаляем PID файл
    del frontend.pid >nul 2>&1
    
    echo    Frontend остановлен.
) else (
    echo    Frontend не запущен.
)

REM ============================================
REM Остановка Docker PostgreSQL (если запущен)
REM ============================================
echo [3/3] Проверка Docker PostgreSQL...

where docker >nul 2>&1
if not errorlevel 1 (
    REM Проверяем запущен ли контейнер liana-postgres
    docker ps --filter "name=liana-postgres" --format "{{.Names}}" | findstr "liana-postgres" >nul 2>&1
    if not errorlevel 1 (
        echo    Остановка Docker PostgreSQL...
        docker stop liana-postgres >nul 2>&1
        echo    Docker PostgreSQL остановлен.
    ) else (
        echo    Docker PostgreSQL не запущен.
    )
) else (
    echo    Docker не установлен. Пропуск.
)

REM ============================================
REM ГОТОВО
REM ============================================
echo.
echo ╔══════════════════════════════════════════════════╗
echo ║          LIANA ОСТАНОВЛЕНА                       ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo Все процессы Liana остановлены.
echo.
echo Чтобы запустить снова:
echo   start.bat
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
