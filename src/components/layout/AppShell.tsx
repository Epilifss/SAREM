import { Outlet } from 'react-router-dom'
import { useAuth } from '../../providers/AuthProvider'

export default function AppShell() {
  const { profile, signOut } = useAuth()

  return (
    <div className="app-container">
      {/* TODO: Transform this into a proper Sidebar component */}
      <aside style={{ width: '260px', background: 'var(--surface-color)', borderRight: '1px solid var(--surface-border)', padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary-color)' }}>SAREM Web</h1>
        </div>
        
        <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <a href="/" style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', textDecoration: 'none', color: 'var(--text-primary)', fontWeight: 500, background: 'rgba(79, 70, 229, 0.1)' }}>Dashboard</a>
          <a href="/bos" style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', textDecoration: 'none', color: 'var(--text-secondary)', fontWeight: 500 }}>Boletins</a>
          {profile?.can_track_bo && (
            <a href="/bos/new" style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', textDecoration: 'none', color: 'var(--text-secondary)', fontWeight: 500 }}>Acompanhar BO</a>
          )}
        </nav>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--surface-border)', marginTop: 'auto' }}>
          <div style={{ marginBottom: '1rem' }}>
            <p style={{ fontSize: '0.875rem', fontWeight: 600 }}>{profile?.username}</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Módulo: {profile?.module}</p>
          </div>
          <button 
            onClick={signOut}
            style={{ width: '100%', padding: '0.5rem', background: 'transparent', border: '1px solid var(--surface-border)', borderRadius: 'var(--radius-md)', cursor: 'pointer', color: 'var(--text-secondary)' }}
          >
            Sair
          </button>
        </div>
      </aside>

      <main style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
        <Outlet />
      </main>
    </div>
  )
}
