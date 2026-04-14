from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import mysql.connector
import pandas as pd

from transformacao import load_bronze_data, transform_bronze_to_dw_frames


BASE_DIR = Path(__file__).resolve().parent.parent
DW_SQL_PATH = BASE_DIR / "dw" / "modelo_estrela.sql"
ENV_PATH = BASE_DIR / ".env"


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


def _parse_service_uri(service_uri):
    parsed = urlparse(service_uri)
    query = parse_qs(parsed.query)
    kwargs = {
        "host": parsed.hostname,
        "port": parsed.port,
        "user": unquote(parsed.username) if parsed.username else None,
        "password": unquote(parsed.password) if parsed.password else None,
        "database": parsed.path.lstrip("/") or None,
    }
    ssl_ca = query.get("ssl-ca", [None])[0]
    if ssl_ca:
        kwargs["ssl_ca"] = ssl_ca
        kwargs["ssl_verify_cert"] = True
    else:
        kwargs["ssl_disabled"] = False
        kwargs["ssl_verify_cert"] = False
    return kwargs


def _get_connection_kwargs():
    service_uri = _get_env("DW_DB_SERVICE_URI")
    if not service_uri:
        return None
    return _parse_service_uri(service_uri)


def _df_to_rows(df, columns):
    subset = df[columns].astype(object)
    subset = subset.where(pd.notnull(subset), None)
    return [tuple(row) for row in subset.itertuples(index=False, name=None)]


def _execute_schema(cursor):
    drop_order = [
        "fato_transacoes_internacionais",
        "dim_transporte",
        "dim_tipo_transacao",
        "dim_moeda_destino",
        "dim_moeda_origem",
        "dim_categoria_produto",
        "dim_produto",
        "dim_pais_destino",
        "dim_pais_origem",
        "dim_tempo",
    ]
    for table in drop_order:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    statements = [stmt.strip() for stmt in DW_SQL_PATH.read_text(encoding="utf-8").split(";") if stmt.strip()]
    for statement in statements:
        cursor.execute(statement)


def _insert_df(cursor, table, columns, df):
    if df.empty:
        return
    placeholders = ",".join(["%s"] * len(columns))
    column_list = ",".join(columns)
    sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
    cursor.executemany(sql, _df_to_rows(df, columns))


def main():
    bronze_data = load_bronze_data()
    dw_frames = transform_bronze_to_dw_frames(bronze_data)

    service_uri = _get_env("DW_DB_SERVICE_URI")
    if not service_uri:
        raise ValueError("Defina DW_DB_SERVICE_URI no arquivo .env antes de executar a carga.")

    connection_kwargs = _get_connection_kwargs()
    if not connection_kwargs:
        raise ValueError("Defina DW_DB_SERVICE_URI no arquivo .env antes de executar a carga.")

    conexao = mysql.connector.connect(**connection_kwargs)
    db_name = conexao.database
    cursor = conexao.cursor()
    if not db_name:
        raise ValueError("O Service URI do DW precisa conter o nome do banco de dados no caminho da URI.")

    _execute_schema(cursor)

    _insert_df(
        cursor,
        "dim_tempo",
        ["sk_tempo", "data_referencia", "dia", "mes", "nome_mes", "trimestre", "ano"],
        dw_frames["dim_tempo"],
    )
    _insert_df(
        cursor,
        "dim_pais_origem",
        [
            "sk_pais_origem",
            "id_pais_origem",
            "nome_pais_origem",
            "codigo_iso_pais_origem",
            "bloco_economico_pais_origem",
        ],
        dw_frames["dim_pais_origem"],
    )
    _insert_df(
        cursor,
        "dim_pais_destino",
        [
            "sk_pais_destino",
            "id_pais_destino",
            "nome_pais_destino",
            "codigo_iso_pais_destino",
            "bloco_economico_pais_destino",
        ],
        dw_frames["dim_pais_destino"],
    )
    _insert_df(
        cursor,
        "dim_categoria_produto",
        ["sk_categoria_produto", "id_categoria_produto", "descricao_categoria_produto"],
        dw_frames["dim_categoria_produto"],
    )
    _insert_df(
        cursor,
        "dim_produto",
        ["sk_produto", "id_produto", "descricao_produto", "codigo_ncm_produto"],
        dw_frames["dim_produto"],
    )
    _insert_df(
        cursor,
        "dim_moeda_origem",
        ["sk_moeda_origem", "id_moeda_origem", "descricao_moeda_origem", "pais_moeda_origem"],
        dw_frames["dim_moeda_origem"],
    )
    _insert_df(
        cursor,
        "dim_moeda_destino",
        ["sk_moeda_destino", "id_moeda_destino", "descricao_moeda_destino", "pais_moeda_destino"],
        dw_frames["dim_moeda_destino"],
    )
    _insert_df(
        cursor,
        "dim_tipo_transacao",
        ["sk_tipo_transacao", "id_tipo_transacao", "descricao_tipo_transacao"],
        dw_frames["dim_tipo_transacao"],
    )
    _insert_df(
        cursor,
        "dim_transporte",
        ["sk_transporte", "id_transporte", "descricao_transporte"],
        dw_frames["dim_transporte"],
    )
    fato_df = dw_frames["fato_transacoes_internacionais"].copy().reset_index(drop=True)
    fato_df.insert(0, "sk_transacao", fato_df.index + 1)

    _insert_df(
        cursor,
        "fato_transacoes_internacionais",
        [
            "sk_transacao",
            "id_transacao",
            "quantidade_transacionada",
            "valor_monetario_transacao",
            "valor_convertido_transacao",
            "taxa_cambio_transacao",
            "custo_transporte_transacao",
            "sk_tempo",
            "sk_pais_origem",
            "sk_pais_destino",
            "sk_produto",
            "sk_categoria_produto",
            "sk_moeda_origem",
            "sk_moeda_destino",
            "sk_tipo_transacao",
            "sk_transporte",
        ],
        fato_df,
    )

    conexao.commit()
    cursor.close()
    conexao.close()
    print("Carga no DW concluida com sucesso.")


if __name__ == "__main__":
    print("Executando carga do DW a partir das transformacoes da camada bronze.")
    main()