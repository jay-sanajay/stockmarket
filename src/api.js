/**
 * API base URL.
 * - Local dev: empty string → Vite proxies /analyze → http://127.0.0.1:8000 (vite.config.js).
 * - Production (Vercel): set VITE_API_BASE_URL to your **public** Render API URL (never localhost).
 * - Fallback: used when env is missing or invalid for production builds.
 */
const PRODUCTION_API_FALLBACK = "https://stockmarket-jay.onrender.com";

function isLocalhostUrl(url) {
  if (!url || typeof url !== "string") return false;
  try {
    const u = url.startsWith("http") ? url : `https://${url}`;
    const host = new URL(u).hostname.toLowerCase();
    return host === "localhost" || host === "127.0.0.1" || host === "[::1]";
  } catch {
    return url.includes("127.0.0.1") || url.includes("localhost");
  }
}

export function getApiBase() {
  let fromEnv = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "").trim();

  // Browsers cannot reach your PC's localhost from Vercel — ignore mistaken env in production
  if (import.meta.env.PROD && fromEnv && isLocalhostUrl(fromEnv)) {
    fromEnv = "";
  }

  if (fromEnv) return fromEnv;
  if (import.meta.env.DEV) return "";
  return PRODUCTION_API_FALLBACK;
}
