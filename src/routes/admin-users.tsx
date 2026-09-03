import { useEffect, useState, type FormEvent } from 'react'
import { supabase } from '../lib/supabase'
import type { Profile } from '../types'
import { DataTable } from '../components/ui/DataTable'
import { useAuth } from '../providers/AuthProvider'

export default function AdminUsers() {
  const [users, setUsers] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const { profile } = useAuth()
  const [isCreating, setIsCreating] = useState(false)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createSuccess, setCreateSuccess] = useState<string | null>(null)
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    module: 'Corporativo',
    is_admin: false,
    can_edit_bo: true,
    can_delete_bo: true,
    can_track_bo: true,
  })

  // Evitar acesso via URL
  if (!profile?.is_admin) {
    return <div style={{ padding: '2rem' }}>Acesso restrito a administradores.</div>
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    setLoading(true)
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .order('username')

    if (!error && data) setUsers(data as Profile[])
    setLoading(false)
  }

  const handleToggle = async (userId: string, field: keyof Profile, currentValue: boolean) => {
    const { error } = await supabase
      .from('profiles')
      .update({ [field]: !currentValue })
      .eq('id', userId)

    if (!error) {
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, [field]: !currentValue } : u))
    }
  }

  const handleModuleChange = async (userId: string, newModule: string) => {
    const { error } = await supabase
      .from('profiles')
      .update({ module: newModule })
      .eq('id', userId)

    if (!error) {
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, module: newModule } : u))
    }
  }

  const handleCreateUser = async (event: FormEvent) => {
    event.preventDefault()
    setIsCreating(true)
    setCreateError(null)
    setCreateSuccess(null)

    try {
      const { data: sessionData } = await supabase.auth.getSession()
      const { data, error } = await supabase.auth.signUp({
        email: newUser.email,
        password: newUser.password,
        options: {
          data: {
            username: newUser.username,
            module: newUser.module,
            is_admin: newUser.is_admin,
            can_edit_bo: newUser.can_edit_bo,
            can_delete_bo: newUser.can_delete_bo,
            can_track_bo: newUser.can_track_bo,
          },
        },
      })

      if (sessionData.session) await supabase.auth.setSession(sessionData.session)
      if (error) throw error
      if (!data.user) throw new Error('O usuário não foi criado.')

      const { error: profileError } = await supabase
        .from('profiles')
        .update({
          username: newUser.username,
          module: newUser.module,
          is_admin: newUser.is_admin,
          can_edit_bo: newUser.can_edit_bo,
          can_delete_bo: newUser.can_delete_bo,
          can_track_bo: newUser.can_track_bo,
        })
        .eq('id', data.user.id)

      if (profileError) throw profileError

      setCreateSuccess('Usuário criado com sucesso.')
      setNewUser({ username: '', email: '', password: '', module: 'Corporativo', is_admin: false, can_edit_bo: true, can_delete_bo: true, can_track_bo: true })
      fetchUsers()
    } catch (err: any) {
      setCreateError(err.message || 'Erro ao criar usuário.')
    } finally {
      setIsCreating(false)
    }
  }

  const columns = [
    { header: 'Usuário', accessor: 'username' as keyof Profile },
    { header: 'Módulo', accessor: (row: Profile) => (
      <select 
        value={row.module} 
        onChange={(e) => handleModuleChange(row.id, e.target.value)}
        style={{ padding: '0.25rem', borderRadius: '4px' }}
      >
        <option value="Corporativo">Corporativo</option>
        <option value="Varejo">Varejo</option>
        <option value="Exportação">Exportação</option>
        <option value="Comercial">Comercial</option>
        <option value="Todos">Todos</option>
      </select>
    ) },
    { header: 'Admin', accessor: (row: Profile) => (
      <input type="checkbox" checked={row.is_admin} onChange={() => handleToggle(row.id, 'is_admin', row.is_admin)} />
    ) },
    { header: 'Editar BO', accessor: (row: Profile) => (
      <input type="checkbox" checked={row.can_edit_bo} onChange={() => handleToggle(row.id, 'can_edit_bo', row.can_edit_bo)} />
    ) },
    { header: 'Acompanhar BO', accessor: (row: Profile) => (
      <input type="checkbox" checked={row.can_track_bo} onChange={() => handleToggle(row.id, 'can_track_bo', row.can_track_bo)} />
    ) },
    { header: 'Excluir BO', accessor: (row: Profile) => (
      <input type="checkbox" checked={row.can_delete_bo} onChange={() => handleToggle(row.id, 'can_delete_bo', row.can_delete_bo)} />
    ) },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <div className="page-heading-row">
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Gestão de Usuários</h1>
            <p style={{ color: 'var(--text-secondary)' }}>Edite as permissões e o módulo dos usuários cadastrados.</p>
          </div>
          <button className="primary-action" type="button" onClick={() => { setCreateError(null); setCreateSuccess(null); setIsCreateModalOpen(true) }}>
            + Adicionar usuário
          </button>
        </div>
      </div>

      {isCreateModalOpen && <div className="modal-backdrop" role="presentation" onMouseDown={() => !isCreating && setIsCreateModalOpen(false)}>
        <section className="admin-create-panel user-create-modal" role="dialog" aria-modal="true" aria-labelledby="new-user-title" onMouseDown={event => event.stopPropagation()}>
        <div className="dashboard-panel-heading">
          <div>
            <h2 id="new-user-title">Novo usuário</h2>
            <p>Cadastre o acesso e as permissões iniciais.</p>
          </div>
          <button className="modal-close" type="button" onClick={() => setIsCreateModalOpen(false)} disabled={isCreating} aria-label="Fechar">×</button>
        </div>
        {createError && <div className="dashboard-error">{createError}</div>}
        {createSuccess && <div className="admin-success">{createSuccess}</div>}
        <form className="admin-create-form" onSubmit={handleCreateUser}>
          <div className="form-group"><label htmlFor="new-username">Usuário</label><input id="new-username" required value={newUser.username} onChange={event => setNewUser({ ...newUser, username: event.target.value })} /></div>
          <div className="form-group"><label htmlFor="new-email">E-mail</label><input id="new-email" required type="email" value={newUser.email} onChange={event => setNewUser({ ...newUser, email: event.target.value })} /></div>
          <div className="form-group"><label htmlFor="new-password">Senha temporária</label><input id="new-password" required minLength={6} type="password" value={newUser.password} onChange={event => setNewUser({ ...newUser, password: event.target.value })} /></div>
          <div className="form-group"><label htmlFor="new-module">Módulo</label><select id="new-module" value={newUser.module} onChange={event => setNewUser({ ...newUser, module: event.target.value })}><option>Corporativo</option><option>Varejo</option><option>Exportação</option><option>Comercial</option><option>Todos</option></select></div>
          <div className="admin-permissions">
            {([['is_admin', 'Administrador'], ['can_edit_bo', 'Editar BO'], ['can_delete_bo', 'Excluir BO'], ['can_track_bo', 'Acompanhar BO']] as const).map(([field, label]) => <label key={field}><input type="checkbox" checked={newUser[field]} onChange={event => setNewUser({ ...newUser, [field]: event.target.checked })} />{label}</label>)}
          </div>
          <button className="auth-button admin-create-button" type="submit" disabled={isCreating}>{isCreating ? 'Criando...' : 'Criar usuário'}</button>
        </form>
        </section>
      </div>}

      <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          As alterações feitas nas caixas de seleção são salvas automaticamente.
        </p>
        <DataTable data={users} columns={columns} isLoading={loading} />
      </div>
    </div>
  )
}
