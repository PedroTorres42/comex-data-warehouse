from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"


def _read_csv_if_exists(path):
    return pd.read_csv(path) if path.exists() else None


def _month_name_pt(month):
    month_map = {
        1: "JANEIRO",
        2: "FEVEREIRO",
        3: "MARCO",
        4: "ABRIL",
        5: "MAIO",
        6: "JUNHO",
        7: "JULHO",
        8: "AGOSTO",
        9: "SETEMBRO",
        10: "OUTUBRO",
        11: "NOVEMBRO",
        12: "DEZEMBRO",
    }
    return month_map.get(month, "DESCONHECIDO")


def load_bronze_data():
    """Carrega dados brutos da camada bronze."""
    transacoes = pd.read_csv(BRONZE_DIR / "transacoes.csv")
    paises = pd.read_csv(BRONZE_DIR / "paises.csv")
    moedas = pd.read_csv(BRONZE_DIR / "moedas.csv")
    cambios = pd.read_csv(BRONZE_DIR / "cambios.csv")
    tipos_transacoes = pd.read_csv(BRONZE_DIR / "tipos_transacoes.csv")
    transportes = pd.read_csv(BRONZE_DIR / "transportes.csv")
    blocos_economicos = pd.read_csv(BRONZE_DIR / "blocos_economicos.csv")
    produtos = _read_csv_if_exists(BRONZE_DIR / "produtos.csv")
    categoria_produtos = _read_csv_if_exists(BRONZE_DIR / "categoria_produtos.csv")

    return {
        "transacoes": transacoes,
        "paises": paises,
        "moedas": moedas,
        "cambios": cambios,
        "tipos_transacoes": tipos_transacoes,
        "transportes": transportes,
        "blocos_economicos": blocos_economicos,
        "produtos": produtos,
        "categoria_produtos": categoria_produtos,
    }


def transform_bronze_to_dw_frames(bronze_data):
    """Transforma dados brutos em dataframes prontos para carga no DW."""
    transacoes = bronze_data["transacoes"]
    paises = bronze_data["paises"]
    moedas = bronze_data["moedas"]
    cambios = bronze_data["cambios"]
    tipos_transacoes = bronze_data["tipos_transacoes"]
    transportes = bronze_data["transportes"]
    blocos_economicos = bronze_data["blocos_economicos"]
    produtos = bronze_data["produtos"]
    categoria_produtos = bronze_data["categoria_produtos"]

    transacoes = transacoes.drop_duplicates()
    transacoes = transacoes.dropna(
        subset=[
            "id",
            "tipo_id",
            "pais_origem",
            "pais_destino",
            "produto_id",
            "valor_monetario",
            "quantidade",
            "transporte_id",
            "cambio_id",
        ]
    )
    transacoes = transacoes[transacoes["valor_monetario"] > 0]
    transacoes = transacoes[transacoes["quantidade"] > 0]
    cambios["data"] = pd.to_datetime(cambios["data"])

    paises_enriquecido = paises.merge(
        blocos_economicos.rename(columns={"id": "bloco_id_join", "nome": "bloco_nome"}),
        left_on="bloco_id",
        right_on="bloco_id_join",
        how="left",
    )

    dim_tempo = cambios[["data"]].drop_duplicates().sort_values("data").reset_index(drop=True)
    dim_tempo["sk_tempo"] = dim_tempo.index + 1
    dim_tempo["data_referencia"] = dim_tempo["data"].dt.date
    dim_tempo["dia"] = dim_tempo["data"].dt.day
    dim_tempo["mes"] = dim_tempo["data"].dt.month
    dim_tempo["nome_mes"] = dim_tempo["mes"].map(_month_name_pt)
    dim_tempo["trimestre"] = dim_tempo["data"].dt.quarter
    dim_tempo["ano"] = dim_tempo["data"].dt.year

    base_pais = paises_enriquecido[["id", "nome", "codigo_iso", "bloco_nome"]].drop_duplicates().reset_index(drop=True)
    dim_pais_origem = base_pais.copy()
    dim_pais_origem["sk_pais_origem"] = dim_pais_origem.index + 1
    dim_pais_destino = base_pais.copy()
    dim_pais_destino["sk_pais_destino"] = dim_pais_destino.index + 1

    if categoria_produtos is not None:
        dim_categoria_produto = categoria_produtos.rename(
            columns={"id": "id_categoria_produto", "descricao": "descricao_categoria_produto"}
        )[["id_categoria_produto", "descricao_categoria_produto"]].drop_duplicates()
    else:
        dim_categoria_produto = pd.DataFrame(
            [{"id_categoria_produto": 0, "descricao_categoria_produto": "SEM_CATEGORIA"}]
        )
    dim_categoria_produto = dim_categoria_produto.sort_values("id_categoria_produto").reset_index(drop=True)
    dim_categoria_produto["sk_categoria_produto"] = dim_categoria_produto.index + 1

    if produtos is not None:
        prod_cols = {
            "id": "id_produto",
            "descricao": "descricao_produto",
            "codigo_ncm": "codigo_ncm_produto",
            "categoria_id": "id_categoria_produto",
        }
        produtos_norm = produtos.rename(columns=prod_cols)
        for col in ["descricao_produto", "codigo_ncm_produto", "id_categoria_produto"]:
            if col not in produtos_norm.columns:
                produtos_norm[col] = None
        produtos_norm["id_categoria_produto"] = produtos_norm["id_categoria_produto"].fillna(0)
        dim_produto = produtos_norm[["id_produto", "descricao_produto", "codigo_ncm_produto", "id_categoria_produto"]]
    else:
        dim_produto = transacoes[["produto_id"]].drop_duplicates().rename(columns={"produto_id": "id_produto"})
        dim_produto["descricao_produto"] = dim_produto["id_produto"].astype(int).astype(str).radd("PRODUTO ")
        dim_produto["codigo_ncm_produto"] = None
        dim_produto["id_categoria_produto"] = 0

    dim_produto = dim_produto.merge(
        dim_categoria_produto[["id_categoria_produto", "descricao_categoria_produto"]],
        on="id_categoria_produto",
        how="left",
    )
    dim_produto["categoria_produto"] = dim_produto["descricao_categoria_produto"].fillna("SEM_CATEGORIA")
    dim_produto = dim_produto.drop(columns=["descricao_categoria_produto"])
    dim_produto = dim_produto.sort_values("id_produto").drop_duplicates(subset=["id_produto"]).reset_index(drop=True)
    dim_produto["sk_produto"] = dim_produto.index + 1

    base_moeda = moedas.rename(
        columns={"id": "id_moeda", "descricao": "descricao_moeda", "pais": "pais_moeda"}
    )[["id_moeda", "descricao_moeda", "pais_moeda"]].drop_duplicates()
    dim_moeda_origem = base_moeda.sort_values("id_moeda").reset_index(drop=True)
    dim_moeda_origem["sk_moeda_origem"] = dim_moeda_origem.index + 1
    dim_moeda_destino = base_moeda.sort_values("id_moeda").reset_index(drop=True)
    dim_moeda_destino["sk_moeda_destino"] = dim_moeda_destino.index + 1

    dim_tipo_transacao = tipos_transacoes.rename(
        columns={"id": "id_tipo_transacao", "descricao": "descricao_tipo_transacao"}
    )[["id_tipo_transacao", "descricao_tipo_transacao"]].drop_duplicates()
    dim_tipo_transacao = dim_tipo_transacao.sort_values("id_tipo_transacao").reset_index(drop=True)
    dim_tipo_transacao["sk_tipo_transacao"] = dim_tipo_transacao.index + 1

    dim_transporte = transportes.rename(columns={"id": "id_transporte", "descricao": "descricao_transporte"})[
        ["id_transporte", "descricao_transporte"]
    ].drop_duplicates()
    dim_transporte = dim_transporte.sort_values("id_transporte").reset_index(drop=True)
    dim_transporte["sk_transporte"] = dim_transporte.index + 1

    cambios_fact = cambios.rename(columns={"id": "cambio_id"})[["cambio_id", "data", "moeda_origem", "moeda_destino", "taxa_cambio"]]
    fato = transacoes.rename(
        columns={
            "id": "id_transacao",
            "valor_monetario": "valor_monetario_transacao",
            "quantidade": "quantidade_transacionada",
        }
    )
    fato = fato.merge(cambios_fact, on="cambio_id", how="left")
    fato["valor_convertido_transacao"] = fato["valor_monetario_transacao"] * fato["taxa_cambio"]
    fato["custo_transporte_transacao"] = 0.0

    tempo_map = dim_tempo.set_index("data")["sk_tempo"]
    pais_origem_map = dim_pais_origem.set_index("id")["sk_pais_origem"]
    pais_destino_map = dim_pais_destino.set_index("id")["sk_pais_destino"]
    produto_map = dim_produto.set_index("id_produto")["sk_produto"]
    categoria_map = dim_produto.set_index("id_produto")["id_categoria_produto"].map(
        dim_categoria_produto.set_index("id_categoria_produto")["sk_categoria_produto"]
    )
    moeda_origem_map = dim_moeda_origem.set_index("id_moeda")["sk_moeda_origem"]
    moeda_destino_map = dim_moeda_destino.set_index("id_moeda")["sk_moeda_destino"]
    tipo_map = dim_tipo_transacao.set_index("id_tipo_transacao")["sk_tipo_transacao"]
    transporte_map = dim_transporte.set_index("id_transporte")["sk_transporte"]

    fato["sk_tempo"] = pd.to_datetime(fato["data"]).map(tempo_map)
    fato["sk_pais_origem"] = fato["pais_origem"].map(pais_origem_map)
    fato["sk_pais_destino"] = fato["pais_destino"].map(pais_destino_map)
    fato["sk_produto"] = fato["produto_id"].map(produto_map)
    fato["sk_categoria_produto"] = fato["produto_id"].map(categoria_map)
    fato["sk_moeda_origem"] = fato["moeda_origem"].map(moeda_origem_map)
    fato["sk_moeda_destino"] = fato["moeda_destino"].map(moeda_destino_map)
    fato["sk_tipo_transacao"] = fato["tipo_id"].map(tipo_map)
    fato["sk_transporte"] = fato["transporte_id"].map(transporte_map)

    fk_cols = [
        "sk_tempo",
        "sk_pais_origem",
        "sk_pais_destino",
        "sk_produto",
        "sk_categoria_produto",
        "sk_moeda_origem",
        "sk_moeda_destino",
        "sk_tipo_transacao",
        "sk_transporte",
    ]
    before = len(fato)
    fato = fato.dropna(subset=fk_cols)
    discarded = before - len(fato)
    if discarded > 0:
        print(f"⚠️ {discarded} transações foram descartadas por falta de chaves de dimensão.")

    fato = fato[
        [
            "id_transacao",
            "quantidade_transacionada",
            "valor_monetario_transacao",
            "valor_convertido_transacao",
            "taxa_cambio",
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
        ]
    ].rename(columns={"taxa_cambio": "taxa_cambio_transacao"})

    return {
        "dim_tempo": dim_tempo,
        "dim_pais_origem": dim_pais_origem.rename(
            columns={
                "id": "id_pais_origem",
                "nome": "nome_pais_origem",
                "codigo_iso": "codigo_iso_pais_origem",
                "bloco_nome": "bloco_economico_pais_origem",
            }
        ),
        "dim_pais_destino": dim_pais_destino.rename(
            columns={
                "id": "id_pais_destino",
                "nome": "nome_pais_destino",
                "codigo_iso": "codigo_iso_pais_destino",
                "bloco_nome": "bloco_economico_pais_destino",
            }
        ),
        "dim_categoria_produto": dim_categoria_produto,
        "dim_produto": dim_produto,
        "dim_moeda_origem": dim_moeda_origem.rename(
            columns={
                "id_moeda": "id_moeda_origem",
                "descricao_moeda": "descricao_moeda_origem",
                "pais_moeda": "pais_moeda_origem",
            }
        ),
        "dim_moeda_destino": dim_moeda_destino.rename(
            columns={
                "id_moeda": "id_moeda_destino",
                "descricao_moeda": "descricao_moeda_destino",
                "pais_moeda": "pais_moeda_destino",
            }
        ),
        "dim_tipo_transacao": dim_tipo_transacao,
        "dim_transporte": dim_transporte,
        "fato_transacoes_internacionais": fato,
    }


def main():
    print("📥 Carregando arquivos da camada bronze...")
    bronze_data = load_bronze_data()
    print("🧹 Transformando dados para o formato do DW...")
    dw_frames = transform_bronze_to_dw_frames(bronze_data)
    print(
        "✅ Transformação concluída! Tabelas prontas para carga: "
        + ", ".join(dw_frames.keys())
    )


if __name__ == "__main__":
    main()