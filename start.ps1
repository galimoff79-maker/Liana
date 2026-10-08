# Liana Start Script (PowerShell)
# Более мощная версия start.bat

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          LIANA — Запуск мессенджера              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$LogFile = Join-Path $PSScriptRoot "start.log"
"=== Liana Start Log ===" | Out-File $LogFile
"Дата: $(Get-Date)" | Out-File $LogFile -Append

Set-Location $PSScriptRoot

# ============================================
# Проверка установки
# ============================================
Write-Host "[1/6] Проверка установки..." -ForegroundColor Yellow

if (-not (Test-Path "backend\venv\Scripts\Activate.ps1")) {
    Write-Host ""
    Write-Host "ОШИБКА: Liana не установлена." -ForegroundColor Red
    Write-Host ""
    Write-Host "Сначала запустите: .\setup.ps1" -ForegroundColor Yellow
    Write-Host "или: setup.bat" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "ОШИБКА: Файл .env не найден." -ForegroundColor Red
    Write-Host ""
    Write-Host "Сначала запустите: .\setup.ps1" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "    Установка найдена." -ForegroundColor Green
"Установка: OK" | Out-File $LogFile -Append

# ============================================
# Проверка что не запущено
# ============================================
Write-Host "[2/6] Проверка запущенных процессов..." -ForegroundColor Yellow

if (Test-Path "backend.pid") {
    $backendPid = Get-Content backend.pid
    try {
        Get-Process -Id $backendPid -ErrorAction Stop | Out-Null
        Write-Host ""
        Write-Host "ОШИБКА: Backend уже запущен (PID: $backendPid)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Сначала остановите: .\stop.ps1" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Нажмите Enter для выхода"
        exit 1
    } catch {
        # Процесс не существует, удаляем старый PID файл
        Remove-Item backend.pid -Force
    }
}

if (Test-Path "frontend.pid") {
    $frontendPid = Get-Content frontend.pid
    try {
        Get-Process -Id $frontendPid -ErrorAction Stop | Out-Null
        Write-Host ""
        Write-Host "ОШИБКА: Frontend уже запущен (PID: $frontendPid)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Сначала остановите: .\stop.ps1" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Нажмите Enter для выхода"
        exit 1
    } catch {
        Remove-Item frontend.pid -Force
    }
}

Write-Host "    Процессы не запущены." -ForegroundColor Green
"Процессы: OK" | Out-File $LogFile -Append

# ============================================
# Запуск Backend
# ============================================
Write-Host "[3/6] Запуск Backend..." -ForegroundColor Yellow

Set-Location backend

$backendProcess = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "& .\venv\Scripts\Activate.ps1; uvicorn app.main:app --host 0.0.0.0 --port 8000" -WindowStyle Minimized -PassThru

$backendProcess.Id | Out-File ..\backend.pid

Write-Host "    Backend запущен (PID: $($backendProcess.Id))" -ForegroundColor Green
"Backend PID: $($backendProcess.Id)" | Out-File ..\start.log -Append

Set-Location ..

# Ждём запуска backend
Write-Host "    Ожидание запуска backend..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Проверяем healthcheck
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "    Backend: OK" -ForegroundColor Green
        "Backend healthcheck: OK" | Out-File $LogFile -Append
    } else {
        throw "Healthcheck failed"
    }
} catch {
    Write-Host "    Ожидание ещё 3 секунды..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "    Backend: OK" -ForegroundColor Green
            "Backend healthcheck: OK" | Out-File $LogFile -Append
        } else {
            throw "Healthcheck failed"
        }
    } catch {
        Write-Host ""
        Write-Host "ОШИБКА: Backend не отвечает." -ForegroundColor Red
        Write-Host ""
        Write-Host "Проверьте лог: backend.log" -ForegroundColor Gray
        Read-Host "Нажмите Enter для выхода"
        exit 1
    }
}

# ============================================
# Запуск Frontend
# ============================================
Write-Host "[4/6] Запуск Frontend..." -ForegroundColor Yellow

$frontendProcess = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "npm run dev" -WindowStyle Minimized -PassThru

$frontendProcess.Id | Out-File frontend.pid

Write-Host "    Frontend запущен (PID: $($frontendProcess.Id))" -ForegroundColor Green
"Frontend PID: $($frontendProcess.Id)" | Out-File $LogFile -Append

# Ждём запуска frontend
Write-Host "    Ожидание запуска frontend..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Проверяем доступность
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "    Frontend: OK" -ForegroundColor Green
        "Frontend доступность: OK" | Out-File $LogFile -Append
    } else {
        throw "Frontend not available"
    }
} catch {
    Write-Host "    Ожидание ещё 3 секунды..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "    Frontend: OK" -ForegroundColor Green
            "Frontend доступность: OK" | Out-File $LogFile -Append
        } else {
            throw "Frontend not available"
        }
    } catch {
        Write-Host ""
        Write-Host "ОШИБКА: Frontend не отвечает." -ForegroundColor Red
        Write-Host ""
        Write-Host "Проверьте лог: frontend.log" -ForegroundColor Gray
        Read-Host "Нажмите Enter для выхода"
        exit 1
    }
}

# ============================================
# Открытие браузера
# ============================================
Write-Host "[5/6] Открытие браузера..." -ForegroundColor Yellow

Start-Process "http://localhost:3000"

Write-Host "    Браузер открыт." -ForegroundColor Green
"Браузер: OK" | Out-File $LogFile -Append

# ============================================
# Финальная проверка
# ============================================
Write-Host "[6/6] Финальная проверка..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.Content -match "ok") {
        Write-Host "    API healthcheck: OK" -ForegroundColor Green
        "API healthcheck: OK" | Out-File $LogFile -Append
    } else {
        throw "API check failed"
    }
} catch {
    Write-Host "    Предупреждение: API healthcheck не прошёл." -ForegroundColor Yellow
    Write-Host "    Но сервисы запущены." -ForegroundColor Gray
    "API healthcheck: WARNING" | Out-File $LogFile -Append
}

# ============================================
# ГОТОВО
# ============================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          LIANA УСПЕШНО ЗАПУЩЕНА!                 ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Адрес мессенджера:" -ForegroundColor White
Write-Host "  http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API:" -ForegroundColor White
Write-Host "  http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Документация API:" -ForegroundColor White
Write-Host "  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Чтобы остановить Liana:" -ForegroundColor Yellow
Write-Host "  Запустите: .\stop.ps1" -ForegroundColor White
Write-Host "  или: stop.bat" -ForegroundColor White
Write-Host ""
Write-Host "Логи:" -ForegroundColor Gray
Write-Host "  backend.log" -ForegroundColor Gray
Write-Host "  frontend.log" -ForegroundColor Gray
Write-Host ""
Read-Host "Нажмите Enter для выхода (Liana продолжит работать в фоне)"
