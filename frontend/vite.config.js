import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// The policy itself lives in scripts/csp.mjs, so that the check which asserts
// it still permits what the page does reads the same source the build writes.
import { cspPlugin } from './scripts/csp.mjs'

export default defineConfig(({ mode }) => {
  const apiBase = loadEnv(mode, process.cwd(), 'VITE_').VITE_API_BASE ?? ''
  return {
    plugins: [react(), tailwindcss(), cspPlugin(apiBase)],
    server: {
      port: 5173,
      // The API runs as a separate process. Proxying keeps the browser on one
      // origin, which matters for the server-sent event stream: cross-origin
      // EventSource is subject to buffering that delays the live activity log.
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})