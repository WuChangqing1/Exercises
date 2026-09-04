#!/usr/bin/env bash
# Route the Product Hub to "/" and preserve the old homepage at "/home/".
set -euo pipefail

TS="$(date +%Y%m%d%H%M%S)"
SNIPPET="/etc/nginx/snippets/exercises-locations.conf"

echo "==> Backing up nginx configs"
cp /etc/nginx/conf.d/mysite.conf "/etc/nginx/conf.d/mysite.conf.backup-${TS}"
cp /etc/nginx/sites-available/fitness "/etc/nginx/sites-available/fitness.backup-${TS}"

echo "==> Installing snippet"
mkdir -p /etc/nginx/snippets
cat > "${SNIPPET}" <<'SNIPPET'
# Exercises Platform locations — include inside existing server{} blocks.

location = /hub { return 301 /; }
location /hub/ { return 301 /; }

location = /training { return 301 /training/; }
location /training/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location = /health {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
SNIPPET

echo "==> Rewriting mysite.conf root location"
python3 - <<'PY'
import pathlib, re

p = pathlib.Path("/etc/nginx/conf.d/mysite.conf")
t = p.read_text()

if "location /home/" in t:
    print("mysite.conf already has /home/ — skipping")
else:
    anchor = re.compile(
        r"location / \{ root /var/www/homepage; index index\.html index\.htm;\s*\n\s*\}"
    )
    replacement = (
        "location /home/ {\n"
        "        alias /var/www/homepage/;\n"
        "        index index.html;\n"
        "    }\n\n"
        "    location / {\n"
        "        proxy_pass http://127.0.0.1:8000;\n"
        "        proxy_set_header Host $host;\n"
        "        proxy_set_header X-Real-IP $remote_addr;\n"
        "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
        "        proxy_set_header X-Forwarded-Proto $scheme;\n"
        "    }"
    )
    new, n = anchor.subn(replacement, t, count=1)
    if n == 0:
        print("ERROR: root location anchor not found in mysite.conf")
        raise SystemExit(1)
    p.write_text(new)
    print("mysite.conf root location updated")
PY

echo "==> Testing nginx config"
nginx -t

echo "==> Reloading nginx"
systemctl reload nginx
echo "nginx integration complete."
