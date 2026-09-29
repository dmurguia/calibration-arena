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
      variables: {
        colorPrimary: '#303c35',
        colorBackground: '#fcfbf7',
        colorForeground: '#30312e',
        fontFamily: "'Schibsted Grotesk', sans-serif",
        borderRadius: '12px',
      },
    }}
  >
    {children}
  </ClerkProvider>
}

export function ClerkBridge({
  me,
  refresh,
  onError,
}: {
  me: Me | null
  refresh: () => Promise<void>
  onError: (message: string) => void
}) {
  const { getToken, isLoaded, isSignedIn } = useAuth()
  const exchanging = useRef(false)
  const clearingSignedOut = useRef(false)

  useEffect(() => {
    if (!isLoaded) return
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
  }, [getToken, isLoaded, isSignedIn, me?.account, onError, refresh])

  return null
}
