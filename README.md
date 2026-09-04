# Exercises Platform

A single-user **Exercises Platform** with two parts:

- **Product Hub** — a responsive product-card homepage that links to all products on the server.
- **Training Tracker** — a personal workout planning and logging app (check-in, calendar, stats).

Built to live safely alongside existing products: existing routes and services are never overwritten.

## Stack

FastAPI · Jinja2 · HTMX · SQLite · SQLAlchemy 2.x · Alembic · Argon2 · Chart.js · PicoCSS · Uvicorn · Nginx · systemd · pytest.

## Layout

```
app/            FastAPI application (routes, services, models, templates, static)
app/data/       training_plan.yaml
config/         products.example.yaml
instance/       production products.yaml (git-ignored)
deploy/         systemd unit + nginx snippet
scripts/        deploy.sh, backup.sh, restore.sh, fetch_vendor.sh
tests/          pytest suite
```

## Local development

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.cli init-db
python -m app.cli create-admin   # prompts for username/password (not echoed)
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/hub/` for the Hub and `/training/` for the Tracker.

Third-party front-end assets (htmx, Chart.js, PicoCSS) are fetched with `scripts/fetch_vendor.sh`.

## Configuration

Copy `.env.example` to `.env` and set:

- `SECRET_KEY` (generate with `openssl rand -hex 32`)
- `DATABASE_URL`
- `PRODUCTS_CONFIG_PATH` (production: `instance/products.yaml`)

## Tests

```bash
pytest
```

## Production

```bash
ssh fengz
cd /opt/exercises
bash scripts/deploy.sh
```

See `deploy/exercises.service` and `deploy/nginx.exercises-locations.conf` for the systemd unit and nginx snippet.

## Backup / restore

```bash
bash scripts/backup.sh                      # SQLite online backup, keeps 30
bash scripts/restore.sh <backup-file>       # DANGEROUS: stops service, restores
```

## Security

- Argon2 password hashing, HttpOnly SameSite=Lax session cookie, CSRF protection, login rate limiting.
- Secrets, `.env`, and production `instance/products.yaml` are never committed.

## Routing

- `/hub/` — Product Hub
- `/training/` — Training Tracker
- `/health` — health check
