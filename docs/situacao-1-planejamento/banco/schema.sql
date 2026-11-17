-- Aceito! – esquema físico (PostgreSQL)
-- Na aplicação, o mesmo esquema é gerado pelos models SQLAlchemy e versionado com Flask-Migrate
-- (migrations/versions/). Este arquivo é a referência do documento de planejamento (seção 13).

CREATE TABLE usuario (
    id          SERIAL        PRIMARY KEY,
    nome        VARCHAR(100)  NOT NULL,
    email       VARCHAR(120)  NOT NULL UNIQUE,
    senha_hash  VARCHAR(255)  NOT NULL,
    criado_em   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE casamento (
    id                    SERIAL         PRIMARY KEY,
    usuario_id            INTEGER        NOT NULL UNIQUE REFERENCES usuario (id),
    nome_casal            VARCHAR(120)   NOT NULL,
    data_casamento        DATE           NOT NULL,
    local                 VARCHAR(150),
    orcamento_total       NUMERIC(12,2)  NOT NULL CHECK (orcamento_total > 0),
    convidados_estimados  INTEGER        CHECK (convidados_estimados >= 0)
);

CREATE TABLE categoria (
    id               SERIAL         PRIMARY KEY,
    casamento_id     INTEGER        NOT NULL REFERENCES casamento (id),
    nome             VARCHAR(60)    NOT NULL,
    valor_planejado  NUMERIC(12,2)  NOT NULL DEFAULT 0 CHECK (valor_planejado >= 0),
    CONSTRAINT uq_categoria_nome UNIQUE (casamento_id, nome)
);

CREATE TABLE fornecedor (
    id            SERIAL         PRIMARY KEY,
    categoria_id  INTEGER        NOT NULL REFERENCES categoria (id) ON DELETE RESTRICT,
    nome          VARCHAR(120)   NOT NULL,
    telefone      VARCHAR(20),
    email         VARCHAR(120),
    valor_orcado  NUMERIC(12,2)  CHECK (valor_orcado >= 0),
    status        VARCHAR(12)    NOT NULL DEFAULT 'ORCAMENTO'
                  CHECK (status IN ('ORCAMENTO', 'CONTRATADO', 'DESCARTADO')),
    observacoes   TEXT
);

CREATE TABLE despesa (
    id                SERIAL         PRIMARY KEY,
    categoria_id      INTEGER        NOT NULL REFERENCES categoria (id) ON DELETE RESTRICT,
    fornecedor_id     INTEGER        REFERENCES fornecedor (id) ON DELETE SET NULL,
    descricao         VARCHAR(150)   NOT NULL,
    valor_total       NUMERIC(12,2)  NOT NULL CHECK (valor_total > 0),
    data_contratacao  DATE           NOT NULL
);

CREATE TABLE parcela (
    id               SERIAL         PRIMARY KEY,
    despesa_id       INTEGER        NOT NULL REFERENCES despesa (id) ON DELETE CASCADE,
    numero           SMALLINT       NOT NULL CHECK (numero BETWEEN 1 AND 24),
    valor            NUMERIC(12,2)  NOT NULL CHECK (valor > 0),
    data_vencimento  DATE           NOT NULL,
    data_pagamento   DATE,
    CONSTRAINT uq_parcela_numero UNIQUE (despesa_id, numero)
);

CREATE TABLE convidado (
    id             SERIAL        PRIMARY KEY,
    casamento_id   INTEGER       NOT NULL REFERENCES casamento (id) ON DELETE CASCADE,
    nome           VARCHAR(120)  NOT NULL,
    telefone       VARCHAR(20),
    email          VARCHAR(120),
    grupo          VARCHAR(15)   NOT NULL DEFAULT 'OUTROS'
                   CHECK (grupo IN ('FAMILIA_NOIVA', 'FAMILIA_NOIVO', 'AMIGOS', 'TRABALHO', 'OUTROS')),
    acompanhantes  SMALLINT      NOT NULL DEFAULT 0 CHECK (acompanhantes BETWEEN 0 AND 10),
    status_rsvp    VARCHAR(10)   NOT NULL DEFAULT 'PENDENTE'
                   CHECK (status_rsvp IN ('PENDENTE', 'CONFIRMADO', 'RECUSADO'))
);

-- Índices para as consultas mais frequentes do painel e das listas
CREATE INDEX idx_categoria_casamento  ON categoria (casamento_id);
CREATE INDEX idx_fornecedor_categoria ON fornecedor (categoria_id);
CREATE INDEX idx_despesa_categoria    ON despesa (categoria_id);
CREATE INDEX idx_parcela_vencimento   ON parcela (data_vencimento);
CREATE INDEX idx_convidado_casamento  ON convidado (casamento_id, status_rsvp);
