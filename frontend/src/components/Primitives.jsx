import { useT } from '../hooks/useLanguage'

// Shared building blocks. Kept plain and high-contrast: this interface is read
// by people under stress, often on a phone in a hospital corridor, so clarity
// beats decoration everywhere it competes with it.

export function Card({ children, className = '' }) {
  return (
    <section className={`rounded-xl border border-line bg-surface ${className}`}>
      {children}
    </section>
  )
}

export function CardHeader({ title, subtitle, aside }) {
  return (
    <header className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
      <div>
        <h2 className="text-[0.9375rem] font-semibold tracking-tight">{title}</h2>
        {subtitle && <p className="mt-0.5 text-[0.875rem] text-muted">{subtitle}</p>}
      </div>
      {aside}
    </header>
  )
}

export function Button({ variant = 'primary', className = '', ...props }) {
  const styles = {
    primary: 'bg-brand text-on-brand hover:bg-brand/90 disabled:bg-brand/40',
    secondary: 'border border-line bg-surface hover:bg-canvas disabled:opacity-50',
    ghost: 'text-brand hover:bg-brand-soft disabled:opacity-50',
  }[variant]
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-[0.875rem] font-medium transition disabled:cursor-not-allowed ${styles} ${className}`}
      {...props}
    />
  )
}

export function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[0.8125rem] font-medium text-muted">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-[0.75rem] text-muted">{hint}</span>}
    </label>
  )
}

// 16px on a phone, and smaller only once there is a pointer. Safari zooms the
// whole page in when a field under 16px is focused, and then leaves it zoomed:
// you fill one box and spend the next minute pinching the page back. It is the
// single most irritating thing a form can do on a phone, and it is a font size.
const controlClass =
  'w-full rounded-lg border border-line bg-surface px-3 py-2.5 text-base outline-none focus:border-brand focus:ring-2 focus:ring-brand/15 sm:py-2 sm:text-[0.875rem]'

export function Select({ className = '', ...props }) {
  return <select className={`${controlClass} ${className}`} {...props} />
}

export function Input({ className = '', ...props }) {
  return <input className={`${controlClass} ${className}`} {...props} />
}

export function Badge({ tone = 'neutral', children }) {
  const tones = {
    neutral: 'bg-canvas text-muted border-line',
    good: 'bg-brand-soft text-brand border-brand/20',
    warn: 'bg-warn-soft text-warn border-warn/20',
    bad: 'bg-danger-soft text-danger border-danger/20',
  }[tone]
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[0.75rem] font-medium ${tones}`}>
      {children}
    </span>
  )
}

// Always present alongside any figure. The problem statement forbids binding
// insurance advice, and an estimate shown without this reads as a quote.
export function Disclaimer({ className = '' }) {
  const t = useT()
  return (
    <p className={`text-[0.75rem] leading-relaxed text-muted ${className}`}>
      {t(
        'disclaimer',
        'Estimates for guidance only: not a quote, not an approval, not ' +
          'medical advice. Confirm every amount with your insurer and the ' +
          'hospital insurance desk.')}
    </p>
  )
}

export function Spinner({ label }) {
  return (
    <div className="flex items-center gap-2.5 text-[0.875rem] text-muted">
      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-line border-t-brand" />
      {label}
    </div>
  )
}

export function ErrorNote({ children, onDismiss }) {
  const t = useT()
  if (!children) return null
  return (
    <div className="flex items-start justify-between gap-3 rounded-lg border border-danger/25 bg-danger-soft px-4 py-3 text-[0.875rem] text-danger">
      <span>{children}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="shrink-0 text-[0.8125rem] underline">
          {t('error.dismiss', 'dismiss')}
        </button>
      )}
    </div>
  )
}

// The way into settings, wherever the app happens to be.
//
// It lives here rather than in the header because the first two screens have
// no header, and those are the two where it matters most: the language control
// is inside this panel, and somebody who cannot read the sign-in screen has to
// be able to reach it before they are asked to type a name.
export function SettingsButton({ onClick, className = '' }) {
  const t = useT()
  return (
    <button
      onClick={onClick}
      aria-label={t('nav.settings', 'Settings')}
      title={t('nav.settings', 'Settings')}
      className={`rounded-lg border border-line px-2.5 py-2 text-[0.875rem] text-muted transition hover:bg-canvas hover:text-ink ${className}`}
    >
      <svg
        width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="2" strokeLinecap="round"
        strokeLinejoin="round" aria-hidden="true"
      >
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    </button>
  )
}
