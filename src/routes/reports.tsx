import { useEffect, useState, type FormEvent } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../providers/AuthProvider'
import type { BoRecord } from '../types'

type ReportItem = { bo_ref: string; cod: string | null; desc: string | null; motivo: string | null }
type ReportPreset = 'all' | 'open' | 'progress' | 'closed' | 'products'
type ReportRow = Record<string, string>

const presets: Array<{ value: ReportPreset; label: string }> = [
  { value: 'all', label: 'Todos os BOs' },
  { value: 'open', label: 'BOs em aberto' },
  { value: 'progress', label: 'BOs em andamento' },
  { value: 'closed', label: 'BOs encerrados' },
  { value: 'products', label: 'Produtos com mais problemas' },
]

const getMessage = (error: unknown) => error instanceof Error ? error.message : String(error)

function formatRows(records: BoRecord[], items: ReportItem[], preset: ReportPreset): ReportRow[] {
  if (preset === 'products') {
    const products = items.reduce<Record<string, { description: string; count: number }>>((result, item) => {
      const code = item.cod?.trim() || 'Não informado'
      const current = result[code] || { description: item.desc?.trim() || 'Descrição não informada', count: 0 }
      result[code] = { description: current.description, count: current.count + 1 }
      return result
    }, {})
    return Object.entries(products).sort(([, left], [, right]) => right.count - left.count).map(([code, product]) => ({
      Produto: code,
      Descrição: product.description,
      Ocorrências: String(product.count),
    }))
  }

  return records.map(record => ({
    BO: record.bo_number,
    OP: record.op || '-',
    Loja: record.loja || '-',
    Status: record.status || 'Não informado',
    Setor: record.setor_responsavel || 'Não informado',
    Módulo: record.modulo || 'Não informado',
    Causa: record.causa || 'Não informado',
    Custo: record.custo || 'Não informado',
  }))
}

export default function Reports() {
  const { profile } = useAuth()
  const [records, setRecords] = useState<BoRecord[]>([])
  const [items, setItems] = useState<ReportItem[]>([])
  const [rows, setRows] = useState<ReportRow[]>([])
  const [preset, setPreset] = useState<ReportPreset>('all')
  const [term, setTerm] = useState('')
  const [status, setStatus] = useState('')
  const [module, setModule] = useState('')
  const [sector, setSector] = useState('')
  const [cause, setCause] = useState('')
  const [dateStart, setDateStart] = useState('')
  const [dateEnd, setDateEnd] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generated, setGenerated] = useState(false)

  useEffect(() => {
    if (!profile) return
    const loadOptions = async () => {
      let query = supabase.from('bo_records').select('*').or('d_e_l_e_t_.neq.*,d_e_l_e_t_.is.null')
      if (profile.module !== 'Todos' && !profile.is_admin) query = query.eq('modulo', profile.module)
      const { data, error: queryError } = await query.order('created_at', { ascending: false })
      if (queryError) throw queryError
      const loadedRecords = (data || []) as BoRecord[]
      setRecords(loadedRecords)
      const boNumbers = loadedRecords.map(record => record.bo_number)
      if (boNumbers.length) {
        const { data: itemData, error: itemError } = await supabase.from('bo_itens').select('bo_ref, cod, desc, motivo').in('bo_ref', boNumbers)
        if (itemError) throw itemError
        setItems((itemData || []) as ReportItem[])
      }
    }

    loadOptions().catch(errorValue => setError(getMessage(errorValue)))
  }, [profile])

  const generateReport = (event?: FormEvent) => {
    event?.preventDefault()
    setLoading(true)
    setError(null)
    try {
      if (dateStart && dateEnd && dateStart > dateEnd) throw new Error('A data inicial não pode ser maior que a data final.')
      const filtered = records.filter(record => {
        const searchable = `${record.bo_number} ${record.op || ''} ${record.loja || ''}`.toLocaleLowerCase()
        const matchesPreset = preset === 'all' || (preset === 'open' && record.status !== 'Embarcado') || (preset === 'progress' && record.status === 'Em Andamento') || (preset === 'closed' && record.status === 'Embarcado')
        const matchesTerm = !term.trim() || searchable.includes(term.trim().toLocaleLowerCase())
        const matchesStatus = !status || record.status === status
        const matchesModule = !module || record.modulo === module
        const matchesSector = !sector || record.setor_responsavel === sector
        const matchesCause = !cause || record.causa === cause
        const matchesStart = !dateStart || (record.emissao_totvs || '') >= dateStart
        const matchesEnd = !dateEnd || (record.emissao_totvs || '') <= dateEnd
        return matchesPreset && matchesTerm && matchesStatus && matchesModule && matchesSector && matchesCause && matchesStart && matchesEnd
      })
      const filteredItems = preset === 'products' ? items.filter(item => filtered.some(record => record.bo_number.trim() === item.bo_ref.trim())) : items
      setRows(formatRows(filtered, filteredItems, preset))
      setGenerated(true)
    } catch (errorValue) {
      setError(getMessage(errorValue))
    } finally {
      setLoading(false)
    }
  }

  const unique = (values: Array<string | null>) => [...new Set(values.map(value => value?.trim()).filter(Boolean) as string[])].sort()
  const reportTitle = presets.find(option => option.value === preset)?.label || 'Relatório personalizado'
  const headers = Object.keys(rows[0] || {})

  return (
    <div className="reports-page">
      <div className="page-heading-row">
        <div><h1>Relatórios</h1><p>Escolha um modelo pronto ou combine filtros para emitir um relatório personalizado.</p></div>
      </div>
      <form className="reports-filter-panel" onSubmit={generateReport}>
        <div className="reports-filter-heading"><div><h2>Parâmetros do relatório</h2><span>{generated ? `${rows.length} registros encontrados` : 'Defina os filtros e gere o relatório'}</span></div><button className="primary-action" type="submit" disabled={loading}>{loading ? 'Gerando...' : 'Gerar relatório'}</button></div>
        {error && <div className="dashboard-error">{error}</div>}
        <div className="reports-filter-grid">
          <div className="form-group"><label htmlFor="report-preset">Relatório predefinido</label><select id="report-preset" value={preset} onChange={event => setPreset(event.target.value as ReportPreset)}>{presets.map(option => <option value={option.value} key={option.value}>{option.label}</option>)}</select></div>
          <div className="form-group"><label htmlFor="report-term">Buscar BO, OP ou loja</label><input id="report-term" value={term} onChange={event => setTerm(event.target.value)} placeholder="Digite um termo" /></div>
          <div className="form-group"><label htmlFor="report-status">Status</label><select id="report-status" value={status} onChange={event => setStatus(event.target.value)}><option value="">Todos</option>{unique(records.map(record => record.status)).map(value => <option key={value}>{value}</option>)}</select></div>
          <div className="form-group"><label htmlFor="report-module">Módulo</label><select id="report-module" value={module} onChange={event => setModule(event.target.value)}><option value="">Todos</option>{unique(records.map(record => record.modulo)).map(value => <option key={value}>{value}</option>)}</select></div>
          <div className="form-group"><label htmlFor="report-sector">Setor responsável</label><select id="report-sector" value={sector} onChange={event => setSector(event.target.value)}><option value="">Todos</option>{unique(records.map(record => record.setor_responsavel)).map(value => <option key={value}>{value}</option>)}</select></div>
          <div className="form-group"><label htmlFor="report-cause">Causa</label><select id="report-cause" value={cause} onChange={event => setCause(event.target.value)}><option value="">Todas</option>{unique(records.map(record => record.causa)).map(value => <option key={value}>{value}</option>)}</select></div>
          <div className="form-group"><label htmlFor="report-date-start">Emissão a partir de</label><input id="report-date-start" type="date" value={dateStart} onChange={event => setDateStart(event.target.value)} /></div>
          <div className="form-group"><label htmlFor="report-date-end">Emissão até</label><input id="report-date-end" type="date" value={dateEnd} onChange={event => setDateEnd(event.target.value)} /></div>
        </div>
      </form>
      <section className="reports-result-panel">
        <div className="reports-result-heading"><div><h2>{reportTitle}</h2><span>{generated ? 'Resultado pronto para impressão' : 'O resultado aparecerá aqui'}</span></div><button className="secondary-action" type="button" onClick={() => window.print()} disabled={!generated || rows.length === 0}>Imprimir relatório</button></div>
        {!generated ? <div className="reports-empty">Configure os parâmetros acima e clique em “Gerar relatório”.</div> : rows.length === 0 ? <div className="reports-empty">Nenhum registro encontrado para os filtros selecionados.</div> : <div className="dashboard-table-wrap"><table className="dashboard-table reports-table"><thead><tr>{headers.map(header => <th key={header}>{header}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.BO || row.Produto || 'linha'}-${index}`}>{headers.map(header => <td key={header}>{row[header]}</td>)}</tr>)}</tbody></table></div>}
      </section>
    </div>
  )
}
