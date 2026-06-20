-- ============================================================
--  CheckFace — Esquema do banco de dados (PostgreSQL)
-- ============================================================

-- Registro de professores
CREATE TABLE professores (
    id_professor SERIAL       PRIMARY KEY,
    nome         VARCHAR(120) NOT NULL,
    siape        VARCHAR(30)  UNIQUE NOT NULL,
    senha        VARCHAR(255) NOT NULL,   -- hash
    encoding     TEXT,                    -- vetor facial (512)
    termo_aceito BOOLEAN      DEFAULT FALSE
);

-- Registro de alunos
CREATE TABLE alunos (
    id_aluno     SERIAL       PRIMARY KEY,
    nome         VARCHAR(120) NOT NULL,
    matricula    VARCHAR(30)  UNIQUE NOT NULL,  -- RGA
    senha        VARCHAR(255),                  -- hash
    encoding     TEXT,                          -- vetor facial (512)
    termo_aceito BOOLEAN      DEFAULT FALSE
);

-- Liberacao: professor libera aluno (entidade associativa, sem id proprio)
CREATE TABLE professores_alunos (
    id_professor    INT NOT NULL REFERENCES professores(id_professor) ON DELETE CASCADE,
    id_aluno        INT NOT NULL REFERENCES alunos(id_aluno)          ON DELETE CASCADE,
    acesso_liberado TIMESTAMP,              -- quando foi liberado (NULL = nao liberado)
    PRIMARY KEY (id_professor, id_aluno)
);

-- Registro de acessos pelo totem (entidade associativa, sem id proprio)
CREATE TABLE acessos (
    id_professor INT REFERENCES professores(id_professor),
    id_aluno     INT REFERENCES alunos(id_aluno),
    status       VARCHAR(10) NOT NULL CHECK (status IN ('liberado', 'negado')),
    data         DATE        NOT NULL,
    hora         TIME        NOT NULL,
    confianca    FLOAT,
    -- cada acesso e de um aluno OU de um professor (nunca os dois ao mesmo tempo)
    CHECK (NOT (id_professor IS NOT NULL AND id_aluno IS NOT NULL))
);