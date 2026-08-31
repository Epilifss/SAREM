# Documentação do Banco de Dados (Supabase / PostgreSQL)

O modelo de dados baseia-se fortemente nas regras de negócio originais do SAREM. As tabelas principais refletem as entidades do sistema. O Supabase cuida da autenticação em `auth.users`, sendo sincronizado com `public.profiles`.

## Tabelas e Relacionamentos

### 1. `public.profiles`
Contém informações estendidas do usuário e configurações de permissões. É populada automaticamente através de uma Trigger após a criação do usuário no Supabase Auth.
- **Relacionamentos:**
  - FK `id` -> `auth.users.id` (1:1)
- **Campos importantes:**
  - `module`: Indica a qual módulo o usuário pertence ("Corporativo", "Varejo", "Todos").
  - `is_admin`, `can_edit_bo`, `can_delete_bo`, `can_track_bo`: Controle fino de permissões do legado.

### 2. `public.bo_records`
Representa um Boletim de Ocorrência. É a tabela central onde ocorre o acompanhamento.
- **Relacionamentos:**
  - FK `user_include`, `user_edit`, `user_delet` -> `public.profiles.id` (N:1)
- **Campos importantes:**
  - `bo_number`: Identificador único no sistema e no Protheus.
  - `modulo`: Copiado do perfil do usuário que rastreia/inclui o BO. Fundamental para os filtros.
  - `is_deleted`: Usado para o Soft Delete.

### 3. `public.bo_itens`
Representa itens e descrições das OCs agrupadas dentro de um único BO.
- **Relacionamentos:**
  - FK `bo_id` -> `public.bo_records.id` (N:1, exclusão em cascata).

### 4. `public.audit_logs`
Armazena histórico de alterações (Criação, Atualização e Deleção) sobre as entidades principais, em especial os BOs. Mantido via Database Triggers (`public.audit_bo_changes`).

## Segurança
Todas as tabelas `public` estão com o **Row Level Security (RLS)** ativado, de forma que o vazamento de dados por endpoints seja virtualmente impossível se as queries não possuírem um contexto autenticado (`auth.uid()`).
