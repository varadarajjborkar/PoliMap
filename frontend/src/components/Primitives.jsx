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
        <h2 className="text-[15px] font-semibold tracking-tight">{title}</h2>
        {subtitle && <p className="mt-0.5 text-[13px] text-muted">{subtitle}</p>}
      </div>
      {aside}
    </header>
  )
}

export function Button({ variant = 'primary', className = '', ...props }) {
  const styles = {
    primary: 'bg-brand text-white hover:bg-brand/90 disabled:bg-brand/40',
    secondary: 'border border-line bg-surface hover:bg-canvas disabled:opacity-50',
    ghost: 'text-brand hover:bg-brand-soft disabled:opacity-50',
  }[variant]
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-[13px] font-medium transition disabled:cursor-not-allowed ${styles} ${className}`}
      {...props}
    />
  )
}

export function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[12px] font-medium text-muted">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-[11px] text-muted">{hint}</span>}
    </label>
  )
}

const controlClass =
  'w-full rounded-lg border border-line bg-surface px-3 py-2 text-[13px] outline-none focus:border-brand focus:ring-2 focus:ring-brand/15'

export function Select({ className = '', ...props }) {
  return <select className={`${controlClass} ${className}`} {...props} />
}

export function Input({ className = '', ...props }) {
  return <input className={`${controlClass} ${className}`} {...props} />
}

// A switch with its label as part of the hit area. Anything smaller is hard to
// use one-handed, which is how this app tends to get used.
export function Toggle({ checked, onChange, label, hint, disabled }) {
  return (
    <label
      className={`flex items-start justify-between gap-4 py-3 ${
        disabled ? 'opacity-50' : 'cursor-pointer'
      }`}
    >
      <span className="min-w-0">
        <span className="block text-[13px] font-medium">{label}</span>
        {hint && (
          <span className="mt-0.5 block text-[12px] leading-relaxed text-muted">
            {hint}
          </span>
        )}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative mt-0.5 h-6 w-11 shrink-0 rounded-full transition ${
          checked ? 'bg-brand' : 'bg-line'
        }`}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-surface shadow-sm transition-all ${
            checked ? 'left-[22px]' : 'left-0.5'
          }`}
        />
      </button>
    </label>
  )
}

export function Badge({ tone = 'neutral', children }) {
  const tones = {
    neutral: 'bg-canvas text-muted border-line',
    good: 'bg-brand-soft text-brand border-brand/20',
    warn: 'bg-warn-soft text-warn border-warn/20',
    bad: 'bg-danger-soft text-danger border-danger/20',
  }[tone]
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${tones}`}>
      {children}
    </span>
  )
}

export function Money({ value, className = '' }) {
  return <span className={`tabular-nums ${className}`}>{value}</span>
}

// Always present alongside any figure. The problem statement forbids binding
// insurance advice, and an estimate shown without this reads as a quote.
export function Disclaimer({ className = '' }) {
  return (
    <p className={`text-[11px] leading-relaxed text-muted ${className}`}>
      Estimates are for guidance only, not a quote, not an approval, and not
      medical advice. Confirm all amounts with your insurer and the hospital
      insurance desk.
    </p>
  )
}

export function Spinner({ label }) {
  return (
    <div className="flex items-center gap-2.5 text-[13px] text-muted">
      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-line border-t-brand" />
      {label}
    </div>
  )
}

export function EmptyState({ title, children }) {
  return (
    <div className="px-5 py-12 text-center">
      <p className="text-[14px] font-medium">{title}</p>
      {children && <p className="mx-auto mt-1.5 max-w-md text-[13px] text-muted">{children}</p>}
    </div>
  )
}

export function ErrorNote({ children, onDismiss }) {
  if (!children) return null
  return (
    <div className="flex items-start justify-between gap-3 rounded-lg border border-danger/25 bg-danger-soft px-4 py-3 text-[13px] text-danger">
      <span>{children}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="shrink-0 text-[12px] underline">
          dismiss
        </button>
      )}
    </div>
  )
}
