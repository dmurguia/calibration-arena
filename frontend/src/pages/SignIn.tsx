import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppShell } from '../components/app/AppShell'
import { PaperTexture } from '../components/brand/PaperTexture'
import { CalibratedMark } from '../components/brand/CalibratedMark'
import { AuthPanel } from '../components/app/AuthPanel'
import { useAuth } from '../lib/auth'

export function SignIn() {
  const { user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (user) navigate('/', { replace: true })
  }, [user, navigate])

  return (
    <AppShell>
      <div className="relative flex min-h-screen items-center justify-center px-6">
        <PaperTexture seed={19} />
        <div className="relative w-full max-w-[420px] rounded-xl border border-hairline bg-card p-7 shadow-lift">
          <CalibratedMark size={26} className="text-ink" title="Calibrated Co." />
          <div className="mt-4">
            <AuthPanel onDone={() => navigate('/')} />
          </div>
        </div>
      </div>
    </AppShell>
  )
}
