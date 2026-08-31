import { useEffect, useState } from 'react'
import { useAuth } from '../providers/AuthProvider'
import { supabase } from '../lib/supabase'

export default function Dashboard() {
  const { profile } = useAuth()
  const [stats, setStats] = useState({
    abertos: 0,
    emAndamento: 0,
    encerrados: 0,
    total: 0
  })

  useEffect(() => {
    if (profile) fetchStats()
  }, [profile])

  const fetchStats = async () => {
    let query = supabase
      .from('bo_records')
      .select('status')
      .eq('is_deleted', false)

    if (profile && profile.module !== 'Todos' && !profile.is_admin) {
      query = query.eq('modulo', profile.module)
    }

    const { data, error } = await query

    if (!error && data) {
      const emAndamento = data.filter(b => b.status === 'Em Andamento').length
      const encerrados = data.filter(b => b.status === 'Embarcado').length
      const abertos = data.filter(b => b.status !== 'Embarcado').length

      setStats({
        abertos,
        emAndamento,
        encerrados,
        total: data.length
      })
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Dashboard</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Visão geral dos Boletins de Ocorrência.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
        <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
          <h3 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>BOs em Aberto</h3>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--primary-color)' }}>{stats.abertos}</p>
        </div>

        <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
          <h3 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Em Andamento</h3>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: '#f59e0b' }}>{stats.emAndamento}</p>
        </div>

        <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
          <h3 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Encerrados</h3>
          <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--success-color)' }}>{stats.encerrados}</p>
        </div>

        <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
          <h3 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Total Histórico</h3>
          <p style={{ fontSize: '2rem', fontWeight: 700 }}>{stats.total}</p>
        </div>
      </div>
    </div>
  )
}
