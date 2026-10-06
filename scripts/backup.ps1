# Backup script for ПриватЧат (Windows PowerShell)
# Usage: .\backup.ps1 [backup_dir]

param(
    [string]$BackupDir = ".\backups"
)

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupName = "privatchat_backup_$Timestamp"

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host "🔒 ПриватЧат Backup - $Timestamp" -ForegroundColor Green
Write-Host "================================"

# Backup PostgreSQL
Write-Host "📦 Backing up database..."
docker compose exec -T postgres pg_dump -U privatchat privatchat | Out-File -FilePath "$BackupDir\${BackupName}_db.sql" -Encoding UTF8
Compress-Archive -Path "$BackupDir\${BackupName}_db.sql" -DestinationPath "$BackupDir\${BackupName}_db.sql.zip"
Remove-Item "$BackupDir\${BackupName}_db.sql"
Write-Host "✅ Database backed up"

# Backup uploads
Write-Host "📁 Backing up uploads..."
docker compose exec -T backend tar czf - /app/uploads | Out-File -FilePath "$BackupDir\${BackupName}_uploads.tar.gz" -Encoding Byte
Write-Host "✅ Uploads backed up"

# Backup .env
if (Test-Path .env) {
    Copy-Item .env "$BackupDir\${BackupName}_env"
    Write-Host "✅ Environment backed up"
}

Write-Host ""
Write-Host "📋 Backup complete!" -ForegroundColor Green
Write-Host "Location: $BackupDir\$BackupName*"
