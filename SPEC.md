# SPEC.md — Exercises Platform

## Goal

A safe, single-user Exercises Platform: a **Product Hub** that links to all products, and a **Training Tracker** for personal workout planning and logging. Existing products on the server must be preserved unchanged.

## Product Hub

- Serves a responsive product-card homepage listing enabled products.
- Products come from a YAML registry (`instance/products.yaml` in production), separate from code.
- No login for the Hub; each product handles its own auth.
- V1: no CMS, no polling, no monitoring.

### Registry fields

`id`, `name`, `description`, `url`, `enabled`, `order` (optional: `icon`, `category`).

## Existing-product safety rules

- Existing products keep their own URLs/routes/ports.
- Hub adapts to existing products; products are not migrated into the Hub.
- Never overwrite `/`, nginx configs, unknown services, containers, or databases.
- Root `/` was already in use, so Product Hub is served at `/hub/` (Case B).

## Training Tracker

- Single user, mobile-first (phone primary, desktop secondary).
- Auth required (Argon2 password hash, HttpOnly SameSite=Lax session cookie).
- Today's workout: one-tap checkbox per exercise, saved immediately (HTMX), progress + status update.
- Plan/actual separation: planned sets/reps/duration/distance plus optional actual sets/reps/time/distance/RPE/note.
- Workout statuses: `not_started`, `partial`, `completed`, `skipped`, `rest`.
- Skip today with optional reason; checking a box on a skipped day un-skips it.
- Calendar month view with per-day status, backfill and edit past records.
- Stats + Chart.js (weekly completion, pull-up max trend, weekly run volume).
- Settings (start date, default time, timezone, username, password change, in-app reminder).
- Export (full JSON, workout CSV, exercise CSV) and backup/restore.

## Training plan

- `app/data/training_plan.yaml` drives the schedule (change volume by editing YAML).
- Default start: `2026-09-07` (Monday), 8-week program.
- Weekday template: Mon back+core, Tue easy run, Wed rest, Thu back+core+intervals, Fri rest, Sat endurance run, Sun rest.
- Week 8+ → maintenance (repeat week 8) with a "program finished" notice.
- Timezone default `Asia/Shanghai`; all date math uses the configured timezone.

## Data model

- `User` (username, Argon2 password hash)
- `AppSettings` (single row: program_start_date, default_training_time, timezone)
- `WorkoutDay` (date, week_number, day_type, status, skip_reason, note, completed_at)
- `ExerciseLog` (planned + actual fields, per-workout-day, unique per exercise key)

`actual_reps` is stored as a JSON list, e.g. `[5,5,4,3]`.

## V1 scope

FastAPI + Jinja2 + HTMX + SQLite + SQLAlchemy 2.x + Alembic + Argon2 + Chart.js + PicoCSS + Uvicorn + Nginx + systemd. PWA limited to `/training/`.

## Out of scope (V1)

AI coaching, multi-user, social/leaderboards, payments, wearable/GPS integration, WeChat/SMS/email push, complex monitoring, a Hub admin CMS.
