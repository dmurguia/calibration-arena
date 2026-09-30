import { useEffect } from 'react'
import { XIcon } from 'lucide-react'
import { useAuth } from '../../lib/auth'
import { CalibratedMark } from '../brand/CalibratedMark'
import { AuthPanel } from './AuthPanel'

const reasons: Record<string, { title: string; body: string }> = {
  search: {
    title: 'Sign in to Calibration Arena',
    body: 'Searching your work needs an account — your sessions are private to you.',
  },
  projects: {
    title: 'Sign in to Calibration Arena',
    body: 'Your projects live in your account. Sign in to pick up where you left off.',
  },
  judging: {
    title: 'Keep judging — make it count.',
    body: 'Sign in with your work email so your votes carry weight on the boards. Your bracket picks up right where you left it.',
  },
}

export function AuthModal() {
  const { gate, dismissAuth } = useAuth()

  useEffect(() => {
    if (!gate) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') dismissAuth()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [gate, dismissAuth])

  if (!gate) return null
  const reason = reasons[gate] ?? reasons.projects

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close sign in"
        onClick={dismissAuth}
        className="absolute inset-0 bg-ink/25"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-title"
        className="relative w-full max-w-[420px] rounded-xl border border-hairline bg-card p-7 shadow-lift"
      >
        <button
          type="button"
          onClick={dismissAuth}
          aria-label="Close"
          className="absolute right-4 top-4 text-muted transition-colors duration-150 ease-out hover:text-ink"
        >
          <XIcon className="h-4 w-4" />
        </button>

        <CalibratedMark size={26} className="text-ink" title="Calibrated Co." />
        <div className="mt-4" id="auth-title">
          <AuthPanel title={reason.title} body={reason.body} onDone={dismissAuth} />
        </div>
      </div>
    </div>
  )
}
