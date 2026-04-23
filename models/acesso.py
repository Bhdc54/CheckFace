class Acesso:
    def __init__(self, id: int, usuario_id: int, data, hora, status: str, confianca: float = None):
        self.id = id
        self.usuario_id = usuario_id
        self.data = data
        self.hora = hora
        self.status = status  # 'liberado' ou 'negado'
        self.confianca = confianca

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "data": str(self.data),
            "hora": str(self.hora),
            "status": self.status,
            "confianca": self.confianca
        }