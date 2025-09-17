class BO:
    def __init__(self, bo_number, op, loja, filial, emissao_totvs, tipo_ocorrencia, descricao, setor_responsavel, frete, previsao_embarque, modulo, status, user_include):
        self.bo_number = bo_number
        self.op = op
        self.loja = loja
        self.filial = filial
        self.emissao_totvs = emissao_totvs
        self.tipo_ocorrencia = tipo_ocorrencia
        self.descricao = descricao
        self.setor_responsavel = setor_responsavel
        self.frete = frete
        self.previsao_embarque = previsao_embarque
        self.modulo = modulo
        self.status = status
        self.user_include = user_include

    def __repr__(self):
        return f"<BO {self.bo_number} - {self.loja} - {self.status}>"