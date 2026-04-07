CREATE TABLE dim_tempo (
    sk_tempo INT PRIMARY KEY,
    data_referencia DATE NOT NULL,
    dia INT NOT NULL,
    mes INT NOT NULL,
    nome_mes VARCHAR(20) NOT NULL,
    trimestre INT NOT NULL,
    ano INT NOT NULL
);

CREATE TABLE dim_pais_origem (
    sk_pais_origem INT PRIMARY KEY,
    id_pais_origem INT NOT NULL,
    nome_pais_origem VARCHAR(100) NOT NULL,
    codigo_iso_pais_origem VARCHAR(10) NOT NULL,
    bloco_economico_pais_origem VARCHAR(100)
);

CREATE TABLE dim_pais_destino (
    sk_pais_destino INT PRIMARY KEY,
    id_pais_destino INT NOT NULL,
    nome_pais_destino VARCHAR(100) NOT NULL,
    codigo_iso_pais_destino VARCHAR(10) NOT NULL,
    bloco_economico_pais_destino VARCHAR(100)
);

CREATE TABLE dim_produto (
    sk_produto INT PRIMARY KEY,
    id_produto INT NOT NULL,
    descricao_produto VARCHAR(255) NOT NULL,
    codigo_ncm_produto INT,
    categoria_produto VARCHAR(100)
);

CREATE TABLE dim_categoria_produto (
    sk_categoria_produto INT PRIMARY KEY,
    id_categoria_produto INT NOT NULL,
    descricao_categoria_produto VARCHAR(100) NOT NULL
);

CREATE TABLE dim_moeda_origem (
    sk_moeda_origem INT PRIMARY KEY,
    id_moeda_origem INT NOT NULL,
    descricao_moeda_origem VARCHAR(50) NOT NULL,
    pais_moeda_origem VARCHAR(100) NOT NULL
);

CREATE TABLE dim_moeda_destino (
    sk_moeda_destino INT PRIMARY KEY,
    id_moeda_destino INT NOT NULL,
    descricao_moeda_destino VARCHAR(50) NOT NULL,
    pais_moeda_destino VARCHAR(100) NOT NULL
);

CREATE TABLE dim_tipo_transacao (
    sk_tipo_transacao INT PRIMARY KEY,
    id_tipo_transacao INT NOT NULL,
    descricao_tipo_transacao VARCHAR(100) NOT NULL
);

CREATE TABLE dim_transporte (
    sk_transporte INT PRIMARY KEY,
    id_transporte INT NOT NULL,
    descricao_transporte VARCHAR(100) NOT NULL
);

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