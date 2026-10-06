# Restore script for ПриватЧат (Windows PowerShell)
# Usage: .\restore.ps1 -BackupName "privatchat_backup_20240101_120000"

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupName
)

$BackupDir = ".\backups"

Write-Host "🔄 ПриватЧат Restore - $BackupName" -ForegroundColor Yellow
Write-Host "================================"

# Check backup exists
if (-not (Test-Path "$BackupDir\${BackupName}_db.sql.zip")) {
    Write-Host "❌ Backup not found" -ForegroundColor Red
    exit 1
}

# Stop services
Write-Host "⏹ Stopping services..."
docker compose stop backend

# Restore database
Write-Host "📦 Restoring database..."
Expand-Archive -Path "$BackupDir\${BackupName}_db.sql.zip" -DestinationPath "$BackupDir\temp" -Force
Get-Content "$BackupDir\temp\${BackupName}_db.sql" | docker compose exec -T postgres psql -U privatchat privatchat
Remove-Item "$BackupDir\temp" -Recurse -Force
Write-Host "✅ Database restored"

# Restore uploads
Write-Host "📁 Restoring uploads..."
docker compose exec -T backend rm -rf /app/uploads/*
Get-Content "$BackupDir\${BackupName}_uploads.tar.gz" -Encoding Byte | docker compose exec -T backend tar xzf - -C /
Write-Host "✅ Uploads restored"

# Restore .env
if (Test-Path "$BackupDir\${BackupName}_env") {
    Copy-Item "$BackupDir\${BackupName}_env" .env
    Write-Host "✅ Environment restored"
}

# Restart
Write-Host "🚀 Restarting services..."
docker compose start backend

Write-Host ""
Write-Host "✅ Restore complete!" -ForegroundColor Green
