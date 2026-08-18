// Theme and text size, applied before the first paint.
//
// React applies both as well, but it can only do so once it has mounted, and a
// dark theme arriving after mount means a white page flashes past first. That
// flash is at its worst in the situation this app is for: a phone, at night,
// in a hospital.
//
// This is a file rather than an inline script so the page can be served under
// a content security policy that allows no inline script at all. An inline
// block would need either 'unsafe-inline', which is the thing the policy
// exists to forbid, or a hash regenerated on every edit. A blocking script tag
// in the head runs at exactly the same moment, so nothing is given up.
;(function () {
  try {
    var saved = JSON.parse(localStorage.getItem('polimap.settings') || '{}')
    var theme = saved.theme || 'system'
    var dark =
      theme === 'dark' ||
      (theme === 'system' &&
        window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.toggle('theme-dark', dark)
    document.documentElement.dataset.text = saved.textSize || 'default'
    document
      .querySelector('meta[name="theme-color"]')
      .setAttribute('content', dark ? '#0d1117' : '#f6f8fa')
  } catch {
    // No stored settings, or storage refused. The defaults in the stylesheet
    // stand, which is a correct page either way.
  }
})()
