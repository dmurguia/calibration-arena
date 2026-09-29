import { FormEvent, ReactNode, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { call, setToken } from './api'

function AuthPage({ title, children }: { title: string; children: ReactNode }) {
  return <div className="p-narrow"><p className="p-eyebrow">Your Calibrated account</p><h1>{title}</h1>{children}</div>
}

function ErrorMessage({ message }: { message: string }) {
  return message ? <p className="p-error" role="alert">{message}</p> : null
}

interface AuthResult { token: string }

export function SignIn({ onSignedIn, embedded = false }: { onSignedIn: () => Promise<void>; embedded?: boolean }) {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const result = await call<AuthResult>('/auth/login', { email, password })
      setToken(result.token)
      await onSignedIn()
      if (!embedded) navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not sign in.')
    } finally {
      setBusy(false)
    }
  }
  const form = <form className="p-card" onSubmit={submit}>
      <label>Email<input type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} /></label>
      <label>Password<input type="password" required maxLength={256} autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} /></label>
      <ErrorMessage message={error} />
      <button className="p-button" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
    </form>
  if (embedded) return form
  return <AuthPage title="Sign in.">
    <p className="p-lead">Your notebook follows your account across devices.</p>
    {form}
    <p className="p-fine">Forgot your password? Ask the Calibrated team for a reset link.</p>
    <p className="p-fine">New here? <Link to="/signup">Create an account</Link>.</p>
  </AuthPage>
}

export function SignUp({ onSignedIn }: { onSignedIn: () => Promise<void> }) {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const result = await call<AuthResult>('/auth/signup', { name, email, password })
      setToken(result.token)
      await onSignedIn()
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create your account.')
    } finally {
      setBusy(false)
    }
  }
  return <AuthPage title="Keep your notebook.">
    <p className="p-lead">Create an account to return to your sessions on any device.</p>
    <form className="p-card" onSubmit={submit}>
      <label>Name<input required minLength={1} maxLength={120} autoComplete="name" value={name} onChange={e => setName(e.target.value)} /></label>
      <label>Email<input type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} /></label>
      <label>Password<input type="password" required minLength={10} maxLength={256} autoComplete="new-password" value={password} onChange={e => setPassword(e.target.value)} /><span className="p-fine">Use at least 10 characters.</span></label>
      <ErrorMessage message={error} />
      <button className="p-button" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</button>
    </form>
    <p className="p-fine">Already have an account? <Link to="/signin">Sign in</Link>.</p>
  </AuthPage>
}

export function Reset({ onSignedIn }: { onSignedIn: () => Promise<void> }) {
  const location = useLocation()
  const navigate = useNavigate()
  const resetToken = new URLSearchParams(location.hash.slice(1)).get('token') || ''
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const result = await call<AuthResult>('/auth/reset', { token: resetToken, password })
      setToken(result.token)
      await onSignedIn()
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not reset your password.')
    } finally {
      setBusy(false)
    }
  }
  return <AuthPage title="Choose a new password.">
    {resetToken ? <form className="p-card" onSubmit={submit}>
      <label>New password<input type="password" required minLength={10} maxLength={256} autoComplete="new-password" value={password} onChange={e => setPassword(e.target.value)} /><span className="p-fine">Use at least 10 characters.</span></label>
      <ErrorMessage message={error} />
      <button className="p-button" disabled={busy}>{busy ? 'Saving…' : 'Save password'}</button>
    </form> : <p className="p-lead">This reset link is missing or invalid. Ask the Calibrated team for a new link.</p>}
    <p className="p-fine"><Link to="/signin">Return to sign in</Link>.</p>
  </AuthPage>
}
