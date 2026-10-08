# Liana Stop Script (PowerShell)
# Более мощная версия stop.bat

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          LIANA — Остановка мессенджера           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# ============================================
# Остановка Backend
# ============================================
Write-Host "[1/3] Остановка Backend..." -ForegroundColor Yellow

if (Test-Path "backend.pid") {
    $backendPid = Get-Content backend.pid
    Write-Host "    Остановка процесса PID: $backendPid" -ForegroundColor Gray
    
    try {
        Stop-Process -Id $backendPid -Force -ErrorAction SilentlyContinue
        Write-Host "    Backend остановлен." -ForegroundColor Green
    } catch {
        Write-Host "    Процесс уже остановлен." -ForegroundColor Gray
    }
    
    Remove-Item backend.pid -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "    Backend не запущен." -ForegroundColor Gray
}

# Дополнительно: убиваем все процессы с окном "Liana Backend"
Get-Process | Where-Object { $_.MainWindowTitle -eq "Liana Backend" } | Stop-Process -Force -ErrorAction SilentlyContinue

# ============================================
# Остановка Frontend
# ============================================
Write-Host "[2/3] Остановка Frontend..." -ForegroundColor Yellow

if (Test-Path "frontend.pid") {
    $frontendPid = Get-Content frontend.pid
    Write-Host "    Остановка процесса PID: $frontendPid" -ForegroundColor Gray
    
    try {
        Stop-Process -Id $frontendPid -Force -ErrorAction SilentlyContinue
        Write-Host "    Frontend остановлен." -ForegroundColor Green
    } catch {
        Write-Host "    Процесс уже остановлен." -ForegroundColor Gray
    }
    
    Remove-Item frontend.pid -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "    Frontend не запущен." -ForegroundColor Gray
}

# Дополнительно: убиваем все процессы с окном "Liana Frontend"
Get-Process | Where-Object { $_.MainWindowTitle -eq "Liana Frontend" } | Stop-Process -Force -ErrorAction SilentlyContinue

# ============================================
# Остановка Docker PostgreSQL
# ============================================
Write-Host "[3/3] Проверка Docker PostgreSQL..." -ForegroundColor Yellow

try {
    $dockerRunning = docker ps --filter "name=liana-postgres" --format "{{.Names}}" 2>&1
    if ($dockerRunning -match "liana-postgres") {
        Write-Host "    Остановка Docker PostgreSQL..." -ForegroundColor Gray
        docker stop liana-postgres 2>&1 | Out-Null
        Write-Host "    Docker PostgreSQL остановлен." -ForegroundColor Green
    } else {
        Write-Host "    Docker PostgreSQL не запущен." -ForegroundColor Gray
    }
} catch {
    Write-Host "    Docker не установлен или не запущен." -ForegroundColor Gray
}

# ============================================
# ГОТОВО
# ============================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          LIANA ОСТАНОВЛЕНА                       ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Все процессы Liana остановлены." -ForegroundColor White
Write-Host ""
Write-Host "Чтобы запустить снова:" -ForegroundColor Yellow
Write-Host "  .\start.ps1" -ForegroundColor White
Write-Host "  или: start.bat" -ForegroundColor White
Write-Host ""
Read-Host "Нажмите Enter для выхода"
