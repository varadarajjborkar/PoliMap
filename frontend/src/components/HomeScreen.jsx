import { useState } from 'react'
import { describeStay } from '../lib/stays'
import { Button, Card, Disclaimer, Input } from './Primitives'

// The screen before anything else.
//
// It asks for a name and nothing more. There is no password because there is no
// account: the name picks which set of stays on this device to open, and that
// is all it does. Saying so plainly matters, because a family being asked to
// register during an admission will simply close the tab.

export function SignIn({ onSignIn }) {
  const [name, setName] = useState('')
  const clean = name.trim()

  return (
    <div className="mx-auto flex max-w-md flex-col justify-center px-4 py-16 motion-safe:animate-rise">
      <div className="text-center">
        <img
          src="/logo-64.png" alt="" width="52" height="52"
          className="mx-auto h-13 w-13"
        />
        <h1 className="mt-4 text-2xl font-semibold tracking-tight">
          Know what your hospital stay will cost
        </h1>
        <p className="mx-auto mt-2.5 max-w-sm text-[0.9375rem] leading-relaxed text-muted">
          Choose a name to keep your admissions under. It stays on this device.
        </p>
      </div>

      <Card className="mt-7 p-5">
        <form
          onSubmit={(e) => { e.preventDefault(); if (clean) onSignIn(clean) }}
          className="space-y-3.5"
        >
          <label className="block">
            <span className="mb-1.5 block text-[0.9375rem] font-medium">
              What should we call you?
            </span>
            <Input
              autoFocus
              value={name}
              maxLength={40}
              placeholder="Your name, or anything you will remember"
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <Button type="submit" className="w-full" disabled={!clean}>
            Continue
          </Button>
        </form>

        <p className="mt-4 border-t border-line pt-3.5 text-[0.875rem] leading-relaxed text-muted">
          There is no password and no account. Nothing you enter is sent
          anywhere to identify you, and a different name on this device opens a
          different, separate set of stays.
        </p>
      </Card>

      <Disclaimer className="mt-6 text-center" />
    </div>
  )
}

export function StayList({ user, stays, onOpen, onNew, onDelete, onSwitchUser }) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-10 motion-safe:animate-rise">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome back, {user}
          </h1>
          <p className="mt-1.5 text-[0.9375rem] text-muted">
            {stays.length
              ? 'Pick up where you left off, or start a new admission.'
              : 'Start by reading a policy. Everything after that is saved here.'}
          </p>
        </div>
        <button
          onClick={onSwitchUser}
          className="shrink-0 text-[0.875rem] text-muted underline-offset-2 transition hover:text-brand hover:underline"
        >
          Not you?
        </button>
      </div>

      <Button className="mt-6 w-full py-3 text-[0.9375rem]" onClick={onNew}>
        Start a new stay
      </Button>

      {stays.length > 0 && (
        <>
          <h2 className="mt-9 mb-2.5 text-[0.9375rem] font-semibold">
            Your stays
          </h2>
          <ul className="space-y-2.5">
            {stays.map((stay, index) => (
              <li
                key={stay.id}
                style={{ animationDelay: `${Math.min(index, 6) * 45}ms` }}
                className="motion-safe:animate-rise"
              >
                <Card className="flex items-center gap-3 p-3.5 transition hover:border-brand/40 hover:shadow-sm">
                  <button
                    onClick={() => onOpen(stay)}
                    className="min-w-0 flex-1 text-left"
                  >
                    <span className="block truncate text-[0.9375rem] font-medium">
                      {describeStay(stay)}
                    </span>
                    <span className="mt-0.5 block truncate text-[0.875rem] text-muted">
                      {[stay.procedure, stay.stageLabel]
                        .filter(Boolean).join(' · ') || 'Policy read'}
                      {' · '}
                      {relativeTime(stay.updatedAt)}
                    </span>
                  </button>
                  <button
                    onClick={() => onDelete(stay)}
                    aria-label={`Delete ${describeStay(stay)}`}
                    className="shrink-0 rounded-lg px-2.5 py-2 text-[0.8125rem] text-muted transition hover:bg-danger-soft hover:text-danger"
                  >
                    Delete
                  </button>
                </Card>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-[0.875rem] leading-relaxed text-muted">
            These are stored on this device only. Clearing your browser data
            removes them.
          </p>
        </>
      )}

      <Disclaimer className="mt-8" />
    </div>
  )
}

function relativeTime(at) {
  if (!at) return 'just now'
  const minutes = Math.round((Date.now() - at) / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} hr ago`
  const days = Math.round(hours / 24)
  return days === 1 ? 'yesterday' : `${days} days ago`
}
