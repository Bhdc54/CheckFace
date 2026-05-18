-- ============================================================
-- CheckFace: Sistema Integrado de Gestão e Controle de Acesso
-- via Reconhecimento Facial em Tempo Real
-- Schema do banco de dados — versão 3.0.0
-- ============================================================

-- ============================================================
-- PROFESSORES
-- Administradores do sistema que gerenciam os acessos
-- ============================================================
CREATE TABLE IF NOT EXISTS professores (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(120) NOT NULL,
    siape       VARCHAR(30) UNIQUE NOT NULL,
    senha       VARCHAR(255) NOT NULL,          -- hash bcrypt
    encoding    TEXT,                           -- embedding facial (512 floats)
    criado_em   TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ALUNOS (USUÁRIOS)
-- Usuários que se cadastram pelo app e aguardam liberação
-- ============================================================
CREATE TABLE IF NOT EXISTS alunos (
    id               SERIAL PRIMARY KEY,
    nome             VARCHAR(120) NOT NULL,
    matricula        VARCHAR(30) UNIQUE NOT NULL, -- RGA
    senha            VARCHAR(255),                -- hash bcrypt
    encoding         TEXT,                        -- embedding facial (512 floats)
    foto_url         TEXT,
    acesso_liberado  BOOLEAN DEFAULT FALSE,       -- liberado pelo professor
    criado_em        TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ACESSOS
-- Registro de todas as tentativas de acesso pelo totem
-- ============================================================
CREATE TABLE IF NOT EXISTS acessos (
    id          SERIAL PRIMARY KEY,
    usuario_id  INT REFERENCES alunos(id) ON DELETE SET NULL,
    data        DATE NOT NULL,
    hora        TIME NOT NULL,
    status      VARCHAR(10) NOT NULL CHECK (status IN ('liberado', 'negado')),
    confianca   FLOAT,                           -- 0.0 a 1.0
    criado_em   TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES para melhorar performance das consultas
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_acessos_data ON acessos (data);
CREATE INDEX IF NOT EXISTS idx_acessos_usuario ON acessos (usuario_id);
CREATE INDEX IF NOT EXISTS idx_alunos_matricula ON alunos (matricula);
CREATE INDEX IF NOT EXISTS idx_professores_siape ON professores (siape);

-- ============================================================
-- MIGRAÇÕES (caso o banco já exista, aplique estes ALTER)
-- ============================================================

-- Adicionar encoding nos professores (caso não exista)
ALTER TABLE professores ADD COLUMN IF NOT EXISTS encoding TEXT;

-- Adicionar acesso_liberado nos alunos (caso não exista)
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS acesso_liberado BOOLEAN DEFAULT FALSE;

-- Adicionar senha nos alunos (caso não exista)
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS senha VARCHAR(255);