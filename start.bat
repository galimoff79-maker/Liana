@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title Liana — Запуск

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║          LIANA — Запуск мессенджера              ║
echo ╚══════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM Создаём лог-файл
set LOGFILE=%~dp0start.log
echo === Liana Start Log === > "%LOGFILE%"
echo Дата: %date% %time% >> "%LOGFILE%"
echo.

REM ============================================
REM Проверка установки
REM ============================================
echo [1/6] Проверка установки...
echo [1/6] Проверка установки... >> "%LOGFILE%"

if not exist "backend\venv\Scripts\activate.bat" (
    echo.
    echo ОШИБКА: Liana не установлена.
    echo.
    echo Сначала запустите: setup.bat
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)

if not exist ".env" (
    echo.
    echo ОШИБКА: Файл .env не найден.
    echo.
    echo Сначала запустите: setup.bat
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)

echo    Установка найдена.
echo    Установка: OK >> "%LOGFILE%"

REM ============================================
REM Проверка что не запущено
REM ============================================
echo [2/6] Проверка запущенных процессов...
echo [2/6] Проверка запущенных процессов... >> "%LOGFILE%"

REM Проверяем PID файлы
if exist "backend.pid" (
    set /p BACKEND_PID=<backend.pid
    tasklist /FI "PID eq !BACKEND_PID!" 2>NUL | find "!BACKEND_PID!" >NUL
    if !errorlevel! equ 0 (
        echo.
        echo ОШИБКА: Backend уже запущен (PID: !BACKEND_PID!)
        echo.
        echo Сначала остановите: stop.bat
        echo.
        echo Нажмите любую клавишу для выхода...
        pause >nul
        exit /b 1
    )
)

if exist "frontend.pid" (
    set /p FRONTEND_PID=<frontend.pid
    tasklist /FI "PID eq !FRONTEND_PID!" 2>NUL | find "!FRONTEND_PID!" >NUL
    if !errorlevel! equ 0 (
        echo.
        echo ОШИБКА: Frontend уже запущен (PID: !FRONTEND_PID!)
        echo.
        echo Сначала остановите: stop.bat
        echo.
        echo Нажмите любую клавишу для выхода...
        pause >nul
        exit /b 1
    )
)

echo    Процессы не запущены.
echo    Процессы: OK >> "%LOGFILE%"

REM ============================================
REM Запуск Backend
REM ============================================
echo [3/6] Запуск Backend...
echo [3/6] Запуск Backend... >> "%LOGFILE%"

cd backend
call venv\Scripts\activate.bat

REM Запускаем backend в отдельном окне
start "Liana Backend" /MIN cmd /c "title Liana Backend && call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 >> ..\backend.log 2>&1"

REM Сохраняем PID
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Liana Backend" /NH 2^>NUL ^| findstr /R /C:"[0-9]"') do (
    echo %%i> ..\backend.pid
    echo    Backend запущен (PID: %%i)
    echo    Backend PID: %%i >> ..\start.log
)

cd ..

REM Ждём запуска backend
echo    Ожидание запуска backend...
timeout /t 3 /nobreak >nul

REM Проверяем healthcheck
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo    Ожидание ещё 3 секунды...
    timeout /t 3 /nobreak >nul
    curl -s http://localhost:8000/api/health >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ОШИБКА: Backend не отвечает.
        echo.
        echo Проверьте лог: backend.log
        echo.
        echo Нажмите любую клавишу для выхода...
        pause >nul
        exit /b 1
    )
)

echo    Backend: OK
echo    Backend healthcheck: OK >> "%LOGFILE%"

REM ============================================
REM Запуск Frontend
REM ============================================
echo [4/6] Запуск Frontend...
echo [4/6] Запуск Frontend... >> "%LOGFILE%"

REM Запускаем frontend в отдельном окне
start "Liana Frontend" /MIN cmd /c "title Liana Frontend && npm run dev >> frontend.log 2>&1"

REM Сохраняем PID
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq Liana Frontend" /NH 2^>NUL ^| findstr /R /C:"[0-9]"') do (
    echo %%i> frontend.pid
    echo    Frontend запущен (PID: %%i)
    echo    Frontend PID: %%i >> "%LOGFILE%"
)

REM Ждём запуска frontend
echo    Ожидание запуска frontend...
timeout /t 5 /nobreak >nul

REM Проверяем доступность
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo    Ожидание ещё 3 секунды...
    timeout /t 3 /nobreak >nul
    curl -s http://localhost:3000 >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ОШИБКА: Frontend не отвечает.
        echo.
        echo Проверьте лог: frontend.log
        echo.
        echo Нажмите любую клавишу для выхода...
        pause >nul
        exit /b 1
    )
)

echo    Frontend: OK
echo    Frontend доступность: OK >> "%LOGFILE%"

REM ============================================
REM Открытие браузера
REM ============================================
echo [5/6] Открытие браузера...
echo [5/6] Открытие браузера... >> "%LOGFILE%"

start http://localhost:3000

echo    Браузер открыт.
echo    Браузер: OK >> "%LOGFILE%"

REM ============================================
REM Финальная проверка
REM ============================================
echo [6/6] Финальная проверка...
echo [6/6] Финальная проверка... >> "%LOGFILE%"

REM Проверяем API
curl -s http://localhost:8000/api/health | findstr "ok" >nul
if errorlevel 1 (
    echo    Предупреждение: API healthcheck не прошёл.
    echo    Но сервисы запущены.
    echo    API healthcheck: WARNING >> "%LOGFILE%"
) else (
    echo    API healthcheck: OK >> "%LOGFILE%"
)

REM ============================================
REM ГОТОВО
REM ============================================
echo.
echo ╔══════════════════════════════════════════════════╗
echo ║          LIANA УСПЕШНО ЗАПУЩЕНА!                 ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo Адрес мессенджера:
echo   http://localhost:3000
echo.
echo Backend API:
echo   http://localhost:8000
echo.
echo Документация API:
echo   http://localhost:8000/docs
echo.
echo Чтобы остановить Liana:
echo   Запустите: stop.bat
echo.
echo Логи:
echo   backend.log
echo   frontend.log
echo.
echo Нажмите любую клавишу для выхода...
echo (Liana продолжит работать в фоне)
pause >nul
