import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.professor import Professor


class ProfessorRepository:

    def criar(self, nome: str, siape: str, senha: str) -> Professor:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO professores (nome, siape, senha) VALUES (%s, %s, %s) RETURNING id, criado_em",
            (nome, siape, senha)
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return Professor(row[0], nome, siape, criado_em=row[1])

    def buscar_por_siape(self, siape: str):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, siape, senha FROM professores WHERE siape = %s",
            (siape,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        return Professor(row[0], row[1], row[2], row[3])

    def listar(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, siape, criado_em FROM professores ORDER BY nome")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Professor(r[0], r[1], r[2], criado_em=r[3]) for r in rows]

    def vincular_turma(self, professor_id: int, turma_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO professor_turmas (professor_id, turma_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (professor_id, turma_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

    def desvincular_turma(self, professor_id: int, turma_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM professor_turmas WHERE professor_id = %s AND turma_id = %s",
            (professor_id, turma_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

    def listar_turmas_do_professor(self, professor_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.nome, t.professor
            FROM turmas t
            JOIN professor_turmas pt ON pt.turma_id = t.id
            WHERE pt.professor_id = %s
            ORDER BY t.nome
        """, (professor_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [{"id": r[0], "nome": r[1], "professor": r[2]} for r in rows]