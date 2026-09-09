-- Permite que o gatilho registre alterações sem liberar inserções manuais em audit_logs.
CREATE OR REPLACE FUNCTION public.audit_bo_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO public.audit_logs (user_id, action, entity, entity_id, metadata)
        VALUES (auth.uid(), 'BO_CREATED', 'bo_records', NEW.bo_number, row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        IF (NEW.D_E_L_E_T_ = '*' AND OLD.D_E_L_E_T_ != '*') THEN
            INSERT INTO public.audit_logs (user_id, action, entity, entity_id, metadata)
            VALUES (auth.uid(), 'BO_DELETED', 'bo_records', NEW.bo_number, NULL);
        ELSE
            INSERT INTO public.audit_logs (user_id, action, entity, entity_id, metadata)
            VALUES (auth.uid(), 'BO_UPDATED', 'bo_records', NEW.bo_number, row_to_json(NEW));
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$;