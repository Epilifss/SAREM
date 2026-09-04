import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import type { BoRecord } from '../types'
import { DataTable } from '../components/ui/DataTable'
import { useAuth } from '../providers/AuthProvider'
import { logApplicationError } from '../services/errorLogger'

export default function BoList() {
  const [bos, setBos] = useState<BoRecord[]>([])
  const [itemCounts, setItemCounts] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { profile } = useAuth()

  const [filterTerm, setFilterTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterDateStart, setFilterDateStart] = useState('')
  const [filterDateEnd, setFilterDateEnd] = useState('')

  useEffect(() => {
    if (profile) fetchBOs()
  }, [profile])

  const fetchBOs = async (e?: React.FormEvent, filters = { filterTerm, filterStatus, filterDateStart, filterDateEnd }) => {
    if (e) e.preventDefault()
    setLoading(true)

    let query = supabase
      .from('bo_records')
      .select('*')
      .or('d_e_l_e_t_.neq.*,d_e_l_e_t_.is.null')
      .order('created_at', { ascending: false })
      .limit(100)

    if (profile && profile.module !== 'Todos' && !profile.is_admin) {
      query = query.eq('modulo', profile.module)
    }

    if (filters.filterStatus) {
      query = query.eq('status', filters.filterStatus)
    }

    if (filters.filterDateStart) {
      query = query.gte('emissao_totvs', filters.filterDateStart)
    }

    if (filters.filterDateEnd) {
      query = query.lte('emissao_totvs', filters.filterDateEnd)
    }

    if (filters.filterTerm) {
      const term = filters.filterTerm.trim()
      query = query.or(`bo_number.ilike.%${term}%,op.ilike.%${term}%,loja.ilike.%${term}%`)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching BOs:', error.message)
      void logApplicationError(error, { source: 'BoList.fetchBOs' })
    } else {
      setBos(data as BoRecord[])
      const { data: itemRows, error: itemsError } = await supabase
        .from('bo_itens')
        .select('bo_ref')

      if (itemsError) {
        console.error('Error fetching BO item counts:', itemsError.message)
        void logApplicationError(itemsError, { source: 'BoList.fetchItemCounts' })
      } else {
        const counts = (itemRows || []).reduce<Record<string, number>>((result, item) => {
          const key = item.bo_ref?.trim()
          if (key) result[key] = (result[key] || 0) + 1
          return result
        }, {})
        setItemCounts(counts)
      }
    }
    setLoading(false)
  }

  const columns = [
    { header: 'BO', accessor: 'bo_number' as keyof BoRecord },
    { header: 'OP', accessor: 'op' as keyof BoRecord },
    { header: 'Loja', accessor: 'loja' as keyof BoRecord },
    { header: 'Tipo Ocorrência', accessor: 'tipo_ocorrencia' as keyof BoRecord },
    { header: 'Itens', accessor: (row: BoRecord) => itemCounts[row.bo_number.trim()] || 0 },
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
    <div style={{ width: '100%', maxWidth: '1500px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
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
              onChange={e => {
                const value = e.target.value
                setFilterTerm(value)
                fetchBOs(undefined, { filterTerm: value, filterStatus, filterDateStart, filterDateEnd })
              }}
              style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: '1 1 150px' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Status</label>
            <select 
              value={filterStatus}
              onChange={e => {
                const value = e.target.value
                setFilterStatus(value)
                fetchBOs(undefined, { filterTerm, filterStatus: value, filterDateStart, filterDateEnd })
              }}
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
              onChange={e => {
                const value = e.target.value
                setFilterDateStart(value)
                fetchBOs(undefined, { filterTerm, filterStatus, filterDateStart: value, filterDateEnd })
              }}
              style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: '1 1 120px' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Emissão (Fim)</label>
            <input 
              type="date" 
              value={filterDateEnd}
              onChange={e => {
                const value = e.target.value
                setFilterDateEnd(value)
                fetchBOs(undefined, { filterTerm, filterStatus, filterDateStart, filterDateEnd: value })
              }}
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

      <div style={{ maxHeight: 'calc(100vh - 22rem)', minHeight: '260px', overflowY: 'auto', borderRadius: 'var(--radius-lg)' }}>
        <DataTable 
          data={bos} 
          columns={columns} 
          isLoading={loading} 
          onRowClick={(row) => navigate(`/bos/${row.id}`)}
        />
      </div>
    </div>
  )
}
