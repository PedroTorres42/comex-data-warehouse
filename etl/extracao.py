from pathlib import Path

import mysql.connector
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
BRONZE_DIR = BASE_DIR / "data" / "bronze"


def _load_env_file(path):
    values = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


ENV_VALUES = _load_env_file(ENV_PATH)


def _get_env(name, default=None):
    return ENV_VALUES.get(name) or default


def _get_connection_kwargs(prefix):
    kwargs = {
        "host": _get_env(f"{prefix}_DB_HOST"),
        "port": int(_get_env(f"{prefix}_DB_PORT")),
        "user": _get_env(f"{prefix}_DB_USER"),
        "password": _get_env(f"{prefix}_DB_PASSWORD"),
        "database": _get_env(f"{prefix}_DB_NAME"),
    }
    ssl_ca = _get_env(f"{prefix}_DB_SSL_CA")
    if ssl_ca:
        kwargs["ssl_ca"] = ssl_ca
        kwargs["ssl_verify_cert"] = True
    return kwargs

# Criar pasta bronze
BRONZE_DIR.mkdir(parents=True, exist_ok=True)

# Credenciais via arquivo .env
required_env = ["EXTRACAO_DB_USER", "EXTRACAO_DB_PASSWORD", "EXTRACAO_DB_HOST", "EXTRACAO_DB_PORT", "EXTRACAO_DB_NAME"]
missing_env = [name for name in required_env if not _get_env(name)]
if missing_env:
    raise ValueError(
        "Defina EXTRACAO_DB_USER, EXTRACAO_DB_PASSWORD, EXTRACAO_DB_HOST, EXTRACAO_DB_PORT e EXTRACAO_DB_NAME no arquivo .env antes de executar a extracao."
    )

# Conexão
conexao = mysql.connector.connect(**_get_connection_kwargs("EXTRACAO"))

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