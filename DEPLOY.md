# Deploy JayQuant (frontend + API)

This repo is a **monorepo**: React (Vite) at the root **and** FastAPI (`main.py`). Deploy them as **two services**.

## Your live site (reference)

- **Frontend (Vercel):** [https://stockmarket-rho.vercel.app/](https://stockmarket-rho.vercel.app/)
- **Backend (Fly.io):** `https://<your-app>.fly.dev` — must match **`VITE_API_BASE_URL`** on Vercel and (if you rely on it) **`PRODUCTION_API_FALLBACK`** in `src/api.js`.

## 1. Backend (Fly.io)

Prerequisites: [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) installed and logged in (`fly auth login`).

From the **repo root** (where `main.py`, `Dockerfile`, and `fly.toml` live):

1. **First deploy**
   - Edit `fly.toml` → set `app = "your-unique-name"` (or run `fly launch` and let it generate/update `fly.toml`).
   - Deploy: `fly deploy`
2. **Secrets** (never commit real keys):

   ```bash
   fly secrets set GEMINI_API_KEY="..." NEWSDATA_API_KEY="..."
   fly secrets set CORS_ORIGINS="https://stockmarket-rho.vercel.app"
   fly secrets set ENVIRONMENT="production"
   ```

   Optional:

   ```bash
   fly secrets set SKIP_GEMINI_SENTIMENT="1"
   fly secrets set ANALYSIS_CACHE_TTL="3600"
   ```

3. **CORS**
   - **`CORS_ORIGINS`** must include your production Vercel origin (e.g. `https://stockmarket-rho.vercel.app`).
   - **Vercel preview** URLs (`https://stockmarket-….vercel.app`) are allowed automatically when the app runs on Fly.io (**`FLY_APP_NAME`** is set by the platform) or Render — see `get_cors_origin_regex` in `config.py`. Set `CORS_VERCEL_REGEX=0` only if you need to turn that off.

4. After deploy, your API is at **`https://<app-name>.fly.dev`**. Check **`https://<app-name>.fly.dev/health`**.

Fly sets **`FLY_APP_NAME`** automatically; you do not need to set it yourself. The app uses it for the same **30-minute default analyze cache** and Vercel preview CORS behavior as on Render.

### “Works on localhost, fails on Vercel” (rate limits)

Free tiers for **Yahoo Finance**, **Gemini**, and **NewsData** often throttle **shared outbound IPs**. Mitigations: **`SKIP_GEMINI_SENTIMENT=1`**, longer cache (default on Fly when unset), spacing out tests, or paid / higher quotas.

### Leaving Render

Remove the old Render web service when Fly is verified. Update Vercel **`VITE_API_BASE_URL`** to your **`.fly.dev`** URL and redeploy the frontend.

## 2. Frontend (Vercel)

- **Framework:** Vite (auto-detected if `vite.config.js` exists).
- **Build:** `npm run build` → output `dist/`.
- **Critical:** Vite reads env at **build time**. In Vercel → Project → **Settings → Environment Variables**, add:

  | Name | Value | Environment |
  |------|--------|----------------|
  | `VITE_API_BASE_URL` | `https://YOUR-APP.fly.dev` (no trailing slash) | Production (and Preview if you want) |

- **Redeploy** after changing env vars: Deployments → **Redeploy** (or push a new commit).

If your Fly app name differs from the default in `src/api.js`, either set `VITE_API_BASE_URL` (recommended) or update **`PRODUCTION_API_FALLBACK`** in `src/api.js` to match.

## 3. Ship your latest code

```bash
git add -A
git status
git commit -m "Deploy: API on Fly.io"
git push origin main
```

Then `fly deploy` for the API; Vercel redeploys if connected to the repo.

## 4. Verify

- Open `https://YOUR-APP.fly.dev/health` → JSON `status: ok`.
- Open your Vercel site → Analyze a symbol → browser **Network** tab should call `https://YOUR-APP.fly.dev/analyze`, not `127.0.0.1`.

## 5. Troubleshooting

| Issue | Fix |
|-------|-----|
| Old frontend bundle | Redeploy Vercel **after** setting `VITE_API_BASE_URL`; hard-refresh (Ctrl+Shift+R). |
| API not updated | `fly deploy`; check build logs. |
| CORS errors | Set `CORS_ORIGINS` on Fly to include production Vercel URL; redeploy API. Never use `127.0.0.1` in `VITE_API_BASE_URL` on Vercel. |
| HTTP 500 from `/analyze` | `fly logs` — often missing secrets or Gemini/model errors. |
| Docker build fails (matplotlib) | Open an issue; we can add apt packages to the `Dockerfile` for your image. |

## 6. Optional: Procfile (Railway / Heroku-style)

`Procfile` is unchanged for platforms that use it. Fly.io uses **`Dockerfile`** + **`fly.toml`**.
