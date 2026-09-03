import { useEffect, useState } from 'react'
import { useAuth } from '../providers/AuthProvider'
import { supabase } from '../lib/supabase'

type DashboardRecord = {
  status: string | null
  setor_responsavel: string | null
  modulo: string | null
  tipo_ocorrencia: string | null
}

type ReportRow = { label: string; count: number }

function countBy(records: DashboardRecord[], field: keyof DashboardRecord): ReportRow[] {
  const counts = records.reduce<Record<string, number>>((result, record) => {
    const value = record[field]?.trim() || 'Não informado'
    result[value] = (result[value] || 0) + 1
    return result
  }, {})

  return Object.entries(counts)
    .map(([label, count]) => ({ label, count }))
    .sort((left, right) => right.count - left.count)
}

function compactRows(rows: ReportRow[], limit = 8): ReportRow[] {
  if (rows.length <= limit) return rows
  const visible = rows.slice(0, limit)
  const others = rows.slice(limit).reduce((total, row) => total + row.count, 0)
  return [...visible, { label: 'Outros', count: others }]
}

function BarReport({ title, rows, color }: { title: string; rows: ReportRow[]; color: string }) {
  const chartRows = compactRows(rows)
  const maximum = chartRows[0]?.count || 1

  return (
    <section className="dashboard-panel">
      <div className="dashboard-panel-heading">
        <h2>{title}</h2>
        <span>{rows.reduce((total, row) => total + row.count, 0)} BOs</span>
      </div>
      {chartRows.length === 0 ? <p className="dashboard-empty">Nenhum dado disponível.</p> : (
        <div className="dashboard-bars">
          {chartRows.map(row => (
            <div className="dashboard-bar-row" key={row.label}>
              <div className="dashboard-bar-label" title={row.label}>
                <span>{row.label}</span>
                <strong>{row.count}</strong>
              </div>
              <div className="dashboard-bar-track">
                <div className="dashboard-bar-fill" style={{ width: `${(row.count / maximum) * 100}%`, background: color }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export default function Dashboard() {
  const { profile } = useAuth()
  const [records, setRecords] = useState<DashboardRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!profile) return

    const fetchDashboard = async () => {
      setLoading(true)
      setError(null)
      let query = supabase
        .from('bo_records')
        .select('status, setor_responsavel, modulo, tipo_ocorrencia')
        .or('d_e_l_e_t_.neq.*,d_e_l_e_t_.is.null')

      if (profile.module !== 'Todos' && !profile.is_admin) query = query.eq('modulo', profile.module)

      const { data, error: queryError } = await query
      if (queryError) setError(queryError.message)
      else setRecords((data as DashboardRecord[]) || [])
      setLoading(false)
    }

    fetchDashboard()
  }, [profile])

  const statusRows = countBy(records, 'status')
  const sectorRows = countBy(records, 'setor_responsavel')
  const moduleRows = countBy(records, 'modulo')
  const occurrenceRows = countBy(records, 'tipo_ocorrencia')
  const closed = records.filter(record => record.status === 'Embarcado').length
  const inProgress = records.filter(record => record.status === 'Em Andamento').length

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <div><h1>Dashboard</h1><p>Visão geral dos Boletins de Ocorrência.</p></div>
        <span className="dashboard-scope">{profile?.module === 'Todos' || profile?.is_admin ? 'Todos os módulos' : `Módulo ${profile?.module}`}</span>
      </div>
      {error && <div className="dashboard-error">Erro ao carregar os relatórios: {error}</div>}
      {loading ? <div className="dashboard-loading">Carregando relatórios...</div> : (
        <>
          <div className="dashboard-stat-grid">
            <div className="dashboard-stat"><span>Total de BOs</span><strong>{records.length}</strong><small>Registros ativos</small></div>
            <div className="dashboard-stat"><span>Em aberto</span><strong>{records.length - closed}</strong><small>Precisam de acompanhamento</small></div>
            <div className="dashboard-stat"><span>Em andamento</span><strong>{inProgress}</strong><small>Status atual</small></div>
            <div className="dashboard-stat"><span>Encerrados</span><strong>{closed}</strong><small>BOs embarcados</small></div>
          </div>
          <div className="dashboard-report-grid">
            <BarReport title="BOs por setor responsável" rows={sectorRows} color="var(--primary-color)" />
            <BarReport title="BOs por status" rows={statusRows} color="var(--secondary-color)" />
            <BarReport title="BOs por módulo" rows={moduleRows} color="var(--accent-color)" />
            <BarReport title="Tipos de ocorrência" rows={occurrenceRows} color="#f59e0b" />
          </div>
          <section className="dashboard-panel dashboard-table-panel">
            <div className="dashboard-panel-heading"><h2>Relatório por setor</h2><span>Distribuição dos registros</span></div>
            <div className="dashboard-table-wrap">
              <table className="dashboard-table">
                <thead><tr><th>Setor responsável</th><th>Quantidade</th><th>Participação</th></tr></thead>
                <tbody>{sectorRows.map(row => <tr key={row.label}><td>{row.label}</td><td>{row.count}</td><td>{records.length ? `${Math.round((row.count / records.length) * 100)}%` : '0%'}</td></tr>)}</tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
