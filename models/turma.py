class Turma:
    def __init__(self, id: int, nome: str, professor: str, criado_em=None):
        self.id = id
        self.nome = nome
        self.professor = professor
        self.criado_em = criado_em

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "professor": self.professor,
            "criado_em": str(self.criado_em)
        }