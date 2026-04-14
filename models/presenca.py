class Presenca:
    def __init__(self, id: int, aluno_id: int, aula_id: int, data, hora, confianca: float = None):
        self.id = id
        self.aluno_id = aluno_id
        self.aula_id = aula_id
        self.data = data
        self.hora = hora
        self.confianca = confianca

    def to_dict(self):
        return {
            "id": self.id,
            "aluno_id": self.aluno_id,
            "aula_id": self.aula_id,
            "data": str(self.data),
            "hora": str(self.hora),
            "confianca": self.confianca
        }