# JayQuant daily dashboard

This document describes the **v2** dashboard APIs, storage, and how to run everything locally or on Render + Vercel.

## What changed

- **SQLite** (default) or **PostgreSQL** via `DATABASE_URL` for users, watchlists, alerts, holdings, verdict history, and cached daily summaries.
- **JWT auth** (`/auth/register`, `/auth/login`, `/auth/me`) — watchlists, alerts, and portfolio require a bearer token.
- **Public** (no auth): `/health`, `/analyze`, `/dashboard/daily-summary`, `/stocks/{symbol}/verdict-history`, `/compare`, `/assistant/chat`.
- Existing **`GET /analyze?stock=`** behavior is preserved; verdicts are still appended to `verdict_log.json` **and** mirrored to the DB when configured.

## Environment variables

Copy `.env.example` to `.env` (repo root). Important keys:

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Analysis + daily summary + assistant |
| `NEWSDATA_API_KEY` | News |
| `JWT_SECRET` | **Required in production** for signing tokens |
| `DATABASE_URL` | Optional; default SQLite `sqlite:///./data/jayquant.db` |
| `CORS_ORIGINS` | Frontend origins (comma-separated) |
| `VITE_API_BASE_URL` | **Frontend (Vercel):** full API URL, e.g. `https://xxx.onrender.com` |

## Migration from JSON-only verdict log

On startup, if the `verdict_records` table is **empty** and `verdict_log.json` exists, rows are imported once. The JSON file is **not** removed; it remains a backward-compatible audit trail.

## Run locally

**Terminal 1 — API**

```text
cd /path/to/stockmarket
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — UI**

```text
npm install
npm run dev
```

Vite proxies `/analyze`, `/auth`, `/watchlists`, `/dashboard`, `/stocks`, `/alerts`, `/portfolio`, `/compare`, `/assistant` to `http://127.0.0.1:8000` (see `vite.config.js`). Leave `VITE_API_BASE_URL` unset in dev.

**One command:** `npm run dev:all` (API + Vite via `concurrently`).

## API route map (summary)

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | No |
| GET | `/analyze?stock=` | No |
| POST | `/auth/register` | No |
| POST | `/auth/login` | No |
| GET | `/auth/me` | Bearer |
| GET/POST/DELETE | `/watchlists`, `/watchlists/{id}/items`, … | Bearer |
| GET | `/watchlists/{id}/cards` | Bearer |
| GET | `/dashboard/daily-summary` | No |
| GET | `/stocks/{symbol}/verdict-history` | No |
| CRUD | `/alerts` | Bearer |
| POST | `/alerts/check-now` | Bearer |
| GET/POST/DELETE | `/portfolio/holdings`, `/portfolio/summary` | Bearer |
| GET | `/compare?a=&b=` | No |
| POST | `/assistant/chat` | Optional |

OpenAPI: `/docs` when the API is running.

## Frontend routes

| Path | Page |
|------|------|
| `/` | Daily market dashboard (`/dashboard/daily-summary`) |
| `/analyze` | Stock analysis (unchanged flow) |
| `/watchlist` | Watchlists + cards |
| `/alerts` | Alert rules + “Check now” |
| `/portfolio` | Holdings + summary |
| `/compare` | Two-symbol compare |
| `/login` | Register / login |

## Deploy notes

- **Render (API):** set `DATABASE_URL` (Postgres), `JWT_SECRET`, `GEMINI_API_KEY`, and `CORS_ORIGINS` including your Vercel URL.
- **Vercel (frontend):** set `VITE_API_BASE_URL` to the public Render URL. Browsers cannot call `localhost` from Vercel.

## Data directory

SQLite writes under `./data/`. The directory is created automatically; `./data` is listed in `.gitignore`.
