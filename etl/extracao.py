import mysql.connector
import pandas as pd
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
BRONZE_DIR = BASE_DIR / "data" / "bronze"

# Criar pasta bronze
os.makedirs(BRONZE_DIR, exist_ok=True)

# Credenciais via variaveis de ambiente
DB_USER = os.getenv("DB_USER", "consulta")
DB_PASSWORD = os.getenv("DB_PASSWORD", "") 
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = int(os.getenv("DB_PORT", "13729"))
DB_NAME = os.getenv("DB_NAME", "comex")

if not DB_PASSWORD:
    raise ValueError("Defina a variavel de ambiente DB_PASSWORD antes de executar a extracao.")

# Conexão
conexao = mysql.connector.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

print("✅ Conectado ao banco!")

# Tabelas
tabelas = [
    "blocos_economicos",
    "cambios",
    "categoria_produtos",
    "moedas",
    "paises",
    "produtos",
    "tipos_transacoes",
    "transacoes",
    "transportes"
]

# Extração
for tabela in tabelas:
    print(f"📥 Extraindo {tabela}...")

    query = f"SELECT * FROM {tabela}"
    df = pd.read_sql(query, conexao)

    df.to_csv(BRONZE_DIR / f"{tabela}.csv", index=False, encoding="utf-8-sig")

print("🚀 Extração finalizada!")
conexao.close()