import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../../providers/AuthProvider'

export default function AppShell() {
  const { profile, signOut } = useAuth()
  const { pathname } = useLocation()
  const linkStyle = (isActive: boolean) => ({
    padding: '0.75rem',
    borderRadius: 'var(--radius-md)',
    textDecoration: 'none',
    color: isActive ? 'var(--primary-color)' : 'var(--text-secondary)',
    fontWeight: 500,
    background: isActive ? 'rgba(79, 70, 229, 0.1)' : 'transparent',
  })
  const isBoListActive = pathname === '/bos' || (pathname.startsWith('/bos/') && pathname !== '/bos/new')

  return (
    <div className="app-container">
      <aside className="app-sidebar">
        <div className="app-brand">
          <img src="/favicon.svg" alt="SAREM" />
          <span>SAREM</span>
        </div>
        
        <nav className="app-nav">
          <NavLink to="/" end style={({ isActive }) => linkStyle(isActive)}>Dashboard</NavLink>
          <NavLink to="/bos" style={() => linkStyle(isBoListActive)}>Boletins</NavLink>
          {profile?.can_track_bo && (
            <NavLink to="/bos/new" style={() => linkStyle(pathname === '/bos/new')}>Acompanhar BO</NavLink>
          )}
          {profile?.is_admin && (
            <NavLink to="/admin/users" style={({ isActive }) => ({ ...linkStyle(isActive), marginTop: '1rem', borderTop: '1px solid var(--surface-border)' })}>Gestão de Usuários</NavLink>
          )}
        </nav>

        <div className="app-user-panel">
          <div className="app-user-details">
            <p style={{ fontSize: '0.875rem', fontWeight: 600 }}>{profile?.username}</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Módulo: {profile?.module}</p>
          </div>
          <button className="app-signout"
            onClick={signOut}
          >
            Sair
          </button>
        </div>
      </aside>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
