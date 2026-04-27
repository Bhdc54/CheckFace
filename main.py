import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from repositories.aluno_repository import AlunoRepository
from repositories.acesso_repository import AcessoRepository
from repositories.professor_repository import ProfessorRepository
from services.reconhecimento_service import ReconhecimentoService

app = FastAPI(
    title="CheckFace — Sistema Integrado de Gestão e Controle de Acesso via Reconhecimento Facial em Tempo Real",
    version="3.0.0"
)

usuario_repo = AlunoRepository()
acesso_repo = AcessoRepository()
professor_repo = ProfessorRepository()
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
        "matricula": usuario.matricula,
        "acesso_liberado": usuario.acesso_liberado
    }


@app.post("/login/admin")
def login_admin(siape: str = Form(...), senha: str = Form(...)):
    admin = professor_repo.verificar_login(siape, senha)
    if not admin:
        raise HTTPException(status_code=401, detail="SIAPE ou senha inválidos.")
    return {"tipo": "admin", "id": admin.id, "nome": admin.nome, "siape": admin.siape}


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
    usuario = usuario_repo.criar(nome, matricula, encoding_str, senha)
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "matricula": usuario.matricula,
        "mensagem": "Cadastro realizado! Aguarde liberação do administrador."
    }


@app.delete("/usuarios/{usuario_id}")
def deletar_usuario(usuario_id: int):
    usuario_repo.deletar(usuario_id)
    return {"mensagem": "Usuário removido."}


# ============================================================
# CONTROLE DE ACESSO — ADMIN
# ============================================================
@app.post("/admin/liberar_acesso")
def liberar_acesso(matricula: str = Form(...)):
    """Admin libera acesso pelo RGA do usuário."""
    row = usuario_repo.liberar_acesso(matricula)
    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return {"mensagem": f"Acesso liberado para {row[1]}!"}


@app.post("/admin/revogar_acesso")
def revogar_acesso(matricula: str = Form(...)):
    """Admin revoga acesso pelo RGA do usuário."""
    row = usuario_repo.revogar_acesso(matricula)
    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return {"mensagem": f"Acesso revogado para {row[1]}."}


@app.post("/admin/cadastrar")
def cadastrar_admin(nome: str = Form(...), siape: str = Form(...), senha: str = Form(...)):
    if professor_repo.buscar_por_siape(siape):
        raise HTTPException(status_code=409, detail="SIAPE já cadastrado.")
    admin = professor_repo.criar(nome, siape, senha)
    return {"id": admin.id, "nome": admin.nome, "mensagem": "Admin cadastrado!"}


# ============================================================
# RECONHECIMENTO
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
    return acesso_repo.listar_todos()


@app.get("/acessos/hoje")
def acessos_hoje():
    return acesso_repo.listar_hoje()


@app.get("/usuarios/{usuario_id}/acessos")
def historico_usuario(usuario_id: int):
    return acesso_repo.listar_por_usuario(usuario_id)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)