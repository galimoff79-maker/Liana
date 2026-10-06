#!/bin/bash
# Restore script for ПриватЧат
# Usage: ./restore.sh <backup_name>

if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup_name>"
    echo "Example: ./restore.sh privatchat_backup_20240101_120000"
    exit 1
fi

BACKUP_DIR="./backups"
BACKUP_NAME="$1"

echo "🔄 ПриватЧат Restore - $BACKUP_NAME"
echo "================================"

# Check backup exists
if [ ! -f "$BACKUP_DIR/${BACKUP_NAME}_db.sql.gz" ]; then
    echo "❌ Backup not found: $BACKUP_DIR/${BACKUP_NAME}_db.sql.gz"
    exit 1
fi

# Stop services
echo "⏹ Stopping services..."
docker compose stop backend

# Restore database
echo "📦 Restoring database..."
gunzip -c "$BACKUP_DIR/${BACKUP_NAME}_db.sql.gz" | docker compose exec -T postgres psql -U privatchat privatchat
echo "✅ Database restored"

# Restore uploads
echo "📁 Restoring uploads..."
docker compose exec -T backend rm -rf /app/uploads/*
cat "$BACKUP_DIR/${BACKUP_NAME}_uploads.tar.gz" | docker compose exec -T backend tar xzf - -C /
echo "✅ Uploads restored"

# Restore .env
if [ -f "$BACKUP_DIR/${BACKUP_NAME}_env" ]; then
    cp "$BACKUP_DIR/${BACKUP_NAME}_env" .env
    echo "✅ Environment restored"
fi

# Restart services
echo "🚀 Restarting services..."
docker compose start backend

echo ""
echo "✅ Restore complete!"
