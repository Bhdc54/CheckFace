import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from repositories.aluno_repository import AlunoRepository
from repositories.acesso_repository import AcessoRepository
from repositories.professor_repository import ProfessorRepository
from repositories.sala_repository import SalaRepository
from services.reconhecimento_service import ReconhecimentoService

app = FastAPI(
    title="CheckFace — Sistema Integrado de Gestão e Controle de Acesso via Reconhecimento Facial em Tempo Real",
    version="3.0.0"
)

usuario_repo = AlunoRepository()
acesso_repo = AcessoRepository()
professor_repo = ProfessorRepository()
sala_repo = SalaRepository()
reconhecimento_service = ReconhecimentoService()


# ============================================================
# RAIZ
# ============================================================
@app.get("/")
def inicio():
    return {"mensagem": "CheckFace API funcionando", "versao": "3.0.0"}


# ============================================================
# LOGIN
# ============================================================
@app.post("/login/usuario")
def login_usuario(matricula: str = Form(...), senha: str = Form(...)):
    usuario = usuario_repo.buscar_por_matricula_e_senha(matricula, senha)
    if not usuario:
        raise HTTPException(status_code=401, detail="Matrícula ou senha inválidos.")
    return {
        "tipo": "usuario",
        "id": usuario.id,
        "nome": usuario.nome,
        "matricula": usuario.matricula
    }


@app.post("/login/admin")
def login_admin(siape: str = Form(...), senha: str = Form(...)):
    admin = professor_repo.verificar_login(siape, senha)
    if not admin:
        raise HTTPException(status_code=401, detail="SIAPE ou senha inválidos.")
    return {
        "tipo": "admin",
        "id": admin.id,
        "nome": admin.nome,
        "siape": admin.siape
    }


# ============================================================
# USUÁRIOS
# ============================================================
@app.get("/usuarios")
def listar_usuarios():
    return [u.to_dict() for u in usuario_repo.listar()]


@app.post("/usuarios/cadastrar")
async def cadastrar_usuario(
    nome: str = Form(...),
    matricula: str = Form(...),
    senha: str = Form(...),
    foto: UploadFile = File(...)
):
    conteudo = await foto.read()
    encoding, erro = reconhecimento_service.extrair_encoding(conteudo)
    if erro == "sem_rosto":
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado na foto.")
    if erro == "multiplos_rostos":
        raise HTTPException(status_code=400, detail="Mais de um rosto detectado. Envie foto individual.")
    if usuario_repo.buscar_por_matricula(matricula):
        raise HTTPException(status_code=409, detail="Matrícula já cadastrada.")
    encoding_str = reconhecimento_service.encoding_para_texto(encoding)
    usuario = usuario_repo.criar(nome, matricula, 1, encoding_str, senha)
    return {"id": usuario.id, "nome": usuario.nome, "matricula": usuario.matricula, "mensagem": "Usuário cadastrado com sucesso!"}


@app.delete("/usuarios/{usuario_id}")
def deletar_usuario(usuario_id: int):
    usuario_repo.deletar(usuario_id)
    return {"mensagem": "Usuário removido."}


# ============================================================
# RECONHECIMENTO / CONTROLE DE ACESSO
# ============================================================
@app.post("/reconhecer")
async def reconhecer(foto: UploadFile = File(...)):
    conteudo = await foto.read()
    return reconhecimento_service.reconhecer(conteudo)


# ============================================================
# ACESSOS
# ============================================================
@app.get("/acessos")
def listar_acessos():
    """Lista todos os acessos — para o admin."""
    return acesso_repo.listar_todos()


@app.get("/acessos/hoje")
def acessos_hoje():
    """Lista acessos do dia — para o admin ver em tempo real."""
    return acesso_repo.listar_hoje()


@app.get("/usuarios/{usuario_id}/acessos")
def historico_usuario(usuario_id: int):
    """Histórico de acessos do usuário — para ele ver no app."""
    return acesso_repo.listar_por_usuario(usuario_id)


# ============================================================
# ADMIN
# ============================================================
@app.post("/admin/cadastrar")
def cadastrar_admin(
    nome: str = Form(...),
    siape: str = Form(...),
    senha: str = Form(...)
):
    if professor_repo.buscar_por_siape(siape):
        raise HTTPException(status_code=409, detail="SIAPE já cadastrado.")
    admin = professor_repo.criar(nome, siape, senha)
    return {"id": admin.id, "nome": admin.nome, "mensagem": "Admin cadastrado!"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)