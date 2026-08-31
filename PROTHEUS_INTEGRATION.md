# Integração com o ERP Protheus

A premissa da nova arquitetura web do SAREM é que **o frontend e o banco web (Supabase) NÃO DEVEM se comunicar diretamente com o banco de dados do Protheus** por questões de segurança, desempenho e isolamento arquitetural.

## Fluxo Atual (Mocks)
Como a API REST do Protheus ainda não está finalizada, o arquivo `src/services/protheus/protheusService.ts` contém dados estáticos (Mocks) que imitam o comportamento esperado.

## Futuro (API REST)
Quando a equipe de ERP finalizar o desenvolvimento da API no Protheus (possivelmente usando TLPP / REST-Protheus), o arquivo `protheusService.ts` deverá ser substituído por chamadas HTTP:

```typescript
// Exemplo de como ficará o protheusService.ts no futuro
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_PROTHEUS_API_URL,
  headers: {
    'Authorization': `Bearer ${import.meta.env.VITE_PROTHEUS_TOKEN}`
  }
});

export const protheusService = {
  async searchBOs(termo: string): Promise<ProtheusBO[]> {
    const response = await api.get('/bos', { params: { search: termo } });
    return response.data;
  },
  // ...
}
```

## Dados Importados (Domain Mapping)
A busca por um BO no Protheus deve retornar o esqueleto operacional da venda/pedido, sem os dados de rastreio que pertencem estritamente ao SAREM. O SAREM fará o enriquecimento (com tipo ocorrência, frete, status).
- `C5_PEDREPR` -> `bo_number`
- `C5_NUM` -> `op`
- `C5_FILIAL` -> `filial`
- `C5_EMISSAO` -> `emissao_totvs`
