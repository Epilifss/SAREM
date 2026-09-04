import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../providers/AuthProvider'
import { logApplicationError } from '../services/errorLogger'
import { ErrorModal } from '../components/ui/ErrorModal'

type ErrorLog = {
  id: string
  source: string
  message: string
  details: string | null
  stack: string | null
  path: string | null
  created_at: string
  profiles?: { username: string } | null
}

export default function AdminErrorLogs() {
  const { profile } = useAuth()
  const [logs, setLogs] = useState<ErrorLog[]>([])
  const [loading, setLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    const fetchLogs = async () => {
      const { data, error } = await supabase
        .from('application_error_logs')
        .select('*, profiles(username)')
        .order('created_at', { ascending: false })
        .limit(200)

      if (error) {
        setErrorMessage(error.message)
        await logApplicationError(error, { source: 'AdminErrorLogs.fetchLogs' })
      } else {
        setLogs((data || []) as ErrorLog[])
      }
      setLoading(false)
    }

    if (profile?.is_admin) fetchLogs()
  }, [profile])

  if (!profile?.is_admin) return <div style={{ padding: '2rem' }}>Acesso restrito a administradores.</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <ErrorModal message={errorMessage} onClose={() => setErrorMessage(null)} />
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Logs de erros</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Erros registrados pela aplicação nos últimos eventos.</p>
      </div>
      <div className="admin-log-panel">
        {loading ? <p>Carregando logs...</p> : logs.length === 0 ? <p>Nenhum erro registrado.</p> : (
          <div className="admin-log-list">
            {logs.map(log => (
              <article className="admin-log-entry" key={log.id}>
                <div className="admin-log-heading">
                  <strong>{log.message}</strong>
                  <time>{new Date(log.created_at).toLocaleString()}</time>
                </div>
                <div className="admin-log-meta">{log.source} · {log.path || '-'} · {log.profiles?.username || 'Usuário desconhecido'}</div>
                {log.details && <p>{log.details}</p>}
                {log.stack && <details><summary>Detalhes técnicos</summary><pre>{log.stack}</pre></details>}
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}