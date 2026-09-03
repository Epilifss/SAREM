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
  id: number
  bo_number: string
  op: string | null
  loja: string | null
  emissao_totvs: string | null
  tipo_ocorrencia: string | null
  motivo: string | null
  frete: string | null
  setor_responsavel: string | null
  status: string | null
  previsao_embarque: string | null
  dt_embarque: string | null
  descricao: string | null
  modulo: string | null
  filial: string | null
  user_edit: string | null
  edited_at: string | null
  d_e_l_e_t_: string | null
  user_delet: string | null
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export type BoItem = {
  id: number
  bo_ref: string
  cod: string | null
  desc: string | null
  linha: string | null
  motivo: string | null
}

export type AuditLog = {
  id: string
  user_id: string | null
  action: string
  entity: string
  entity_id: string
  metadata: any
  created_at: string
}
