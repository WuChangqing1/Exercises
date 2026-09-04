#!/usr/bin/env bash
# Deploy the Exercises Platform (run on the server as the app user).
# Does NOT touch existing products or rewrite nginx.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Checking Python"
command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }

echo "==> Virtualenv"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "==> Ensuring directories"
mkdir -p instance data backups logs

echo "==> Preserving local config"
if [ ! -f .env ]; then
  cp -n .env.example .env
  echo "Created .env from example — fill in SECRET_KEY."
fi
if [ ! -f instance/products.yaml ]; then
  cp -n config/products.example.yaml instance/products.yaml
  echo "Created instance/products.yaml from example."
fi

echo "==> Fetching vendor assets"
bash scripts/fetch_vendor.sh

echo "==> Backing up database before migration"
if [ -f data/training.db ]; then
  python -c "from app.services.backup import create_backup; print('Pre-deploy backup:', create_backup())" || true
fi

echo "==> Running migrations"
alembic upgrade head

echo "==> Restarting service"
if systemctl list-unit-files 2>/dev/null | grep -q '^exercises\.service'; then
  sudo systemctl restart exercises.service || systemctl restart exercises.service
else
  echo "exercises.service not installed yet — start manually after installing it."
fi

echo "==> Health check"
sleep 2
curl -fsS http://127.0.0.1:8000/health && echo "" || echo "health check failed (service may need first-time install)"
echo "Deploy finished."
