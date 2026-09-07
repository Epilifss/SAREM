-- Grant the table privileges required by PostgREST.
-- RLS policies restrict rows; they do not grant SQL table privileges.

GRANT USAGE ON SCHEMA public TO authenticated;

GRANT SELECT, UPDATE ON public.profiles TO authenticated;

GRANT SELECT, INSERT, UPDATE ON public.bo_records TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.bo_itens TO authenticated;
GRANT SELECT, INSERT ON public.audit_logs TO authenticated;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

GRANT SELECT, INSERT ON public.application_error_logs TO authenticated;