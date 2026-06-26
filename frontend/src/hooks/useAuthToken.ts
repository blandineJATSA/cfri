import { useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { setAuthToken } from '@/lib/api'

export function useAuthToken() {
  const { getToken, isSignedIn, isLoaded } = useAuth()

  useEffect(() => {
    if (!isLoaded) return

    if (!isSignedIn) {
      setAuthToken(null)
      return
    }

    // Récupérer le token et l'injecter dans Axios
    const injectToken = async () => {
      const token = await getToken()
      setAuthToken(token)
    }

    injectToken()

    // Renouveler le token toutes les 50 secondes
    // (les tokens Clerk expirent après 60 secondes)
    const interval = setInterval(injectToken, 50000)
    return () => clearInterval(interval)
  }, [isLoaded, isSignedIn, getToken])
}