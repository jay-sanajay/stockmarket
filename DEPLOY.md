# Deploy JayQuant (frontend + API)

This repo is a **monorepo**: React (Vite) at the root **and** FastAPI (`main.py`). Deploy them as **two services**.

## Your live site (reference)

- **Frontend (Vercel):** [https://stockmarket-rho.vercel.app/](https://stockmarket-rho.vercel.app/)
- **Backend (Render):** use your service URL (e.g. `https://something.onrender.com`) — it must match `VITE_API_BASE_URL` on Vercel and `PRODUCTION_API_FALLBACK` in `src/api.js` if you rely on the fallback.

## 1. Backend (Render / Railway / similar)

### First deploy (new Render account)

1. Push this repo to **GitHub** (if it is not already).
2. In [Render Dashboard](https://dashboard.render.com) → **New +** → **Web Service**.
3. **Connect** your `stockmarket` (or fork) repository and choose branch **`main`**.
4. Configure:
   - **Name:** anything (e.g. `jayquant-api`) — this becomes `https://<name>.onrender.com`.
   - **Region:** pick one close to you.
   - **Root directory:** leave **empty** (repo root — where `main.py` lives).
   - **Runtime:** **Python 3**.
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`  
     (same as `Procfile`; Render sets `PORT` and **`RENDER=true`** automatically.)
5. Under **Environment**, add:

   | Key | Value |
   |-----|--------|
   | `GEMINI_API_KEY` | from [Google AI Studio](https://aistudio.google.com/apikey) |
   | `NEWSDATA_API_KEY` | from [newsdata.io](https://newsdata.io/) |
   | `CORS_ORIGINS` | `https://stockmarket-rho.vercel.app` (comma-separate if you add more origins) |
   | `ENVIRONMENT` | `production` (optional) |

   Optional: `SKIP_GEMINI_SENTIMENT` = `1`, `ANALYSIS_CACHE_TTL` = `3600` (see table below).

6. Choose **Free** plan if you want, then **Create Web Service**. Wait for the first deploy (several minutes). Cold starts on free tier can take ~30–60s after idle.
7. Open **`https://<your-service-name>.onrender.com/health`** — you should see `{"status":"ok",...}`.
8. Point the **Vercel** frontend at this URL: **`VITE_API_BASE_URL`** = `https://<your-service-name>.onrender.com` (no trailing slash), then **redeploy** Vercel. Optionally update **`PRODUCTION_API_FALLBACK`** in `src/api.js` to the same URL if you rely on the fallback.

**Blueprint (optional):** If you prefer infra-as-code, use **New + → Blueprint** with this repo; `render.yaml` defines the same web service. You will still need to set secret env vars in the dashboard after the service is created.

---

- **Root directory:** repo root (where `main.py` and `requirements.txt` live).
- **Build:** `pip install -r requirements.txt` (or leave empty if the platform auto-detects Python).
- **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT` (Render/Railway set `PORT`; `Procfile` matches this).
- **Environment variables** (set in the host dashboard, never commit real values):

  | Variable | Required |
  |----------|----------|
  | `GEMINI_API_KEY` | Yes |
  | `NEWSDATA_API_KEY` | Yes |
  | `CORS_ORIGINS` | Yes — include your **production** Vercel URL (e.g. `https://stockmarket-rho.vercel.app`). **Preview** deploys (`*.vercel.app`) are allowed automatically when `RENDER=true` via regex in `config.py` (any subdomain, not only `stockmarket-*`). |
  | `ENVIRONMENT` | Optional — `production` |
  | `PERPLEXITY_API_KEY` | Optional |
  | `ANALYSIS_CACHE_TTL` | Optional — seconds for in-memory `/analyze` cache (Render defaults to **1 hour** when unset). |
  | `SKIP_GEMINI_SENTIMENT` | Optional — on Render, keyword sentiment is the **default** (fewer Gemini calls). Set to `0` / `false` if you want Gemini for news sentiment anyway. |

- After deploy, copy the public API URL, e.g. `https://xxxxx.onrender.com`.

### Local works, deployed does not — two different causes

| What you see | Likely cause | What to do |
|--------------|--------------|------------|
| Browser **Network** shows request to `127.0.0.1` or fails instantly; or console **CORS** errors | **Frontend** still using wrong API URL, or **Render** blocking your Vercel origin | Set **`VITE_API_BASE_URL`** = `https://<your-service>.onrender.com` on Vercel → **Redeploy**. On Render, **`CORS_ORIGINS`** must include your **production** Vercel URL. Redeploy API after env changes. |
| Request reaches Render (`…onrender.com/analyze`) with **200** but red banner: “Data providers are busy…” | **Yahoo / Gemini / News** rate-limiting Render’s **shared IP** (normal on free tier) | Wait 2–3 minutes, retry; use **`SKIP_GEMINI_SENTIMENT`** defaults on Render; avoid hammering Analyze; upgrade quotas if needed. |
| **502 / 503** or long wait then response | **Cold start** (free tier sleeps when idle) | First click after idle can take **30–60s**; retry once. |

### “Works on localhost, fails on Vercel” (rate limits only)

Free tiers for **Yahoo Finance**, **Gemini**, and **NewsData** often throttle **shared outbound IPs** (Render, etc.). Your app may show the friendly “wait 2–3 minutes” message. Mitigations: keyword sentiment default on Render, longer cache, wait between tests, or paid / higher quotas.

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
