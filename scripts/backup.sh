#!/usr/bin/env bash
# Create a SQLite backup and prune to the latest 30.
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

python - <<'PY'
from app.services.backup import create_backup
print("Backup created:", create_backup())
PY

ls -1t backups/training-*.db 2>/dev/null | tail -n +31 | xargs -r rm -f
echo "Backups pruned to latest 30."
