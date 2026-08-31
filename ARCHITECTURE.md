# Arquitetura Frontend

O sistema foi reconstruído como uma Single Page Application (SPA) utilizando Vite + React + TypeScript.

## Stack Utilizado
- **React 19**: Biblioteca UI principal.
- **React Router v6**: Para navegação (SPA) protegida por sessão.
- **Supabase JS**: Cliente para gerenciar autenticação (Auth) e requisições ao PostgreSQL (Database).
- **React Hook Form + Zod**: Gerenciamento de estado de formulários complexos e validação estrita baseada em schemas.

## Estrutura de Pastas (Implementada)
```
src/
├── components/
│   ├── layout/         # AppShell (Sidebar, Header, Layouts)
│   ├── navigation/     # ProtectedRoute, menus
│   └── ui/             # Componentes genéricos (Table, Input, Button)
├── lib/
│   └── supabase.ts     # Instância única do cliente Supabase
├── providers/
│   └── AuthProvider.tsx# Contexto de autenticação global e controle de sessão
├── routes/
│   └── auth.tsx        # Rotas em modo componente-página (/login, etc)
├── services/
│   └── protheus/       # Serviços e Mocks para comunicação com Protheus
├── types/
│   └── index.ts        # Definições TS centrais (Profile, BO_Record)
```

## Estilização (Vanilla CSS)
A pedido do projeto, a estilização central é feita sem bibliotecas como Tailwind. Foi criado um **Design System leve** no arquivo `index.css`, expondo variáveis de tema (cores, espaçamentos, sombras) inspiradas no *glassmorphism* e num visual corporativo premium, com uso da fonte *Inter*.
