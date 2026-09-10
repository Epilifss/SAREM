import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/navigation/ProtectedRoute'
import AppShell from './components/layout/AppShell'
import AuthPage from './routes/auth'
import Dashboard from './routes/dashboard'
import BoList from './routes/bo-list'
import BoNew from './routes/bo-new'
import BoDetail from './routes/bo-detail'
import AdminUsers from './routes/admin-users'
import ProfilePage from './routes/profile'
import AdminErrorLogs from './routes/admin-error-logs'
import Reports from './routes/reports'
import { supabase } from './lib/supabase'
import { useAuth } from './providers/AuthProvider'





function ShipmentSyncScheduler() {
  const { profile } = useAuth()

  useEffect(() => {
    if (!profile) return

    let cancelled = false
    let timer: number | undefined

    const schedule = async () => {
      const { data } = await supabase
        .from('app_settings')
        .select('value')
        .eq('key', 'shipment_check_interval_minutes')
        .maybeSingle()

      const minutes = Number((data?.value as { minutes?: number } | null)?.minutes)
      const intervalMs = Math.max(1, Number.isFinite(minutes) ? minutes : 5) * 60 * 1000

      await supabase.functions.invoke('sync-embarked-bos', { body: {} })
      if (!cancelled) timer = window.setTimeout(schedule, intervalMs)
    }

    void schedule()
    return () => {
      cancelled = true
      if (timer) window.clearTimeout(timer)
    }
  }, [profile])

  return null
}

function App() {
  return (
    <>
      <ShipmentSyncScheduler />
    <Routes>
      <Route path="/login" element={<AuthPage />} />
      
      <Route path="/" element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="reports" element={<Reports />} />
        <Route path="bos" element={<BoList />} />
        <Route path="bos/new" element={<BoNew />} />
        <Route path="bos/:id" element={<BoDetail />} />
        <Route path="admin/users" element={<AdminUsers />} />
        <Route path="admin/error-logs" element={<AdminErrorLogs />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
    </>
  )
}

export default App
