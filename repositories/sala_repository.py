import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.sala import Sala


class SalaRepository:

    def listar(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, descricao, criado_em FROM salas ORDER BY nome")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Sala(r[0], r[1], r[2], r[3]) for r in rows]

    def buscar_por_id(self, sala_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, descricao FROM salas WHERE id = %s", (sala_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        return Sala(row[0], row[1], row[2])

    def criar(self, nome: str, descricao: str = None) -> Sala:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO salas (nome, descricao) VALUES (%s, %s) RETURNING id",
            (nome, descricao)
        )
        sala_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return Sala(sala_id, nome, descricao)

    def deletar(self, sala_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM salas WHERE id = %s", (sala_id,))
        conn.commit()
        cursor.close()
        conn.close()