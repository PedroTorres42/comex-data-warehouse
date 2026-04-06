CREATE TABLE dim_tempo (
    sk_tempo INT PRIMARY KEY,
    data DATE,
    ano INT,
    mes INT
);

CREATE TABLE fato_transacoes (
    id INT PRIMARY KEY,
    valor DECIMAL(10,2),
    quantidade INT,
    sk_tempo INT,
    FOREIGN KEY (sk_tempo) REFERENCES dim_tempo(sk_tempo)
);