import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import face_recognition
import io

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from repositories.turma_repository import TurmaRepository
from repositories.aluno_repository import AlunoRepository
from repositories.aula_repository import AulaRepository
from repositories.presenca_repository import PresencaRepository
from services.reconhecimento_service import ReconhecimentoService
from services.relatorio_service import RelatorioService

app = FastAPI(title="CheckFace API", version="2.0.0")

turma_repo = TurmaRepository()
aluno_repo = AlunoRepository()
aula_repo = AulaRepository()
presenca_repo = PresencaRepository()
reconhecimento_service = ReconhecimentoService()
relatorio_service = RelatorioService()

@app.get("/")
def inicio():
    return {"mensagem": "API CheckFace funcionando", "versao": "2.0.0"}

@app.get("/turmas")
def listar_turmas():
    return [t.to_dict() for t in turma_repo.listar()]

@app.post("/turmas")
def criar_turma(nome: str = Form(...), professor: str = Form(...)):
    return turma_repo.criar(nome, professor).to_dict()

@app.get("/alunos")
def listar_alunos():
    return [a.to_dict() for a in aluno_repo.listar()]

@app.get("/alunos/turma/{turma_id}")
def listar_alunos_por_turma(turma_id: int):
    return [a.to_dict() for a in aluno_repo.listar_por_turma(turma_id)]

@app.post("/alunos/cadastrar")
async def cadastrar_aluno(
    nome: str = Form(...),
    matricula: str = Form(...),
    turma_id: int = Form(...),
    foto: UploadFile = File(...)
):
    conteudo = await foto.read()
    encoding, erro = reconhecimento_service.extrair_encoding(conteudo)
    if erro == "sem_rosto":
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado na foto.")
    if erro == "multiplos_rostos":
        raise HTTPException(status_code=400, detail="Mais de um rosto detectado. Envie foto individual.")
    if aluno_repo.buscar_por_matricula(matricula):
        raise HTTPException(status_code=409, detail="Matrícula já cadastrada.")
    encoding_str = reconhecimento_service.encoding_para_texto(encoding)
    aluno = aluno_repo.criar(nome, matricula, turma_id, encoding_str)
    return {"id": aluno.id, "nome": aluno.nome, "matricula": aluno.matricula, "mensagem": "Aluno cadastrado com sucesso!"}

@app.delete("/alunos/{aluno_id}")
def deletar_aluno(aluno_id: int):
    aluno_repo.deletar(aluno_id)
    return {"mensagem": "Aluno removido."}

@app.post("/reconhecer")
async def reconhecer(foto: UploadFile = File(...), aula_id: int = Form(...)):
    conteudo = await foto.read()
    return reconhecimento_service.reconhecer(conteudo, aula_id)

@app.post("/aulas/iniciar")
def iniciar_aula(turma_id: int = Form(...)):
    aula_existente = aula_repo.buscar_ativa(turma_id)
    if aula_existente:
        return {"id": aula_existente.id, "mensagem": "Aula já estava em andamento.", "status": "ja_ativa"}
    aula = aula_repo.criar(turma_id)
    return {"id": aula.id, "turma_id": aula.turma_id, "mensagem": "Aula iniciada!", "status": "iniciada"}

@app.get("/aulas/ativa/{turma_id}")
def aula_ativa(turma_id: int):
    aula = aula_repo.buscar_ativa(turma_id)
    if not aula:
        return {"ativa": False}
    return {"ativa": True, "id": aula.id, "iniciada_em": str(aula.iniciada_em)}

@app.get("/aulas/{aula_id}/presencas")
def presencas_da_aula(aula_id: int):
    dados = presenca_repo.listar_por_aula(aula_id)
    total = aula_repo.contar_alunos_turma(aula_id)
    return {
        "total_turma": total,
        "total_presentes": len(dados),
        "presencas": [{"nome": d[0], "matricula": d[1], "hora": str(d[2]), "confianca": d[3]} for d in dados]
    }

@app.post("/aulas/{aula_id}/finalizar")
def finalizar_aula(aula_id: int):
    aula = aula_repo.buscar_por_id(aula_id)
    if not aula:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    caminho = relatorio_service.gerar_excel(aula_id)
    aula_repo.finalizar(aula_id)
    nome_turma = aula[3].replace(' ', '_')
    return FileResponse(caminho, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=f"presenca_{nome_turma}_aula{aula_id}.xlsx")

@app.get("/presencas")
def listar_presencas():
    dados = presenca_repo.listar_todas()
    return [{"nome": d[0], "matricula": d[1], "data": str(d[2]), "hora": str(d[3]), "confianca": d[4], "turma": d[5]} for d in dados]