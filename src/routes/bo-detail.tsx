import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { supabase } from '../lib/supabase'
import type { BoRecord, AuditLog } from '../types'
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
  const [history, setHistory] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<'info' | 'history'>('info')

  const { register, handleSubmit, reset } = useForm<EditFormData>({
    resolver: zodResolver(editSchema)
  })

  useEffect(() => {
    if (id) {
      fetchBo()
      fetchHistory()
    }
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
    reset({
      tipo_ocorrencia: data.tipo_ocorrencia,
      setor_responsavel: data.setor_responsavel,
      frete: data.frete,
      descricao: data.descricao
    })

    const { data: itemsData } = await supabase
      .from('bo_itens')
      .select('*')
      .eq('bo_id', id)
    
    setItems(itemsData || [])
    setLoading(false)
  }

  const fetchHistory = async () => {
    const { data: boData } = await supabase.from('bo_records').select('bo_number').eq('id', id).single()
    if (!boData) return

    const { data, error } = await supabase
      .from('audit_logs')
      .select('*, profiles(username)')
      .eq('entity_id', boData.bo_number)
      .order('created_at', { ascending: false })
      .limit(50)
      
    if (!error && data) {
      setHistory(data as any[])
    }
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
      fetchHistory() // refresh history
    } else {
      alert('Erro ao atualizar BO: ' + error.message)
    }
    setIsSaving(false)
  }

  const handleStatusChange = async (newStatus: string) => {
    if (!profile?.can_edit_bo || !bo) return
    if (!window.confirm(`Mudar status para ${newStatus}?`)) return
    
    const { error } = await supabase
      .from('bo_records')
      .update({ 
        status: newStatus,
        user_edit: profile.id 
      })
      .eq('id', id)

    if (!error) {
      setBo(prev => prev ? { ...prev, status: newStatus } : null)
      fetchHistory()
    } else {
      alert('Erro ao mudar status: ' + error.message)
    }
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
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-color"></div>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* HEADER E STATUS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', background: 'var(--surface-color)', padding: '2rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
            {bo.bo_number} 
            <span style={{ fontSize: '0.85rem', padding: '0.25rem 0.75rem', background: bo.status === 'Embarcado' ? 'var(--success-color)' : 'var(--primary-color)', color: 'white', borderRadius: '12px', fontWeight: 600 }}>
              {bo.status}
            </span>
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Loja/Cliente: {bo.loja} | Módulo: {bo.modulo}</p>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end' }}>
          {profile?.can_edit_bo && (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Mudar Status:</span>
              <select 
                value={bo.status} 
                onChange={(e) => handleStatusChange(e.target.value)}
                style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}
              >
                <option value="Em Andamento">Em Andamento</option>
                <option value="Aguardando Aprovação">Aguardando Aprovação</option>
                <option value="Aguardando Coleta">Aguardando Coleta</option>
                <option value="Embarcado">Embarcado</option>
              </select>
            </div>
          )}
          {profile?.can_delete_bo && (
            <button onClick={handleDelete} style={{ background: 'transparent', color: 'var(--error-color)', border: 'none', cursor: 'pointer', fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Excluir BO
            </button>
          )}
        </div>
      </div>

      {/* TABS */}
      <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid var(--surface-border)' }}>
        <button 
          onClick={() => setActiveTab('info')}
          style={{ padding: '1rem', background: 'transparent', border: 'none', borderBottom: activeTab === 'info' ? '2px solid var(--primary-color)' : '2px solid transparent', color: activeTab === 'info' ? 'var(--primary-color)' : 'var(--text-secondary)', fontWeight: 600, cursor: 'pointer' }}
        >
          Detalhes do BO
        </button>
        <button 
          onClick={() => setActiveTab('history')}
          style={{ padding: '1rem', background: 'transparent', border: 'none', borderBottom: activeTab === 'history' ? '2px solid var(--primary-color)' : '2px solid transparent', color: activeTab === 'history' ? 'var(--primary-color)' : 'var(--text-secondary)', fontWeight: 600, cursor: 'pointer' }}
        >
          Histórico
        </button>
      </div>

      {/* TAB: INFO */}
      {activeTab === 'info' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                <h3 style={{ color: 'var(--text-secondary)' }}>Dados do SAREM</h3>
                {profile?.can_edit_bo && !isEditing && (
                  <button onClick={() => setIsEditing(true)} style={{ background: 'transparent', color: 'var(--primary-color)', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Editar</button>
                )}
              </div>
              
              {!isEditing ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div><strong style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Ocorrência:</strong> {bo.tipo_ocorrencia}</div>
                  <div><strong style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Setor Responsável:</strong> {bo.setor_responsavel}</div>
                  <div><strong style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Frete:</strong> {bo.frete}</div>
                  <div><strong style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Descrição:</strong> {bo.descricao || '-'}</div>
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
                    <button type="button" onClick={() => setIsEditing(false)} style={{ flex: 1, padding: '0.5rem', background: '#e2e8f0', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}>Cancelar</button>
                    <button type="submit" disabled={isSaving} style={{ flex: 1, padding: '0.5rem', background: 'var(--primary-color)', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}>
                      {isSaving ? 'Salvando...' : 'Salvar'}
                    </button>
                  </div>
                </form>
              )}
            </div>

            <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)' }}>
              <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>Dados do Protheus</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div><strong style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>OP:</strong> {bo.op || '-'}</div>
                <div><strong style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Filial:</strong> {bo.filial}</div>
                <div><strong style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Emissão Totvs:</strong> {bo.emissao_totvs ? new Date(bo.emissao_totvs).toLocaleDateString() : '-'}</div>
                <div><strong style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Prev. Embarque:</strong> {bo.previsao_embarque ? new Date(bo.previsao_embarque).toLocaleDateString() : '-'}</div>
              </div>
            </div>
          </div>

          <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)' }}>
            <h3 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>Itens Vinculados</h3>
            {items.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>Nenhum item vinculado.</p>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--surface-border)' }}>
                    <th style={{ padding: '0.75rem 0', color: 'var(--text-secondary)' }}>Código</th>
                    <th style={{ padding: '0.75rem 0', color: 'var(--text-secondary)' }}>Descrição</th>
                    <th style={{ padding: '0.75rem 0', color: 'var(--text-secondary)' }}>Linha</th>
                    <th style={{ padding: '0.75rem 0', color: 'var(--text-secondary)' }}>Motivo</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map(item => (
                    <tr key={item.id} style={{ borderBottom: '1px solid var(--surface-border)' }}>
                      <td style={{ padding: '0.75rem 0', fontWeight: 500 }}>{item.cod}</td>
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
      )}

      {/* TAB: HISTÓRICO */}
      {activeTab === 'history' && (
        <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)' }}>
          <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>Linha do Tempo</h3>
          {history.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>Nenhum histórico disponível.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {history.map((log) => (
                <div key={log.id} style={{ display: 'flex', gap: '1rem', paddingBottom: '1rem', borderBottom: '1px solid var(--surface-border)' }}>
                  <div style={{ width: '120px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    {new Date(log.created_at).toLocaleString()}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600 }}>{(log as any).profiles?.username || 'Usuário Desconhecido'}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      {log.action === 'BO_CREATED' && 'Iniciou o acompanhamento do BO'}
                      {log.action === 'BO_UPDATED' && (
                        <span>Atualizou o BO. <em style={{ fontSize: '0.8rem' }}>(Status atual da edição: {log.metadata?.status})</em></span>
                      )}
                      {log.action === 'BO_DELETED' && 'Excluiu o BO'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
