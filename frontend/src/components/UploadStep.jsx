import { useRef, useState } from 'react'
import { useT } from '../hooks/useLanguage'
import { Button, Card, Disclaimer, ErrorNote, Field, Input, Select, Spinner } from './Primitives'

// The first screen. Written on the assumption that the person here is not
// technical, may be in a hurry, and may only have a phone photo of a document
// they do not fully understand.

// Matches the server's limit. Refusing here means someone who picked the wrong
// file, or a photo straight off a modern phone camera, is told immediately
// instead of after a long upload that ends in an error.
const MAX_UPLOAD_MB = 25

// Matches the server. Enough for a schedule, a wording, an endorsement and a
// few photographed pages; beyond that the upload is likelier a mistake.
const MAX_FILES = 6

export function UploadStep({
  reference, onUploaded, onManual, busy, error, onClearError, progress,
  done = false,
}) {
  const t = useT()
  const [mode, setMode] = useState('upload')
  const [insurerId, setInsurerId] = useState('')
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [refused, setRefused] = useState('')
  const inputRef = useRef(null)

  const insurers = (reference?.insurers ?? []).filter((i) => !i.scheme)
  const schemes = (reference?.insurers ?? []).filter((i) => i.scheme)

  // Several files at once, because one policy usually arrives in pieces: the
  // schedule, the wording, a photograph of an endorsement. They are read
  // together unless they turn out to name two different policies, which the
  // server checks and refuses rather than merging silently.
  function pick(selected) {
    const chosen = [...(selected ?? [])].filter(Boolean)
    if (chosen.length === 0) return

    const combined = [...files, ...chosen]
    if (combined.length > MAX_FILES) {
      setRefused(
        t(
          'upload.too_many',
          'That is more than {limit} files. The pages listing your cover are ' +
            'usually enough on their own.',
          { limit: MAX_FILES }
        )
      )
      return
    }

    const total = combined.reduce((sum, f) => sum + f.size, 0)
    if (total > MAX_UPLOAD_MB * 1024 * 1024) {
      setRefused(
        t(
          'upload.too_large',
          'Those come to {size} MB, and we can read up to {limit} MB. The ' +
            'pages listing your cover are usually enough on their own.',
          { size: (total / 1024 / 1024).toFixed(0), limit: MAX_UPLOAD_MB }
        )
      )
      return
    }

    setRefused('')
    setFiles(combined)
    onClearError?.()
  }

  function drop(index) {
    setFiles((current) => current.filter((_, i) => i !== index))
  }

  function dismiss() {
    setRefused('')
    onClearError?.()
  }

  // Once a policy has been read this section stays on the page, because the
  // flow scrolls rather than replaces. Collapsed to what it achieved, with a
  // way back in: somebody who uploaded the wrong document should be able to
  // say so without starting the stay again.
  if (done && !busy) {
    return (
      <div className="mx-auto max-w-2xl motion-safe:animate-fade">
        <Card>
          <div className="flex items-start gap-3 px-5 py-4">
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand text-[0.6875rem] text-on-brand">
              ✓
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-[0.9375rem] font-medium">
                {t('upload.done', 'Your policy has been read')}
              </p>
              <p className="mt-0.5 text-[0.875rem] leading-relaxed text-muted">
                {t(
                  'upload.done.hint',
                  'What it says is below. Correct anything we got wrong before ' +
                    'you go on.'
                )}
              </p>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <div className="text-center">
        <h1 className="text-[1.625rem] font-semibold tracking-tight">
          {t('upload.title', 'Find out what your hospital stay will really cost')}
        </h1>
        <p className="mx-auto mt-2 max-w-lg text-[0.9375rem] leading-relaxed text-muted">
          {t(
            'upload.subtitle',
            'Upload your health insurance policy and we will show you which ' +
              'hospitals you are covered at, what room you are entitled to, ' +
              'and what you would pay yourself.'
          )}
        </p>
      </div>

      <ErrorNote onDismiss={dismiss}>{refused || error}</ErrorNote>

      <Card>
        <div className="flex border-b border-line">
          {[
            ['upload', t('upload.tab.file', 'Upload my policy')],
            ['manual', t('upload.tab.manual', "I don't have the document")],
          ].map(([value, label]) => (
            <button
              key={value}
              onClick={() => setMode(value)}
              className={`flex-1 px-4 py-3 text-[0.875rem] font-medium transition ${
                mode === value
                  ? 'border-b-2 border-brand text-brand'
                  : 'text-muted hover:text-ink'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="space-y-4 p-5">
          <Field
            label={t('upload.insurer', 'Who is your insurance with?')}
            hint={t(
              'upload.insurer.hint',
              'This tells us which hospitals offer you cashless treatment.'
            )}
          >
            <Select value={insurerId} onChange={(e) => setInsurerId(e.target.value)}>
              <option value="">{t('upload.insurer.choose', 'Select your insurer')}</option>
              <optgroup label={t('upload.insurer.companies', 'Insurance companies')}>
                {insurers.map((i) => (
                  <option key={i.id} value={i.id}>{i.name}</option>
                ))}
              </optgroup>
              <optgroup label={t('upload.insurer.schemes', 'Government schemes')}>
                {schemes.map((i) => (
                  <option key={i.id} value={i.id}>{i.name}</option>
                ))}
              </optgroup>
            </Select>
          </Field>

          {mode === 'upload' ? (
            <>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setDragging(false)
                  pick(e.dataTransfer.files)
                }}
                onClick={() => inputRef.current?.click()}
                className={`cursor-pointer rounded-xl border-2 border-dashed px-6 py-10 text-center transition ${
                  dragging ? 'border-brand bg-brand-soft' : 'border-line hover:border-brand/40'
                }`}
              >
                <input
                  ref={inputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.webp,.tif,.tiff"
                  className="hidden"
                  multiple
                  onChange={(e) => { pick(e.target.files); e.target.value = '' }}
                />
                <p className="text-[0.9375rem] font-medium">
                  {files.length
                    ? t('upload.drop.more', 'Add another page, or click to choose more')
                    : t('upload.drop', 'Drop your policy here, or click to choose')}
                </p>
                <p className="mt-1.5 text-[0.8125rem] leading-relaxed text-muted">
                  {t(
                    'upload.drop.hint',
                    'PDFs and photos both work, and you can add several. A ' +
                      'photo of each page taken on your phone is fine; we will ' +
                      'read them and put them together.'
                  )}
                </p>
              </div>

              {files.length > 0 && (
                <ul className="space-y-1.5">
                  {files.map((chosen, index) => (
                    <li
                      key={`${chosen.name}-${index}`}
                      className="flex items-center gap-2 rounded-lg border border-line px-3 py-2 motion-safe:animate-fade"
                    >
                      <span className="min-w-0 flex-1 truncate text-[0.875rem]">
                        {chosen.name}
                      </span>
                      <span className="shrink-0 text-[0.75rem] text-muted">
                        {(chosen.size / 1024 / 1024).toFixed(1)} MB
                      </span>
                      <button
                        onClick={() => drop(index)}
                        aria-label={t('upload.remove', 'Remove {name}', {
                          name: chosen.name,
                        })}
                        className="shrink-0 rounded px-1.5 text-[0.875rem] text-muted transition hover:text-danger"
                      >
                        &times;
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              {busy ? (
                // The live panel when the parent has one, which it does for an
                // upload. A spinner only when there is nothing better to show.
                progress ?? (
                  <div className="rounded-lg bg-canvas px-4 py-3">
                    <Spinner label={t('upload.reading', 'Reading your policy.')} />
                  </div>
                )
              ) : (
                <Button
                  className="w-full"
                  disabled={files.length === 0}
                  onClick={() => onUploaded(files, insurerId)}
                >
                  {files.length > 1
                    ? t('upload.read_many', 'Read these {count} documents', {
                        count: files.length,
                      })
                    : t('upload.read', 'Read my policy')}
                </Button>
              )}
            </>
          ) : (
            <ManualForm insurerId={insurerId} onSubmit={onManual} busy={busy} />
          )}
        </div>
      </Card>

      <Disclaimer className="text-center" />
    </div>
  )
}

function ManualForm({ insurerId, onSubmit, busy }) {
  const t = useT()
  const [values, setValues] = useState({
    sum_insured: '500000',
    room_limit_type: 'flat',
    room_limit_amount: '5000',
    room_limit_pct: '1',
    copay_pct: '0',
  })

  const set = (key) => (event) =>
    setValues((current) => ({ ...current, [key]: event.target.value }))

  return (
    <div className="space-y-4">
      <Field
        label={t('manual.sum_insured', 'Total cover amount')}
        hint={t('manual.sum_insured.hint', 'The most your insurer pays in a year.')}
      >
        <Input type="number" value={values.sum_insured} onChange={set('sum_insured')} />
      </Field>

      <Field
        label={t('manual.room', 'Room rent limit')}
        hint={t(
          'manual.room.hint',
          'Most policies cap this. A room above your limit also reduces what ' +
            'your insurer pays on other charges.'
        )}
      >
        <Select value={values.room_limit_type} onChange={set('room_limit_type')}>
          <option value="flat">{t('manual.room.flat', 'A fixed amount per day')}</option>
          <option value="pct">{t('manual.room.pct', 'A percentage of my cover')}</option>
          <option value="none">{t('manual.room.none', 'No limit')}</option>
        </Select>
      </Field>

      {values.room_limit_type === 'flat' && (
        <Field label={t('manual.room.amount', 'Amount per day')}>
          <Input type="number" value={values.room_limit_amount} onChange={set('room_limit_amount')} />
        </Field>
      )}
      {values.room_limit_type === 'pct' && (
        <Field label={t('manual.room.percent', 'Percentage of cover, per day')}>
          <Input type="number" step="0.5" value={values.room_limit_pct} onChange={set('room_limit_pct')} />
        </Field>
      )}

      <Field
        label={t('manual.copay', 'Co-payment')}
        hint={t(
          'manual.copay.hint',
          'The share of every claim you pay yourself. Enter 0 if none.'
        )}
      >
        <Input type="number" value={values.copay_pct} onChange={set('copay_pct')} />
      </Field>

      <Button
        className="w-full"
        disabled={busy || !values.sum_insured}
        onClick={() =>
          onSubmit({
            insurer_id: insurerId,
            sum_insured: Number(values.sum_insured),
            room_limit_type: values.room_limit_type,
            room_limit_amount: Number(values.room_limit_amount) || null,
            room_limit_pct: Number(values.room_limit_pct) || null,
            copay_pct: Number(values.copay_pct) || 0,
          })
        }
      >
        {busy ? t('manual.working', 'Working\u2026') : t('manual.continue', 'Continue')}
      </Button>
    </div>
  )
}
