# ARCHITECTURE.md — Exercises Platform

## Topology

```
Browser
   │
   ▼
Nginx (existing products untouched)
   │
   ├── existing routes (unchanged)
   │
   ├── /hub/  ─────────┐
   ├── /training/ ─────┤
   └── /health ────────┤
                       ▼
                 Uvicorn (127.0.0.1:8000)
                       │
                 FastAPI (app.main)
                 ├── Product Hub (routes/hub.py)
                 └── Training Tracker (routes/*)
                       │
                     SQLite (data/training.db)
```

One FastAPI app serves both Hub and Training Tracker behind one `exercises.service`.

## Routing

- `/hub/` → Product Hub (public, no auth).
- `/training/` → Training Tracker (auth required; redirects to `/training/login`).
- `/health` → JSON health check (app + SQLite).
- Nginx passes the full URI through (`proxy_pass http://127.0.0.1:8000;`), so the app owns the `/hub/` and `/training/` prefixes.
- Existing `location` blocks are never overwritten; Exercises locations are added as a snippet.

## Product registry

YAML (`instance/products.yaml` in production). Loaded by `app/services/products.py`; invalid/missing config degrades to a safe fallback (Training Tracker only).

## Authentication

- Starlette `SessionMiddleware` (signed, HttpOnly, SameSite=Lax, Secure when HTTPS).
- Argon2 password hashing.
- Per-session CSRF token verified on all unsafe requests (header or form).
- In-memory login rate limit (no Redis).

## PWA scope

Training Tracker PWA is scoped to `/training/` only (`manifest.json` and `sw.js` served at `/training/...`). It never controls `/`, the Hub, or existing products.

## Database

SQLite with WAL, foreign keys, and busy_timeout. Schema managed by Alembic (`alembic upgrade head`).

## Backup / restore

- `scripts/backup.sh` uses the SQLite online-backup API and prunes to 30.
- `scripts/restore.sh` stops the service, backs up current DB, restores, checks integrity, restarts, health-checks.

## Deployment

- `scripts/deploy.sh`: venv → deps → dirs → preserve `.env`/`products.yaml` → vendor assets → backup → `alembic upgrade head` → restart → health check.
- `deploy/exercises.service`: systemd unit (WorkingDirectory `/opt/exercises`, uvicorn on `127.0.0.1:8000`).
- `deploy/nginx.exercises-locations.conf`: nginx location snippet to include in existing server blocks.
