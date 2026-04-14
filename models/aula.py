class Aula:
    def __init__(self, id: int, turma_id: int, iniciada_em=None, finalizada_em=None, relatorio_path: str = None):
        self.id = id
        self.turma_id = turma_id
        self.iniciada_em = iniciada_em
        self.finalizada_em = finalizada_em
        self.relatorio_path = relatorio_path

    def to_dict(self):
        return {
            "id": self.id,
            "turma_id": self.turma_id,
            "iniciada_em": str(self.iniciada_em),
            "finalizada_em": str(self.finalizada_em) if self.finalizada_em else None
        }