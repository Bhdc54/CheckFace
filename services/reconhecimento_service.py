import io
import numpy as np
from datetime import datetime
from deepface import DeepFace
from PIL import Image

from repositories.aluno_repository import AlunoRepository
from repositories.acesso_repository import AcessoRepository

MODELO = "ArcFace"
TOLERANCIA = 1.10  # Aumentado para compensar diferença entre câmeras
DETECTOR = "retinaface"


class ReconhecimentoService:

    def __init__(self):
        self.usuario_repo = AlunoRepository()
        self.acesso_repo = AcessoRepository()

    def encoding_para_texto(self, encoding: np.ndarray) -> str:
        return ",".join(map(str, encoding))

    def texto_para_encoding(self, texto: str) -> np.ndarray:
        return np.array(list(map(float, texto.split(","))))

    def _bytes_para_imagem(self, foto_bytes: bytes) -> np.ndarray:
        imagem = Image.open(io.BytesIO(foto_bytes)).convert("RGB")
        return np.array(imagem)

    def extrair_encoding(self, foto_bytes: bytes):
        try:
            img = self._bytes_para_imagem(foto_bytes)
            resultado = DeepFace.represent(
                img_path=img, model_name=MODELO,
                enforce_detection=True, detector_backend=DETECTOR
            )
            if not resultado:
                return None, "sem_rosto"
            if len(resultado) > 1:
                return None, "multiplos_rostos"
            return np.array(resultado[0]["embedding"]), None
        except ValueError:
            return None, "sem_rosto"
        except Exception as e:
            print(f"Erro ao extrair encoding: {e}")
            return None, "sem_rosto"

    def _calcular_distancia(self, enc1: np.ndarray, enc2: np.ndarray) -> float:
        enc1 = enc1 / np.linalg.norm(enc1)
        enc2 = enc2 / np.linalg.norm(enc2)
        return float(np.linalg.norm(enc1 - enc2))

    def reconhecer(self, foto_bytes: bytes) -> dict:
        agora = datetime.now()
        data_str = agora.strftime("%d/%m/%Y")
        hora_str = agora.strftime("%H:%M:%S")

        try:
            img = self._bytes_para_imagem(foto_bytes)
            resultado = DeepFace.represent(
                img_path=img, model_name=MODELO,
                enforce_detection=True, detector_backend=DETECTOR
            )
            if not resultado:
                return {"status": "negado", "mensagem": "Acesso NEGADO — nenhum rosto detectado.", "data": data_str, "hora": hora_str}
            encoding_capturado = np.array(resultado[0]["embedding"])
        except ValueError:
            return {"status": "negado", "mensagem": "Acesso NEGADO — nenhum rosto detectado.", "data": data_str, "hora": hora_str}
        except Exception as e:
            print(f"Erro: {e}")
            return {"status": "negado", "mensagem": "Acesso NEGADO — erro no processamento.", "data": data_str, "hora": hora_str}

        usuarios = self.usuario_repo.listar_com_encoding()
        melhor_usuario = None
        menor_distancia = float("inf")

        for usuario in usuarios:
            distancia = self._calcular_distancia(encoding_capturado, self.texto_para_encoding(usuario.encoding))
            print(f"Distancia para {usuario.nome}: {distancia:.4f}")
            if distancia < menor_distancia:
                menor_distancia = distancia
                melhor_usuario = usuario

        print(f"Menor distancia: {menor_distancia:.4f} | Tolerancia: {TOLERANCIA}")

        if melhor_usuario is None or menor_distancia > TOLERANCIA:
            self.acesso_repo.registrar(None, agora.date(), agora.time(), "negado", 0.0)
            return {"status": "negado", "mensagem": "Acesso NEGADO — pessoa não cadastrada.", "data": data_str, "hora": hora_str}

        confianca = round(max(0.0, min(1.0, 1 - (menor_distancia / TOLERANCIA))), 2)

        if not melhor_usuario.acesso_liberado:
            self.acesso_repo.registrar(melhor_usuario.id, agora.date(), agora.time(), "negado", confianca)
            return {
                "status": "negado",
                "mensagem": f"Acesso NEGADO — {melhor_usuario.nome} não tem permissão.",
                "nome": melhor_usuario.nome,
                "data": data_str,
                "hora": hora_str
            }

        self.acesso_repo.registrar(melhor_usuario.id, agora.date(), agora.time(), "liberado", confianca)
        return {
            "status": "liberado",
            "mensagem": f"Acesso LIBERADO — Bem-vindo, {melhor_usuario.nome}!",
            "nome": melhor_usuario.nome,
            "matricula": melhor_usuario.matricula,
            "confianca": confianca,
            "data": data_str,
            "hora": hora_str
        }