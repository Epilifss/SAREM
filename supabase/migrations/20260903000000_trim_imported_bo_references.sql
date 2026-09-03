-- Remove o preenchimento de espacos herdado dos campos VARCHAR do SQL Server.
UPDATE public.bo_records
SET bo_number = btrim(bo_number)
WHERE bo_number <> btrim(bo_number);

UPDATE public.bo_itens
SET bo_ref = btrim(bo_ref)
WHERE bo_ref IS NOT NULL
  AND bo_ref <> btrim(bo_ref);