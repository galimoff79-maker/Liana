@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title Liana — Установка

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║          LIANA — Установка мессенджера           ║
echo ╚══════════════════════════════════════════════════╝
echo.

REM Создаём лог-файл
set LOGFILE=%~dp0setup.log
echo === Liana Setup Log === > "%LOGFILE%"
echo Дата: %date% %time% >> "%LOGFILE%"
echo.

cd /d "%~dp0"

REM ============================================
REM ШАГ 1: Проверка Python
REM ============================================
echo [1/8] Проверка Python...
echo [1/8] Проверка Python... >> "%LOGFILE%"

where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo ╔══════════════════════════════════════════════════╗
    echo ║  ОШИБКА: Python не найден                        ║
    echo ╚══════════════════════════════════════════════════╝
    echo.
    echo Python необходим для работы Liana.
    echo.
    echo Что нужно сделать:
    echo   1. Скачайте Python с https://www.python.org/downloads/
    echo   2. При установке ОБЯЗАТЕЛЬНО отметьте:
    echo      "Add Python to PATH"
    echo   3. Перезапустите этот скрипт
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)

REM Проверяем версию Python
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo    Найдена версия: %PYVER%
echo    Версия Python: %PYVER% >> "%LOGFILE%"

REM ============================================
REM ШАГ 2: Проверка Node.js
REM ============================================
echo [2/8] Проверка Node.js...
echo [2/8] Проверка Node.js... >> "%LOGFILE%"

where node >nul 2>&1
if errorlevel 1 (
    echo.
    echo ╔══════════════════════════════════════════════════╗
    echo ║  ОШИБКА: Node.js не найден                       ║
    echo ╚══════════════════════════════════════════════════╝
    echo.
    echo Node.js необходим для интерфейса Liana.
    echo.
    echo Что нужно сделать:
    echo   1. Скачайте Node.js с https://nodejs.org/
    echo   2. Установите (версия LTS)
    echo   3. Перезапустите этот скрипт
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)

for /f "delims=v" %%v in ('node --version') do set NODEVER=%%v
echo    Найдена версия: !NODEVER!
echo    Версия Node.js: !NODEVER! >> "%LOGFILE%"

REM ============================================
REM ШАГ 3: Проверка Docker (опционально)
REM ============================================
echo [3/8] Проверка Docker...
echo [3/8] Проверка Docker... >> "%LOGFILE%"

set HAS_DOCKER=0
where docker >nul 2>&1
if not errorlevel 1 (
    docker info >nul 2>&1
    if not errorlevel 1 (
        set HAS_DOCKER=1
        echo    Docker найден. Будет использоваться для PostgreSQL.
        echo    Docker: найден >> "%LOGFILE%"
    ) else (
        echo    Docker установлен, но не запущен.
        echo    Будет использована SQLite (локальная БД).
        echo    Docker: установлен, не запущен >> "%LOGFILE%"
    )
) else (
    echo    Docker не найден. Будет использована SQLite (локальная БД).
    echo    Это нормально для разработки.
    echo    Docker: не найден >> "%LOGFILE%"
)

REM ============================================
REM ШАГ 4: Создание виртуального окружения
REM ============================================
echo [4/8] Создание виртуального окружения...
echo [4/8] Создание виртуального окружения... >> "%LOGFILE%"

cd backend

if not exist "venv" (
    python -m venv venv >> "%LOGFILE%" 2>&1
    if errorlevel 1 (
        echo.
        echo ОШИБКА: Не удалось создать виртуальное окружение.
        echo Лог: %LOGFILE%
        echo.
        echo Возможные причины:
        echo   - Python установлен неправильно
        echo   - Антивирус блокирует создание venv
        echo   - Недостаточно прав
        echo.
        echo Нажмите любую клавишу для выхода...
        pause >nul
        exit /b 1
    )
    echo    Создано успешно.
) else (
    echo    Уже существует. Пропуск.
)
echo    venv: OK >> "%LOGFILE%"

REM ============================================
REM ШАГ 5: Установка зависимостей Backend
REM ============================================
echo [5/8] Установка зависимостей Backend...
echo [5/8] Установка зависимостей Backend... >> "%LOGFILE%"

call venv\Scripts\activate.bat
pip install --upgrade pip >> "%LOGFILE%" 2>&1
pip install -r requirements.txt >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось установить зависимости Backend.
    echo Проверьте интернет-соединение.
    echo Лог: %LOGFILE%
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)
echo    Зависимости Backend установлены.
echo    pip install: OK >> "%LOGFILE%"

REM ============================================
REM ШАГ 6: Установка зависимостей Frontend
REM ============================================
echo [6/8] Установка зависимостей Frontend...
echo [6/8] Установка зависимостей Frontend... >> "%LOGFILE%"

cd ..

call npm install >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось установить зависимости Frontend.
    echo Лог: %LOGFILE%
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)
echo    Зависимости Frontend установлены.
echo    npm install: OK >> "%LOGFILE%"

REM ============================================
REM ШАГ 7: Настройка окружения
REM ============================================
echo [7/8] Настройка окружения...
echo [7/8] Настройка окружения... >> "%LOGFILE%"

if not exist ".env" (
    echo # Liana Configuration> .env
    echo # Создано автоматически >> .env
    echo.>> .env
    echo # Database (SQLite для локальной разработки)>> .env
    echo DATABASE_URL=sqlite:///./liana.db>> .env
    echo.>> .env
    echo # Security>> .env
    
    REM Генерируем случайный SECRET_KEY
    for /f %%i in ('python -c "import secrets; print(secrets.token_urlsafe(48))"') do set SECRET=%%i
    echo SECRET_KEY=!SECRET!>> .env
    echo.>> .env
    echo # Frontend>> .env
    echo FRONTEND_URL=http://localhost:3000>> .env
    echo.>> .env
    echo # Environment>> .env
    echo ENVIRONMENT=development>> .env
    echo.>> .env
    echo # Files>> .env
    echo UPLOAD_DIR=./uploads>> .env
    echo FILE_RETENTION_DAYS=30>> .env
    echo MAX_FILE_SIZE_MB=500>> .env
    
    echo    Файл .env создан.
    echo    .env: создан >> "%LOGFILE%"
) else (
    echo    Файл .env уже существует. Пропуск.
    echo    .env: существует >> "%LOGFILE%"
)

REM Создаём директории для файлов
if not exist "uploads" mkdir uploads
if not exist "uploads\images" mkdir uploads\images
if not exist "uploads\videos" mkdir uploads\videos
if not exist "uploads\voices" mkdir uploads\voices
if not exist "uploads\files" mkdir uploads\files
if not exist "uploads\avatars" mkdir uploads\avatars
echo    Директории uploads: OK >> "%LOGFILE%"

REM ============================================
REM ШАГ 8: Проверка работоспособности
REM ============================================
echo [8/8] Проверка работоспособности...
echo [8/8] Проверка работоспособности... >> "%LOGFILE%"

REM Проверяем что backend может запуститься
cd backend
call venv\Scripts\activate.bat
python -c "from app.main import app; print('Backend OK')" >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo.
    echo ОШИБКА: Backend не может быть загружен.
    echo Проверьте лог: %LOGFILE%
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)
echo    Backend: OK
echo    Backend проверка: OK >> "%LOGFILE%"
cd ..

REM Собираем frontend
call npm run build >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось собрать Frontend.
    echo Лог: %LOGFILE%
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)
echo    Frontend сборка: OK
echo    Frontend сборка: OK >> "%LOGFILE%"

REM ============================================
REM ГОТОВО
REM ============================================
echo.
echo ╔══════════════════════════════════════════════════╗
echo ║          УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!            ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo Liana установлена и готова к запуску.
echo.
echo Следующий шаг:
echo   Запустите: start.bat
echo.
echo После запуска откройте в браузере:
echo   http://localhost:3000
echo.
echo Лог установки: %LOGFILE%
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
