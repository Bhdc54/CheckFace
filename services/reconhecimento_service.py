import io
import numpy as np
import face_recognition
from datetime import datetime

from repositories.aluno_repository import AlunoRepository
from repositories.presenca_repository import PresencaRepository

TOLERANCIA = 0.50


class ReconhecimentoService:

    def __init__(self):
        self.aluno_repo = AlunoRepository()
        self.presenca_repo = PresencaRepository()

    def encoding_para_texto(self, encoding: np.ndarray) -> str:
        return ",".join(map(str, encoding))

    def texto_para_encoding(self, texto: str) -> np.ndarray:
        return np.array(list(map(float, texto.split(","))))

    def extrair_encoding(self, foto_bytes: bytes) -> np.ndarray:
        imagem = face_recognition.load_image_file(io.BytesIO(foto_bytes))
        locais = face_recognition.face_locations(imagem)
        if len(locais) == 0:
            return None, "sem_rosto"
        if len(locais) > 1:
            return None, "multiplos_rostos"
        encoding = face_recognition.face_encodings(imagem, locais)[0]
        return encoding, None

    def reconhecer(self, foto_bytes: bytes, aula_id: int) -> dict:
        imagem = face_recognition.load_image_file(io.BytesIO(foto_bytes))
        locais = face_recognition.face_locations(imagem)

        if len(locais) == 0:
            return {"status": "sem_rosto"}

        encoding_capturado = face_recognition.face_encodings(imagem, locais)[0]
        alunos = self.aluno_repo.listar_com_encoding()

        melhor_aluno = None
        menor_distancia = 1.0

        for aluno in alunos:
            encoding_salvo = self.texto_para_encoding(aluno.encoding)
            distancia = face_recognition.face_distance([encoding_salvo], encoding_capturado)[0]
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
        confianca = round(1 - menor_distancia, 2)

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