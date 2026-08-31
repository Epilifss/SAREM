import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { protheusService } from '../services/protheus/protheusService'
import type { ProtheusBO, ProtheusBOItem } from '../services/protheus/protheusService'
import { supabase } from '../lib/supabase'
import { useAuth } from '../providers/AuthProvider'

const formSchema = z.object({
  tipo_ocorrencia: z.string().min(1, 'Selecione o tipo de ocorrência'),
  setor_responsavel: z.string().min(1, 'Selecione o setor responsável'),
  frete: z.string().min(1, 'Selecione o tipo de frete'),
  descricao: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

export default function BoNew() {
  const navigate = useNavigate()
  const { profile } = useAuth()
  
  const [search, setSearch] = useState('')
  const [searchResults, setSearchResults] = useState<ProtheusBO[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [selectedBo, setSelectedBo] = useState<ProtheusBO | null>(null)
  const [boItems, setBoItems] = useState<ProtheusBOItem[]>([])
  const [isSaving, setIsSaving] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(formSchema)
  })

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!search.trim()) return

    setIsSearching(true)
    setErrorMsg(null)
    try {
      const results = await protheusService.searchBOs(search)
      setSearchResults(results)
    } catch (err: any) {
      setErrorMsg('Erro ao buscar no Protheus.')
    } finally {
      setIsSearching(false)
    }
  }

  const handleSelectBo = async (bo: ProtheusBO) => {
    setSelectedBo(bo)
    setErrorMsg(null)
    
    // Check if BO already exists in tracking
    const { data: existingBo } = await supabase
      .from('bo_records')
      .select('id')
      .eq('bo_number', bo.bo_number)
      .eq('is_deleted', false)
      .single()

    if (existingBo) {
      setErrorMsg(`O Boletim ${bo.bo_number} já está sendo acompanhado pelo sistema.`)
      setSelectedBo(null)
      return
    }

    try {
      const items = await protheusService.getBOItems(bo.bo_number)
      setBoItems(items)
    } catch (err) {
      setErrorMsg('Erro ao buscar os itens do BO.')
    }
  }

  const onSubmit = async (data: FormData) => {
    if (!selectedBo || !profile) return
    setIsSaving(true)
    setErrorMsg(null)

    try {
      // Inserir registro principal
      const { data: insertedBo, error: boError } = await supabase
        .from('bo_records')
        .insert({
          bo_number: selectedBo.bo_number,
          op: selectedBo.op,
          loja: selectedBo.nome_cliente,
          filial: selectedBo.filial,
          emissao_totvs: selectedBo.emissao_totvs,
          previsao_embarque: selectedBo.previsao_entrega,
          tipo_ocorrencia: data.tipo_ocorrencia,
          setor_responsavel: data.setor_responsavel,
          frete: data.frete,
          descricao: data.descricao,
          modulo: profile.module,
          user_include: profile.id,
          status: 'Em Andamento'
        })
        .select()
        .single()

      if (boError) throw boError

      // Inserir Itens
      if (boItems.length > 0) {
        const itemsToInsert = boItems.map(item => ({
          bo_id: insertedBo.id,
          cod: item.cod,
          desc: item.desc,
          linha: item.linha,
          // Em uma versão mais completa, o motivo seria coletado por item no formulário
          motivo: 'Não especificado' 
        }))

        const { error: itemsError } = await supabase
          .from('bo_itens')
          .insert(itemsToInsert)

        if (itemsError) throw itemsError
      }

      // Sucesso!
      navigate(`/bos/${insertedBo.id}`)

    } catch (err: any) {
      console.error(err)
      setErrorMsg(err.message || 'Erro ao iniciar o acompanhamento do BO.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Acompanhar Novo BO</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Busque um Boletim de Ocorrência no ERP Protheus para iniciar o acompanhamento.</p>
      </div>

      {errorMsg && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--error-color)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(239,68,68,0.2)' }}>
          {errorMsg}
        </div>
      )}

      {/* Fase 1: Busca */}
      {!selectedBo && (
        <div style={{ background: 'var(--surface-color)', padding: '2rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
            <input 
              type="text" 
              placeholder="Digite o número do BO, OP ou Cliente..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ flex: 1, padding: '0.875rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}
            />
            <button 
              type="submit" 
              disabled={isSearching}
              style={{ background: 'var(--primary-color)', color: 'white', border: 'none', padding: '0.875rem 1.5rem', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontWeight: 600 }}
            >
              {isSearching ? 'Buscando...' : 'Pesquisar'}
            </button>
          </form>

          {searchResults.length > 0 && (
            <div>
              <h3 style={{ marginBottom: '1rem', fontWeight: 600 }}>Resultados encontrados:</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {searchResults.map(bo => (
                  <div key={bo.bo_number} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', border: '1px solid var(--surface-border)', borderRadius: 'var(--radius-md)', background: '#fff' }}>
                    <div>
                      <strong>{bo.bo_number}</strong> - {bo.nome_cliente}
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>OP: {bo.op} | Filial: {bo.filial}</div>
                    </div>
                    <button 
                      onClick={() => handleSelectBo(bo)}
                      style={{ background: 'var(--secondary-color)', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontWeight: 500 }}
                    >
                      Selecionar
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Fase 2: Complemento de Dados */}
      {selectedBo && (
        <div style={{ background: 'var(--surface-color)', padding: '2rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid var(--surface-border)' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--primary-color)' }}>{selectedBo.bo_number}</h2>
              <p style={{ color: 'var(--text-secondary)' }}>Cliente: {selectedBo.nome_cliente}</p>
            </div>
            <button 
              onClick={() => setSelectedBo(null)}
              style={{ background: 'transparent', border: '1px solid var(--surface-border)', padding: '0.5rem 1rem', borderRadius: 'var(--radius-md)', cursor: 'pointer', color: 'var(--text-secondary)' }}
            >
              Trocar BO
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div className="form-group">
                <label>Tipo de Ocorrência</label>
                <select {...register('tipo_ocorrencia')} style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}>
                  <option value="">Selecione...</option>
                  <option value="Avaria Produtiva">Avaria Produtiva</option>
                  <option value="Assistência Técnica">Assistência Técnica</option>
                  <option value="Falta de Material">Falta de Material</option>
                </select>
                {errors.tipo_ocorrencia && <span style={{ color: 'var(--error-color)', fontSize: '0.8rem' }}>{errors.tipo_ocorrencia.message}</span>}
              </div>

              <div className="form-group">
                <label>Setor Responsável</label>
                <select {...register('setor_responsavel')} style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}>
                  <option value="">Selecione...</option>
                  <option value="Produção">Produção</option>
                  <option value="Qualidade">Qualidade</option>
                  <option value="Comercial">Comercial</option>
                  <option value="Logística">Logística</option>
                </select>
                {errors.setor_responsavel && <span style={{ color: 'var(--error-color)', fontSize: '0.8rem' }}>{errors.setor_responsavel.message}</span>}
              </div>

              <div className="form-group">
                <label>Frete</label>
                <select {...register('frete')} style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1' }}>
                  <option value="">Selecione...</option>
                  <option value="CIF">CIF</option>
                  <option value="FOB">FOB</option>
                </select>
                {errors.frete && <span style={{ color: 'var(--error-color)', fontSize: '0.8rem' }}>{errors.frete.message}</span>}
              </div>
            </div>

            <div className="form-group">
              <label>Descrição Opcional</label>
              <textarea 
                {...register('descricao')} 
                rows={3} 
                style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #cbd5e1', resize: 'vertical' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button 
                type="submit" 
                disabled={isSaving}
                style={{ background: 'var(--primary-color)', color: 'white', border: 'none', padding: '1rem 2rem', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontWeight: 600 }}
              >
                {isSaving ? 'Salvando...' : 'Iniciar Acompanhamento'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
