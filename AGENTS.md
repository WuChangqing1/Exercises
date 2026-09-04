# AGENTS.md — Exercises Platform

Stable context for DeepSeek Harness (and any AI agent) maintaining this repository.
Read this first, then read only the files relevant to the task.

## Project root & runtime

- Project Root: `D:\CodingData\Github\Exercises`
- Development Harness: DeepSeek Harness
- Repository: public GitHub
- Production: `ssh fengz` (already configured; do not scan other hosts)

## Platform

Exercises Platform = **Product Hub** (server homepage / product entry) + **Training Tracker** (single-user workout planning & logging).

Routing (production, Case B — root already belongs to existing products):

- `/hub/` → Product Hub
- `/training/` → Training Tracker
- `/health` → platform health

## Repo map

| Area | Location |
|---|---|
| App entrypoint | `app/main.py` |
| Config (env) | `app/config.py` |
| Database engine | `app/database.py` |
| Models | `app/models/` |
| CLI (`create-admin`, `init-db`) | `app/cli.py` |
| Security (auth/CSRF/rate-limit) | `app/security.py` |
| Product Hub route | `app/routes/hub.py` |
| Product Registry loader | `app/services/products.py` |
| Training plan (YAML) | `app/data/training_plan.yaml` |
| Schedule engine | `app/services/schedule.py` |
| Workout materialization/status | `app/services/workout.py` |
| Stats | `app/services/stats.py` |
| Export | `app/services/export.py` |
| Backup | `app/services/backup.py` |
| Dashboard route | `app/routes/dashboard.py` |
| Training actions | `app/routes/training.py` |
| Calendar route | `app/routes/calendar.py` |
| Stats route | `app/routes/stats.py` |
| Settings/export/backup route | `app/routes/settings.py` |
| Templates | `app/templates/` |
| Static assets | `app/static/` |
| PWA (scope `/training/`) | `app/training_static/` |
| Tests | `tests/` (pytest) |
| Deploy scripts | `scripts/deploy.sh`, `scripts/backup.sh`, `scripts/restore.sh` |
| systemd / nginx templates | `deploy/` |

## Product registry (kept out of git)

- Example: `config/products.example.yaml`
- Production: `instance/products.yaml` (never committed)
- Set `PRODUCTS_CONFIG_PATH` to point at the production file.

## Per-task workflow

1. Read `AGENTS.md` (this file).
2. Identify the affected module(s) from the map.
3. Read only the relevant files.
4. Change, then run the relevant tests: `.venv\Scripts\python.exe -m pytest`.
5. Commit.

## Security rules (non-negotiable)

- Never request, store, print, or commit SSH or sudo passwords.
- Never read SSH private key contents.
- Never commit secrets, `.env`, or production `instance/products.yaml`.
- Never commit server public IPs, internal ports, or internal URLs.
- Never overwrite existing production apps, or stop/delete unknown services or containers.
- Inspect existing nginx config before modifying it; always `nginx -t` before reload.
- Production SSH entry is always: `ssh fengz`.
