import { supabase } from '../lib/supabase'

type LogErrorContext = {
  source: string
  details?: string
  stack?: string
}

export async function logApplicationError(error: unknown, context: LogErrorContext) {
  const normalizedError = error instanceof Error ? error : new Error(String(error))

  try {
    const { data: { user } } = await supabase.auth.getUser()
    await supabase.from('application_error_logs').insert({
      user_id: user?.id || null,
      source: context.source,
      message: normalizedError.message,
      details: context.details || null,
      stack: context.stack || normalizedError.stack || null,
      path: window.location.pathname,
    })
  } catch {
    // Logging must never mask the original application error.
  }
}