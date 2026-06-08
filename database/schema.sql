-- ============================================================
-- CheckFace: Sistema Integrado de Gestão e Controle de Acesso
-- via Reconhecimento Facial em Tempo Real
-- Schema do banco de dados — versão 3.2.0
-- ============================================================

-- ============================================================
-- PROFESSORES
-- Administradores do sistema que gerenciam os acessos
-- ============================================================
CREATE TABLE IF NOT EXISTS professores (
    id             SERIAL PRIMARY KEY,
    nome           VARCHAR(120) NOT NULL,
    siape          VARCHAR(30) UNIQUE NOT NULL,
    senha          VARCHAR(255) NOT NULL,          -- hash bcrypt
    encoding       TEXT,                           -- embedding facial (512 floats)
    termo_aceito   BOOLEAN DEFAULT FALSE,          -- aceite do termo de uso de imagem
    termo_aceito_em TIMESTAMP,                     -- data/hora do aceite
    criado_em      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ALUNOS (USUÁRIOS)
-- Usuários que se cadastram pelo app e aguardam liberação
-- ============================================================
CREATE TABLE IF NOT EXISTS alunos (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(120) NOT NULL,
    matricula       VARCHAR(30) UNIQUE NOT NULL,   -- RGA
    senha           VARCHAR(255),                  -- hash bcrypt
    encoding        TEXT,                          -- embedding facial (512 floats)
    acesso_liberado BOOLEAN DEFAULT FALSE,         -- liberado pelo professor
    termo_aceito    BOOLEAN DEFAULT FALSE,         -- aceite do termo de uso de imagem
    termo_aceito_em TIMESTAMP,                     -- data/hora do aceite
    criado_em       TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SALAS
-- Ambientes físicos controlados pelo sistema
-- ============================================================
CREATE TABLE IF NOT EXISTS salas (
    id         SERIAL PRIMARY KEY,
    nome       VARCHAR(120) NOT NULL,
    descricao  VARCHAR(255),
    criado_em  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ACESSOS
-- Registro de todas as tentativas de acesso pelo totem.
-- Suporta alunos e professores sem FK rígida, pois ambos
-- os perfis podem ser reconhecidos pelo totem.
-- ============================================================
CREATE TABLE IF NOT EXISTS acessos (
    id           SERIAL PRIMARY KEY,
    usuario_id   INT,                              -- id do aluno ou professor
    tipo_usuario VARCHAR(10) DEFAULT 'aluno'
                 CHECK (tipo_usuario IN ('aluno', 'professor', 'desconhecido')),
    sala_id      INT REFERENCES salas(id) ON DELETE SET NULL,
    data         DATE NOT NULL,
    hora         TIME NOT NULL,
    status       VARCHAR(10) NOT NULL
                 CHECK (status IN ('liberado', 'negado')),
    confianca    FLOAT,                            -- 0.0 a 1.0
    criado_em    TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES para melhorar performance das consultas
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_acessos_data      ON acessos (data);
CREATE INDEX IF NOT EXISTS idx_acessos_usuario   ON acessos (usuario_id);
CREATE INDEX IF NOT EXISTS idx_acessos_tipo      ON acessos (tipo_usuario);
CREATE INDEX IF NOT EXISTS idx_acessos_sala      ON acessos (sala_id);
CREATE INDEX IF NOT EXISTS idx_alunos_matricula  ON alunos (matricula);
CREATE INDEX IF NOT EXISTS idx_professores_siape ON professores (siape);

-- ============================================================
-- MIGRAÇÕES (caso o banco já exista, aplique estes ALTER)
-- ============================================================

-- Professores
ALTER TABLE professores ADD COLUMN IF NOT EXISTS encoding TEXT;
ALTER TABLE professores ADD COLUMN IF NOT EXISTS termo_aceito BOOLEAN DEFAULT FALSE;
ALTER TABLE professores ADD COLUMN IF NOT EXISTS termo_aceito_em TIMESTAMP;

-- Alunos
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS acesso_liberado BOOLEAN DEFAULT FALSE;
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS senha VARCHAR(255);
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS termo_aceito BOOLEAN DEFAULT FALSE;
ALTER TABLE alunos ADD COLUMN IF NOT EXISTS termo_aceito_em TIMESTAMP;
ALTER TABLE alunos DROP COLUMN IF EXISTS foto_url;

-- Acessos
ALTER TABLE acessos ADD COLUMN IF NOT EXISTS tipo_usuario VARCHAR(10) DEFAULT 'aluno';
ALTER TABLE acessos ADD COLUMN IF NOT EXISTS sala_id INT REFERENCES salas(id) ON DELETE SET NULL;
ALTER TABLE acessos DROP CONSTRAINT IF EXISTS acessos_usuario_id_fkey;