class Professor:
    def __init__(self, id: int, nome: str, siape: str, senha: str = None, criado_em=None):
        self.id = id
        self.nome = nome
        self.siape = siape
        self.senha = senha
        self.criado_em = criado_em

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "siape": self.siape,
            "criado_em": str(self.criado_em) if self.criado_em else None
        }