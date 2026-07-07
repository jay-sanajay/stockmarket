import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Same-origin requests from the dev server → FastAPI (no browser CORS issues)
      '/analyze': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/auth': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/watchlists': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/dashboard': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/stocks': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/alerts': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/portfolio': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/compare': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/assistant': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/prediction': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/intraday': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/breakout': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/docs': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/openapi.json': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/ws': { target: 'http://127.0.0.1:8000', changeOrigin: true, ws: true },
    },
  },
})
