import React from 'react'

type Column<T> = {
  header: string
  accessor: keyof T | ((row: T) => React.ReactNode)
}

type DataTableProps<T> = {
  data: T[]
  columns: Column<T>[]
  isLoading?: boolean
  onRowClick?: (row: T) => void
}

export function DataTable<T>({ data, columns, isLoading, onRowClick }: DataTableProps<T>) {
  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-color mx-auto mb-2"></div>
        Carregando dados...
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', background: 'var(--surface-color)', borderRadius: 'var(--radius-lg)' }}>
        Nenhum registro encontrado.
      </div>
    )
  }

  return (
    <div style={{ overflowX: 'auto', background: 'var(--surface-color)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--surface-border)', background: 'rgba(0,0,0,0.02)' }}>
            {columns.map((col, index) => (
              <th key={index} style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr 
              key={rowIndex} 
              onClick={() => onRowClick?.(row)}
              style={{ 
                borderBottom: rowIndex === data.length - 1 ? 'none' : '1px solid var(--surface-border)',
                cursor: onRowClick ? 'pointer' : 'default',
                transition: 'background var(--transition-fast)'
              }}
              onMouseEnter={(e) => {
                if (onRowClick) (e.currentTarget as HTMLTableRowElement).style.background = 'rgba(79, 70, 229, 0.05)'
              }}
              onMouseLeave={(e) => {
                if (onRowClick) (e.currentTarget as HTMLTableRowElement).style.background = 'transparent'
              }}
            >
              {columns.map((col, colIndex) => (
                <td key={colIndex} style={{ padding: '1rem', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                  {typeof col.accessor === 'function' ? col.accessor(row) : (row[col.accessor] as React.ReactNode)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
