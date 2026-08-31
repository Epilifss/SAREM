export type Profile = {
  id: string
  username: string
  module: string
  is_admin: boolean
  can_edit_bo: boolean
  can_delete_bo: boolean
  can_track_bo: boolean
}

export type BoRecord = {
  id: string
  bo_number: string
  op: string | null
  loja: string | null
  filial: string | null
  emissao_totvs: string | null
  tipo_ocorrencia: string | null
  frete: string | null
  setor_responsavel: string | null
  status: string
  previsao_embarque: string | null
  descricao: string | null
  modulo: string
  is_deleted: boolean
  created_at: string
}
