import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import type { Profile } from '../types'
import { DataTable } from '../components/ui/DataTable'
import { useAuth } from '../providers/AuthProvider'

export default function AdminUsers() {
  const [users, setUsers] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const { profile } = useAuth()

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
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Gestão de Usuários</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Edite as permissões e o módulo dos usuários cadastrados.</p>
      </div>

      <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-sm)' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          As alterações feitas nas caixas de seleção são salvas automaticamente.
        </p>
        <DataTable data={users} columns={columns} isLoading={loading} />
      </div>
    </div>
  )
}
