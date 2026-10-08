# Liana Setup Script (PowerShell)
# Более мощная версия setup.bat

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          LIANA — Установка мессенджера           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$LogFile = Join-Path $PSScriptRoot "setup.log"
"=== Liana Setup Log ===" | Out-File $LogFile
"Дата: $(Get-Date)" | Out-File $LogFile -Append

Set-Location $PSScriptRoot

# ============================================
# ШАГ 1: Проверка Python
# ============================================
Write-Host "[1/8] Проверка Python..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "    Найдена версия: $pythonVersion" -ForegroundColor Green
    "Python: $pythonVersion" | Out-File $LogFile -Append
} catch {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  ОШИБКА: Python не найден                        ║" -ForegroundColor Red
    Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "Python необходим для работы Liana." -ForegroundColor White
    Write-Host ""
    Write-Host "Что нужно сделать:" -ForegroundColor Yellow
    Write-Host "  1. Скачайте Python с https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "  2. При установке ОБЯЗАТЕЛЬНО отметьте:" -ForegroundColor White
    Write-Host "     'Add Python to PATH'" -ForegroundColor White
    Write-Host "  3. Перезапустите этот скрипт" -ForegroundColor White
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# ============================================
# ШАГ 2: Проверка Node.js
# ============================================
Write-Host "[2/8] Проверка Node.js..." -ForegroundColor Yellow

try {
    $nodeVersion = node --version 2>&1
    Write-Host "    Найдена версия: $nodeVersion" -ForegroundColor Green
    "Node.js: $nodeVersion" | Out-File $LogFile -Append
} catch {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  ОШИБКА: Node.js не найден                       ║" -ForegroundColor Red
    Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "Node.js необходим для интерфейса Liana." -ForegroundColor White
    Write-Host ""
    Write-Host "Что нужно сделать:" -ForegroundColor Yellow
    Write-Host "  1. Скачайте Node.js с https://nodejs.org/" -ForegroundColor White
    Write-Host "  2. Установите (версия LTS)" -ForegroundColor White
    Write-Host "  3. Перезапустите этот скрипт" -ForegroundColor White
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# ============================================
# ШАГ 3: Проверка Docker
# ============================================
Write-Host "[3/8] Проверка Docker..." -ForegroundColor Yellow

$hasDocker = $false
try {
    $dockerVersion = docker --version 2>&1
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $hasDocker = $true
        Write-Host "    Docker найден и запущен." -ForegroundColor Green
        "Docker: найден" | Out-File $LogFile -Append
    } else {
        Write-Host "    Docker установлен, но не запущен." -ForegroundColor Yellow
        Write-Host "    Будет использована SQLite (локальная БД)." -ForegroundColor Gray
        "Docker: установлен, не запущен" | Out-File $LogFile -Append
    }
} catch {
    Write-Host "    Docker не найден. Будет использована SQLite." -ForegroundColor Gray
    Write-Host "    Это нормально для разработки." -ForegroundColor Gray
    "Docker: не найден" | Out-File $LogFile -Append
}

# ============================================
# ШАГ 4: Создание виртуального окружения
# ============================================
Write-Host "[4/8] Создание виртуального окружения..." -ForegroundColor Yellow

Set-Location backend

if (-not (Test-Path "venv")) {
    try {
        python -m venv venv 2>&1 | Out-File $LogFile -Append
        Write-Host "    Создано успешно." -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "ОШИБКА: Не удалось создать виртуальное окружение." -ForegroundColor Red
        Write-Host "Лог: $LogFile" -ForegroundColor Gray
        Read-Host "Нажмите Enter для выхода"
        exit 1
    }
} else {
    Write-Host "    Уже существует. Пропуск." -ForegroundColor Gray
}
"venv: OK" | Out-File $LogFile -Append

# ============================================
# ШАГ 5: Установка зависимостей Backend
# ============================================
Write-Host "[5/8] Установка зависимостей Backend..." -ForegroundColor Yellow

& .\venv\Scripts\Activate.ps1
try {
    pip install -r requirements.txt 2>&1 | Out-File $LogFile -Append
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
    Write-Host "    Зависимости Backend установлены." -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ОШИБКА: Не удалось установить зависимости Backend." -ForegroundColor Red
    Write-Host "Проверьте интернет-соединение." -ForegroundColor Yellow
    Write-Host "Лог: $LogFile" -ForegroundColor Gray
    Read-Host "Нажмите Enter для выхода"
    exit 1
}
"pip install: OK" | Out-File $LogFile -Append

# ============================================
# ШАГ 6: Установка зависимостей Frontend
# ============================================
Write-Host "[6/8] Установка зависимостей Frontend..." -ForegroundColor Yellow

Set-Location ..

try {
    npm install 2>&1 | Out-File $LogFile -Append
    if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
    Write-Host "    Зависимости Frontend установлены." -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ОШИБКА: Не удалось установить зависимости Frontend." -ForegroundColor Red
    Write-Host "Лог: $LogFile" -ForegroundColor Gray
    Read-Host "Нажмите Enter для выхода"
    exit 1
}
"npm install: OK" | Out-File $LogFile -Append

# ============================================
# ШАГ 7: Настройка окружения
# ============================================
Write-Host "[7/8] Настройка окружения..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    $secretKey = python -c "import secrets; print(secrets.token_urlsafe(48))"
    
    @"
# Liana Configuration
# Создано автоматически

# Database (SQLite для локальной разработки)
DATABASE_URL=sqlite:///./liana.db

# Security
SECRET_KEY=$secretKey

# Frontend
FRONTEND_URL=http://localhost:3000

# Environment
ENVIRONMENT=development

# Files
UPLOAD_DIR=./uploads
FILE_RETENTION_DAYS=30
MAX_FILE_SIZE_MB=500
"@ | Out-File .env -Encoding UTF8
    
    Write-Host "    Файл .env создан." -ForegroundColor Green
    ".env: создан" | Out-File $LogFile -Append
} else {
    Write-Host "    Файл .env уже существует. Пропуск." -ForegroundColor Gray
    ".env: существует" | Out-File $LogFile -Append
}

# Создаём директории для файлов
$dirs = @("uploads", "uploads\images", "uploads\videos", "uploads\voices", "uploads\files", "uploads\avatars")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}
"Директории uploads: OK" | Out-File $LogFile -Append

# ============================================
# ШАГ 8: Проверка работоспособности
# ============================================
Write-Host "[8/8] Проверка работоспособности..." -ForegroundColor Yellow

Set-Location backend
& .\venv\Scripts\Activate.ps1

try {
    python -c "from app.main import app; print('Backend OK')" 2>&1 | Out-File ..\setup.log -Append
    if ($LASTEXITCODE -ne 0) { throw "Backend check failed" }
    Write-Host "    Backend: OK" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ОШИБКА: Backend не может быть загружен." -ForegroundColor Red
    Write-Host "Проверьте лог: $LogFile" -ForegroundColor Gray
    Read-Host "Нажмите Enter для выхода"
    exit 1
}
"Backend проверка: OK" | Out-File $LogFile -Append

Set-Location ..

try {
    npm run build 2>&1 | Out-File $LogFile -Append
    if ($LASTEXITCODE -ne 0) { throw "Build failed" }
    Write-Host "    Frontend сборка: OK" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ОШИБКА: Не удалось собрать Frontend." -ForegroundColor Red
    Write-Host "Лог: $LogFile" -ForegroundColor Gray
    Read-Host "Нажмите Enter для выхода"
    exit 1
}
"Frontend сборка: OK" | Out-File $LogFile -Append

# ============================================
# ГОТОВО
# ============================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!            ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Liana установлена и готова к запуску." -ForegroundColor White
Write-Host ""
Write-Host "Следующий шаг:" -ForegroundColor Yellow
Write-Host "  Запустите: .\start.ps1" -ForegroundColor White
Write-Host "  или: start.bat" -ForegroundColor White
Write-Host ""
Write-Host "После запуска откройте в браузере:" -ForegroundColor Yellow
Write-Host "  http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Лог установки: $LogFile" -ForegroundColor Gray
Write-Host ""
Read-Host "Нажмите Enter для выхода"
