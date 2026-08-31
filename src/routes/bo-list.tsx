import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import type { BoRecord } from '../types'
import { DataTable } from '../components/ui/DataTable'
import { useAuth } from '../providers/AuthProvider'

export default function BoList() {
  const [bos, setBos] = useState<BoRecord[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { profile } = useAuth()

  const [filterTerm, setFilterTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterDateStart, setFilterDateStart] = useState('')
  const [filterDateEnd, setFilterDateEnd] = useState('')

  useEffect(() => {
    fetchBOs()
  }, []) // initial load

  const fetchBOs = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setLoading(true)

    let query = supabase
      .from('bo_records')
      .select('*')
      .eq('is_deleted', false)
      .order('created_at', { ascending: false })
      .limit(100)

    if (filterStatus) {
      query = query.eq('status', filterStatus)
    }

    if (filterDateStart) {
      query = query.gte('emissao_totvs', filterDateStart)
    }

    if (filterDateEnd) {
      query = query.lte('emissao_totvs', filterDateEnd)
    }

    if (filterTerm) {
      const term = filterTerm.trim()
      query = query.or(`bo_number.ilike.%${term}%,op.ilike.%${term}%,loja.ilike.%${term}%`)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching BOs:', error.message)
    } else {
      setBos(data as BoRecord[])
    }
    setLoading(false)
  }

  const columns = [
    { header: 'BO', accessor: 'bo_number' as keyof BoRecord },
    { header: 'OP', accessor: 'op' as keyof BoRecord },
    { header: 'Loja', accessor: 'loja' as keyof BoRecord },
    { header: 'Tipo Ocorrência', accessor: 'tipo_ocorrencia' as keyof BoRecord },
    { header: 'Status', accessor: (row: BoRecord) => (
        <span style={{ 
          fontSize: '0.8rem', padding: '0.2rem 0.5rem', borderRadius: '12px',
          background: row.status === 'Embarcado' ? 'var(--success-color)' : 'var(--primary-color)', color: 'white' 
        }}>
          {row.status}
        </span>
      ) 
    },
    { 
      header: 'Emissão Totvs', 
      accessor: (row: BoRecord) => row.emissao_totvs ? new Date(row.emissao_totvs).toLocaleDateString() : '-' 
    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Boletins de Ocorrência</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Acompanhamento e listagem de BOs do seu módulo.</p>
        </div>
        {profile?.can_track_bo && (
          <button 
            onClick={() => navigate('/bos/new')}
            style={{ 
              background: 'linear-gradient(135deg, var(--primary-color), var(--secondary-color))',
              color: 'white', padding: '0.75rem 1.25rem', borderRadius: 'var(--radius-md)', 
              border: 'none', fontWeight: 600, cursor: 'pointer', boxShadow: 'var(--shadow-md)' 
            }}
          >
            + Acompanhar BO
          </button>
        )}
      </div>

      <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
        <form onSubmit={fetchBOs} style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'flex-end' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: '1 1 200px' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Buscar</label>
            <input 
              type="text" 
              placeholder="BO, OP ou Loja..." 
              value={filterTerm}
              onChange={e => setFilterTerm(e.target.value)}
              style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: '1 1 150px' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Status</label>
            <select 
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}
            >
              <option value="">Todos</option>
              <option value="Em Andamento">Em Andamento</option>
              <option value="Aguardando Aprovação">Aguardando Aprovação</option>
              <option value="Aguardando Coleta">Aguardando Coleta</option>
              <option value="Embarcado">Embarcado</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: '1 1 120px' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Emissão (Início)</label>
            <input 
              type="date" 
              value={filterDateStart}
              onChange={e => setFilterDateStart(e.target.value)}
              style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: '1 1 120px' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Emissão (Fim)</label>
            <input 
              type="date" 
              value={filterDateEnd}
              onChange={e => setFilterDateEnd(e.target.value)}
              style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}
            />
          </div>

          <button 
            type="submit" 
            style={{ padding: '0.75rem 1.5rem', background: 'var(--primary-color)', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer' }}
          >
            Filtrar
          </button>
        </form>
      </div>

      <DataTable 
        data={bos} 
        columns={columns} 
        isLoading={loading} 
        onRowClick={(row) => navigate(`/bos/${row.id}`)}
      />
    </div>
  )
}
