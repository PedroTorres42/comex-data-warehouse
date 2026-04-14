-- ==============================
-- DIMENSÃO TEMPO
-- ==============================
CREATE TABLE dim_tempo (
    sk_tempo INT PRIMARY KEY,
    data_referencia DATE NOT NULL,
    dia INT NOT NULL,
    mes INT NOT NULL,
    nome_mes VARCHAR(20) NOT NULL,
    trimestre INT NOT NULL,
    ano INT NOT NULL
);

-- ==============================
-- DIMENSÃO PAÍS ORIGEM
-- ==============================
CREATE TABLE dim_pais_origem (
    sk_pais_origem INT PRIMARY KEY,
    id_pais_origem INT NOT NULL,
    nome_pais_origem VARCHAR(100) NOT NULL,
    codigo_iso_pais_origem VARCHAR(10) NOT NULL,
    bloco_economico_pais_origem VARCHAR(100)
);

-- ==============================
-- DIMENSÃO PAÍS DESTINO
-- ==============================
CREATE TABLE dim_pais_destino (
    sk_pais_destino INT PRIMARY KEY,
    id_pais_destino INT NOT NULL,
    nome_pais_destino VARCHAR(100) NOT NULL,
    codigo_iso_pais_destino VARCHAR(10) NOT NULL,
    bloco_economico_pais_destino VARCHAR(100)
);

-- ==============================
-- DIMENSÃO PRODUTO (CORRIGIDA)
-- ==============================
CREATE TABLE dim_produto (
    sk_produto INT PRIMARY KEY,
    id_produto INT NOT NULL,
    descricao_produto VARCHAR(255) NOT NULL,
    codigo_ncm_produto INT
);

-- ==============================
-- DIMENSÃO CATEGORIA PRODUTO
-- ==============================
CREATE TABLE dim_categoria_produto (
    sk_categoria_produto INT PRIMARY KEY,
    id_categoria_produto INT NOT NULL,
    descricao_categoria_produto VARCHAR(100) NOT NULL
);

-- ==============================
-- DIMENSÃO MOEDA ORIGEM
-- ==============================
CREATE TABLE dim_moeda_origem (
    sk_moeda_origem INT PRIMARY KEY,
    id_moeda_origem INT NOT NULL,
    descricao_moeda_origem VARCHAR(50) NOT NULL,
    pais_moeda_origem VARCHAR(100) NOT NULL
);

-- ==============================
-- DIMENSÃO MOEDA DESTINO
-- ==============================
CREATE TABLE dim_moeda_destino (
    sk_moeda_destino INT PRIMARY KEY,
    id_moeda_destino INT NOT NULL,
    descricao_moeda_destino VARCHAR(50) NOT NULL,
    pais_moeda_destino VARCHAR(100) NOT NULL
);

-- ==============================
-- DIMENSÃO TIPO TRANSAÇÃO
-- ==============================
CREATE TABLE dim_tipo_transacao (
    sk_tipo_transacao INT PRIMARY KEY,
    id_tipo_transacao INT NOT NULL,
    descricao_tipo_transacao VARCHAR(100) NOT NULL
);

-- ==============================
-- DIMENSÃO TRANSPORTE
-- ==============================
CREATE TABLE dim_transporte (
    sk_transporte INT PRIMARY KEY,
    id_transporte INT NOT NULL,
    descricao_transporte VARCHAR(100) NOT NULL
);

-- ==============================
-- TABELA FATO (CORRIGIDA)
-- ==============================
CREATE TABLE fato_transacoes_internacionais (
    sk_transacao INT PRIMARY KEY,
    id_transacao INT,

    quantidade_transacionada INT NOT NULL,
    valor_monetario_transacao DECIMAL(15,2) NOT NULL,
    valor_convertido_transacao DECIMAL(15,2),
    taxa_cambio_transacao DECIMAL(10,4),
    custo_transporte_transacao DECIMAL(15,2),

    sk_tempo INT NOT NULL,
    sk_pais_origem INT NOT NULL,
    sk_pais_destino INT NOT NULL,
    sk_produto INT NOT NULL,
    sk_categoria_produto INT NOT NULL,
    sk_moeda_origem INT NOT NULL,
    sk_moeda_destino INT NOT NULL,
    sk_tipo_transacao INT NOT NULL,
    sk_transporte INT NOT NULL,

    FOREIGN KEY (sk_tempo) REFERENCES dim_tempo(sk_tempo),
    FOREIGN KEY (sk_pais_origem) REFERENCES dim_pais_origem(sk_pais_origem),
    FOREIGN KEY (sk_pais_destino) REFERENCES dim_pais_destino(sk_pais_destino),
    FOREIGN KEY (sk_produto) REFERENCES dim_produto(sk_produto),
    FOREIGN KEY (sk_categoria_produto) REFERENCES dim_categoria_produto(sk_categoria_produto),
    FOREIGN KEY (sk_moeda_origem) REFERENCES dim_moeda_origem(sk_moeda_origem),
    FOREIGN KEY (sk_moeda_destino) REFERENCES dim_moeda_destino(sk_moeda_destino),
    FOREIGN KEY (sk_tipo_transacao) REFERENCES dim_tipo_transacao(sk_tipo_transacao),
    FOREIGN KEY (sk_transporte) REFERENCES dim_transporte(sk_transporte)
);

-- ==============================
-- ÍNDICES PARA PERFORMANCE
-- ==============================

-- Dimensao tempo (usada em agrupamentos por ano/mes/trimestre)
CREATE INDEX idx_dim_tempo_ano_mes ON dim_tempo (ano, mes);
CREATE INDEX idx_dim_tempo_trimestre ON dim_tempo (ano, trimestre);

-- Dimensoes de pais (usadas em agrupamentos por nome e bloco)
CREATE INDEX idx_dim_pais_origem_nome ON dim_pais_origem (nome_pais_origem);
CREATE INDEX idx_dim_pais_origem_bloco ON dim_pais_origem (bloco_economico_pais_origem);
CREATE INDEX idx_dim_pais_destino_nome ON dim_pais_destino (nome_pais_destino);
CREATE INDEX idx_dim_pais_destino_bloco ON dim_pais_destino (bloco_economico_pais_destino);

-- Dimensoes de produto e categoria
CREATE INDEX idx_dim_produto_descricao ON dim_produto (descricao_produto);
CREATE INDEX idx_dim_categoria_descricao ON dim_categoria_produto (descricao_categoria_produto);

-- Dimensao de moeda usada em visao cambial
CREATE INDEX idx_dim_moeda_origem_descricao ON dim_moeda_origem (descricao_moeda_origem);

-- Fato: chaves de junção e colunas usadas em filtros/ordenacoes analiticas
CREATE INDEX idx_fato_sk_tempo ON fato_transacoes_internacionais (sk_tempo);
CREATE INDEX idx_fato_sk_pais_origem ON fato_transacoes_internacionais (sk_pais_origem);
CREATE INDEX idx_fato_sk_pais_destino ON fato_transacoes_internacionais (sk_pais_destino);
CREATE INDEX idx_fato_sk_produto ON fato_transacoes_internacionais (sk_produto);
CREATE INDEX idx_fato_sk_categoria_produto ON fato_transacoes_internacionais (sk_categoria_produto);
CREATE INDEX idx_fato_sk_moeda_origem ON fato_transacoes_internacionais (sk_moeda_origem);
CREATE INDEX idx_fato_sk_moeda_destino ON fato_transacoes_internacionais (sk_moeda_destino);
CREATE INDEX idx_fato_sk_tipo_transacao ON fato_transacoes_internacionais (sk_tipo_transacao);
CREATE INDEX idx_fato_sk_transporte ON fato_transacoes_internacionais (sk_transporte);
CREATE INDEX idx_fato_id_transacao ON fato_transacoes_internacionais (id_transacao);