CREATE OR REPLACE FUNCTION public.soft_delete_bo(p_id BIGINT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM public.profiles
        WHERE id = auth.uid()
          AND can_delete_bo = TRUE
    ) THEN
        RAISE EXCEPTION 'Usuário sem permissão para excluir BO' USING ERRCODE = '42501';
    END IF;

    UPDATE public.bo_records
    SET d_e_l_e_t_ = '*',
        user_delet = auth.uid(),
        deleted_at = timezone('utc'::text, now())
    WHERE id = p_id
      AND COALESCE(d_e_l_e_t_, ' ') <> '*';
END;
$$;

REVOKE ALL ON FUNCTION public.soft_delete_bo(BIGINT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.soft_delete_bo(BIGINT) TO authenticated;