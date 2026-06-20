import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.acesso import Acesso


def _formatar_hora(hora) -> str:
    return str(hora)[:8] if hora else ""


def _formatar_data(data) -> str:
    if not data:
        return ""
    d = str(data)
    partes = d.split("-")
    if len(partes) == 3:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return d


# tipo_usuario derivado de qual FK esta preenchida
_TIPO = ("CASE WHEN a.id_aluno IS NOT NULL THEN 'aluno' "
         "WHEN a.id_professor IS NOT NULL THEN 'professor' "
         "ELSE 'desconhecido' END")


class AcessoRepository:

    def registrar(self, usuario_id, data, hora, status: str,
                  confianca: float = None, tipo_usuario: str = "aluno") -> Acesso:
        # Decide qual coluna preencher conforme o tipo reconhecido.
        id_professor = usuario_id if tipo_usuario == "professor" else None
        id_aluno     = usuario_id if tipo_usuario == "aluno"     else None

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO acessos (id_professor, id_aluno, data, hora, status, confianca)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (id_professor, id_aluno, data, hora, status, confianca)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return Acesso(id_professor, id_aluno, data, hora, status, confianca)

    def listar_por_usuario(self, usuario_id: int):
        # Historico do aluno (a tela do aluno usa o proprio id_aluno).
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.data, a.hora, a.status, a.confianca
            FROM acessos a
            WHERE a.id_aluno = %s
            ORDER BY a.data DESC, a.hora DESC
        """, (usuario_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "data": _formatar_data(r[0]),
                "hora": _formatar_hora(r[1]),
                "status": r[2],
                "confianca": r[3]
            }
            for r in rows
        ]

    def listar_todos(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                COALESCE(al.nome, pr.nome, 'Desconhecido') AS nome,
                COALESCE(al.matricula, pr.siape, '-')       AS matricula,
                a.data, a.hora, a.status, a.confianca,
                {_TIPO} AS tipo_usuario
            FROM acessos a
            LEFT JOIN alunos      al ON al.id_aluno     = a.id_aluno
            LEFT JOIN professores pr ON pr.id_professor = a.id_professor
            ORDER BY a.data DESC, a.hora DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "nome": r[0],
                "matricula": r[1],
                "data": _formatar_data(r[2]),
                "hora": _formatar_hora(r[3]),
                "status": r[4],
                "confianca": r[5],
                "tipo_usuario": r[6]
            }
            for r in rows
        ]

    def listar_hoje(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                COALESCE(al.nome, pr.nome, 'Desconhecido') AS nome,
                COALESCE(al.matricula, pr.siape, '-')       AS matricula,
                a.hora, a.status, a.confianca,
                {_TIPO} AS tipo_usuario
            FROM acessos a
            LEFT JOIN alunos      al ON al.id_aluno     = a.id_aluno
            LEFT JOIN professores pr ON pr.id_professor = a.id_professor
            WHERE a.data = CURRENT_DATE
            ORDER BY a.hora DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "nome": r[0],
                "matricula": r[1],
                "hora": _formatar_hora(r[2]),
                "status": r[3],
                "confianca": r[4],
                "tipo_usuario": r[5]
            }
            for r in rows
        ]

    def listar_por_data(self, data: str):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                COALESCE(al.nome, pr.nome, 'Desconhecido') AS nome,
                COALESCE(al.matricula, pr.siape, '-')       AS matricula,
                a.hora, a.status, a.confianca,
                {_TIPO} AS tipo_usuario
            FROM acessos a
            LEFT JOIN alunos      al ON al.id_aluno     = a.id_aluno
            LEFT JOIN professores pr ON pr.id_professor = a.id_professor
            WHERE a.data = %s
            ORDER BY a.hora DESC
        """, (data,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "nome": r[0],
                "matricula": r[1],
                "hora": _formatar_hora(r[2]),
                "status": r[3],
                "confianca": r[4],
                "tipo_usuario": r[5]
            }
            for r in rows
        ]