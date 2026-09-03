-- Migration: Initial Schema for SAREM Web MVP (Refactored for Supabase Auth)

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: public.profiles (Acomoda as permissões do sistema vinculadas ao Auth nativo)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    module VARCHAR(50) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    can_edit_bo BOOLEAN DEFAULT TRUE,
    can_delete_bo BOOLEAN DEFAULT TRUE,
    can_track_bo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile" 
    ON public.profiles FOR SELECT 
    USING ( auth.uid() = id );

CREATE POLICY "Admins can view all profiles"
    ON public.profiles FOR SELECT
    USING ( EXISTS (SELECT 1 FROM public.profiles p WHERE p.id = auth.uid() AND p.is_admin = TRUE) );

CREATE POLICY "Admins can manage profiles"
    ON public.profiles FOR ALL
    USING ( EXISTS (SELECT 1 FROM public.profiles p WHERE p.id = auth.uid() AND p.is_admin = TRUE) );

-- Trigger para criar perfil automaticamente no Signup ou na importação dos usuários via SDK
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, username, module, is_admin, can_edit_bo, can_delete_bo, can_track_bo)
  VALUES (
    new.id,
    COALESCE(new.raw_user_meta_data->>'username', split_part(new.email, '@', 1)),
    COALESCE(new.raw_user_meta_data->>'module', 'Corporativo'),
    COALESCE((new.raw_user_meta_data->>'is_admin')::boolean, false),
    COALESCE((new.raw_user_meta_data->>'can_edit_bo')::boolean, true),
    COALESCE((new.raw_user_meta_data->>'can_delete_bo')::boolean, true),
    COALESCE((new.raw_user_meta_data->>'can_track_bo')::boolean, true)
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();


-- Table: public.bo_records (Totalmente compatível com colunas do SQL Server)
CREATE TABLE public.bo_records (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bo_number VARCHAR(20) UNIQUE NOT NULL,
    op VARCHAR(30),
    loja VARCHAR(100),
    emissao_totvs VARCHAR(50),
    tipo_ocorrencia VARCHAR(100),
    motivo VARCHAR(100),
    frete VARCHAR(50),
    setor_responsavel VARCHAR(100),
    status VARCHAR(50),
    previsao_embarque DATE,
    dt_embarque DATE,
    descricao TEXT,
    modulo VARCHAR(50),
    filial VARCHAR(15),
    user_edit VARCHAR(50),
    edited_at TIMESTAMP WITH TIME ZONE,
    D_E_L_E_T_ CHAR(1) DEFAULT ' ',
    user_delet VARCHAR(50),
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.bo_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view BOs according to their module"
    ON public.bo_records FOR SELECT
    USING (
        (modulo = (SELECT module FROM public.profiles WHERE id = auth.uid()) OR 
         (SELECT module FROM public.profiles WHERE id = auth.uid()) = 'Todos' OR
         (SELECT is_admin FROM public.profiles WHERE id = auth.uid()) = TRUE)
         AND COALESCE(D_E_L_E_T_, ' ') != '*'
    );

CREATE POLICY "Users can create BOs if allowed"
    ON public.bo_records FOR INSERT
    WITH CHECK (
        (SELECT can_track_bo FROM public.profiles WHERE id = auth.uid()) = TRUE
    );

CREATE POLICY "Users can update BOs if allowed"
    ON public.bo_records FOR UPDATE
    USING (
        (SELECT can_edit_bo FROM public.profiles WHERE id = auth.uid()) = TRUE OR
        (SELECT can_delete_bo FROM public.profiles WHERE id = auth.uid()) = TRUE
    );


-- Table: public.bo_itens (Mantidos os campos em maiúsculo do SQL Server)
CREATE TABLE public.bo_itens (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bo_ref VARCHAR(20),
    cod VARCHAR(10),
    "desc" VARCHAR(200),
    linha VARCHAR(50),
    motivo VARCHAR(200)
);

ALTER TABLE public.bo_itens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view BO items"
    ON public.bo_itens FOR SELECT
    USING ( EXISTS (SELECT 1 FROM public.bo_records WHERE bo_number = bo_ref) );

CREATE POLICY "Users can insert BO items"
    ON public.bo_itens FOR INSERT
    WITH CHECK ( (SELECT can_track_bo FROM public.profiles WHERE id = auth.uid()) = TRUE );

CREATE POLICY "Users can update BO items"
    ON public.bo_itens FOR UPDATE
    USING ( (SELECT can_edit_bo FROM public.profiles WHERE id = auth.uid()) = TRUE );

CREATE POLICY "Users can delete BO items"
    ON public.bo_itens FOR DELETE
    USING ( (SELECT can_edit_bo FROM public.profiles WHERE id = auth.uid()) = TRUE );


-- Table: public.audit_logs
CREATE TABLE public.audit_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id),
    action VARCHAR(50) NOT NULL,
    entity VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can view audit logs"
    ON public.audit_logs FOR SELECT
    USING ( (SELECT is_admin FROM public.profiles WHERE id = auth.uid()) = TRUE );


-- Triggers para atualização de datas e auditoria
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER handle_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE PROCEDURE public.handle_updated_at();

CREATE TRIGGER handle_bo_records_updated_at
    BEFORE UPDATE ON public.bo_records
    FOR EACH ROW EXECUTE PROCEDURE public.handle_updated_at();

CREATE OR REPLACE FUNCTION public.audit_bo_changes()
RETURNS TRIGGER AS $$
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
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_bo_changes_trigger
    AFTER INSERT OR UPDATE ON public.bo_records
    FOR EACH ROW EXECUTE PROCEDURE public.audit_bo_changes();