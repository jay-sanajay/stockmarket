/**
 * API base URL.
 * - Local dev: empty string → Vite proxies /analyze → http://127.0.0.1:8000 (vite.config.js).
 * - Production (Vercel): set VITE_API_BASE_URL to your Render API URL in Vercel → Environment Variables.
 * - Fallback: only used if VITE_API_BASE_URL is missing at build time — should match your Render service.
 */
const PRODUCTION_API_FALLBACK = "https://stockmarket-rz6w.onrender.com";

export function getApiBase() {
  const fromEnv = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");
  if (fromEnv) return fromEnv;
  if (import.meta.env.DEV) return "";
  return PRODUCTION_API_FALLBACK;
}
