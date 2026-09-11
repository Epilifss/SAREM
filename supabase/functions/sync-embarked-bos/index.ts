import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

type ShipmentResponse = {
  embarcado?: boolean
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }

  const supabaseUrl = Deno.env.get('SUPABASE_URL')
  const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
  if (!supabaseUrl || !serviceRoleKey) {
    return new Response(JSON.stringify({ error: 'Supabase service role não configurado' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }

  const supabase = createClient(supabaseUrl, serviceRoleKey)
  const apiUrl = (Deno.env.get('PROTHEUS_API_URL') ?? 'https://api.tidelli.com.br').replace(/\/$/, '')
  const apiKey = Deno.env.get('PROTHEUS_API_KEY')

  const { data: bos, error: queryError } = await supabase
    .from('bo_records')
    .select('id, bo_number, op, filial, status')
    .neq('status', 'Embarcado')
    .or('d_e_l_e_t_.neq.*,d_e_l_e_t_.is.null')

  if (queryError) {
    return new Response(JSON.stringify({ error: queryError.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }

  let checked = 0
  let updated = 0
  const errors: string[] = []

  for (const bo of bos ?? []) {
    if (!bo.op || !bo.filial) continue
    checked += 1

    try {
      const url = new URL(`${apiUrl}/pedidos/embarque/${encodeURIComponent(String(bo.op).trim())}`)
      url.searchParams.set('filial', String(bo.filial).trim())
      const response = await fetch(url, {
        redirect: 'manual',
        headers: apiKey ? { 'X-API-Key': apiKey } : undefined,
      })

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`)
      }

      const shipment = await response.json() as ShipmentResponse
      if (shipment.embarcado !== true) continue

      const { error: updateError } = await supabase
        .from('bo_records')
        .update({ status: 'Embarcado', dt_embarque: new Date().toISOString() })
        .eq('id', bo.id)
        .neq('status', 'Embarcado')

      if (updateError) throw updateError
      updated += 1
    } catch (error) {
      errors.push(`${bo.bo_number}: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  return new Response(JSON.stringify({ checked, updated, errors }), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  })
})