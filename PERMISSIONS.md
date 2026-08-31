# Documentação de Permissões (Security & Roles)

A autorização na aplicação SAREM Web foi projetada em duas camadas:
1. **Camada de Banco (Supabase RLS)**: Impede vazamento ou manipulação indevida de dados.
2. **Camada de UI (React)**: Melhora a experiência do usuário, ocultando ações não permitidas.

## Row Level Security (RLS)
Todas as tabelas do `public` têm policies associadas.
- O acesso a BOs é sempre segregado por `modulo`. Se um usuário pertence ao 'Varejo', só lerá BOs do Varejo. Usuários com `is_admin=true` ou módulo='Todos' têm permissão de visualizar qualquer BO.
- Operações de `INSERT`, `UPDATE` e Soft Delete estão amarradas às *flags* (booleanas) de permissão encontradas na tabela `public.profiles` (`can_track_bo`, `can_edit_bo`, `can_delete_bo`).

## Camada Frontend (UI)
As funções utilitárias no frontend devem imitar a lógica das policies de banco para prover feedback em tempo real e não exibir botões que resultariam em erro (403/Forbidden) no backend.

Exemplo de utilitário sugerido:
```typescript
type Profile = {
  is_admin: boolean;
  can_edit_bo: boolean;
  can_delete_bo: boolean;
  can_track_bo: boolean;
}

export function can(user: Profile, action: 'bo.create' | 'bo.edit' | 'bo.delete'): boolean {
    if (user.is_admin) return true;
    switch (action) {
        case 'bo.create': return user.can_track_bo;
        case 'bo.edit': return user.can_edit_bo;
        case 'bo.delete': return user.can_delete_bo;
        default: return false;
    }
}
```

Nenhum token JWT hardcoded será utilizado no Frontend. A sessão Supabase cuidará de carregar as credenciais com segurança.
