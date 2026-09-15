-- Permite múltiplos registros com o mesmo bo_number (ex: registros marcados com D_E_L_E_T_ ou histórico de edições)
ALTER TABLE public.bo_records DROP CONSTRAINT IF EXISTS bo_records_bo_number_key;
DROP INDEX IF EXISTS public.bo_records_bo_number_key;
