#!/usr/bin/env bash
# Download third-party front-end assets (run on the server, which has internet).
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p app/static/vendor

curl -fsSL -o app/static/vendor/htmx.min.js \
  "https://cdn.jsdelivr.net/npm/htmx.org@1.9.12/dist/htmx.min.js"
curl -fsSL -o app/static/vendor/chart.umd.min.js \
  "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"
curl -fsSL -o app/static/vendor/pico.min.css \
  "https://cdn.jsdelivr.net/npm/@picocss/pico@2.0.6/css/pico.min.css"

echo "Vendor files downloaded."
