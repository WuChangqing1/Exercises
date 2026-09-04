#!/usr/bin/env bash
# Restore a backup (DANGEROUS). Usage: scripts/restore.sh <backup-file>
set -euo pipefail
cd "$(dirname "$0")/.."

BACKUP_FILE="${1:-}"
if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup-file>"
  exit 1
fi
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "This will stop exercises.service, back up the current DB, and restore from:"
echo "  $BACKUP_FILE"
read -r -p "Type YES to continue: " confirm
if [ "$confirm" != "YES" ]; then
  echo "Aborted."
  exit 1
fi

echo "==> Integrity check"
python3 - "$BACKUP_FILE" <<'PY'
import sqlite3, sys
try:
    conn = sqlite3.connect(sys.argv[1])
    conn.execute("PRAGMA integrity_check").fetchall()
    conn.close()
    print("Integrity OK")
except Exception as e:
    print("Integrity FAILED:", e)
    sys.exit(1)
PY

echo "==> Stopping service"
sudo systemctl stop exercises.service || true

echo "==> Backing up current database"
source .venv/bin/activate 2>/dev/null || true
python - <<'PY'
from app.services.backup import create_backup
print("Pre-restore backup:", create_backup())
PY

echo "==> Restoring"
cp "$BACKUP_FILE" data/training.db
rm -f data/training.db-wal data/training.db-shm

echo "==> Starting service"
sudo systemctl start exercises.service
sleep 2
curl -fsS http://127.0.0.1:8000/health && echo "" && echo "Restore complete."
