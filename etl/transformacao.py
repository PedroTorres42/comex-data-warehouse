import pandas as pd
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"

# Criar pasta silver
os.makedirs(SILVER_DIR, exist_ok=True)

# ==============================
# 📥 Carregar dados
# ==============================
transacoes = pd.read_csv(BRONZE_DIR / "transacoes.csv")
paises = pd.read_csv(BRONZE_DIR / "paises.csv")
moedas = pd.read_csv(BRONZE_DIR / "moedas.csv")
cambios = pd.read_csv(BRONZE_DIR / "cambios.csv")
tipos_transacoes = pd.read_csv(BRONZE_DIR / "tipos_transacoes.csv")
transportes = pd.read_csv(BRONZE_DIR / "transportes.csv")

# ==============================
# 🧹 Limpeza
# ==============================

# Remover duplicados
transacoes = transacoes.drop_duplicates()

# Remover nulos críticos
transacoes = transacoes.dropna(subset=["id", "valor_monetario"])

# ==============================
# 📅 Tratamento de datas
# ==============================
cambios["data"] = pd.to_datetime(cambios["data"])

# ==============================
# 🔎 Validações
# ==============================

# Valor não pode ser negativo
transacoes = transacoes[transacoes["valor_monetario"] > 0]

# ==============================
# 🔗 Integração completa (JOINs para fato)
# ==============================

# Rename para padronização
transacoes_r = transacoes.rename(columns={
    "id": "id_transacao",
    "tipo_id": "id_tipo_transacao",
    "pais_origem": "id_pais_origem",
    "pais_destino": "id_pais_destino",
    "produto_id": "id_produto",
    "valor_monetario": "valor_monetario_transacao",
    "quantidade": "quantidade_transacionada",
    "transporte_id": "id_transporte",
    "cambio_id": "id_cambio"
})

# Rename em tabelas dimensões
paises_r = paises.rename(columns={
    "id": "id_pais",
    "nome": "nome_pais",
    "codigo_iso": "codigo_iso_pais",
    "bloco_id": "bloco_id"
})

tipos_r = tipos_transacoes.rename(columns={
    "id": "id_tipo_transacao",
    "descricao": "descricao_tipo_transacao"
})

transporte_r = transportes.rename(columns={
    "id": "id_transporte",
    "descricao": "descricao_transporte"
})

moedas_r = moedas.rename(columns={
    "id": "id_moeda",
    "descricao": "descricao_moeda",
    "pais": "pais_moeda"
})

cambios_r = cambios.rename(columns={
    "id": "id_cambio",
    "moeda_origem": "id_moeda_origem",
    "moeda_destino": "id_moeda_destino",
    "taxa_cambio": "taxa_cambio_transacao"
})

# ==============================
# 🔗 Executar JOINs
# ==============================

df = transacoes_r.copy()

# Join com tipos de transação
df = df.merge(tipos_r, on="id_tipo_transacao", how="left")

# Join com transportes
df = df.merge(transporte_r, on="id_transporte", how="left")

# Join com câmbios para obter moedas e taxa
df = df.merge(cambios_r, on="id_cambio", how="left")

# Join com moedas origem
moedas_origem = moedas_r.copy()
moedas_origem = moedas_origem.rename(columns={
    "id_moeda": "id_moeda_origem",
    "descricao_moeda": "descricao_moeda_origem",
    "pais_moeda": "pais_moeda_origem"
})
df = df.merge(moedas_origem[["id_moeda_origem", "descricao_moeda_origem", "pais_moeda_origem"]], 
              on="id_moeda_origem", how="left")

# Join com moedas destino
moedas_destino = moedas_r.copy()
moedas_destino = moedas_destino.rename(columns={
    "id_moeda": "id_moeda_destino",
    "descricao_moeda": "descricao_moeda_destino",
    "pais_moeda": "pais_moeda_destino"
})
df = df.merge(moedas_destino[["id_moeda_destino", "descricao_moeda_destino", "pais_moeda_destino"]], 
              on="id_moeda_destino", how="left")

# Join com países origem
paises_origem = paises_r.copy()
paises_origem = paises_origem.rename(columns={
    "id_pais": "id_pais_origem",
    "nome_pais": "nome_pais_origem",
    "codigo_iso_pais": "codigo_iso_pais_origem",
    "bloco_id": "bloco_id_origem"
})
df = df.merge(paises_origem[["id_pais_origem", "nome_pais_origem", "codigo_iso_pais_origem", "bloco_id_origem"]], 
              on="id_pais_origem", how="left")

# Join com países destino
paises_destino = paises_r.copy()
paises_destino = paises_destino.rename(columns={
    "id_pais": "id_pais_destino",
    "nome_pais": "nome_pais_destino",
    "codigo_iso_pais": "codigo_iso_pais_destino",
    "bloco_id": "bloco_id_destino"
})
df = df.merge(paises_destino[["id_pais_destino", "nome_pais_destino", "codigo_iso_pais_destino", "bloco_id_destino"]], 
              on="id_pais_destino", how="left")

# ==============================
# 💱 Conversão de moeda
# ==============================

if "taxa_cambio_transacao" in df.columns:
    df["valor_convertido_transacao"] = df["valor_monetario_transacao"] * df["taxa_cambio_transacao"].fillna(1.0)
else:
    df["valor_convertido_transacao"] = df["valor_monetario_transacao"]

# ==============================
# 💾 Salvar camada Silver
# ==============================

df.to_csv(SILVER_DIR / "dados_tratados.csv", index=False)

print("✅ Transformação concluída!")
print(f"📊 Registros transformados: {len(df)}")
print(f"📁 Arquivo: {SILVER_DIR / 'dados_tratados.csv'}")