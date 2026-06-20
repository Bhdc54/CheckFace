class Acesso:
    def __init__(self, id_professor=None, id_aluno=None, data=None, hora=None,
                 status: str = None, confianca: float = None):
        self.id_professor = id_professor
        self.id_aluno = id_aluno
        self.data = data
        self.hora = hora
        self.status = status  # 'liberado' ou 'negado'
        self.confianca = confianca

    def to_dict(self):
        return {
            "id_professor": self.id_professor,
            "id_aluno": self.id_aluno,
            "data": str(self.data),
            "hora": str(self.hora),
            "status": self.status,
            "confianca": self.confianca
        }