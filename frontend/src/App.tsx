import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import LandingPage from '@/pages/Landing'
import DashboardPage from '@/pages/Dashboard'
import ProblemsPage from '@/pages/Problems'
import CustomersPage from '@/pages/Customers'
import ImportPage from '@/pages/Import'

export default function App() {
  return (
    <Routes>
      {/* Landing page — sans sidebar */}
      <Route path="/" element={<LandingPage />} />

      {/* Pages dashboard — avec sidebar */}
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/problems" element={<ProblemsPage />} />
        <Route path="/customers" element={<CustomersPage />} />
        <Route path="/import" element={<ImportPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}