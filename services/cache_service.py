import json
import os
import threading

import numpy as np
import redis

# TTL = tempo em segundos que o dado permanece no cache
TTL_EMBEDDINGS = 300  # 5 minutos
TTL_RESULTADO  = 30   # 30 segundos

KEY_EMBEDDINGS = "checkface:usuarios_embeddings"
KEY_RESULTADO  = "checkface:resultado:{hash}"


class CacheService:
    """
    Gerencia o cache Redis em duas camadas:
    - Camada 1: lista de todos os usuários (alunos + professores) e embeddings
    - Camada 2: resultado do reconhecimento por rosto
    """

    def __init__(self):
        self._cliente = self._conectar()
        self._lock    = threading.Lock()

    def _conectar(self):
        # REDIS_URL é definida automaticamente pelo Railway ao adicionar o serviço Redis
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            cliente = redis.from_url(url, decode_responses=True)
            cliente.ping()
            print("Redis conectado.")
            return cliente
        except Exception as e:
            print(f"Redis indisponivel: {e}. Rodando sem cache.")
            return None

    @property
    def disponivel(self) -> bool:
        return self._cliente is not None

    # ------ Camada 1: embeddings ------

    def get_embeddings(self):
        if not self.disponivel:
            return None
        try:
            dados = self._cliente.get(KEY_EMBEDDINGS)
            if dados:
                return json.loads(dados)
        except Exception as e:
            print(f"Erro ao ler cache de embeddings: {e}")
        return None

    def salvar_embeddings(self, usuarios: list):
        """
        Serializa e salva a lista unificada de alunos e professores.
        Espera objetos com os atributos: id, nome, matricula, encoding, acesso_liberado.
        """
        if not self.disponivel:
            return
        with self._lock:
            try:
                dados = json.dumps([
                    {
                        "id":              u.id,
                        "nome":            u.nome,
                        "matricula":       u.matricula,
                        "encoding":        u.encoding,
                        "acesso_liberado": u.acesso_liberado,
                    }
                    for u in usuarios
                ])
                self._cliente.setex(KEY_EMBEDDINGS, TTL_EMBEDDINGS, dados)
            except Exception as e:
                print(f"Erro ao salvar cache de embeddings: {e}")

    def invalidar_embeddings(self):
        # Chame após cadastrar, editar ou alterar permissão de qualquer usuário
        if not self.disponivel:
            return
        try:
            self._cliente.delete(KEY_EMBEDDINGS)
        except Exception as e:
            print(f"Erro ao invalidar cache: {e}")

    # ------ Camada 2: resultado ------

    def _chave_resultado(self, encoding: np.ndarray) -> str:
        # Usa os 8 primeiros valores do embedding como chave única
        return KEY_RESULTADO.format(
            hash="_".join(f"{v:.2f}" for v in encoding[:8])
        )

    def get_resultado(self, encoding: np.ndarray):
        if not self.disponivel:
            return None
        try:
            dados = self._cliente.get(self._chave_resultado(encoding))
            if dados:
                return json.loads(dados)
        except Exception as e:
            print(f"Erro ao ler cache de resultado: {e}")
        return None

    def salvar_resultado(self, encoding: np.ndarray, resultado: dict):
        if not self.disponivel:
            return
        try:
            self._cliente.setex(
                self._chave_resultado(encoding),
                TTL_RESULTADO,
                json.dumps(resultado)
            )
        except Exception as e:
            print(f"Erro ao salvar cache de resultado: {e}")