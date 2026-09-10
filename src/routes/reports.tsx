import { useEffect, useState, type FormEvent } from 'react'
import ExcelJS from 'exceljs'
import { supabase } from '../lib/supabase'
import { useAuth } from '../providers/AuthProvider'
import type { BoRecord } from '../types'
import logoSarem from '../img/logo_sarem.svg'
import logoSaremPng from '../img/SAREM.png'
import { toComparableDate } from '../lib/date'

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
const reportFooter = 'Todos os direitos reservados - SAREM'

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
  })[character] || character)
}

async function imageDataUrl(source: string): Promise<string | null> {
  const response = await fetch(source)
  if (!response.ok) return null
  const blob = await response.blob()
  return await new Promise(resolve => {
    const reader = new FileReader()
    reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : null)
    reader.onerror = () => resolve(null)
    reader.readAsDataURL(blob)
  })
}

function printReport(title: string, rows: ReportRow[]) {
  const printWindow = window.open('', '_blank', 'width=1100,height=800')
  if (!printWindow) return
  const generatedAt = new Date().toLocaleString('pt-BR')
  const logoUrl = new URL(logoSarem, window.location.href).href
  const headers = Object.keys(rows[0] || { BO: '', Status: '' })
  const tableRows = rows.map(row => `<tr>${headers.map(header => `<td>${escapeHtml(row[header] || '-')}</td>`).join('')}</tr>`).join('')
  printWindow.document.write(`<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><title>${escapeHtml(title)}</title><style>
    @page { margin: 16mm; } body { font-family: Arial, sans-serif; color: #172033; margin: 0; } header { display: flex; align-items: center; gap: 16px; border-bottom: 2px solid #24577f; padding-bottom: 14px; } header img { width: 130px; max-height: 54px; object-fit: contain; } h1 { font-size: 20px; margin: 0 0 6px; } p { margin: 0; color: #64748b; font-size: 12px; } table { width: 100%; border-collapse: collapse; margin-top: 22px; font-size: 11px; } th, td { border: 1px solid #cbd5e1; padding: 7px; text-align: left; } th { background: #e8f0f6; color: #24577f; } footer { border-top: 1px solid #cbd5e1; margin-top: 24px; padding-top: 10px; text-align: center; color: #64748b; font-size: 10px; }
  </style></head><body><header><img src="${escapeHtml(logoUrl)}" alt="SAREM"><div><h1>${escapeHtml(title)}</h1><p>Gerado em ${escapeHtml(generatedAt)}</p></div></header><table><thead><tr>${headers.map(header => `<th>${escapeHtml(header)}</th>`).join('')}</tr></thead><tbody>${tableRows || `<tr><td colspan="${headers.length}">Nenhum registro encontrado.</td></tr>`}</tbody></table><footer>${reportFooter}</footer></body></html>`)
  printWindow.document.close()
  const print = () => { printWindow.focus(); printWindow.print() }
  const logo = printWindow.document.querySelector('img')
  if (logo && !logo.complete) logo.addEventListener('load', print, { once: true })
  else window.setTimeout(print, 100)
}

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
        const comparableEmissionDate = toComparableDate(record.emissao_totvs)
        const matchesStart = !dateStart || (comparableEmissionDate !== '' && comparableEmissionDate >= dateStart)
        const matchesEnd = !dateEnd || (comparableEmissionDate !== '' && comparableEmissionDate <= dateEnd)
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
  const filterSummary = [term && `Busca: ${term}`, status && `Status: ${status}`, module && `Módulo: ${module}`, sector && `Setor: ${sector}`, cause && `Causa: ${cause}`, dateStart && `De: ${dateStart}`, dateEnd && `Até: ${dateEnd}`].filter(Boolean).join(' | ') || 'Sem filtros adicionais'

  const exportXlsx = async () => {
    const workbook = new ExcelJS.Workbook()
    workbook.creator = 'SAREM'
    workbook.created = new Date()
    const worksheet = workbook.addWorksheet('Relatório', { views: [{ state: 'frozen', ySplit: 4 }] })
    const lastColumn = Math.max(headers.length, 1)
    worksheet.mergeCells(1, 1, 1, lastColumn)
    worksheet.getCell(1, 1).value = 'SAREM'
    worksheet.getCell(1, 1).font = { name: 'Arial', size: 18, bold: true, color: { argb: 'FFFFFFFF' } }
    worksheet.getCell(1, 1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: '24577FFF' } }
    worksheet.getCell(1, 1).alignment = { vertical: 'middle', horizontal: 'left' }
    worksheet.getRow(1).height = 30
    const logoData = await imageDataUrl(logoSaremPng)
    if (logoData) {
      const logoId = workbook.addImage({ base64: logoData, extension: 'png' })
      worksheet.addImage(logoId, { tl: { col: 0.15, row: 0.15 }, ext: { width: 92, height: 25 } })
    }
    worksheet.mergeCells(2, 1, 2, lastColumn)
    worksheet.getCell(2, 1).value = reportTitle
    worksheet.getCell(2, 1).font = { name: 'Arial', size: 14, bold: true, color: { argb: '24577FFF' } }
    worksheet.mergeCells(3, 1, 3, lastColumn)
    worksheet.getCell(3, 1).value = `${filterSummary} | Gerado em ${new Date().toLocaleString('pt-BR')}`
    worksheet.getCell(3, 1).font = { name: 'Arial', italic: true, color: { argb: '64748BFF' } }
    const headerRow = worksheet.addRow(headers)
    headerRow.height = 24
    headerRow.eachCell(cell => {
      cell.font = { name: 'Arial', bold: true, color: { argb: 'FFFFFFFF' } }
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: '0F766EFF' } }
      cell.alignment = { vertical: 'middle', horizontal: 'left' }
      cell.border = { bottom: { style: 'thin', color: { argb: 'CBD5E1FF' } } }
    })
    rows.forEach(row => worksheet.addRow(headers.map(header => row[header] || '')))
    worksheet.autoFilter = { from: { row: 4, column: 1 }, to: { row: Math.max(4, rows.length + 4), column: lastColumn } }
    worksheet.columns = headers.map(header => ({ header, key: header, width: Math.min(34, Math.max(16, header.length + 4)) }))
    worksheet.eachRow((row, rowNumber) => {
      if (rowNumber < 5) return
      row.eachCell(cell => {
        cell.font = { name: 'Arial', size: 10, color: { argb: '172033FF' } }
        cell.alignment = { vertical: 'top', wrapText: true }
        if (rowNumber % 2 === 1) cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'F1F5F9FF' } }
        cell.border = { bottom: { style: 'hair', color: { argb: 'E2E8F0FF' } } }
      })
    })
    const footerRow = worksheet.addRow([reportFooter])
    worksheet.mergeCells(footerRow.number, 1, footerRow.number, lastColumn)
    footerRow.getCell(1).font = { name: 'Arial', italic: true, color: { argb: '64748BFF' } }
    footerRow.getCell(1).alignment = { horizontal: 'center' }
    worksheet.pageSetup = { orientation: 'landscape', fitToPage: true, fitToWidth: 1, fitToHeight: 0, horizontalDpi: 300, verticalDpi: 300 }
    const buffer = await workbook.xlsx.writeBuffer()
    const link = document.createElement('a')
    link.href = URL.createObjectURL(new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }))
    link.download = `${reportTitle.toLowerCase().replace(/[^a-z0-9]+/gi, '-')}.xlsx`
    link.click()
    URL.revokeObjectURL(link.href)
  }

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
        <div className="reports-result-heading"><div><h2>{reportTitle}</h2><span>{generated ? `${filterSummary} · ${rows.length} registros` : 'O resultado aparecerá aqui'}</span></div><div className="report-actions"><button className="secondary-action" type="button" onClick={() => printReport(reportTitle, rows)} disabled={!generated || rows.length === 0}>Imprimir / PDF</button><button className="primary-action" type="button" onClick={exportXlsx} disabled={!generated || rows.length === 0}>Exportar XLSX</button></div></div>
        {!generated ? <div className="reports-empty">Configure os parâmetros acima e clique em “Gerar relatório”.</div> : rows.length === 0 ? <div className="reports-empty">Nenhum registro encontrado para os filtros selecionados.</div> : <div className="dashboard-table-wrap"><table className="dashboard-table reports-table"><thead><tr>{headers.map(header => <th key={header}>{header}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.BO || row.Produto || 'linha'}-${index}`}>{headers.map(header => <td key={header}>{row[header]}</td>)}</tr>)}</tbody></table></div>}
      </section>
    </div>
  )
}
