import pandas as pd
import os

# ==============================
# 📁 Criar pasta GOLD
# ==============================
os.makedirs("../data/gold", exist_ok=True)

# ==============================
# 📥 Carregar dados da SILVER
# ==============================
df = pd.read_csv("../data/silver/dados_tratados.csv")

# ==============================
# 📅 DIMENSÃO TEMPO
# ==============================
df["data"] = pd.to_datetime(df["data"])

dim_tempo = df[["data"]].drop_duplicates().reset_index(drop=True)
dim_tempo["sk_tempo"] = dim_tempo.index + 1

dim_tempo["dia"] = dim_tempo["data"].dt.day
dim_tempo["mes"] = dim_tempo["data"].dt.month
dim_tempo["nome_mes"] = dim_tempo["data"].dt.month_name()
dim_tempo["trimestre"] = dim_tempo["data"].dt.quarter
dim_tempo["ano"] = dim_tempo["data"].dt.year

# ==============================
# 🌍 DIMENSÃO PAÍS ORIGEM
# ==============================
dim_pais_origem = df[["id_pais_origem", "nome_pais_origem"]].drop_duplicates().reset_index(drop=True)
dim_pais_origem["sk_pais_origem"] = dim_pais_origem.index + 1

# ==============================
# 🌍 DIMENSÃO PAÍS DESTINO
# ==============================
dim_pais_destino = df[["id_pais_destino", "nome_pais_destino"]].drop_duplicates().reset_index(drop=True)
dim_pais_destino["sk_pais_destino"] = dim_pais_destino.index + 1

# ==============================
# 📦 DIMENSÃO PRODUTO
# ==============================
dim_produto = df[["id_produto", "descricao_produto"]].drop_duplicates().reset_index(drop=True)
dim_produto["sk_produto"] = dim_produto.index + 1

# ==============================
# 🏷 DIMENSÃO CATEGORIA
# ==============================
dim_categoria = df[["id_categoria", "descricao_categoria"]].drop_duplicates().reset_index(drop=True)
dim_categoria["sk_categoria_produto"] = dim_categoria.index + 1

# ==============================
# 💰 DIMENSÃO MOEDA ORIGEM
# ==============================
dim_moeda_origem = df[["id_moeda_origem", "descricao_moeda_origem"]].drop_duplicates().reset_index(drop=True)
dim_moeda_origem["sk_moeda_origem"] = dim_moeda_origem.index + 1

# ==============================
# 💰 DIMENSÃO MOEDA DESTINO
# ==============================
dim_moeda_destino = df[["id_moeda_destino", "descricao_moeda_destino"]].drop_duplicates().reset_index(drop=True)
dim_moeda_destino["sk_moeda_destino"] = dim_moeda_destino.index + 1

# ==============================
# 🔄 DIMENSÃO TIPO TRANSACAO
# ==============================
dim_tipo = df[["id_tipo_transacao", "descricao_tipo_transacao"]].drop_duplicates().reset_index(drop=True)
dim_tipo["sk_tipo_transacao"] = dim_tipo.index + 1

# ==============================
# 🚚 DIMENSÃO TRANSPORTE
# ==============================
dim_transporte = df[["id_transporte", "descricao_transporte"]].drop_duplicates().reset_index(drop=True)
dim_transporte["sk_transporte"] = dim_transporte.index + 1

# ==============================
# 🔗 CRIAR FATO COM SKs
# ==============================
fato = df.copy()

# JOINs
fato = fato.merge(dim_tempo[["data", "sk_tempo"]], on="data", how="left")

fato = fato.merge(dim_pais_origem, on=["id_pais_origem", "nome_pais_origem"], how="left")
fato = fato.merge(dim_pais_destino, on=["id_pais_destino", "nome_pais_destino"], how="left")

fato = fato.merge(dim_produto, on=["id_produto", "descricao_produto"], how="left")
fato = fato.merge(dim_categoria, on=["id_categoria", "descricao_categoria"], how="left")

fato = fato.merge(dim_moeda_origem, on=["id_moeda_origem", "descricao_moeda_origem"], how="left")
fato = fato.merge(dim_moeda_destino, on=["id_moeda_destino", "descricao_moeda_destino"], how="left")

fato = fato.merge(dim_tipo, on=["id_tipo_transacao", "descricao_tipo_transacao"], how="left")
fato = fato.merge(dim_transporte, on=["id_transporte", "descricao_transporte"], how="left")

# ==============================
# ⭐ TABELA FATO FINAL
# ==============================
fato_final = fato[[
    "id_transacao",
    "quantidade",
    "valor",
    "valor_convertido",
    "taxa_cambio",
    "custo_transporte",
    "sk_tempo",
    "sk_pais_origem",
    "sk_pais_destino",
    "sk_produto",
    "sk_categoria_produto",
    "sk_moeda_origem",
    "sk_moeda_destino",
    "sk_tipo_transacao",
    "sk_transporte"
]]

# ==============================
# 💾 SALVAR GOLD
# ==============================
dim_tempo.to_csv("../data/gold/dim_tempo.csv", index=False)
dim_pais_origem.to_csv("../data/gold/dim_pais_origem.csv", index=False)
dim_pais_destino.to_csv("../data/gold/dim_pais_destino.csv", index=False)
dim_produto.to_csv("../data/gold/dim_produto.csv", index=False)
dim_categoria.to_csv("../data/gold/dim_categoria.csv", index=False)
dim_moeda_origem.to_csv("../data/gold/dim_moeda_origem.csv", index=False)
dim_moeda_destino.to_csv("../data/gold/dim_moeda_destino.csv", index=False)
dim_tipo.to_csv("../data/gold/dim_tipo_transacao.csv", index=False)
dim_transporte.to_csv("../data/gold/dim_transporte.csv", index=False)

fato_final.to_csv("../data/gold/fato_transacoes.csv", index=False)

print("🚀 Data Warehouse carregado com sucesso!")