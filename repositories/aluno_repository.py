import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.aluno import Aluno


class AlunoRepository:

    def listar(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.nome, a.matricula, a.turma_id, a.encoding
            FROM alunos a
            ORDER BY a.nome
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Aluno(r[0], r[1], r[2], r[3], r[4]) for r in rows]

    def listar_por_turma(self, turma_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, matricula, turma_id, encoding FROM alunos WHERE turma_id = %s ORDER BY nome",
            (turma_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Aluno(r[0], r[1], r[2], r[3], r[4]) for r in rows]

    def listar_com_encoding(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, matricula, encoding FROM alunos WHERE encoding IS NOT NULL")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Aluno(r[0], r[1], r[2], encoding=r[3]) for r in rows]

    def buscar_por_matricula(self, matricula: str):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM alunos WHERE matricula = %s", (matricula,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def criar(self, nome: str, matricula: str, turma_id: int, encoding_str: str) -> Aluno:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO alunos (nome, matricula, turma_id, encoding) VALUES (%s, %s, %s, %s) RETURNING id",
            (nome, matricula, turma_id, encoding_str)
        )
        aluno_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return Aluno(aluno_id, nome, matricula, turma_id)

    def deletar(self, aluno_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alunos WHERE id = %s", (aluno_id,))
        conn.commit()
        cursor.close()
        conn.close()