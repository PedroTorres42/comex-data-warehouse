-- ============================================================
-- CRIAÇÃO DO DATA WAREHOUSE - COMEX
-- ============================================================

-- Criar banco de dados
DROP DATABASE IF EXISTS comex_dw;
CREATE DATABASE comex_dw CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE comex_dw;

-- ============================================================
-- DIMENSÕES
-- ============================================================

-- Dimensão Tempo
CREATE TABLE dim_tempo (
    sk_tempo INT PRIMARY KEY AUTO_INCREMENT,
    data_referencia DATE NOT NULL,
    dia INT NOT NULL,
    mes INT NOT NULL,
    nome_mes VARCHAR(20) NOT NULL,
    trimestre INT NOT NULL,
    ano INT NOT NULL,
    UNIQUE KEY uk_data_referencia (data_referencia)
);

-- Dimensão País Origem
CREATE TABLE dim_pais_origem (
    sk_pais_origem INT PRIMARY KEY AUTO_INCREMENT,
    id_pais_origem INT NOT NULL,
    nome_pais_origem VARCHAR(100) NOT NULL,
    codigo_iso_pais_origem VARCHAR(10) NOT NULL,
    bloco_economico_pais_origem VARCHAR(100),
    UNIQUE KEY uk_id_pais_origem (id_pais_origem)
);

-- Dimensão País Destino
CREATE TABLE dim_pais_destino (
    sk_pais_destino INT PRIMARY KEY AUTO_INCREMENT,
    id_pais_destino INT NOT NULL,
    nome_pais_destino VARCHAR(100) NOT NULL,
    codigo_iso_pais_destino VARCHAR(10) NOT NULL,
    bloco_economico_pais_destino VARCHAR(100),
    UNIQUE KEY uk_id_pais_destino (id_pais_destino)
);

-- Dimensão Produto
CREATE TABLE dim_produto (
    sk_produto INT PRIMARY KEY AUTO_INCREMENT,
    id_produto INT NOT NULL,
    descricao_produto VARCHAR(255) NOT NULL,
    codigo_ncm_produto INT,
    categoria_produto VARCHAR(100),
    UNIQUE KEY uk_id_produto (id_produto)
);

-- Dimensão Categoria Produto
CREATE TABLE dim_categoria_produto (
    sk_categoria_produto INT PRIMARY KEY AUTO_INCREMENT,
    id_categoria_produto INT NOT NULL,
    descricao_categoria_produto VARCHAR(100) NOT NULL,
    UNIQUE KEY uk_id_categoria (id_categoria_produto)
);

-- Dimensão Moeda Origem
CREATE TABLE dim_moeda_origem (
    sk_moeda_origem INT PRIMARY KEY AUTO_INCREMENT,
    id_moeda_origem INT NOT NULL,
    descricao_moeda_origem VARCHAR(50) NOT NULL,
    pais_moeda_origem VARCHAR(100) NOT NULL,
    UNIQUE KEY uk_id_moeda_origem (id_moeda_origem)
);

-- Dimensão Moeda Destino
CREATE TABLE dim_moeda_destino (
    sk_moeda_destino INT PRIMARY KEY AUTO_INCREMENT,
    id_moeda_destino INT NOT NULL,
    descricao_moeda_destino VARCHAR(50) NOT NULL,
    pais_moeda_destino VARCHAR(100) NOT NULL,
    UNIQUE KEY uk_id_moeda_destino (id_moeda_destino)
);

-- Dimensão Tipo Transação
CREATE TABLE dim_tipo_transacao (
    sk_tipo_transacao INT PRIMARY KEY AUTO_INCREMENT,
    id_tipo_transacao INT NOT NULL,
    descricao_tipo_transacao VARCHAR(100) NOT NULL,
    UNIQUE KEY uk_id_tipo_transacao (id_tipo_transacao)
);

-- Dimensão Transporte
CREATE TABLE dim_transporte (
    sk_transporte INT PRIMARY KEY AUTO_INCREMENT,
    id_transporte INT NOT NULL,
    descricao_transporte VARCHAR(100) NOT NULL,
    UNIQUE KEY uk_id_transporte (id_transporte)
);

-- ============================================================
-- FATO (Tabela de Fatos)
-- ============================================================

CREATE TABLE fato_transacoes_internacionais (
    id_transacao INT PRIMARY KEY,
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
    -- Índices para performance
    INDEX idx_sk_tempo (sk_tempo),
    INDEX idx_sk_pais_origem (sk_pais_origem),
    INDEX idx_sk_pais_destino (sk_pais_destino),
    INDEX idx_sk_produto (sk_produto),
    INDEX idx_sk_moeda_origem (sk_moeda_origem),
    INDEX idx_sk_moeda_destino (sk_moeda_destino),
    -- Foreign Keys
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

-- ============================================================
-- VIEWS ÚTEIS PARA ANÁLISE
-- ============================================================

CREATE VIEW vw_transacoes_detalha AS
SELECT 
    f.id_transacao,
    f.quantidade_transacionada,
    f.valor_monetario_transacao,
    f.valor_convertido_transacao,
    f.taxa_cambio_transacao,
    dt.data_referencia,
    dt.ano,
    dt.mes,
    dt.nome_mes,
    dt.trimestre,
    dpo.nome_pais_origem,
    dpo.bloco_economico_pais_origem,
    dpd.nome_pais_destino,
    dpd.bloco_economico_pais_destino,
    dp.descricao_produto,
    dcp.descricao_categoria_produto,
    dmo.descricao_moeda_origem,
    dmd.descricao_moeda_destino,
    dtt.descricao_tipo_transacao,
    dtr.descricao_transporte
FROM fato_transacoes_internacionais f
JOIN dim_tempo dt ON f.sk_tempo = dt.sk_tempo
JOIN dim_pais_origem dpo ON f.sk_pais_origem = dpo.sk_pais_origem
JOIN dim_pais_destino dpd ON f.sk_pais_destino = dpd.sk_pais_destino
JOIN dim_produto dp ON f.sk_produto = dp.sk_produto
JOIN dim_categoria_produto dcp ON f.sk_categoria_produto = dcp.sk_categoria_produto
JOIN dim_moeda_origem dmo ON f.sk_moeda_origem = dmo.sk_moeda_origem
JOIN dim_moeda_destino dmd ON f.sk_moeda_destino = dmd.sk_moeda_destino
JOIN dim_tipo_transacao dtt ON f.sk_tipo_transacao = dtt.sk_tipo_transacao
JOIN dim_transporte dtr ON f.sk_transporte = dtr.sk_transporte;

-- ============================================================
-- VERIFICAÇÃO FINAL
-- ============================================================

SELECT 'Data Warehouse criado com sucesso!' AS status;
SHOW TABLES;
