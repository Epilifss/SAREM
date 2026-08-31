import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { BoRecord } from '../types'
import { DataTable } from '../components/ui/DataTable'
import { useAuth } from '../providers/AuthProvider'

export default function BoList() {
  const [bos, setBos] = useState<BoRecord[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { profile } = useAuth()

  useEffect(() => {
    fetchBOs()
  }, [])

  const fetchBOs = async () => {
    setLoading(true)
    const { data, error } = await supabase
      .from('bo_records')
      .select('*')
      .eq('is_deleted', false)
      .order('created_at', { ascending: false })
      .limit(50)

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
    { header: 'Status', accessor: 'status' as keyof BoRecord },
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

      <div style={{ background: 'var(--surface-color)', padding: '1rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)' }}>
        {/* Placeholder para os Filtros */}
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Filtros em construção...</p>
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
