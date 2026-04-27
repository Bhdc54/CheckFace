import sys
import os
import bcrypt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.aluno import Aluno


class AlunoRepository:

    def _hash_senha(self, senha: str) -> str:
        return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verificar_senha(self, senha: str, hash_salvo: str) -> bool:
        return bcrypt.checkpw(senha.encode('utf-8'), hash_salvo.encode('utf-8'))

    def listar(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome, matricula, encoding, acesso_liberado
            FROM alunos
            ORDER BY nome
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Aluno(r[0], r[1], r[2], encoding=r[3], acesso_liberado=r[4]) for r in rows]

    def listar_com_encoding(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, matricula, encoding, acesso_liberado FROM alunos WHERE encoding IS NOT NULL")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Aluno(r[0], r[1], r[2], encoding=r[3], acesso_liberado=r[4]) for r in rows]

    def buscar_por_matricula(self, matricula: str):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM alunos WHERE matricula = %s", (matricula,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def buscar_por_matricula_e_senha(self, matricula: str, senha: str):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, matricula, senha, acesso_liberado FROM alunos WHERE matricula = %s",
            (matricula,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        if not row[3] or not self._verificar_senha(senha, row[3]):
            return None
        return Aluno(row[0], row[1], row[2], acesso_liberado=row[4])

    def criar(self, nome: str, matricula: str, encoding_str: str, senha: str = None) -> 'Aluno':
        conn = conectar()
        cursor = conn.cursor()
        senha_hash = self._hash_senha(senha) if senha else None
        cursor.execute(
            """INSERT INTO alunos (nome, matricula, encoding, senha, acesso_liberado)
               VALUES (%s, %s, %s, %s, FALSE) RETURNING id""",
            (nome, matricula, encoding_str, senha_hash)
        )
        aluno_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return Aluno(aluno_id, nome, matricula, acesso_liberado=False)

    def liberar_acesso(self, matricula: str):
        """Admin libera acesso pelo RGA do aluno."""
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE alunos SET acesso_liberado = TRUE WHERE matricula = %s RETURNING id, nome",
            (matricula,)
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return row

    def revogar_acesso(self, matricula: str):
        """Admin revoga acesso pelo RGA do aluno."""
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE alunos SET acesso_liberado = FALSE WHERE matricula = %s RETURNING id, nome",
            (matricula,)
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return row

    def deletar(self, aluno_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alunos WHERE id = %s", (aluno_id,))
        conn.commit()
        cursor.close()
        conn.close()