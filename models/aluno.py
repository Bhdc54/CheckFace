class Aluno:
    def __init__(self, id: int, nome: str, matricula: str, turma_id: int = None,
                 encoding: str = None, foto_url: str = None, acesso_liberado: bool = False):
        self.id = id
        self.nome = nome
        self.matricula = matricula
        self.turma_id = turma_id
        self.encoding = encoding
        self.foto_url = foto_url
        self.acesso_liberado = acesso_liberado

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "matricula": self.matricula,
            "acesso_liberado": self.acesso_liberado
        }