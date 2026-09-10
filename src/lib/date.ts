const datePartsPattern = /^(\d{4})-(\d{2})-(\d{2})$/
const brazilianDatePattern = /^(\d{2})\/(\d{2})\/(\d{4})$/

function createValidDate(year: number, month: number, day: number): Date | null {
  const date = new Date(year, month - 1, day)
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day ? date : null
}

export function parseDate(value: string | null | undefined): Date | null {
  if (!value) return null

  const normalizedValue = value.trim()
  const isoMatch = normalizedValue.match(datePartsPattern)
  if (isoMatch) return createValidDate(Number(isoMatch[1]), Number(isoMatch[2]), Number(isoMatch[3]))

  const brazilianMatch = normalizedValue.match(brazilianDatePattern)
  if (brazilianMatch) return createValidDate(Number(brazilianMatch[3]), Number(brazilianMatch[2]), Number(brazilianMatch[1]))

  const date = new Date(normalizedValue)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDate(value: string | null | undefined): string {
  const date = parseDate(value)
  return date ? date.toLocaleDateString('pt-BR') : '-'
}

export function toComparableDate(value: string | null | undefined): string {
  const date = parseDate(value)
  if (!date) return ''

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}