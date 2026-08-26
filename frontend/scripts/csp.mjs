// The content security policy, written into the built page.
//
// Its own module so that two things can read it: the build, which puts it in
// the page, and check-csp.mjs, which asserts it still permits what the page
// actually does. A policy is one of the few things that can be tightened by
// somebody being careful and break a screen nobody thought to open afterwards,
// and it does it silently, because a blocked image looks exactly like a file
// that will not load.
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
// which exists in the page anybody is served. Which is also why the policy has
// to be checked rather than noticed: nothing in development is subject to it.

export function directives(apiBase) {
  const api = (apiBase || '').replace(/\/$/, '')
  const connect = ["'self'", api].filter(Boolean).join(' ')

  const list = [
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
    // `blob:` is how a bill somebody attached is shown back to them. The file
    // never leaves the device, so there is no URL to fetch it from: the page
    // reads it out of its own store and mints a blob URL over bytes it is
    // already holding. Nothing else can create one for this origin.
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    `connect-src ${connect}`,
    // Only a blob, and only ever one whose type this page decided from the
    // file's own extension, so a document that is not the PDF it claims to be
    // is handed to the PDF viewer and refused rather than rendered as a page.
    'frame-src blob:',
    "worker-src 'self'",
    "manifest-src 'self'",
  ]

  // Only where every request the page makes is already secure. With an API on
  // plain HTTP, which is what a local preview of a production build points at,
  // this would rewrite those calls to https and break every one of them.
  if (!api.startsWith('http://')) list.push('upgrade-insecure-requests')

  return list
}

export const policyFor = (apiBase) => directives(apiBase).join('; ')

export function cspPlugin(apiBase) {
  const policy = policyFor(apiBase)
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
