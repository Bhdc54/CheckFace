import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.aula import Aula


class AulaRepository:

    def buscar_ativa(self, turma_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, turma_id, iniciada_em FROM aulas WHERE turma_id = %s AND finalizada_em IS NULL",
            (turma_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        return Aula(row[0], row[1], row[2])

    def criar(self, turma_id: int) -> Aula:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO aulas (turma_id) VALUES (%s) RETURNING id, iniciada_em",
            (turma_id,)
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return Aula(row[0], turma_id, row[1])

    def buscar_por_id(self, aula_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT au.id, au.turma_id, au.iniciada_em, t.nome, t.professor
            FROM aulas au
            JOIN turmas t ON t.id = au.turma_id
            WHERE au.id = %s
        """, (aula_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def finalizar(self, aula_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE aulas SET finalizada_em = NOW() WHERE id = %s",
            (aula_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()

    def buscar_alunos_da_turma(self, aula_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT matricula, nome
            FROM alunos
            WHERE turma_id = (SELECT turma_id FROM aulas WHERE id = %s)
            ORDER BY nome
        """, (aula_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def contar_alunos_turma(self, aula_id: int) -> int:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM alunos
            WHERE turma_id = (SELECT turma_id FROM aulas WHERE id = %s)
        """, (aula_id,))
        total = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return total