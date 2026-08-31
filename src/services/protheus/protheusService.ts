export type ProtheusBOItem = {
  bo_number: string;
  cod: string;
  desc: string;
  linha: string;
}

export type ProtheusBO = {
  bo_number: string;
  op: string;
  nome_cliente: string;
  filial: string;
  emissao_totvs: string; // YYYY-MM-DD
  previsao_entrega: string; // YYYY-MM-DD
}

// SIMULANDO BANCO PROTHEUS E SUAS RESPOSTAS
const MOCK_PROTHEUS_BOS: ProtheusBO[] = [
  { bo_number: 'BO00123', op: '001001', nome_cliente: 'CLIENTE A', filial: 'TIDELLI', emissao_totvs: '2023-10-01', previsao_entrega: '2023-10-15' },
  { bo_number: 'BO00124', op: '001002', nome_cliente: 'CLIENTE B', filial: 'NAUTICA', emissao_totvs: '2023-10-02', previsao_entrega: '2023-10-20' },
  { bo_number: 'BO00125', op: '001003', nome_cliente: 'CLIENTE C', filial: 'TIDELLI', emissao_totvs: '2023-10-05', previsao_entrega: '2023-11-01' },
];

const MOCK_PROTHEUS_ITEMS: ProtheusBOItem[] = [
  { bo_number: 'BO00123', cod: 'IT001', desc: 'MESA REDONDA', linha: 'EXTERNA' },
  { bo_number: 'BO00123', cod: 'IT002', desc: 'CADEIRA ACO', linha: 'EXTERNA' },
  { bo_number: 'BO00124', cod: 'IT003', desc: 'SOFA RECLINAVEL', linha: 'INTERNA' },
];

export const protheusService = {
  
  async searchBOs(termo: string): Promise<ProtheusBO[]> {
    // Simula delay de rede
    await new Promise(r => setTimeout(r, 600));
    const upperTerm = termo.toUpperCase();
    return MOCK_PROTHEUS_BOS.filter(bo => 
      bo.bo_number.includes(upperTerm) || 
      bo.op.includes(upperTerm) ||
      bo.nome_cliente.toUpperCase().includes(upperTerm)
    );
  },

  async getBOItems(boNumber: string): Promise<ProtheusBOItem[]> {
    await new Promise(r => setTimeout(r, 400));
    return MOCK_PROTHEUS_ITEMS.filter(item => item.bo_number === boNumber);
  },

  async getBODetails(boNumber: string): Promise<ProtheusBO | null> {
    await new Promise(r => setTimeout(r, 300));
    return MOCK_PROTHEUS_BOS.find(bo => bo.bo_number === boNumber) || null;
  }
}
