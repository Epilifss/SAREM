-- Reforca a chave primaria apos importacoes que recriam a tabela.
DO $$
BEGIN
    CREATE SEQUENCE IF NOT EXISTS public.bo_records_repair_seq;
    PERFORM setval(
        'public.bo_records_repair_seq',
        COALESCE((SELECT MAX(id) FROM public.bo_records), 0) + 1,
        false
    );

    WITH duplicate_rows AS (
        SELECT ctid,
               row_number() OVER (PARTITION BY id ORDER BY bo_number, ctid) AS row_number
        FROM public.bo_records
    )
    UPDATE public.bo_records AS records
    SET id = nextval('public.bo_records_repair_seq')
    FROM duplicate_rows
    WHERE records.ctid = duplicate_rows.ctid
      AND duplicate_rows.row_number > 1;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.bo_records'::regclass
          AND contype = 'p'
    ) THEN
        ALTER TABLE public.bo_records ADD CONSTRAINT bo_records_pkey PRIMARY KEY (id);
    END IF;
END $$;