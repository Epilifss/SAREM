import { Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/navigation/ProtectedRoute'
import AppShell from './components/layout/AppShell'
import AuthPage from './routes/auth'
import Dashboard from './routes/dashboard'
import BoList from './routes/bo-list'
import BoNew from './routes/bo-new'
import BoDetail from './routes/bo-detail'
import AdminUsers from './routes/admin-users'





function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage />} />
      
      <Route path="/" element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="bos" element={<BoList />} />
        <Route path="bos/new" element={<BoNew />} />
        <Route path="bos/:id" element={<BoDetail />} />
        <Route path="admin/users" element={<AdminUsers />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
