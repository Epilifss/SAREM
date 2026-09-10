CREATE TABLE IF NOT EXISTS public.app_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_by UUID REFERENCES public.profiles(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.app_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read app settings"
    ON public.app_settings FOR SELECT
    USING (auth.uid() IS NOT NULL);

CREATE POLICY "Admins can manage app settings"
    ON public.app_settings FOR ALL
    USING (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND is_admin = TRUE))
    WITH CHECK (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND is_admin = TRUE));

GRANT SELECT, UPDATE, INSERT ON public.app_settings TO authenticated;

INSERT INTO public.app_settings (key, value)
VALUES ('shipment_check_interval_minutes', '{"minutes": 5}'::jsonb)
ON CONFLICT (key) DO NOTHING;

CREATE OR REPLACE FUNCTION public.protect_bo_status_and_embarked_records()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
BEGIN
    IF auth.role() <> 'service_role' THEN
        IF TG_OP = 'INSERT' AND COALESCE(NEW.status, '') <> 'Em Andamento' THEN
            RAISE EXCEPTION 'BOs devem iniciar com status Em Andamento';
        END IF;

        IF TG_OP = 'UPDATE' AND OLD.status = 'Embarcado' THEN
            RAISE EXCEPTION 'BOs embarcados nao podem ser editados';
        END IF;

        IF TG_OP = 'UPDATE' AND NEW.status IS DISTINCT FROM OLD.status THEN
            RAISE EXCEPTION 'O status da BO so pode ser alterado pelo sincronizador de embarque';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS protect_bo_status_and_embarked_records_trigger ON public.bo_records;
CREATE TRIGGER protect_bo_status_and_embarked_records_trigger
    BEFORE INSERT OR UPDATE ON public.bo_records
    FOR EACH ROW EXECUTE PROCEDURE public.protect_bo_status_and_embarked_records();