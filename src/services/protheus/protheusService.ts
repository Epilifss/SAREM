import { supabase } from '../../lib/supabase'

export type ProtheusBOItem = {
  bo_number: string;
  cod: string;
  desc: string;
  linha: string;
}

export type ProtheusBO = {
  bo_number: string;
  op: string;
  nome_cliente: string;
  filial: string;
  emissao_totvs: string; // YYYY-MM-DD
  previsao_entrega: string; // YYYY-MM-DD
  items: ProtheusBOItem[]
}

type ProtheusApiItem = {
  C6_ITEM: string
  C6_CODTIDI: string
  C6_DESCRI: string
  C6_LINHA: string
}

type ProtheusApiBO = {
  C5_PEDREPR: string
  C5_NUM: string
  C5_NOME: string
  FILIAL: string
  EMISSAO: string
  PREVISAO_ENTREGA: string
  ITENS?: ProtheusApiItem[]
}

const API_URL = '/api/protheus/bos'

function parseDate(date: string): string {
  const [day, month, year] = date.split('/')
  return year && month && day ? `${year}-${month}-${day}` : date
}

function mapBO(bo: ProtheusApiBO): ProtheusBO {
  const boNumber = bo.C5_PEDREPR.trim()
  return {
    bo_number: boNumber,
    op: bo.C5_NUM.trim(),
    nome_cliente: bo.C5_NOME.trim(),
    filial: bo.FILIAL.trim(),
    emissao_totvs: parseDate(bo.EMISSAO.trim()),
    previsao_entrega: parseDate(bo.PREVISAO_ENTREGA.trim()),
    items: (bo.ITENS || []).map(item => ({
      bo_number: boNumber,
      cod: item.C6_CODTIDI.trim(),
      desc: item.C6_DESCRI.trim(),
      linha: item.C6_LINHA.trim(),
    })),
  }
}

export const protheusService = {
  
  async searchBOs(termo = ''): Promise<ProtheusBO[]> {
    const response = await fetch(API_URL)
    if (!response.ok) {
      throw new Error(`Erro ao consultar o Protheus (${response.status})`)
    }

    const payload = await response.json() as ProtheusApiBO | ProtheusApiBO[]
    const apiBos = Array.isArray(payload) ? payload : [payload]
    const bos = apiBos.map(mapBO)
    const { data: trackedBos, error } = await supabase
      .from('bo_records')
      .select('bo_number')

    if (error) throw error

    const trackedNumbers = new Set((trackedBos || []).map(bo => bo.bo_number.trim().toUpperCase()))
    const upperTerm = termo.trim().toUpperCase()
    return bos.filter(bo => !trackedNumbers.has(bo.bo_number.toUpperCase())).filter(bo =>
      bo.bo_number.includes(upperTerm) || 
      bo.op.includes(upperTerm) ||
      bo.nome_cliente.toUpperCase().includes(upperTerm)
    )
  },

  async getBOItems(boNumber: string): Promise<ProtheusBOItem[]> {
    const response = await fetch(API_URL)
    if (!response.ok) throw new Error(`Erro ao consultar itens no Protheus (${response.status})`)
    const payload = await response.json() as ProtheusApiBO | ProtheusApiBO[]
    const apiBos = Array.isArray(payload) ? payload : [payload]
    const bo = apiBos.find(item => item.C5_PEDREPR.trim() === boNumber.trim())
    return bo ? mapBO(bo).items : []
  },

  async getBODetails(boNumber: string): Promise<ProtheusBO | null> {
    const response = await fetch(API_URL)
    if (!response.ok) throw new Error(`Erro ao consultar detalhes no Protheus (${response.status})`)
    const payload = await response.json() as ProtheusApiBO | ProtheusApiBO[]
    const apiBos = Array.isArray(payload) ? payload : [payload]
    const bo = apiBos.find(item => item.C5_PEDREPR.trim() === boNumber.trim())
    return bo ? mapBO(bo) : null
  }
}
