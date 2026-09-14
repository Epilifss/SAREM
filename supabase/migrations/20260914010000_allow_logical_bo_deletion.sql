-- A logical deletion changes D_E_L_E_T_ to '*', which is intentionally hidden by SELECT RLS.
DROP POLICY IF EXISTS "Users can update BOs if allowed" ON public.bo_records;

CREATE POLICY "Users can update BOs if allowed"
    ON public.bo_records FOR UPDATE
    USING (
        (SELECT can_edit_bo FROM public.profiles WHERE id = auth.uid()) = TRUE OR
        (SELECT can_delete_bo FROM public.profiles WHERE id = auth.uid()) = TRUE
    )
    WITH CHECK (TRUE);