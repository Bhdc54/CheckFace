import sys
import os
import bcrypt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.conectar import conectar
from models.aluno import Aluno

# Um aluno esta "liberado" se existe vinculo dele na tabela de juncao.
_LIB = ("EXISTS (SELECT 1 FROM professores_alunos pa "
        "WHERE pa.id_aluno = a.id_aluno) AS acesso_liberado")


class AlunoRepository:

    def _hash_senha(self, senha: str) -> str:
        return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verificar_senha(self, senha: str, hash_salvo: str) -> bool:
        return bcrypt.checkpw(senha.encode('utf-8'), hash_salvo.encode('utf-8'))

    def listar(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT a.id_aluno, a.nome, a.matricula, a.encoding, {_LIB}
            FROM alunos a ORDER BY a.nome
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Aluno(r[0], r[1], r[2], encoding=r[3], acesso_liberado=r[4]) for r in rows]

    def listar_com_encoding(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT a.id_aluno, a.nome, a.matricula, a.encoding, {_LIB}
            FROM alunos a WHERE a.encoding IS NOT NULL
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Aluno(r[0], r[1], r[2], encoding=r[3], acesso_liberado=r[4]) for r in rows]

    def buscar_por_matricula(self, matricula: str):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id_aluno FROM alunos WHERE matricula = %s", (matricula,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def buscar_por_matricula_completo(self, matricula: str):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            f"""SELECT a.id_aluno, a.nome, a.matricula, a.encoding, {_LIB}
                FROM alunos a WHERE a.matricula = %s""",
            (matricula,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        return Aluno(row[0], row[1], row[2], encoding=row[3], acesso_liberado=row[4])

    def buscar_por_matricula_e_senha(self, matricula: str, senha: str):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            f"""SELECT a.id_aluno, a.nome, a.matricula, a.senha, {_LIB}
                FROM alunos a WHERE a.matricula = %s""",
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
            """INSERT INTO alunos (nome, matricula, encoding, senha, termo_aceito)
               VALUES (%s, %s, %s, %s, TRUE) RETURNING id_aluno""",
            (nome, matricula, encoding_str, senha_hash)
        )
        aluno_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return Aluno(aluno_id, nome, matricula, acesso_liberado=False)

    def redefinir_senha(self, matricula: str, nova_senha: str) -> bool:
        conn = conectar()
        cursor = conn.cursor()
        senha_hash = self._hash_senha(nova_senha)
        cursor.execute(
            "UPDATE alunos SET senha = %s WHERE matricula = %s RETURNING id_aluno",
            (senha_hash, matricula)
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return row is not None

    def liberar_acesso(self, matricula: str, siape: str):
        """Libera o aluno criando o vinculo na professores_alunos.
        Precisa do SIAPE do professor que esta liberando."""
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id_aluno, nome FROM alunos WHERE matricula = %s", (matricula,))
        aluno = cursor.fetchone()
        cursor.execute("SELECT id_professor FROM professores WHERE siape = %s", (siape,))
        prof = cursor.fetchone()
        if not aluno or not prof:
            cursor.close()
            conn.close()
            return None
        cursor.execute(
            """INSERT INTO professores_alunos (id_professor, id_aluno, acesso_liberado)
               VALUES (%s, %s, NOW())
               ON CONFLICT (id_professor, id_aluno) DO UPDATE SET acesso_liberado = NOW()""",
            (prof[0], aluno[0])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return aluno  # (id_aluno, nome)

    def revogar_acesso(self, matricula: str):
        """Revoga removendo os vinculos do aluno na professores_alunos."""
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id_aluno, nome FROM alunos WHERE matricula = %s", (matricula,))
        aluno = cursor.fetchone()
        if not aluno:
            cursor.close()
            conn.close()
            return None
        cursor.execute("DELETE FROM professores_alunos WHERE id_aluno = %s", (aluno[0],))
        conn.commit()
        cursor.close()
        conn.close()
        return aluno  # (id_aluno, nome)

    def deletar(self, aluno_id: int):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alunos WHERE id_aluno = %s", (aluno_id,))
        conn.commit()
        cursor.close()
        conn.close()