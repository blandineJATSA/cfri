import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import LandingPage from '@/pages/Landing'
import SignInPage from '@/pages/SignIn'
import SignUpPage from '@/pages/SignUp'
import DashboardPage from '@/pages/Dashboard'
import ProblemsPage from '@/pages/Problems'
import CustomersPage from '@/pages/Customers'
import ImportPage from '@/pages/Import'
import SettingsPage from '@/pages/Settings'

export default function App() {
  return (
    <Routes>
      {/* Pages publiques */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/sign-in/*" element={<SignInPage />} />
      <Route path="/sign-up/*" element={<SignUpPage />} />

      {/* Pages protégées — nécessite d'être connecté */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/problems" element={<ProblemsPage />} />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="/import" element={<ImportPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}