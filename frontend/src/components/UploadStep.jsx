import { useRef, useState } from 'react'
import { Button, Card, Disclaimer, ErrorNote, Field, Input, Select, Spinner } from './Primitives'

// The first screen. Written on the assumption that the person here is not
// technical, may be in a hurry, and may only have a phone photo of a document
// they do not fully understand.

// Matches the server's limit. Refusing here means someone who picked the wrong
// file, or a photo straight off a modern phone camera, is told immediately
// instead of after a long upload that ends in an error.
const MAX_UPLOAD_MB = 25

export function UploadStep({ reference, onUploaded, onManual, busy, error, onClearError }) {
  const [mode, setMode] = useState('upload')
  const [insurerId, setInsurerId] = useState('')
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [refused, setRefused] = useState('')
  const inputRef = useRef(null)

  const insurers = (reference?.insurers ?? []).filter((i) => !i.scheme)
  const schemes = (reference?.insurers ?? []).filter((i) => i.scheme)

  function pick(selected) {
    if (!selected) return
    if (selected.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setRefused(
        `That file is ${(selected.size / 1024 / 1024).toFixed(0)} MB, and we ` +
          `can read up to ${MAX_UPLOAD_MB} MB. The pages listing your cover ` +
          `are usually enough on their own.`
      )
      return
    }
    setRefused('')
    setFile(selected)
    onClearError?.()
  }

  function dismiss() {
    setRefused('')
    onClearError?.()
  }

  return (
    <div className="mx-auto max-w-2xl space-y-5 py-8">
      <div className="text-center">
        <h1 className="text-[1.625rem] font-semibold tracking-tight">
          Find out what your hospital stay will really cost
        </h1>
        <p className="mx-auto mt-2 max-w-lg text-[0.9375rem] leading-relaxed text-muted">
          Upload your health insurance policy and we will show you which
          hospitals you are covered at, what room you are entitled to, and what
          you would pay yourself.
        </p>
      </div>

      <ErrorNote onDismiss={dismiss}>{refused || error}</ErrorNote>

      <Card>
        <div className="flex border-b border-line">
          {[
            ['upload', 'Upload my policy'],
            ['manual', "I don't have the document"],
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
            label="Who is your insurance with?"
            hint="This tells us which hospitals offer you cashless treatment."
          >
            <Select value={insurerId} onChange={(e) => setInsurerId(e.target.value)}>
              <option value="">Select your insurer</option>
              <optgroup label="Insurance companies">
                {insurers.map((i) => (
                  <option key={i.id} value={i.id}>{i.name}</option>
                ))}
              </optgroup>
              <optgroup label="Government schemes">
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
                  pick(e.dataTransfer.files?.[0])
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
                  onChange={(e) => pick(e.target.files?.[0])}
                />
                {file ? (
                  <>
                    <p className="text-[0.9375rem] font-medium">{file.name}</p>
                    <p className="mt-1 text-[0.8125rem] text-muted">
                      {(file.size / 1024 / 1024).toFixed(1)} MB. Click to choose a different file.
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-[0.9375rem] font-medium">
                      Drop your policy here, or click to choose
                    </p>
                    <p className="mt-1.5 text-[0.8125rem] leading-relaxed text-muted">
                      A PDF or a photo both work. A photo of the printed policy
                      taken on your phone is fine; we will read it.
                    </p>
                  </>
                )}
              </div>

              {busy ? (
                <div className="rounded-lg bg-canvas px-4 py-3">
                  <Spinner label="Reading your policy. This can take a minute for a photo." />
                </div>
              ) : (
                <Button
                  className="w-full"
                  disabled={!file}
                  onClick={() => onUploaded(file, insurerId)}
                >
                  Read my policy
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
      <Field label="Total cover amount" hint="The most your insurer pays in a year.">
        <Input type="number" value={values.sum_insured} onChange={set('sum_insured')} />
      </Field>

      <Field
        label="Room rent limit"
        hint="Most policies cap this. A room above your limit also reduces what your insurer pays on other charges."
      >
        <Select value={values.room_limit_type} onChange={set('room_limit_type')}>
          <option value="flat">A fixed amount per day</option>
          <option value="pct">A percentage of my cover</option>
          <option value="none">No limit</option>
        </Select>
      </Field>

      {values.room_limit_type === 'flat' && (
        <Field label="Amount per day">
          <Input type="number" value={values.room_limit_amount} onChange={set('room_limit_amount')} />
        </Field>
      )}
      {values.room_limit_type === 'pct' && (
        <Field label="Percentage of cover, per day">
          <Input type="number" step="0.5" value={values.room_limit_pct} onChange={set('room_limit_pct')} />
        </Field>
      )}

      <Field label="Co-payment" hint="The share of every claim you pay yourself. Enter 0 if none.">
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
        {busy ? 'Working…' : 'Continue'}
      </Button>
    </div>
  )
}
