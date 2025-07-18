class BOItem:
    def __init__(self, bo_ref, cod, desc, linha, motivo):
        self.bo_ref = bo_ref
        self.cod = cod
        self.desc = desc
        self.linha = linha
        self.motivo = motivo

    def __repr__(self):
        return f"<BOItem {self.cod} - {self.desc}>"