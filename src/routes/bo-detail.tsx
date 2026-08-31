import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { supabase } from '../lib/supabase'
import type { BoRecord } from '../types'
import { useAuth } from '../providers/AuthProvider'

const editSchema = z.object({
  tipo_ocorrencia: z.string().min(1, 'Selecione o tipo'),
  setor_responsavel: z.string().min(1, 'Selecione o setor'),
  frete: z.string().min(1, 'Selecione o frete'),
  descricao: z.string().optional(),
})

type EditFormData = z.infer<typeof editSchema>

export default function BoDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { profile } = useAuth()
  
  const [bo, setBo] = useState<BoRecord | null>(null)
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const { register, handleSubmit, reset } = useForm<EditFormData>({
    resolver: zodResolver(editSchema)
  })

  useEffect(() => {
    if (id) fetchBo()
  }, [id])

  const fetchBo = async () => {
    setLoading(true)
    const { data, error } = await supabase
      .from('bo_records')
      .select('*')
      .eq('id', id)
      .eq('is_deleted', false)
      .single()

    if (error) {
      console.error(error)
      navigate('/bos')
      return
    }
    
    setBo(data as BoRecord)
    
    // reset form
    reset({
      tipo_ocorrencia: data.tipo_ocorrencia,
      setor_responsavel: data.setor_responsavel,
      frete: data.frete,
      descricao: data.descricao
    })

    // Fetch items
    const { data: itemsData } = await supabase
      .from('bo_itens')
      .select('*')
      .eq('bo_id', id)
    
    setItems(itemsData || [])
    setLoading(false)
  }

  const handleUpdate = async (data: EditFormData) => {
    if (!profile) return
    setIsSaving(true)
    
    const { error } = await supabase
      .from('bo_records')
      .update({
        tipo_ocorrencia: data.tipo_ocorrencia,
        setor_responsavel: data.setor_responsavel,
        frete: data.frete,
        descricao: data.descricao,
        user_edit: profile.id
      })
      .eq('id', id)

    if (!error) {
      setBo(prev => prev ? { ...prev, ...data } : null)
      setIsEditing(false)
    } else {
      alert('Erro ao atualizar BO: ' + error.message)
    }
    setIsSaving(false)
  }

  const handleDelete = async () => {
    if (!profile?.can_delete_bo) return
    if (!window.confirm('Deseja realmente excluir este BO?')) return

    const { error } = await supabase
      .from('bo_records')
      .update({ 
        is_deleted: true,
        user_delet: profile.id,
        deleted_at: new Date().toISOString()
      })
      .eq('id', id)
    
    if (!error) {
      navigate('/bos')
    } else {
      alert('Erro ao excluir: ' + error.message)
    }
  }

  if (loading || !bo) {
    return <div>Carregando BO...</div>
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {bo.bo_number} 
            <span style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem', background: 'var(--primary-color)', color: 'white', borderRadius: '12px' }}>
              {bo.status}
            </span>
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Criado em: {new Date(bo.created_at).toLocaleString()}</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          {profile?.can_edit_bo && !isEditing && (
            <button onClick={() => setIsEditing(true)} style={{ padding: '0.5rem 1rem', background: 'var(--secondary-color)', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}>
              Editar
            </button>
          )}
          {profile?.can_delete_bo && (
            <button onClick={handleDelete} style={{ padding: '0.5rem 1rem', background: 'var(--error-color)', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}>
              Excluir
            </button>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)' }}>
          <h3 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>Dados do Protheus</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div><strong>OP:</strong> {bo.op}</div>
            <div><strong>Loja:</strong> {bo.loja}</div>
            <div><strong>Filial:</strong> {bo.filial}</div>
            <div><strong>Emissão:</strong> {bo.emissao_totvs}</div>
            <div><strong>Prev. Embarque:</strong> {bo.previsao_embarque}</div>
          </div>
        </div>

        <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)' }}>
          <h3 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>Dados do SAREM</h3>
          
          {!isEditing ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div><strong>Ocorrência:</strong> {bo.tipo_ocorrencia}</div>
              <div><strong>Setor:</strong> {bo.setor_responsavel}</div>
              <div><strong>Frete:</strong> {bo.frete}</div>
              <div><strong>Descrição:</strong> {bo.descricao || '-'}</div>
            </div>
          ) : (
            <form onSubmit={handleSubmit(handleUpdate)} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-group">
                <label>Tipo de Ocorrência</label>
                <select {...register('tipo_ocorrencia')}>
                  <option value="Avaria Produtiva">Avaria Produtiva</option>
                  <option value="Assistência Técnica">Assistência Técnica</option>
                  <option value="Falta de Material">Falta de Material</option>
                </select>
              </div>
              <div className="form-group">
                <label>Setor Responsável</label>
                <select {...register('setor_responsavel')}>
                  <option value="Produção">Produção</option>
                  <option value="Qualidade">Qualidade</option>
                  <option value="Comercial">Comercial</option>
                  <option value="Logística">Logística</option>
                </select>
              </div>
              <div className="form-group">
                <label>Frete</label>
                <select {...register('frete')}>
                  <option value="CIF">CIF</option>
                  <option value="FOB">FOB</option>
                </select>
              </div>
              <div className="form-group">
                <label>Descrição</label>
                <textarea {...register('descricao')} rows={3}></textarea>
              </div>
              
              <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                <button type="button" onClick={() => setIsEditing(false)} style={{ flex: 1, padding: '0.5rem', background: '#e2e8f0', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}>
                  Cancelar
                </button>
                <button type="submit" disabled={isSaving} style={{ flex: 1, padding: '0.5rem', background: 'var(--primary-color)', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}>
                  {isSaving ? 'Salvando...' : 'Salvar'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)' }}>
        <h3 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>Itens Vinculados</h3>
        {items.length === 0 ? (
          <p style={{ color: 'var(--text-muted)' }}>Nenhum item vinculado a este BO.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--surface-border)' }}>
                <th style={{ padding: '0.75rem 0' }}>Código</th>
                <th style={{ padding: '0.75rem 0' }}>Descrição</th>
                <th style={{ padding: '0.75rem 0' }}>Linha</th>
                <th style={{ padding: '0.75rem 0' }}>Motivo</th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr key={item.id} style={{ borderBottom: '1px solid var(--surface-border)' }}>
                  <td style={{ padding: '0.75rem 0' }}>{item.cod}</td>
                  <td style={{ padding: '0.75rem 0' }}>{item.desc}</td>
                  <td style={{ padding: '0.75rem 0' }}>{item.linha}</td>
                  <td style={{ padding: '0.75rem 0' }}>{item.motivo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

    </div>
  )
}
