import io
import numpy as np
from datetime import datetime
from deepface import DeepFace
from PIL import Image

from repositories.aluno_repository import AlunoRepository
from repositories.presenca_repository import PresencaRepository

MODELO = "Facenet512"
TOLERANCIA = 0.40


class ReconhecimentoService:

    def __init__(self):
        self.aluno_repo = AlunoRepository()
        self.presenca_repo = PresencaRepository()

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
                img_path=img,
                model_name=MODELO,
                enforce_detection=True,
                detector_backend="opencv"
            )
            if not resultado:
                return None, "sem_rosto"
            if len(resultado) > 1:
                return None, "multiplos_rostos"
            encoding = np.array(resultado[0]["embedding"])
            return encoding, None
        except ValueError:
            return None, "sem_rosto"
        except Exception as e:
            print(f"Erro ao extrair encoding: {e}")
            return None, "sem_rosto"

    def _calcular_distancia(self, enc1: np.ndarray, enc2: np.ndarray) -> float:
        enc1 = enc1 / np.linalg.norm(enc1)
        enc2 = enc2 / np.linalg.norm(enc2)
        return float(np.linalg.norm(enc1 - enc2))

    def reconhecer(self, foto_bytes: bytes, aula_id: int) -> dict:
        try:
            img = self._bytes_para_imagem(foto_bytes)
            resultado = DeepFace.represent(
                img_path=img,
                model_name=MODELO,
                enforce_detection=True,
                detector_backend="opencv"
            )
            if not resultado:
                return {"status": "sem_rosto"}
            encoding_capturado = np.array(resultado[0]["embedding"])
        except ValueError:
            return {"status": "sem_rosto"}
        except Exception as e:
            print(f"Erro no reconhecimento: {e}")
            return {"status": "sem_rosto"}

        alunos = self.aluno_repo.listar_com_encoding()

        melhor_aluno = None
        menor_distancia = float("inf")

        for aluno in alunos:
            encoding_salvo = self.texto_para_encoding(aluno.encoding)
            distancia = self._calcular_distancia(encoding_capturado, encoding_salvo)
            if distancia < menor_distancia:
                menor_distancia = distancia
                melhor_aluno = aluno

        if melhor_aluno is None or menor_distancia > TOLERANCIA:
            return {"status": "nao_reconhecido"}

        if self.presenca_repo.ja_registrada(melhor_aluno.id, aula_id):
            return {
                "status": "ja_registrado",
                "aluno": melhor_aluno.nome,
                "mensagem": "Presença já registrada nesta aula."
            }

        agora = datetime.now()
        confianca = round(1 - (menor_distancia / TOLERANCIA), 2)
        confianca = max(0.0, min(1.0, confianca))

        self.presenca_repo.registrar(
            melhor_aluno.id, aula_id,
            agora.date(), agora.time(), confianca
        )

        return {
            "status": "reconhecido",
            "aluno": melhor_aluno.nome,
            "matricula": melhor_aluno.matricula,
            "confianca": confianca,
            "hora": agora.strftime("%H:%M:%S")
        }