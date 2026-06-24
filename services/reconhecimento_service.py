import io

import numpy as np
from datetime import datetime
from deepface import DeepFace
from PIL import Image
import pytz

from repositories.aluno_repository import AlunoRepository
from repositories.acesso_repository import AcessoRepository
from repositories.professor_repository import ProfessorRepository
from services.cache_service import CacheService

MODELO          = "ArcFace"
TOLERANCIA      = 2.0
DISTANCIA_IDEAL = 0.50
DETECTOR        = "retinaface"


class ReconhecimentoService:

    def __init__(self):
        self.usuario_repo   = AlunoRepository()
        self.professor_repo = ProfessorRepository()
        self.acesso_repo    = AcessoRepository()
        self.cache          = CacheService()

    # ------ Conversão ------

    def encoding_para_texto(self, encoding: np.ndarray) -> str:
        return ",".join(map(str, encoding))

    def texto_para_encoding(self, texto: str) -> np.ndarray:
        return np.array(list(map(float, texto.split(","))))

    def _bytes_para_imagem(self, foto_bytes: bytes) -> np.ndarray:
        imagem = Image.open(io.BytesIO(foto_bytes)).convert("RGB")
        return np.array(imagem)

    # ------ Cálculos ------

    def _calcular_distancia(self, enc1: np.ndarray, enc2: np.ndarray) -> float:
        enc1 = enc1 / np.linalg.norm(enc1)
        enc2 = enc2 / np.linalg.norm(enc2)
        return float(np.linalg.norm(enc1 - enc2))

    def _calcular_confianca(self, distancia: float) -> float:
        if distancia <= DISTANCIA_IDEAL:
            return 1.0
        confianca = 1.0 - ((distancia - DISTANCIA_IDEAL) / (TOLERANCIA - DISTANCIA_IDEAL))
        return round(max(0.0, min(1.0, confianca)), 2)

    # ------ Usuários com cache ------

    def _get_usuarios(self) -> list:
        usuarios = self.cache.get_embeddings()
        if usuarios:
            return usuarios

        alunos      = self.usuario_repo.listar_com_encoding()
        professores = self.professor_repo.listar_com_encoding()
        todos       = alunos + professores

        self.cache.salvar_embeddings(todos)
        return todos

    def invalidar_cache(self):
        self.cache.invalidar_embeddings()

    # ------ Extração de encoding app ------

    def extrair_encoding(self, foto_bytes: bytes):
        try:
            img = self._bytes_para_imagem(foto_bytes)
            resultado = DeepFace.represent(
                img_path=img,
                model_name=MODELO,
                enforce_detection=True,
                detector_backend=DETECTOR,
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

    # ------ Reconhecimento principal ------

    def reconhecer(self, foto_bytes: bytes) -> dict:
        fuso     = pytz.timezone("America/Cuiaba")
        agora    = datetime.now(fuso)
        data_str = agora.strftime("%d/%m/%Y")
        hora_str = agora.strftime("%H:%M:%S")

        # 1. Extrai o embedding do rosto capturado pelo totem
        try:
            img = self._bytes_para_imagem(foto_bytes)
            resultado_deepface = DeepFace.represent(
                img_path=img,
                model_name=MODELO,
                enforce_detection=True,
                detector_backend=DETECTOR,
            )
            if not resultado_deepface:
                return {"status": "negado", "mensagem": "Acesso NEGADO — nenhum rosto detectado.", "data": data_str, "hora": hora_str}
            encoding_capturado = np.array(resultado_deepface[0]["embedding"])
        except ValueError:
            return {"status": "negado", "mensagem": "Acesso NEGADO — nenhum rosto detectado.", "data": data_str, "hora": hora_str}
        except Exception as e:
            print(f"Erro: {e}")
            return {"status": "negado", "mensagem": "Acesso NEGADO — erro no processamento.", "data": data_str, "hora": hora_str}

        # 2. Verifica cache de resultado (Camada 2)
        resultado_cacheado = self.cache.get_resultado(encoding_capturado)
        if resultado_cacheado:
            resultado_cacheado["data"] = data_str
            resultado_cacheado["hora"] = hora_str
            return resultado_cacheado

        # 3. Busca alunos + professores (Camada 1)
        usuarios        = self._get_usuarios()
        melhor_usuario  = None
        menor_distancia = float("inf")

        for u in usuarios:
            encoding_texto = u["encoding"] if isinstance(u, dict) else u.encoding
            nome           = u["nome"]     if isinstance(u, dict) else u.nome
            distancia      = self._calcular_distancia(
                encoding_capturado,
                self.texto_para_encoding(encoding_texto)
            )
            print(f"Distancia para {nome}: {distancia:.4f}")
            if distancia < menor_distancia:
                menor_distancia = distancia
                melhor_usuario  = u

        print(f"Menor distancia: {menor_distancia:.4f} | Tolerancia: {TOLERANCIA}")

        # 4. Verifica limiar
        if melhor_usuario is None or menor_distancia > TOLERANCIA:
            # Acesso negado por nao reconhecimento nao e gravado no banco
            resposta = {"status": "negado", "mensagem": "Acesso NEGADO — pessoa nao cadastrada.", "data": data_str, "hora": hora_str}
            self.cache.salvar_resultado(encoding_capturado, resposta)
            return resposta

        # 5. Determina tipo do usuário reconhecido
        confianca       = self._calcular_confianca(menor_distancia)
        acesso_liberado = melhor_usuario["acesso_liberado"] if isinstance(melhor_usuario, dict) else melhor_usuario.acesso_liberado
        nome            = melhor_usuario["nome"]            if isinstance(melhor_usuario, dict) else melhor_usuario.nome
        matricula       = melhor_usuario["matricula"]       if isinstance(melhor_usuario, dict) else melhor_usuario.matricula
        usuario_id      = melhor_usuario["id"]              if isinstance(melhor_usuario, dict) else melhor_usuario.id

        if isinstance(melhor_usuario, dict):
            tipo_usuario = "professor" if melhor_usuario.get("siape") else "aluno"
        else:
            tipo_usuario = "professor" if hasattr(melhor_usuario, "siape") else "aluno"

        # 6. Verifica permissão
        if not acesso_liberado:
            # Acesso negado por falta de permissao nao e gravado no banco
            resposta = {
                "status":       "negado",
                "mensagem":     f"Acesso NEGADO — {nome} nao tem permissao.",
                "nome":         nome,
                "tipo_usuario": tipo_usuario,
                "data":         data_str,
                "hora":         hora_str,
            }
            self.cache.salvar_resultado(encoding_capturado, resposta)
            return resposta

        # 7. Registra acesso liberado
        self.acesso_repo.registrar(usuario_id, agora.date(), agora.time(), "liberado", confianca, tipo_usuario)
        resposta = {
            "status":       "liberado",
            "mensagem":     f"Acesso LIBERADO — Bem-vindo, {nome}!",
            "nome":         nome,
            "matricula":    matricula,
            "confianca":    confianca,
            "tipo_usuario": tipo_usuario,
            "data":         data_str,
            "hora":         hora_str,
        }
        self.cache.salvar_resultado(encoding_capturado, resposta)
        return resposta