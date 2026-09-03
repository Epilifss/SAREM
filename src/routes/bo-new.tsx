import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { protheusService } from '../services/protheus/protheusService'
import type { ProtheusBO, ProtheusBOItem } from '../services/protheus/protheusService'
import { supabase } from '../lib/supabase'
import { useAuth } from '../providers/AuthProvider'
import { SearchSelectModal } from '../components/ui/SearchSelectModal'

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
  const [motivoOptions, setMotivoOptions] = useState<string[]>([])
  const [occurrenceOptions, setOccurrenceOptions] = useState<string[]>([])
  const [sectorOptions, setSectorOptions] = useState<string[]>([])
  const [itemMotives, setItemMotives] = useState<Record<number, string>>({})
  const [customItemMotives, setCustomItemMotives] = useState<Record<number, string>>({})

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(formSchema)
  })
  const occurrence = watch('tipo_ocorrencia')
  const sector = watch('setor_responsavel')
  const freight = watch('frete')

  useEffect(() => {
    const loadInitialData = async () => {
      setIsSearching(true)
      setErrorMsg(null)
      try {
        const [bos, occurrencesResult, itemMotivesResult] = await Promise.all([
          protheusService.searchBOs(),
          supabase.from('bo_records').select('tipo_ocorrencia,setor_responsavel'),
          supabase.from('bo_itens').select('motivo'),
        ])

        if (occurrencesResult.error) throw occurrencesResult.error
        if (itemMotivesResult.error) throw itemMotivesResult.error

        setSearchResults(bos)
        const occurrenceValues = (occurrencesResult.data || []).map(row => row.tipo_ocorrencia)
        const sectorValues = (occurrencesResult.data || []).map(row => row.setor_responsavel)
        const motiveValues = (itemMotivesResult.data || []).map(row => row.motivo)
        const unique = (values: (string | null)[]) => [...new Set(values.map(value => value?.trim()).filter(Boolean) as string[])]
        setOccurrenceOptions(unique(occurrenceValues))
        setSectorOptions(unique(sectorValues))
        setMotivoOptions(unique(motiveValues))
      } catch (err: any) {
        setErrorMsg(err.message || 'Erro ao carregar os BOs do Protheus.')
      } finally {
        setIsSearching(false)
      }
    }

    loadInitialData()
  }, [])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!search.trim()) return

    setIsSearching(true)
    setErrorMsg(null)
    try {
      const results = await protheusService.searchBOs(search)
      setSearchResults(results)
    } catch (err: any) {
      setErrorMsg(err.message || 'Erro ao buscar no Protheus.')
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
      .or('d_e_l_e_t_.neq.*,d_e_l_e_t_.is.null')
      .single()

    if (existingBo) {
      setErrorMsg(`O Boletim ${bo.bo_number} já está sendo acompanhado pelo sistema.`)
      setSelectedBo(null)
      return
    }

    setBoItems(bo.items)
    setItemMotives({})
    setCustomItemMotives({})
  }

  const onSubmit = async (data: FormData) => {
    const userModule = profile?.module?.trim()
    if (!selectedBo || !userModule) {
      setErrorMsg('Não foi possível identificar o módulo do usuário logado.')
      return
    }
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
          modulo: userModule,
          status: 'Em Andamento'
        })
        .select()
        .single()

      if (boError) throw boError

      // Inserir Itens
      if (boItems.length > 0) {
        const itemsToInsert = boItems.map((item, index) => ({
          bo_ref: selectedBo.bo_number,
          cod: item.cod,
          desc: item.desc,
          linha: item.linha,
          motivo: customItemMotives[index] || itemMotives[index] || data.tipo_ocorrencia
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
    <div className="bo-new-page" style={{ width: '100%', maxWidth: '1500px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
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
        <div className="bo-new-panel" style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
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
              <h3 style={{ marginBottom: '1rem', fontWeight: 600 }}>BOs disponíveis ({searchResults.length})</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: 'calc(100vh - 20rem)', overflowY: 'auto', paddingRight: '0.5rem' }}>
                {searchResults.map(bo => (
                  <div key={bo.bo_number} className="bo-result-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', padding: '1rem', border: '1px solid var(--surface-border)', borderRadius: 'var(--radius-md)', background: '#fff' }}>
                    <div style={{ minWidth: 0 }}>
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
        <div className="bo-new-panel" style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
          <div className="bo-selected-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid var(--surface-border)' }}>
            <div style={{ minWidth: 0 }}>
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
            <div className="bo-form-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '1.5rem' }}>
              <div className="form-group">
                <SearchSelectModal label="Tipo de Ocorrência" value={occurrence || ''} placeholder="Selecione..." options={occurrenceOptions} onChange={value => setValue('tipo_ocorrencia', value, { shouldValidate: true })} />
                {errors.tipo_ocorrencia && <span style={{ color: 'var(--error-color)', fontSize: '0.8rem' }}>{errors.tipo_ocorrencia.message}</span>}
              </div>

              <div className="form-group">
                <SearchSelectModal label="Setor Responsável" value={sector || ''} placeholder="Selecione..." options={sectorOptions} onChange={value => setValue('setor_responsavel', value, { shouldValidate: true })} />
                {errors.setor_responsavel && <span style={{ color: 'var(--error-color)', fontSize: '0.8rem' }}>{errors.setor_responsavel.message}</span>}
              </div>

              <div className="form-group">
                <SearchSelectModal label="Frete" value={freight || ''} placeholder="Selecione..." options={['CIF', 'FOB']} onChange={value => setValue('frete', value, { shouldValidate: true })} />
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

            <div className="bo-items-section" style={{ borderTop: '1px solid var(--surface-border)', paddingTop: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>Itens da BO e motivos</h3>
              {boItems.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>Esta BO não possui itens cadastrados.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '360px', overflowY: 'auto', paddingRight: '0.5rem' }}>
                  {boItems.map((item, index) => (
                    <div key={`${item.cod}-${index}`} className="bo-item-row" style={{ display: 'grid', gridTemplateColumns: 'minmax(70px, 100px) minmax(0, 1fr) minmax(220px, 1fr)', gap: '1rem', alignItems: 'center', padding: '0.75rem', border: '1px solid var(--surface-border)', borderRadius: 'var(--radius-md)' }}>
                      <strong style={{ overflowWrap: 'anywhere' }}>{item.cod}</strong>
                      <div style={{ minWidth: 0, overflowWrap: 'anywhere' }}>
                        <div>{item.desc}</div>
                        <small style={{ color: 'var(--text-secondary)' }}>{item.linha}</small>
                      </div>
                      <div className="form-group">
                        <label htmlFor={`motivo-${index}`}>Motivo</label>
                        <SearchSelectModal label="Motivo" value={itemMotives[index] || ''} placeholder="Usar tipo selecionado" options={motivoOptions} onChange={value => {
                          setItemMotives(prev => ({ ...prev, [index]: value }))
                          setCustomItemMotives(prev => ({ ...prev, [index]: '' }))
                        }} />
                        <input
                          type="text"
                          value={customItemMotives[index] || ''}
                          onChange={event => setCustomItemMotives(prev => ({ ...prev, [index]: event.target.value }))}
                          placeholder="Ou insira um novo motivo"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
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
