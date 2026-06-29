import { useAuth } from '@clerk/clerk-react'
import { Navigate, Outlet } from 'react-router-dom'

export function ProtectedRoute() {
  const { isLoaded, isSignedIn } = useAuth()

  // Clerk charge les infos de session au démarrage
  // On attend que ce soit prêt avant de décider
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-50">
        <p className="text-zinc-400 text-sm">Chargement...</p>
      </div>
    )
  }

  // Pas connecté → redirection vers login
  if (!isSignedIn) {
    return <Navigate to="/sign-in" replace />
  }

  // Connecté → afficher la page demandée
  return <Outlet />
}