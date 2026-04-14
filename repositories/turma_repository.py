import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.turma import Turma


class TurmaRepository:

    def listar(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, professor, criado_em FROM turmas ORDER BY id DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Turma(r[0], r[1], r[2], r[3]) for r in rows]

    def criar(self, nome: str, professor: str) -> Turma:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO turmas (nome, professor) VALUES (%s, %s) RETURNING id",
            (nome, professor)
        )
        turma_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return Turma(turma_id, nome, professor)