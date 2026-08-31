import { createClient } from '@supabase/supabase-js'

// Para o MVP usaremos as variáveis de ambiente locais do Vite
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
