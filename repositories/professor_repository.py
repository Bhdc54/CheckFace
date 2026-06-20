import sys
import os
import bcrypt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.professor import Professor


class ProfessorRepository:

    def _hash_senha(self, senha: str) -> str:
        return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verificar_senha(self, senha: str, hash_salvo: str) -> bool:
        return bcrypt.checkpw(senha.encode('utf-8'), hash_salvo.encode('utf-8'))

    def criar(self, nome: str, siape: str, senha: str, encoding_str: str = None) -> Professor:
        conn = conectar()
        cursor = conn.cursor()
        senha_hash = self._hash_senha(senha)
        cursor.execute(
            """INSERT INTO professores (nome, siape, senha, encoding, termo_aceito)
               VALUES (%s, %s, %s, %s, TRUE) RETURNING id_professor""",
            (nome, siape, senha_hash, encoding_str)
        )
        prof_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return Professor(prof_id, nome, siape)

    def buscar_por_siape(self, siape: str):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_professor, nome, siape, senha, encoding FROM professores WHERE siape = %s",
            (siape,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        p = Professor(row[0], row[1], row[2], row[3])
        p.encoding = row[4]
        return p

    def verificar_login(self, siape: str, senha: str):
        professor = self.buscar_por_siape(siape)
        if not professor:
            return None
        if not self._verificar_senha(senha, professor.senha):
            return None
        return professor

    def redefinir_senha(self, siape: str, nova_senha: str) -> bool:
        conn = conectar()
        cursor = conn.cursor()
        senha_hash = self._hash_senha(nova_senha)
        cursor.execute(
            "UPDATE professores SET senha = %s WHERE siape = %s RETURNING id_professor",
            (senha_hash, siape)
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return row is not None

    def listar(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id_professor, nome, siape FROM professores ORDER BY nome")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Professor(r[0], r[1], r[2]) for r in rows]

    def listar_com_encoding(self):
        """Retorna professores como dicts compativeis com o formato dos alunos."""
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id_professor, nome, siape, encoding
               FROM professores
               WHERE encoding IS NOT NULL
               ORDER BY nome"""
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "id":              r[0],
                "nome":            r[1],
                "matricula":       r[2],  
                "siape":           r[2],  
                "encoding":        r[3],
                "acesso_liberado": True,  
            }
            for r in rows
        ]