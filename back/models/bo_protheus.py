class BO_protheus:
    def __init__(self, bo, op, cliente, empresa, emissao, previsao_entrega):
        self.bo = bo
        self.op = op
        self.cliente = cliente
        self.empresa = empresa
        self.emissao = emissao
        self.previsao_entrega = previsao_entrega

    def __repr__(self):
        return f"<BO {self.bo} - {self.cliente} - {self.empresa}>"