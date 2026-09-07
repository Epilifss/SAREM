import { useEffect, useState } from 'react'
import ExcelJS from 'exceljs'
import { useAuth } from '../providers/AuthProvider'
import { supabase } from '../lib/supabase'
import logoSarem from '../img/logo_sarem.svg'
import logoSaremPng from '../img/SAREM.png'

type DashboardRecord = {
  bo_number: string
  status: string | null
  setor_responsavel: string | null
  modulo: string | null
  tipo_ocorrencia: string | null
}

type DashboardItem = {
  bo_ref: string
  motivo: string | null
}

type ReportRow = { label: string; count: number }
type ReportKind = 'total' | 'open' | 'progress' | 'closed' | 'sector' | 'module' | 'occurrence' | 'itemReason'
type DetailedReportRow = Record<string, string>

const reportFooter = 'Todos os direitos reservados - SAREM'

function reportRows(records: DashboardRecord[]): DetailedReportRow[] {
  return records.map(record => ({
    'Número do BO': record.bo_number,
    Status: record.status?.trim() || 'Não informado',
    'Setor responsável': record.setor_responsavel?.trim() || 'Não informado',
    Módulo: record.modulo?.trim() || 'Não informado',
    'Tipo de ocorrência': record.tipo_ocorrencia?.trim() || 'Não informado',
  }))
}

function itemReportRows(items: DashboardItem[]): DetailedReportRow[] {
  return items.map(item => ({
    'Número do BO': item.bo_ref,
    Motivo: item.motivo?.trim() || 'Não informado',
  }))
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, character => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
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

function printReport(title: string, rows: DetailedReportRow[]) {
  const printWindow = window.open('', '_blank', 'width=1100,height=800')
  if (!printWindow) return

  const generatedAt = new Date().toLocaleString('pt-BR')
  const logoUrl = new URL(logoSarem, window.location.href).href
  const headers = Object.keys(rows[0] || {
    'Número do BO': '',
    Status: '',
    'Setor responsável': '',
    Módulo: '',
    'Tipo de ocorrência': '',
  })
  const tableRows = rows.map(row => `<tr>${headers.map(header => `<td>${escapeHtml(row[header as keyof DetailedReportRow])}</td>`).join('')}</tr>`).join('')

  printWindow.document.write(`<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><title>${escapeHtml(title)}</title><style>
    @page { margin: 16mm; } body { font-family: Arial, sans-serif; color: #172033; margin: 0; } header { display: flex; align-items: center; gap: 16px; border-bottom: 2px solid #24577f; padding-bottom: 14px; } header img { width: 130px; max-height: 54px; object-fit: contain; } h1 { font-size: 20px; margin: 0 0 6px; } p { margin: 0; color: #64748b; font-size: 12px; } table { width: 100%; border-collapse: collapse; margin-top: 22px; font-size: 11px; } th, td { border: 1px solid #cbd5e1; padding: 7px; text-align: left; } th { background: #e8f0f6; color: #24577f; } footer { border-top: 1px solid #cbd5e1; margin-top: 24px; padding-top: 10px; text-align: center; color: #64748b; font-size: 10px; }
  </style></head><body><header><img src="${escapeHtml(logoUrl)}" alt="SAREM"><div><h1>${escapeHtml(title)}</h1><p>Gerado em ${escapeHtml(generatedAt)}</p></div></header><table><thead><tr>${headers.map(header => `<th>${escapeHtml(header)}</th>`).join('')}</tr></thead><tbody>${tableRows || '<tr><td colspan="5">Nenhum registro encontrado.</td></tr>'}</tbody></table><footer>${reportFooter}</footer></body></html>`)
  printWindow.document.close()
  const print = () => {
    printWindow.focus()
    printWindow.print()
  }
  const logo = printWindow.document.querySelector('img')
  if (logo && !logo.complete) logo.addEventListener('load', print, { once: true })
  else window.setTimeout(print, 100)
}

function countBy<T extends Record<string, string | null>>(records: T[], field: keyof T): ReportRow[] {
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

function BarReport({ title, rows, color, onOpen }: { title: string; rows: ReportRow[]; color: string; onOpen: () => void }) {
  const chartRows = compactRows(rows)
  const maximum = chartRows[0]?.count || 1

  return (
    <section className="dashboard-panel dashboard-report-card" role="button" tabIndex={0} onClick={onOpen} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') onOpen() }}>
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

function ReportModal({ title, rows, onClose }: { title: string; rows: DetailedReportRow[]; onClose: () => void }) {
  const headers = Object.keys(rows[0] || { 'Número do BO': '', Status: '' })

  const exportXlsx = async () => {
    const workbook = new ExcelJS.Workbook()
    workbook.creator = 'SAREM'
    workbook.created = new Date()
    const worksheet = workbook.addWorksheet('Relatório', { views: [{ state: 'frozen', ySplit: 4 }] })
    const generatedAt = new Date().toLocaleString('pt-BR')
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
    worksheet.getCell(2, 1).value = title
    worksheet.getCell(2, 1).font = { name: 'Arial', size: 14, bold: true, color: { argb: '24577FFF' } }
    worksheet.mergeCells(3, 1, 3, lastColumn)
    worksheet.getCell(3, 1).value = `Gerado em ${generatedAt}`
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
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${title.toLowerCase().replace(/[^a-z0-9]+/gi, '-')}.xlsx`
    link.click()
    URL.revokeObjectURL(link.href)
  }

  return (
    <div className="modal-backdrop report-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="report-modal" role="dialog" aria-modal="true" aria-labelledby="report-modal-title" onMouseDown={event => event.stopPropagation()}>
        <div className="report-toolbar">
          <button className="modal-close" type="button" onClick={onClose} aria-label="Fechar relatório">×</button>
          <div className="report-actions">
            <button className="secondary-action" type="button" onClick={() => printReport(title, rows)}>Imprimir / PDF</button>
            <button className="primary-action" type="button" onClick={exportXlsx}>Exportar XLSX</button>
          </div>
        </div>
        <article className="report-document">
          <header className="report-document-header">
            <img src={logoSarem} alt="SAREM" />
            <div><h2 id="report-modal-title">{title}</h2><p>Gerado em {new Date().toLocaleString('pt-BR')}</p></div>
          </header>
          <div className="report-table-wrap">
            <table className="dashboard-table report-table">
              <thead><tr>{headers.map(header => <th key={header}>{header}</th>)}</tr></thead>
              <tbody>{rows.length ? rows.map((row, index) => <tr key={`${row['Número do BO'] || 'linha'}-${index}`}>{headers.map(header => <td key={header}>{row[header]}</td>)}</tr>) : <tr><td colSpan={headers.length}>Nenhum registro encontrado.</td></tr>}</tbody>
            </table>
          </div>
          <footer className="report-document-footer">{reportFooter}</footer>
        </article>
      </section>
    </div>
  )
}

export default function Dashboard() {
  const { profile } = useAuth()
  const [records, setRecords] = useState<DashboardRecord[]>([])
  const [items, setItems] = useState<DashboardItem[]>([])
  const [selectedReport, setSelectedReport] = useState<{ title: string; rows: DetailedReportRow[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!profile) return

    const fetchDashboard = async () => {
      setLoading(true)
      setError(null)
      let query = supabase
        .from('bo_records')
        .select('bo_number, status, setor_responsavel, modulo, tipo_ocorrencia')
        .or('d_e_l_e_t_.neq.*,d_e_l_e_t_.is.null')

      if (profile.module !== 'Todos' && !profile.is_admin) query = query.eq('modulo', profile.module)

      const { data, error: queryError } = await query
      if (queryError) {
        setError(queryError.message)
        setRecords([])
        setItems([])
      } else {
        const dashboardRecords = (data as DashboardRecord[]) || []
        setRecords(dashboardRecords)

        const boNumbers = dashboardRecords.map(record => record.bo_number)
        if (boNumbers.length === 0) {
          setItems([])
        } else {
          const { data: itemData, error: itemError } = await supabase
            .from('bo_itens')
            .select('motivo, bo_ref')
            .in('bo_ref', boNumbers)

          if (itemError) setError(itemError.message)
          setItems((itemData as DashboardItem[]) || [])
        }
      }
      setLoading(false)
    }

    fetchDashboard()
  }, [profile])

  const statusRows = countBy(records, 'status')
  const sectorRows = countBy(records, 'setor_responsavel')
  const moduleRows = countBy(records, 'modulo')
  const occurrenceRows = countBy(records, 'tipo_ocorrencia')
  const itemMotivoRows = countBy(items, 'motivo')
  const closed = records.filter(record => record.status === 'Embarcado').length
  const inProgress = records.filter(record => record.status === 'Em Andamento').length
  const canSeeAllModules = profile?.module === 'Todos' || profile?.is_admin === true
  const reportData: Record<ReportKind, { title: string; rows: DetailedReportRow[] }> = {
    total: { title: 'Relatório de todos os BOs', rows: reportRows(records) },
    open: { title: 'Relatório de BOs em aberto', rows: reportRows(records.filter(record => record.status !== 'Embarcado')) },
    progress: { title: 'Relatório de BOs em andamento', rows: reportRows(records.filter(record => record.status === 'Em Andamento')) },
    closed: { title: 'Relatório de BOs encerrados', rows: reportRows(records.filter(record => record.status === 'Embarcado')) },
    sector: { title: 'Relatório de BOs por setor responsável', rows: reportRows(records) },
    module: { title: 'Relatório de BOs por módulo', rows: reportRows(records) },
    occurrence: { title: 'Relatório de BOs por tipo de ocorrência', rows: reportRows(records) },
    itemReason: { title: 'Relatório de motivos dos itens', rows: itemReportRows(items) },
  }

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
            {([['total', 'Total de BOs', records.length, 'Registros ativos'], ['open', 'Em aberto', records.length - closed, 'Precisam de acompanhamento'], ['progress', 'Em andamento', inProgress, 'Status atual'], ['closed', 'Encerrados', closed, 'BOs embarcados']] as const).map(([kind, label, value, description]) => (
              <button className="dashboard-stat" type="button" key={kind} onClick={() => setSelectedReport(reportData[kind])}>
                <span>{label}</span><strong>{value}</strong><small>{description}</small>
              </button>
            ))}
          </div>
          <div className="dashboard-report-grid">
            <BarReport title="BOs por setor responsável" rows={sectorRows} color="var(--primary-color)" onOpen={() => setSelectedReport(reportData.sector)} />
            <BarReport title="BOs por status" rows={statusRows} color="var(--secondary-color)" onOpen={() => setSelectedReport(reportData.total)} />
            {canSeeAllModules && <BarReport title="BOs por módulo" rows={moduleRows} color="var(--accent-color)" onOpen={() => setSelectedReport(reportData.module)} />}
            <BarReport title="Tipos de ocorrência" rows={occurrenceRows} color="#f59e0b" onOpen={() => setSelectedReport(reportData.occurrence)} />
            <BarReport title="Motivos dos itens" rows={itemMotivoRows} color="#0f766e" onOpen={() => setSelectedReport(reportData.itemReason)} />
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
      {selectedReport && <ReportModal title={selectedReport.title} rows={selectedReport.rows} onClose={() => setSelectedReport(null)} />}
    </div>
  )
}
