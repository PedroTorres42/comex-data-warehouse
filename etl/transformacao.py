import pandas as pd
import os

# Criar pasta silver
os.makedirs("../data/silver", exist_ok=True)

# ==============================
# 📥 Carregar dados
# ==============================
transacoes = pd.read_csv("../data/bronze/transacoes.csv")
paises = pd.read_csv("../data/bronze/paises.csv")
produtos = pd.read_csv("../data/bronze/produtos.csv")
moedas = pd.read_csv("../data/bronze/moedas.csv")
cambios = pd.read_csv("../data/bronze/cambios.csv")

# ==============================
# 🧹 Limpeza
# ==============================

# Remover duplicados
transacoes = transacoes.drop_duplicates()

# Remover nulos
transacoes = transacoes.dropna()

# Padronização de texto
paises = paises.apply(lambda x: x.astype(str).str.upper())
produtos = produtos.apply(lambda x: x.astype(str).str.upper())

# ==============================
# 📅 Tratamento de datas
# ==============================
cambios["data"] = pd.to_datetime(cambios["data"])

cambios["ano"] = cambios["data"].dt.year
cambios["mes"] = cambios["data"].dt.month
cambios["dia"] = cambios["data"].dt.day
cambios["trimestre"] = cambios["data"].dt.quarter

# ==============================
# 🔎 Validações
# ==============================

# Valor não pode ser negativo
transacoes = transacoes[transacoes["valor"] > 0]

# ==============================
# 🔗 Integração (JOIN)
# ==============================

df = transacoes.merge(paises, on="id_pais", how="left") \
               .merge(produtos, on="id_produto", how="left") \
               .merge(moedas, on="id_moeda", how="left")

# ==============================
# 💱 Conversão de moeda (exemplo)
# ==============================

df = df.merge(cambios, on="data", how="left")

df["valor_convertido"] = df["valor"] * df["taxa_cambio"]

# ==============================
# 💾 Salvar camada Silver
# ==============================

df.to_csv("../data/silver/dados_tratados.csv", index=False)

print("✅ Transformação concluída!")