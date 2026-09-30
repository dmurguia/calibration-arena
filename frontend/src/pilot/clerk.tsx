import { ClerkProvider, useAuth } from '@clerk/react'
import { ReactNode, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { call, clearToken, Me, setToken, token } from './api'

export const clerkPublishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined
export const clerkEnabled = Boolean(clerkPublishableKey)

export function ClerkRoot({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  if (!clerkEnabled) return <>{children}</>
  return <ClerkProvider
    publishableKey={clerkPublishableKey!}
    routerPush={to => navigate(to)}
    routerReplace={to => navigate(to, { replace: true })}
    signInUrl="/signin"
    signUpUrl="/signup"
    afterSignOutUrl="/"
    appearance={{
      // Calibrated Co. tokens (src/styles/calibrated.css). Clerk needs literal values, not CSS vars.
      variables: {
        colorPrimary: '#464643',
        colorPrimaryForeground: '#F4F1E9',
        colorBackground: '#FAF9F6',
        colorForeground: '#464643',
        colorMutedForeground: '#656460',
        colorMuted: '#F4F1E9',
        colorInput: '#FAF9F6',
        colorInputForeground: '#464643',
        colorBorder: '#46464355',
        colorRing: '#656460',
        colorDanger: '#70543E',
        colorSuccess: '#464643',
        colorWarning: '#70543E',
        colorShadow: 'transparent',
        colorModalBackdrop: '#46464366',
        fontFamily: "'IBM Plex Sans', sans-serif",
        fontFamilyButtons: "'IBM Plex Sans', sans-serif",
        fontFamilyMono: "'IBM Plex Mono', monospace",
        fontWeight: { normal: 400, medium: 500, semibold: 500, bold: 500 },
        borderRadius: '12px',
      },
      elements: {
        // The page already carries the eyebrow, title and lead; Clerk's own header would repeat it.
        header: { display: 'none' },
        cardBox: { boxShadow: 'none', border: '1px solid #46464333', borderRadius: '20px' },
        footer: { backgroundImage: 'none', background: '#F4F1E9' },
      },
      // Shadows, the button sheen and leather hover are flattened in pilot.css (.cl-* rules).
    }}
  >
    {children}
  </ClerkProvider>
}

export function ClerkBridge({
  ready,
  me,
  refresh,
  onError,
}: {
  ready: boolean
  me: Me | null
  refresh: () => Promise<void>
  onError: (message: string) => void
}) {
  const { getToken, isLoaded, isSignedIn } = useAuth()
  const exchanging = useRef(false)
  const clearingSignedOut = useRef(false)

  useEffect(() => {
    if (!ready || !isLoaded) return
    if (isSignedIn) {
      clearingSignedOut.current = false
      if (me?.account?.provider === 'clerk' || exchanging.current) return
      exchanging.current = true
      onError('')
      void (async () => {
        try {
          const jwt = await getToken()
          if (!jwt) throw new Error('Your sign-in could not be verified. Please sign in again.')
          const result = await call<{ token: string }>(
            '/auth/clerk',
            { guest_token: token() ?? null },
            {},
            jwt,
          )
          setToken(result.token)
          await refresh()
        } catch (error) {
          onError(error instanceof Error ? error.message : 'Sign-in is temporarily unavailable. Please try again.')
        }
      })()
      return
    }

    exchanging.current = false
    if (!me?.account || clearingSignedOut.current) return
    clearingSignedOut.current = true
    clearToken()
    void refresh().catch(error => {
      onError(error instanceof Error ? error.message : 'Could not refresh your session.')
    })
  }, [getToken, isLoaded, isSignedIn, me?.account, onError, ready, refresh])

  return null
}
