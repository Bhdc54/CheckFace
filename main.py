import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from repositories.turma_repository import TurmaRepository
from repositories.aluno_repository import AlunoRepository
from repositories.aula_repository import AulaRepository
from repositories.presenca_repository import PresencaRepository
from repositories.professor_repository import ProfessorRepository
from services.reconhecimento_service import ReconhecimentoService
from services.relatorio_service import RelatorioService

app = FastAPI(title="CheckFace API", version="2.0.0")

turma_repo = TurmaRepository()
aluno_repo = AlunoRepository()
aula_repo = AulaRepository()
presenca_repo = PresencaRepository()
professor_repo = ProfessorRepository()
reconhecimento_service = ReconhecimentoService()
relatorio_service = RelatorioService()


# ============================================================
# RAIZ
# ============================================================
@app.get("/")
def inicio():
    return {"mensagem": "API CheckFace funcionando", "versao": "2.0.0"}


# ============================================================
# LOGIN
# ============================================================
@app.post("/login/aluno")
def login_aluno(matricula: str = Form(...), senha: str = Form(...)):
    """Login do aluno pelo RGA e senha."""
    aluno = aluno_repo.buscar_por_matricula_e_senha(matricula, senha)
    if not aluno:
        raise HTTPException(status_code=401, detail="RGA ou senha inválidos.")
    return {
        "tipo": "aluno",
        "id": aluno.id,
        "nome": aluno.nome,
        "matricula": aluno.matricula,
        "turma_id": aluno.turma_id
    }


@app.post("/login/professor")
def login_professor(siape: str = Form(...), senha: str = Form(...)):
    """Login do professor pelo SIAPE e senha."""
    professor = professor_repo.buscar_por_siape(siape)
    if not professor or professor.senha != senha:
        raise HTTPException(status_code=401, detail="SIAPE ou senha inválidos.")
    turmas = professor_repo.listar_turmas_do_professor(professor.id)
    return {
        "tipo": "professor",
        "id": professor.id,
        "nome": professor.nome,
        "siape": professor.siape,
        "turmas": turmas
    }


# ============================================================
# PROFESSORES
# ============================================================
@app.get("/professores")
def listar_professores():
    return [p.to_dict() for p in professor_repo.listar()]


@app.post("/professores/cadastrar")
def cadastrar_professor(
    nome: str = Form(...),
    siape: str = Form(...),
    senha: str = Form(...)
):
    if professor_repo.buscar_por_siape(siape):
        raise HTTPException(status_code=409, detail="SIAPE já cadastrado.")
    professor = professor_repo.criar(nome, siape, senha)
    return {"id": professor.id, "nome": professor.nome, "siape": professor.siape, "mensagem": "Professor cadastrado!"}


@app.post("/professores/{professor_id}/vincular_turma")
def vincular_turma(professor_id: int, turma_id: int = Form(...)):
    """Vincula um professor a uma turma."""
    professor_repo.vincular_turma(professor_id, turma_id)
    return {"mensagem": "Professor vinculado à turma com sucesso!"}


@app.delete("/professores/{professor_id}/desvincular_turma/{turma_id}")
def desvincular_turma(professor_id: int, turma_id: int):
    professor_repo.desvincular_turma(professor_id, turma_id)
    return {"mensagem": "Vínculo removido."}


@app.get("/professores/{professor_id}/turmas")
def turmas_do_professor(professor_id: int):
    return professor_repo.listar_turmas_do_professor(professor_id)


# ============================================================
# TURMAS
# ============================================================
@app.get("/turmas")
def listar_turmas():
    return [t.to_dict() for t in turma_repo.listar()]


@app.post("/turmas")
def criar_turma(nome: str = Form(...), professor: str = Form(...)):
    return turma_repo.criar(nome, professor).to_dict()


# ============================================================
# ALUNOS
# ============================================================
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
    senha: str = Form(...),
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
    aluno = aluno_repo.criar(nome, matricula, turma_id, encoding_str, senha)
    return {"id": aluno.id, "nome": aluno.nome, "matricula": aluno.matricula, "mensagem": "Aluno cadastrado com sucesso!"}


@app.delete("/alunos/{aluno_id}")
def deletar_aluno(aluno_id: int):
    aluno_repo.deletar(aluno_id)
    return {"mensagem": "Aluno removido."}


# ============================================================
# RECONHECIMENTO
# ============================================================
@app.post("/reconhecer")
async def reconhecer(foto: UploadFile = File(...), aula_id: int = Form(...)):
    conteudo = await foto.read()
    return reconhecimento_service.reconhecer(conteudo, aula_id)


# ============================================================
# AULAS
# ============================================================
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
    return FileResponse(
        caminho,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"presenca_{nome_turma}_aula{aula_id}.xlsx"
    )


# ============================================================
# PRESENÇAS
# ============================================================
@app.get("/presencas")
def listar_presencas():
    dados = presenca_repo.listar_todas()
    return [{"nome": d[0], "matricula": d[1], "data": str(d[2]), "hora": str(d[3]), "confianca": d[4], "turma": d[5]} for d in dados]


@app.get("/alunos/{matricula}/presencas")
def presencas_do_aluno(matricula: str):
    """Retorna histórico de presenças de um aluno específico."""
    dados = presenca_repo.listar_por_matricula(matricula)
    return dados


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)