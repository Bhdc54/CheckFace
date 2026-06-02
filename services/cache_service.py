import json
import os
import threading

import numpy as np
import redis

TTL_EMBEDDINGS = 300  # 5 minutos
TTL_RESULTADO  = 30   # 30 segundos

KEY_EMBEDDINGS = "checkface:usuarios_embeddings"
KEY_RESULTADO  = "checkface:resultado:{hash}"


class CacheService:

    def __init__(self):
        self._cliente = self._conectar()
        self._lock    = threading.Lock()

    def _conectar(self):
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
        Suporta tanto objetos (alunos) quanto dicts (professores).
        """
        if not self.disponivel:
            return
        with self._lock:
            try:
                def _extrair(u):
                    if isinstance(u, dict):
                        return {
                            "id":              u.get("id"),
                            "nome":            u.get("nome"),
                            "matricula":       u.get("matricula"),
                            "siape":           u.get("siape"),
                            "encoding":        u.get("encoding"),
                            "acesso_liberado": u.get("acesso_liberado", True),
                        }
                    else:
                        return {
                            "id":              u.id,
                            "nome":            u.nome,
                            "matricula":       u.matricula,
                            "siape":           getattr(u, "siape", None),
                            "encoding":        u.encoding,
                            "acesso_liberado": u.acesso_liberado,
                        }

                dados = json.dumps([_extrair(u) for u in usuarios])
                self._cliente.setex(KEY_EMBEDDINGS, TTL_EMBEDDINGS, dados)
            except Exception as e:
                print(f"Erro ao salvar cache de embeddings: {e}")

    def invalidar_embeddings(self):
        if not self.disponivel:
            return
        try:
            self._cliente.delete(KEY_EMBEDDINGS)
        except Exception as e:
            print(f"Erro ao invalidar cache: {e}")

    # ------ Camada 2: resultado ------

    def _chave_resultado(self, encoding: np.ndarray) -> str:
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