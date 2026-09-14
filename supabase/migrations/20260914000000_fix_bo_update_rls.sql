-- Keep logical BO deletion and regular edits covered by the same permission check.
DROP POLICY IF EXISTS "Users can update BOs if allowed" ON public.bo_records;

CREATE POLICY "Users can update BOs if allowed"
    ON public.bo_records FOR UPDATE
    USING (
        (SELECT can_edit_bo FROM public.profiles WHERE id = auth.uid()) = TRUE OR
        (SELECT can_delete_bo FROM public.profiles WHERE id = auth.uid()) = TRUE
    )
    WITH CHECK (TRUE);