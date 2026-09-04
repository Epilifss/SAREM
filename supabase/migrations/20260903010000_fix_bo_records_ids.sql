-- Garante IDs numericos para registros importados e novos BOs.
DO $$
DECLARE
    sequence_name TEXT;
BEGIN
    SELECT pg_get_serial_sequence('public.bo_records', 'id')
      INTO sequence_name;

    IF sequence_name IS NULL THEN
        CREATE SEQUENCE IF NOT EXISTS public.bo_records_id_seq;
        ALTER TABLE public.bo_records
            ALTER COLUMN id SET DEFAULT nextval('public.bo_records_id_seq');
        sequence_name := 'public.bo_records_id_seq';
    END IF;

    EXECUTE format(
        'UPDATE public.bo_records SET id = nextval(%L) WHERE id IS NULL',
        sequence_name
    );

    EXECUTE format(
        'SELECT setval(%L, COALESCE((SELECT MAX(id) FROM public.bo_records), 0) + 1, false)',
        sequence_name
    );

    ALTER TABLE public.bo_records ALTER COLUMN id SET NOT NULL;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.bo_records'::regclass
          AND contype = 'p'
    ) THEN
        ALTER TABLE public.bo_records ADD CONSTRAINT bo_records_pkey PRIMARY KEY (id);
    END IF;
END $$;