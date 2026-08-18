import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// The content security policy, written into the built page.
//
// It has to be built rather than declared statically, because `connect-src`
// has to name the API's origin and that origin is only known at build time,
// from VITE_API_BASE. A static file in vercel.json cannot read it, and a
// policy wide enough to cover any API origin is not a policy.
//
// It is a meta tag rather than a response header for the same reason: the
// header would have to be static. The one directive a meta policy cannot carry
// is frame-ancestors, so framing is denied by X-Frame-Options in vercel.json
// instead, which every current browser honours.
//
// Build only. In development Vite injects its own inline scripts and opens a
// websocket for hot reload, both of which this policy forbids, and neither of
// which exists in the page anybody is served.
function contentSecurityPolicy(apiBase) {
  const api = (apiBase || '').replace(/\/$/, '')
  const connect = ["'self'", api].filter(Boolean).join(' ')

  const directives = [
    "default-src 'self'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
    // No inline scripts anywhere in the page. The one that used to be inline,
    // which sets the theme before first paint, is /theme.js for this reason.
    "script-src 'self'",
    // Tailwind compiles to a stylesheet, but React writes style attributes for
    // the few widths that are computed, and those are governed by this.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self' data:",
    `connect-src ${connect}`,
    "frame-src 'none'",
    "worker-src 'self'",
    "manifest-src 'self'",
  ]

  // Only where every request the page makes is already secure. With an API on
  // plain HTTP, which is what a local preview of a production build points at,
  // this would rewrite those calls to https and break every one of them.
  if (!api.startsWith('http://')) {
    directives.push('upgrade-insecure-requests')
  }

  const policy = directives.join('; ')

  return {
    name: 'polimap-csp',
    apply: 'build',
    transformIndexHtml(html) {
      return html.replace(
        '<head>',
        `<head>\n    <meta http-equiv="Content-Security-Policy" content="${policy}" />`
      )
    },
  }
}

export default defineConfig(({ mode }) => {
  const apiBase = loadEnv(mode, process.cwd(), 'VITE_').VITE_API_BASE ?? ''
  return {
    plugins: [react(), tailwindcss(), contentSecurityPolicy(apiBase)],
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
