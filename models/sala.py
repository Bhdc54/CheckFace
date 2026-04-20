class Sala:
    def __init__(self, id: int, nome: str, descricao: str = None, criado_em=None):
        self.id = id
        self.nome = nome
        self.descricao = descricao
        self.criado_em = criado_em

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "criado_em": str(self.criado_em) if self.criado_em else None
        }