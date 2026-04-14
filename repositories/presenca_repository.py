import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.presenca import Presenca


class PresencaRepository:

    def registrar(self, aluno_id: int, aula_id: int, data, hora, confianca: float) -> Presenca:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO presencas (aluno_id, aula_id, data, hora, confianca) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (aluno_id, aula_id, data, hora, confianca)
        )
        presenca_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return Presenca(presenca_id, aluno_id, aula_id, data, hora, confianca)

    def ja_registrada(self, aluno_id: int, aula_id: int) -> bool:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM presencas WHERE aluno_id = %s AND aula_id = %s",
            (aluno_id, aula_id)
        )
        existe = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return existe

    def listar_por_aula(self, aula_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.nome, a.matricula, p.hora, p.confianca
            FROM presencas p
            JOIN alunos a ON a.id = p.aluno_id
            WHERE p.aula_id = %s
            ORDER BY p.hora
        """, (aula_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def listar_detalhado_por_aula(self, aula_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.matricula, a.nome, p.hora, p.confianca
            FROM presencas p
            JOIN alunos a ON a.id = p.aluno_id
            WHERE p.aula_id = %s
            ORDER BY a.nome
        """, (aula_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def listar_todas(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.nome, a.matricula, p.data, p.hora, p.confianca, t.nome as turma
            FROM presencas p
            JOIN alunos a ON a.id = p.aluno_id
            JOIN aulas au ON au.id = p.aula_id
            JOIN turmas t ON t.id = au.turma_id
            ORDER BY p.data DESC, p.hora DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows