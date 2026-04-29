import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.acesso import Acesso


def _formatar_hora(hora) -> str:
    """Formata hora removendo microssegundos: HH:MM:SS"""
    return str(hora)[:8] if hora else ""


def _formatar_data(data) -> str:
    """Formata data no padrão DD/MM/YYYY."""
    if not data:
        return ""
    d = str(data)
    partes = d.split("-")
    if len(partes) == 3:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return d


class AcessoRepository:

    def registrar(self, usuario_id: int, data, hora, status: str, confianca: float = None) -> Acesso:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO acessos (usuario_id, data, hora, status, confianca) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (usuario_id, data, hora, status, confianca)
        )
        acesso_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return Acesso(acesso_id, usuario_id, data, hora, status, confianca)

    def listar_por_usuario(self, usuario_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.data, a.hora, a.status, a.confianca
            FROM acessos a
            WHERE a.usuario_id = %s
            ORDER BY a.data DESC, a.hora DESC
        """, (usuario_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "id": r[0],
                "data": _formatar_data(r[1]),
                "hora": _formatar_hora(r[2]),
                "status": r[3],
                "confianca": r[4]
            }
            for r in rows
        ]

    def listar_todos(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.nome, u.matricula, a.data, a.hora, a.status, a.confianca
            FROM acessos a
            JOIN alunos u ON u.id = a.usuario_id
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
                "confianca": r[5]
            }
            for r in rows
        ]

    def listar_hoje(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.nome, u.matricula, a.hora, a.status, a.confianca
            FROM acessos a
            JOIN alunos u ON u.id = a.usuario_id
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
                "confianca": r[4]
            }
            for r in rows
        ]

    def listar_por_data(self, data: str):
        """Retorna acessos de uma data específica (formato YYYY-MM-DD)."""
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.nome, u.matricula, a.hora, a.status, a.confianca
            FROM acessos a
            LEFT JOIN alunos u ON u.id = a.usuario_id
            WHERE a.data = %s
            ORDER BY a.hora DESC
        """, (data,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "nome": r[0] or "Desconhecido",
                "matricula": r[1] or "-",
                "hora": _formatar_hora(r[2]),
                "status": r[3],
                "confianca": r[4]
            }
            for r in rows
        ]