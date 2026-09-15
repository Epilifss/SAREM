import { supabase } from './supabase'

export type BoItemReference = {
  bo_ref: string
  cod: string
  desc: string
  motivo: string | null
}

const BO_REFERENCE_BATCH_SIZE = 100

export async function loadBoItemsByReferences(boReferences: string[]): Promise<BoItemReference[]> {
  const batches: string[][] = []
  for (let index = 0; index < boReferences.length; index += BO_REFERENCE_BATCH_SIZE) {
    batches.push(boReferences.slice(index, index + BO_REFERENCE_BATCH_SIZE))
  }

  const results = await Promise.all(batches.map(async batch => {
    const { data, error } = await supabase
      .from('bo_itens')
      .select('bo_ref, cod, desc, motivo')
      .in('bo_ref', batch)

    if (error) throw error
    return (data || []) as BoItemReference[]
  }))

  return results.flat()
}