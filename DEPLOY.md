# Deploy JayQuant (frontend + API)

This repo is a **monorepo**: React (Vite) at the root **and** FastAPI (`main.py`). Deploy them as **two services**.

## Your live site (reference)

- **Frontend (Vercel):** [https://stockmarket-rho.vercel.app/](https://stockmarket-rho.vercel.app/)
- **Backend (Render):** use your service URL (e.g. `https://something.onrender.com`) — it must match `VITE_API_BASE_URL` on Vercel and `PRODUCTION_API_FALLBACK` in `src/api.js` if you rely on the fallback.

## 1. Backend (Render / Railway / similar)

- **Root directory:** repo root (where `main.py` and `requirements.txt` live).
- **Build:** `pip install -r requirements.txt` (or leave empty if the platform auto-detects Python).
- **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT` (Render/Railway set `PORT`; `Procfile` matches this).
- **Environment variables** (set in the host dashboard, never commit real values):

  | Variable | Required |
  |----------|----------|
  | `GEMINI_API_KEY` | Yes |
  | `NEWSDATA_API_KEY` | Yes |
  | `CORS_ORIGINS` | Yes — include **`https://stockmarket-rho.vercel.app`**. **Preview** URLs (`stockmarket-…vercel.app`) are allowed automatically when `RENDER=true` (see `get_cors_origin_regex` in `config.py`). |
  | `ENVIRONMENT` | Optional — `production` |
  | `PERPLEXITY_API_KEY` | Optional |
  | `ANALYSIS_CACHE_TTL` | Optional — seconds for in-memory `/analyze` cache (Render defaults to **30 minutes** when unset to reduce repeat Yahoo/Gemini hits). |
  | `SKIP_GEMINI_SENTIMENT` | Optional — set to `1` to use keyword sentiment instead of a second Gemini call (helps free-tier rate limits on shared hosting IPs). |

- After deploy, copy the public API URL, e.g. `https://xxxxx.onrender.com`.

### “Works on localhost, fails on Vercel” (rate limits)

Free tiers for **Yahoo Finance**, **Gemini**, and **NewsData** often throttle **shared outbound IPs** (Render, etc.). Your app may show the friendly “wait 2–3 minutes” message. Mitigations: enable **`SKIP_GEMINI_SENTIMENT=1`** on Render, rely on the longer default cache on Render, wait between tests, or use paid / higher quotas.

## 2. Frontend (Vercel)

- **Framework:** Vite (auto-detected if `vite.config.js` exists).
- **Build:** `npm run build` → output `dist/`.
- **Critical:** Vite reads env at **build time**. In Vercel → Project → **Settings → Environment Variables**, add:

  | Name | Value | Environment |
  |------|--------|----------------|
  | `VITE_API_BASE_URL` | `https://YOUR-RENDER-URL.onrender.com` (no trailing slash) | Production (and Preview if you want) |

  Without this, the built app falls back to whatever default is in `src/api.js` and may point at an old API.

- **Redeploy** after changing env vars: Deployments → **Redeploy** (or push a new commit).

## 3. Ship your latest code

```bash
git add -A
git status
git commit -m "Deploy: latest UI, API proxy dev, Gemini fallbacks"
git push origin main
```

Trigger redeploy on both Vercel and Render (or enable auto-deploy on push).

## 4. Verify

- Open `https://YOUR-API/health` → JSON `status: ok`.
- Open your Vercel site → Analyze a symbol → browser **Network** tab should call `YOUR-API/analyze`, not `127.0.0.1`.

## 5. “Not all changes” showing

Common causes:

| Issue | Fix |
|-------|-----|
| Old frontend bundle | Redeploy Vercel **after** setting `VITE_API_BASE_URL`; hard-refresh (Ctrl+Shift+R) or disable cache. |
| API not updated | Redeploy Render; confirm branch is `main` and build logs succeed. |
| CORS errors | On Render, include production Vercel URL in `CORS_ORIGINS`; redeploy **this repo** so preview URLs match the built-in regex. Never use `127.0.0.1` in `VITE_API_BASE_URL` on Vercel. |
| HTTP 500 from `/analyze` | Render → **Logs**: often missing `GEMINI_API_KEY` / `NEWSDATA_API_KEY` or Gemini/model error. |
| Wrong API URL in app | Set `VITE_API_BASE_URL` to your **current** Render URL. |
