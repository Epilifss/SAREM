import { useState, type FormEvent } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../providers/AuthProvider'

export default function ProfilePage() {
  const { user, profile, refreshProfile } = useAuth()
  const [username, setUsername] = useState(profile?.username || '')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!user || !profile) return
    setSaving(true)
    setMessage(null)
    setError(null)

    try {
      const { error: profileError } = await supabase
        .from('profiles')
        .update({ username: username.trim() })
        .eq('id', user.id)
      if (profileError) throw profileError

      if (password) {
        if (password.length < 6) throw new Error('A senha deve ter pelo menos 6 caracteres.')
        const { error: passwordError } = await supabase.auth.updateUser({ password })
        if (passwordError) throw passwordError
        setPassword('')
      }

      await refreshProfile()
      setMessage('Perfil atualizado com sucesso.')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Erro ao atualizar o perfil.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="profile-page">
      <div>
        <h1>Meu perfil</h1>
        <p>Atualize seus dados de acesso.</p>
      </div>
      <form className="profile-card" onSubmit={handleSubmit}>
        {error && <div className="dashboard-error">{error}</div>}
        {message && <div className="admin-success">{message}</div>}
        <div className="form-group">
          <label htmlFor="profile-username">Nome de usuário</label>
          <input id="profile-username" required value={username} onChange={event => setUsername(event.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="profile-email">E-mail</label>
          <input id="profile-email" value={user?.email || ''} disabled />
        </div>
        <div className="form-group">
          <label htmlFor="profile-password">Nova senha</label>
          <input id="profile-password" type="password" minLength={6} value={password} onChange={event => setPassword(event.target.value)} placeholder="Deixe vazio para manter a atual" />
        </div>
        <button className="primary-action" type="submit" disabled={saving}>{saving ? 'Salvando...' : 'Salvar alterações'}</button>
      </form>
    </div>
  )
}