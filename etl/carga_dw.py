import pandas as pd
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
GOLD_DIR = BASE_DIR / "data" / "gold"
SILVER_DIR = BASE_DIR / "data" / "silver"

# Criar pasta gold
os.makedirs(GOLD_DIR, exist_ok=True)

# ==============================
# 📥 Carregar dados tratados
# ==============================
df = pd.read_csv(SILVER_DIR / "dados_tratados.csv")

# ==============================
# ⚙️ Funções auxiliares
# ==============================

def criar_surrogate_key(df_dim, id_col):
    """Cria surrogate keys (sk_) para dimensões"""
    df_dim = df_dim.copy()
    df_dim = df_dim.drop_duplicates(subset=[id_col])
    df_dim = df_dim.dropna(subset=[id_col])
    df_dim['sk'] = range(1, len(df_dim) + 1)
    return df_dim.reset_index(drop=True)

# ==============================
# 📅 Dimensão Tempo
# ==============================
if "data" in df.columns:
    df["data"] = pd.to_datetime(df["data"])
    
    import calendar
    dim_tempo = df[["data"]].drop_duplicates().copy()
    dim_tempo["sk_tempo"] = range(1, len(dim_tempo) + 1)
    dim_tempo["data_referencia"] = dim_tempo["data"]
    dim_tempo["dia"] = dim_tempo["data"].dt.day
    dim_tempo["mes"] = dim_tempo["data"].dt.month
    dim_tempo["nome_mes"] = dim_tempo["data"].dt.month.apply(lambda m: calendar.month_name[m])
    dim_tempo["trimestre"] = dim_tempo["data"].dt.quarter
    dim_tempo["ano"] = dim_tempo["data"].dt.year
    
    dim_tempo = dim_tempo[["sk_tempo", "data_referencia", "dia", "mes", "nome_mes", "trimestre", "ano"]]
    dim_tempo.to_csv(GOLD_DIR / "dim_tempo.csv", index=False)
else:
    print("⚠️  Aviso: coluna 'data' não encontrada em dados_tratados.csv")

# ==============================
# 🌍 Dimensão País Origem
# ==============================
if "id_pais_origem" in df.columns:
    dim_pais_origem = df[[
        "id_pais_origem", "nome_pais_origem", "codigo_iso_pais_origem", "bloco_id_origem"
    ]].copy()
    dim_pais_origem = dim_pais_origem.drop_duplicates(subset=["id_pais_origem"])
    dim_pais_origem = dim_pais_origem.dropna(subset=["id_pais_origem"])
    dim_pais_origem["sk_pais_origem"] = range(1, len(dim_pais_origem) + 1)
    
    # Join com blocos econômicos para obter nome
    try:
        blocos = pd.read_csv(BASE_DIR / "data" / "bronze" / "blocos_economicos.csv")
        blocos = blocos.rename(columns={"id": "bloco_id", "nome": "nome_bloco"})
        dim_pais_origem = dim_pais_origem.merge(blocos, left_on="bloco_id_origem", right_on="bloco_id", how="left")
        dim_pais_origem = dim_pais_origem.rename(columns={"nome_bloco": "bloco_economico_pais_origem"})
    except:
        dim_pais_origem["bloco_economico_pais_origem"] = None
    
    dim_pais_origem = dim_pais_origem[["sk_pais_origem", "id_pais_origem", "nome_pais_origem", 
                                         "codigo_iso_pais_origem", "bloco_economico_pais_origem"]]
    dim_pais_origem.to_csv(GOLD_DIR / "dim_pais_origem.csv", index=False)
else:
    print("⚠️  Aviso: coluna 'id_pais_origem' não encontrada")

# ==============================
# 🌍 Dimensão País Destino
# ==============================
if "id_pais_destino" in df.columns:
    dim_pais_destino = df[[
        "id_pais_destino", "nome_pais_destino", "codigo_iso_pais_destino", "bloco_id_destino"
    ]].copy()
    dim_pais_destino = dim_pais_destino.drop_duplicates(subset=["id_pais_destino"])
    dim_pais_destino = dim_pais_destino.dropna(subset=["id_pais_destino"])
    dim_pais_destino["sk_pais_destino"] = range(1, len(dim_pais_destino) + 1)
    
    # Join com blocos econômicos para obter nome
    try:
        blocos = pd.read_csv(BASE_DIR / "data" / "bronze" / "blocos_economicos.csv")
        blocos = blocos.rename(columns={"id": "bloco_id", "nome": "nome_bloco"})
        dim_pais_destino = dim_pais_destino.merge(blocos, left_on="bloco_id_destino", right_on="bloco_id", how="left")
        dim_pais_destino = dim_pais_destino.rename(columns={"nome_bloco": "bloco_economico_pais_destino"})
    except:
        dim_pais_destino["bloco_economico_pais_destino"] = None
    
    dim_pais_destino = dim_pais_destino[["sk_pais_destino", "id_pais_destino", "nome_pais_destino", 
                                          "codigo_iso_pais_destino", "bloco_economico_pais_destino"]]
    dim_pais_destino.to_csv(GOLD_DIR / "dim_pais_destino.csv", index=False)
else:
    print("⚠️  Aviso: coluna 'id_pais_destino' não encontrada")

# ==============================
# 📦 Dimensão Produto
# ==============================
if "id_produto" in df.columns:
    dim_produto = df[["id_produto"]].drop_duplicates()
    dim_produto = dim_produto.dropna(subset=["id_produto"])
    dim_produto["sk_produto"] = range(1, len(dim_produto) + 1)
    dim_produto["descricao_produto"] = "Produto " + dim_produto["id_produto"].astype(str)
    dim_produto = dim_produto[["sk_produto", "id_produto", "descricao_produto"]]
    dim_produto.to_csv(GOLD_DIR / "dim_produto.csv", index=False)
else:
    print("⚠️  Aviso: coluna 'id_produto' não encontrada")

# ==============================
# 🏷️ Dimensão Categoria Produto
# ==============================
# Criar categoria padrão baseada em produto
if "id_produto" in df.columns:
    dim_categoria = df[["id_produto"]].drop_duplicates()
    dim_categoria["id_categoria_produto"] = dim_categoria["id_produto"] % 5 + 1
    dim_categoria = dim_categoria.drop_duplicates(subset=["id_categoria_produto"])
    dim_categoria["sk_categoria_produto"] = range(1, len(dim_categoria) + 1)
    dim_categoria["descricao_categoria_produto"] = "Categoria " + dim_categoria["id_categoria_produto"].astype(str)
    dim_categoria = dim_categoria[["sk_categoria_produto", "id_categoria_produto", "descricao_categoria_produto"]]
    dim_categoria.to_csv(GOLD_DIR / "dim_categoria_produto.csv", index=False)
else:
    print("⚠️  Aviso: não foi possível criar dimensão de categoria")

# ==============================
# 💰 Dimensão Moeda Origem
# ==============================
if "id_moeda_origem" in df.columns:
    dim_moeda_orig = df[[
        "id_moeda_origem", "descricao_moeda_origem", "pais_moeda_origem"
    ]].copy()
    dim_moeda_orig = dim_moeda_orig.drop_duplicates(subset=["id_moeda_origem"])
    dim_moeda_orig = dim_moeda_orig.dropna(subset=["id_moeda_origem"])
    dim_moeda_orig["sk_moeda_origem"] = range(1, len(dim_moeda_orig) + 1)
    dim_moeda_orig = dim_moeda_orig[["sk_moeda_origem", "id_moeda_origem", "descricao_moeda_origem", "pais_moeda_origem"]]
    dim_moeda_orig.to_csv(GOLD_DIR / "dim_moeda_origem.csv", index=False)
else:
    print("⚠️  Aviso: coluna 'id_moeda_origem' não encontrada")

# ==============================
# 💰 Dimensão Moeda Destino
# ==============================
if "id_moeda_destino" in df.columns:
    dim_moeda_dest = df[[
        "id_moeda_destino", "descricao_moeda_destino", "pais_moeda_destino"
    ]].copy()
    dim_moeda_dest = dim_moeda_dest.drop_duplicates(subset=["id_moeda_destino"])
    dim_moeda_dest = dim_moeda_dest.dropna(subset=["id_moeda_destino"])
    dim_moeda_dest["sk_moeda_destino"] = range(1, len(dim_moeda_dest) + 1)
    dim_moeda_dest = dim_moeda_dest[["sk_moeda_destino", "id_moeda_destino", "descricao_moeda_destino", "pais_moeda_destino"]]
    dim_moeda_dest.to_csv(GOLD_DIR / "dim_moeda_destino.csv", index=False)
else:
    print("⚠️  Aviso: coluna 'id_moeda_destino' não encontrada")

# ==============================
# 🔄 Dimensão Tipo Transação
# ==============================
if "id_tipo_transacao" in df.columns and "descricao_tipo_transacao" in df.columns:
    dim_tipo = df[[
        "id_tipo_transacao", "descricao_tipo_transacao"
    ]].drop_duplicates()
    dim_tipo = dim_tipo.dropna(subset=["id_tipo_transacao"])
    dim_tipo["sk_tipo_transacao"] = range(1, len(dim_tipo) + 1)
    dim_tipo = dim_tipo[["sk_tipo_transacao", "id_tipo_transacao", "descricao_tipo_transacao"]]
    dim_tipo.to_csv(GOLD_DIR / "dim_tipo_transacao.csv", index=False)
else:
    print("⚠️  Aviso: coluna 'descricao_tipo_transacao' não encontrada")

# ==============================
# 🚚 Dimensão Transporte
# ==============================
if "id_transporte" in df.columns and "descricao_transporte" in df.columns:
    dim_transporte = df[[
        "id_transporte", "descricao_transporte"
    ]].drop_duplicates()
    dim_transporte = dim_transporte.dropna(subset=["id_transporte"])
    dim_transporte["sk_transporte"] = range(1, len(dim_transporte) + 1)
    dim_transporte = dim_transporte[["sk_transporte", "id_transporte", "descricao_transporte"]]
    dim_transporte.to_csv(GOLD_DIR / "dim_transporte.csv", index=False)
else:
    print("⚠️  Aviso: coluna 'descricao_transporte' não encontrada")

# ==============================
# ⭐ Fato Transações Internacionais
# ==============================

# Criar mapeamento de SKs
tempo_map = {}
if os.path.exists(GOLD_DIR / "dim_tempo.csv"):
    dt = pd.read_csv(GOLD_DIR / "dim_tempo.csv")
    for _, row in dt.iterrows():
        tempo_map[pd.Timestamp(row["data_referencia"])] = row["sk_tempo"]

pais_orig_map = {}
if os.path.exists(GOLD_DIR / "dim_pais_origem.csv"):
    dp = pd.read_csv(GOLD_DIR / "dim_pais_origem.csv")
    pais_orig_map = dict(zip(dp["id_pais_origem"], dp["sk_pais_origem"]))

pais_dest_map = {}
if os.path.exists(GOLD_DIR / "dim_pais_destino.csv"):
    dp = pd.read_csv(GOLD_DIR / "dim_pais_destino.csv")
    pais_dest_map = dict(zip(dp["id_pais_destino"], dp["sk_pais_destino"]))

produto_map = {}
if os.path.exists(GOLD_DIR / "dim_produto.csv"):
    dp = pd.read_csv(GOLD_DIR / "dim_produto.csv")
    produto_map = dict(zip(dp["id_produto"], dp["sk_produto"]))

categoria_map = {}
if os.path.exists(GOLD_DIR / "dim_categoria_produto.csv"):
    dc = pd.read_csv(GOLD_DIR / "dim_categoria_produto.csv")
    # Mapear produto -> categoria
    for _, row in df.drop_duplicates(subset=["id_produto"]).iterrows():
        cat_id = row["id_produto"] % 5 + 1
        if cat_id in dc["id_categoria_produto"].values:
            categoria_map[row["id_produto"]] = dc[dc["id_categoria_produto"] == cat_id]["sk_categoria_produto"].values[0]

moeda_orig_map = {}
if os.path.exists(GOLD_DIR / "dim_moeda_origem.csv"):
    dm = pd.read_csv(GOLD_DIR / "dim_moeda_origem.csv")
    moeda_orig_map = dict(zip(dm["id_moeda_origem"], dm["sk_moeda_origem"]))

moeda_dest_map = {}
if os.path.exists(GOLD_DIR / "dim_moeda_destino.csv"):
    dm = pd.read_csv(GOLD_DIR / "dim_moeda_destino.csv")
    moeda_dest_map = dict(zip(dm["id_moeda_destino"], dm["sk_moeda_destino"]))

tipo_map = {}
if os.path.exists(GOLD_DIR / "dim_tipo_transacao.csv"):
    dt = pd.read_csv(GOLD_DIR / "dim_tipo_transacao.csv")
    tipo_map = dict(zip(dt["id_tipo_transacao"], dt["sk_tipo_transacao"]))

transporte_map = {}
if os.path.exists(GOLD_DIR / "dim_transporte.csv"):
    dt = pd.read_csv(GOLD_DIR / "dim_transporte.csv")
    transporte_map = dict(zip(dt["id_transporte"], dt["sk_transporte"]))

# Montar a fato
fato = df[[
    "id_transacao",
    "quantidade_transacionada",
    "valor_monetario_transacao",
    "valor_convertido_transacao",
    "taxa_cambio_transacao",
    "data",
    "id_pais_origem",
    "id_pais_destino",
    "id_produto",
    "id_moeda_origem",
    "id_moeda_destino",
    "id_tipo_transacao",
    "id_transporte"
]].copy()

fato = fato.drop_duplicates(subset=["id_transacao"])
fato = fato.dropna(subset=["id_transacao"])

# Aplicar mapeamentos de SK
fato["sk_tempo"] = fato["data"].map(lambda x: tempo_map.get(pd.Timestamp(x), 1) if pd.notna(x) else 1)
fato["sk_pais_origem"] = fato["id_pais_origem"].map(lambda x: pais_orig_map.get(x, 1))
fato["sk_pais_destino"] = fato["id_pais_destino"].map(lambda x: pais_dest_map.get(x, 1))
fato["sk_produto"] = fato["id_produto"].map(lambda x: produto_map.get(x, 1))
fato["sk_categoria_produto"] = fato["id_produto"].map(lambda x: categoria_map.get(x, 1))
fato["sk_moeda_origem"] = fato["id_moeda_origem"].map(lambda x: moeda_orig_map.get(x, 1))
fato["sk_moeda_destino"] = fato["id_moeda_destino"].map(lambda x: moeda_dest_map.get(x, 1))
fato["sk_tipo_transacao"] = fato["id_tipo_transacao"].map(lambda x: tipo_map.get(x, 1))
fato["sk_transporte"] = fato["id_transporte"].map(lambda x: transporte_map.get(x, 1))

# Selecionar colunas finais
fato_final = fato[[
    "id_transacao",
    "quantidade_transacionada",
    "valor_monetario_transacao",
    "valor_convertido_transacao",
    "taxa_cambio_transacao",
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

fato_final.to_csv(GOLD_DIR / "fato_transacoes_internacionais.csv", index=False)

print("🚀 Data Warehouse carregado!")
print(f"📊 Registros na fato: {len(fato_final)}")
print(f"📁 Arquivos gerados em: {GOLD_DIR}")