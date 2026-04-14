-- ============================================================
-- CheckFace - Schema do banco de dados
-- ============================================================

CREATE TABLE IF NOT EXISTS turmas (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    professor   VARCHAR(120) NOT NULL,
    criado_em   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alunos (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(120) NOT NULL,
    matricula   VARCHAR(30) UNIQUE NOT NULL,
    turma_id    INT REFERENCES turmas(id) ON DELETE SET NULL,
    encoding    TEXT,          -- vetor facial serializado (128 floats separados por vírgula)
    foto_url    TEXT,
    criado_em   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS aulas (
    id              SERIAL PRIMARY KEY,
    turma_id        INT REFERENCES turmas(id) ON DELETE CASCADE,
    iniciada_em     TIMESTAMP DEFAULT NOW(),
    finalizada_em   TIMESTAMP,
    relatorio_path  TEXT
);

CREATE TABLE IF NOT EXISTS presencas (
    id              SERIAL PRIMARY KEY,
    aluno_id        INT REFERENCES alunos(id) ON DELETE CASCADE,
    aula_id         INT REFERENCES aulas(id) ON DELETE CASCADE,
    data            DATE NOT NULL,
    hora            TIME NOT NULL,
    confianca       FLOAT,     -- 0.0 a 1.0 (quanto maior, mais certeza)
    UNIQUE(aluno_id, aula_id) -- evita duplicata na mesma aula
);