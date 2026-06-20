import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from repositories.aluno_repository import AlunoRepository
from repositories.acesso_repository import AcessoRepository
from repositories.professor_repository import ProfessorRepository
from services.reconhecimento_service import ReconhecimentoService

app = FastAPI(
    title="CheckFace — Sistema Integrado de Gestão e Controle de Acesso via Reconhecimento Facial em Tempo Real",
    version="3.1.0"
)

usuario_repo           = AlunoRepository()
acesso_repo            = AcessoRepository()
professor_repo         = ProfessorRepository()
reconhecimento_service = ReconhecimentoService()

# Limiar restritivo para recuperação de senha:
TOLERANCIA_RECUPERACAO = 0.8


@app.get("/")
def inicio():
    return {"mensagem": "CheckFace API funcionando", "versao": "3.1.0"}


# ============================================================
# LOGIN
# ============================================================

@app.post("/login/usuario")
def login_usuario(matricula: str = Form(...), senha: str = Form(...)):
    usuario = usuario_repo.buscar_por_matricula_e_senha(matricula, senha)
    if not usuario:
        raise HTTPException(status_code=401, detail="Matrícula ou senha inválidos.")
    return {
        "tipo":            "usuario",
        "id":              usuario.id,
        "nome":            usuario.nome,
        "matricula":       usuario.matricula,
        "acesso_liberado": usuario.acesso_liberado,
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
    nome:      str        = Form(...),
    matricula: str        = Form(...),
    senha:     str        = Form(...),
    foto:      UploadFile = File(...)
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
    usuario      = usuario_repo.criar(nome, matricula, encoding_str, senha)

    reconhecimento_service.invalidar_cache()

    return {
        "id":        usuario.id,
        "nome":      usuario.nome,
        "matricula": usuario.matricula,
        "mensagem":  "Cadastro realizado! Aguarde liberação do administrador.",
    }


@app.delete("/usuarios/{usuario_id}")
def deletar_usuario(usuario_id: int):
    usuario_repo.deletar(usuario_id)
    reconhecimento_service.invalidar_cache()
    return {"mensagem": "Usuário removido."}


# ============================================================
# RECUPERAÇÃO DE SENHA — USUÁRIO
# ============================================================

@app.post("/usuarios/recuperar_senha")
async def recuperar_senha_usuario(
    matricula:  str        = Form(...),
    nova_senha: str        = Form(...),
    foto:       UploadFile = File(...)
):
    usuario = usuario_repo.buscar_por_matricula_completo(matricula)
    if not usuario:
        raise HTTPException(status_code=404, detail="RGA não encontrado.")
    if not usuario.encoding:
        raise HTTPException(status_code=400, detail="Usuário sem foto cadastrada.")

    conteudo = await foto.read()
    encoding_novo, erro = reconhecimento_service.extrair_encoding(conteudo)
    if erro == "sem_rosto":
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado na foto.")
    if erro == "multiplos_rostos":
        raise HTTPException(status_code=400, detail="Mais de um rosto detectado.")

    encoding_cadastrado = reconhecimento_service.texto_para_encoding(usuario.encoding)
    distancia = reconhecimento_service._calcular_distancia(encoding_novo, encoding_cadastrado)
    print(f"Recuperacao de senha (usuario {matricula}) — distancia: {distancia:.4f} | limiar: {TOLERANCIA_RECUPERACAO}")

    if distancia > TOLERANCIA_RECUPERACAO:
        raise HTTPException(status_code=401, detail="Rosto não corresponde ao cadastro.")

    if not usuario_repo.redefinir_senha(matricula, nova_senha):
        raise HTTPException(status_code=500, detail="Erro ao redefinir senha.")

    return {"mensagem": f"Senha redefinida com sucesso para {usuario.nome}!", "nome": usuario.nome}


# ============================================================
# RECUPERAÇÃO DE SENHA — PROFESSOR
# ============================================================

@app.post("/admin/recuperar_senha")
async def recuperar_senha_professor(
    siape:      str        = Form(...),
    nova_senha: str        = Form(...),
    foto:       UploadFile = File(...)
):
    professor = professor_repo.buscar_por_siape(siape)
    if not professor:
        raise HTTPException(status_code=404, detail="SIAPE não encontrado.")
    if not professor.encoding:
        raise HTTPException(status_code=400, detail="Professor sem foto cadastrada.")

    conteudo = await foto.read()
    encoding_novo, erro = reconhecimento_service.extrair_encoding(conteudo)
    if erro == "sem_rosto":
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado na foto.")
    if erro == "multiplos_rostos":
        raise HTTPException(status_code=400, detail="Mais de um rosto detectado.")

    encoding_cadastrado = reconhecimento_service.texto_para_encoding(professor.encoding)
    distancia = reconhecimento_service._calcular_distancia(encoding_novo, encoding_cadastrado)
    print(f"Recuperacao de senha (professor {siape}) — distancia: {distancia:.4f} | limiar: {TOLERANCIA_RECUPERACAO}")

    if distancia > TOLERANCIA_RECUPERACAO:
        raise HTTPException(status_code=401, detail="Rosto não corresponde ao cadastro.")

    if not professor_repo.redefinir_senha(siape, nova_senha):
        raise HTTPException(status_code=500, detail="Erro ao redefinir senha.")

    return {"mensagem": f"Senha redefinida com sucesso para {professor.nome}!", "nome": professor.nome}


# ============================================================
# ADMIN
# ============================================================

@app.post("/admin/liberar_acesso")
def liberar_acesso(matricula: str = Form(...), siape: str = Form(...)):
    # A liberacao agora vive na tabela professores_alunos, entao precisamos
    # do SIAPE do professor logado que esta concedendo o acesso.
    row = usuario_repo.liberar_acesso(matricula, siape)
    if not row:
        raise HTTPException(status_code=404, detail="Aluno ou professor não encontrado.")
    reconhecimento_service.invalidar_cache()
    return {"mensagem": f"Acesso liberado para {row[1]}!"}


@app.post("/admin/revogar_acesso")
def revogar_acesso(matricula: str = Form(...)):
    row = usuario_repo.revogar_acesso(matricula)
    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    reconhecimento_service.invalidar_cache()
    return {"mensagem": f"Acesso revogado para {row[1]}."}


@app.post("/admin/cadastrar")
async def cadastrar_admin(
    nome:  str        = Form(...),
    siape: str        = Form(...),
    senha: str        = Form(...),
    foto:  UploadFile = File(...)
):
    if professor_repo.buscar_por_siape(siape):
        raise HTTPException(status_code=409, detail="SIAPE já cadastrado.")

    conteudo = await foto.read()
    encoding, erro = reconhecimento_service.extrair_encoding(conteudo)
    if erro == "sem_rosto":
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado na foto.")
    if erro == "multiplos_rostos":
        raise HTTPException(status_code=400, detail="Mais de um rosto detectado. Envie foto individual.")

    encoding_str = reconhecimento_service.encoding_para_texto(encoding)
    admin        = professor_repo.criar(nome, siape, senha, encoding_str)

    reconhecimento_service.invalidar_cache()

    return {"id": admin.id, "nome": admin.nome, "mensagem": "Professor cadastrado com sucesso!"}


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


@app.get("/acessos/data/{data}")
def acessos_por_data(data: str):
    return acesso_repo.listar_por_data(data)


@app.get("/usuarios/{usuario_id}/acessos")
def historico_usuario(usuario_id: int):
    return acesso_repo.listar_por_usuario(usuario_id)


@app.post("/log_totem")
async def log_totem(dados: dict):
    mensagem = dados.get("mensagem", "")
    print(f"[TOTEM] {mensagem}")
    return {"ok": True}


@app.get("/debug/redis")
async def debug_redis():
    from services.cache_service import CacheService
    cache = CacheService()
    return {
        "disponivel": cache.disponivel,
        "redis_url_presente": bool(os.environ.get("REDIS_URL"))
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)