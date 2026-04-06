import pandas as pd
import os

# Criar pasta gold
os.makedirs("../data/gold", exist_ok=True)

# ==============================
# 📥 Carregar dados tratados
# ==============================
df = pd.read_csv("../data/silver/dados_tratados.csv")

# ==============================
# 📅 Dimensão Tempo
# ==============================
df["data"] = pd.to_datetime(df["data"])

dim_tempo = df[["data"]].drop_duplicates().copy()
dim_tempo["ano"] = dim_tempo["data"].dt.year
dim_tempo["mes"] = dim_tempo["data"].dt.month
dim_tempo["dia"] = dim_tempo["data"].dt.day
dim_tempo["trimestre"] = dim_tempo["data"].dt.quarter

dim_tempo.to_csv("../data/gold/dim_tempo.csv", index=False)

# ==============================
# 🌍 Dimensão País
# ==============================
dim_pais = df[["id_pais", "nome"]].drop_duplicates()
dim_pais.to_csv("../data/gold/dim_pais.csv", index=False)

# ==============================
# 📦 Dimensão Produto
# ==============================
dim_produto = df[["id_produto", "descricao"]].drop_duplicates()
dim_produto.to_csv("../data/gold/dim_produto.csv", index=False)

# ==============================
# 💰 Dimensão Moeda
# ==============================
dim_moeda = df[["id_moeda", "descricao_moeda"]].drop_duplicates()
dim_moeda.to_csv("../data/gold/dim_moeda.csv", index=False)

# ==============================
# ⭐ Fato Transações
# ==============================
fato = df[[
    "id_transacao",
    "valor",
    "valor_convertido",
    "quantidade",
    "data",
    "id_pais",
    "id_produto",
    "id_moeda"
]]

fato.to_csv("../data/gold/fato_transacoes.csv", index=False)

print("🚀 Data Warehouse carregado!")