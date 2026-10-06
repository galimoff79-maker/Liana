#!/bin/bash
# Backup script for ПриватЧат
# Usage: ./backup.sh [backup_dir]

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="privatchat_backup_${TIMESTAMP}"

mkdir -p "$BACKUP_DIR"

echo "🔒 ПриватЧат Backup - $TIMESTAMP"
echo "================================"

# Backup PostgreSQL
echo "📦 Backing up database..."
docker compose exec -T postgres pg_dump -U privatchat privatchat | gzip > "$BACKUP_DIR/${BACKUP_NAME}_db.sql.gz"
echo "✅ Database backed up"

# Backup uploads
echo "📁 Backing up uploads..."
docker compose exec -T backend tar czf - /app/uploads | cat > "$BACKUP_DIR/${BACKUP_NAME}_uploads.tar.gz"
echo "✅ Uploads backed up"

# Backup .env
if [ -f .env ]; then
    cp .env "$BACKUP_DIR/${BACKUP_NAME}_env"
    echo "✅ Environment backed up"
fi

echo ""
echo "📋 Backup complete!"
echo "Location: $BACKUP_DIR/$BACKUP_NAME*"
echo "Size: $(du -sh "$BACKUP_DIR/${BACKUP_NAME}"* | awk '{print $1}' | tail -1)"
