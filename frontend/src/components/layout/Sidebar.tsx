import { NavLink } from 'react-router-dom'
import { useUser, useClerk } from '@clerk/clerk-react'
import {
  LayoutDashboard, AlertTriangle, Users,
  Upload, TrendingUp, LogOut
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { label: "Vue d'ensemble", href: '/dashboard', icon: LayoutDashboard },
  { label: 'Top Problèmes', href: '/problems', icon: AlertTriangle },
  { label: 'Clients à risque', href: '/customers', icon: Users },
  { label: 'Importer', href: '/import', icon: Upload },
]

export function Sidebar() {
  const { user } = useUser()
  const { signOut } = useClerk()

  return (
    <aside className="flex h-screen w-56 flex-col bg-zinc-900 border-r border-zinc-800">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 px-5 border-b border-zinc-800">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-white/10">
          <TrendingUp className="h-4 w-4 text-white" />
        </div>
        <span className="text-sm font-semibold text-white">CFRI</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3">
        <ul className="space-y-0.5">
          {navItems.map((item) => (
            <li key={item.href}>
              <NavLink
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
                    isActive
                      ? 'bg-white/10 text-white font-medium'
                      : 'text-zinc-400 hover:bg-white/5 hover:text-white'
                  )
                }
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer — utilisateur connecté */}
      <div className="p-3 border-t border-zinc-800 space-y-2">
        {/* Infos utilisateur */}
        <div className="rounded-md bg-white/5 px-3 py-2">
          <p className="text-xs text-zinc-500 truncate">
            {user?.primaryEmailAddress?.emailAddress ?? 'Utilisateur'}
          </p>
          <p className="text-xs text-zinc-400 mt-0.5">
            {user?.organizationMemberships?.[0]?.organization?.name ?? 'Organisation'}
          </p>
        </div>

        {/* Bouton déconnexion */}
        <button
          onClick={() => signOut({ redirectUrl: '/' })}
          className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-xs text-zinc-500 hover:bg-white/5 hover:text-zinc-300 transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          Se déconnecter
        </button>
      </div>
    </aside>
  )
}