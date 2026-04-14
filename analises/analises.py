from pathlib import Path
from decimal import Decimal
from urllib.parse import parse_qs, unquote, urlparse

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter
import mysql.connector
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
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


def _connect_dw():
  connection_kwargs = _get_connection_kwargs()
  if not connection_kwargs:
    raise ValueError("Defina DW_DB_SERVICE_URI no arquivo .env antes de executar as analises.")
  return mysql.connector.connect(**connection_kwargs)


def _query_df(conexao, query):
  cursor = conexao.cursor()
  cursor.execute(query)
  rows = cursor.fetchall()
  columns = [desc[0] for desc in cursor.description]
  cursor.close()
  df = pd.DataFrame(rows, columns=columns)
  if df.empty:
    return df
  return df.apply(lambda col: col.map(lambda v: float(v) if isinstance(v, Decimal) else v))


def _format_valor_eixo(valor, _):
  return f"{valor:,.0f}".replace(",", ".")


def _set_value_axis(ax, values, axis="y"):
  if len(values) == 0:
    return
  max_val = float(max(values))
  upper = max_val * 1.15 if max_val > 0 else 1
  if axis == "y":
    ax.set_ylim(0, upper)
    ax.yaxis.set_major_formatter(FuncFormatter(_format_valor_eixo))
  else:
    ax.set_xlim(0, upper)
    ax.xaxis.set_major_formatter(FuncFormatter(_format_valor_eixo))


def _set_comparative_axis(ax, values, axis="x"):
  if len(values) == 0:
    return
  min_val = float(min(values))
  max_val = float(max(values))
  if min_val == max_val:
    min_val *= 0.95
    max_val *= 1.05
  lower = min_val * 0.95 if min_val > 0 else 0
  upper = max_val * 1.05 if max_val > 0 else 1

  if axis == "x":
    ax.set_xlim(lower, upper)
    ax.xaxis.set_major_formatter(FuncFormatter(_format_valor_eixo))
  else:
    ax.set_ylim(lower, upper)
    ax.yaxis.set_major_formatter(FuncFormatter(_format_valor_eixo))


def _annotate_barh_values(ax, df, value_col):
  max_val = float(df[value_col].max()) if len(df) else 1
  for i, value in enumerate(df[value_col]):
    ax.text(value + max_val * 0.005, i, _format_valor_eixo(value, None), va="center", fontsize=9)


def _format_moeda(valor):
  return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def visao_temporal(conexao):
  df_mes = _query_df(
    conexao,
    """
    SELECT t.ano, t.mes, SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo
    GROUP BY t.ano, t.mes
    ORDER BY t.ano, t.mes
    """,
  )
  df_tri = _query_df(
    conexao,
    """
    SELECT t.ano, t.trimestre, SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo
    GROUP BY t.ano, t.trimestre
    ORDER BY t.ano, t.trimestre
    """,
  )
  df_ano = _query_df(
    conexao,
    """
    SELECT t.ano, SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo
    GROUP BY t.ano
    ORDER BY t.ano
    """,
  )

  plt.figure(figsize=(16, 10))

  ax1 = plt.subplot(3, 1, 1)
  labels_mes = df_mes.apply(lambda r: f"{int(r['ano'])}-{int(r['mes']):02d}", axis=1)
  ax1.plot(labels_mes, df_mes["valor_total"], marker="o")
  ax1.set_title("Evolucao Mensal do Valor Financeiro")
  ax1.set_xlabel("Periodo (Ano-Mes)")
  ax1.set_ylabel("Valor Total Movimentado")
  _set_value_axis(ax1, df_mes["valor_total"], axis="y")
  ax1.tick_params(axis="x", rotation=45)

  ax2 = plt.subplot(3, 1, 2)
  labels_tri = df_tri.apply(lambda r: f"{int(r['ano'])}-T{int(r['trimestre'])}", axis=1)
  ax2.bar(labels_tri, df_tri["valor_total"])
  ax2.set_title("Evolucao Trimestral do Valor Financeiro")
  ax2.set_xlabel("Periodo (Ano-Trimestre)")
  ax2.set_ylabel("Valor Total Movimentado")
  _set_value_axis(ax2, df_tri["valor_total"], axis="y")
  ax2.tick_params(axis="x", rotation=45)

  ax3 = plt.subplot(3, 1, 3)
  ax3.plot(df_ano["ano"].astype(str), df_ano["valor_total"], marker="o", linewidth=2)
  ax3.set_title("Evolucao Anual do Valor Financeiro")
  ax3.set_xlabel("Ano")
  ax3.set_ylabel("Valor Total Movimentado")
  _set_value_axis(ax3, df_ano["valor_total"], axis="y")

  plt.tight_layout()
  plt.show()


def visao_paises(conexao):
  origem = _query_df(
    conexao,
    """
    SELECT p.nome_pais_origem AS pais, SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_pais_origem p ON f.sk_pais_origem = p.sk_pais_origem
    GROUP BY p.nome_pais_origem
    ORDER BY valor_total DESC
    LIMIT 10
    """,
  )
  destino = _query_df(
    conexao,
    """
    SELECT p.nome_pais_destino AS pais, SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_pais_destino p ON f.sk_pais_destino = p.sk_pais_destino
    GROUP BY p.nome_pais_destino
    ORDER BY valor_total DESC
    LIMIT 10
    """,
  )

  plt.figure(figsize=(16, 10))

  origem_total = float(origem["valor_total"].sum()) if len(origem) else 1
  destino_total = float(destino["valor_total"].sum()) if len(destino) else 1
  origem["participacao_pct"] = origem["valor_total"] / origem_total * 100
  destino["participacao_pct"] = destino["valor_total"] / destino_total * 100

  ax1 = plt.subplot(2, 1, 1)
  ax1.barh(origem["pais"], origem["valor_total"])
  ax1.set_title("Top 10 Paises de Origem por Valor")
  ax1.set_xlabel("Valor Total Movimentado")
  ax1.set_ylabel("Pais de Origem")
  _set_comparative_axis(ax1, origem["valor_total"], axis="x")
  ax1.invert_yaxis()
  ax1.grid(axis="x", linestyle="--", alpha=0.4)
  _annotate_barh_values(ax1, origem, "valor_total")

  ax1_pct = ax1.twiny()
  ax1_pct.set_xlim(0, 100)
  ax1_pct.set_xlabel("Participacao no Top 10 de Origem (%)")
  ax1_pct.plot(origem["participacao_pct"], origem["pais"], alpha=0)

  ax2 = plt.subplot(2, 1, 2)
  ax2.barh(destino["pais"], destino["valor_total"], color="orange")
  ax2.set_title("Top 10 Paises de Destino por Valor")
  ax2.set_xlabel("Valor Total Movimentado")
  ax2.set_ylabel("Pais de Destino")
  _set_comparative_axis(ax2, destino["valor_total"], axis="x")
  ax2.invert_yaxis()
  ax2.grid(axis="x", linestyle="--", alpha=0.4)
  _annotate_barh_values(ax2, destino, "valor_total")

  ax2_pct = ax2.twiny()
  ax2_pct.set_xlim(0, 100)
  ax2_pct.set_xlabel("Participacao no Top 10 de Destino (%)")
  ax2_pct.plot(destino["participacao_pct"], destino["pais"], alpha=0)

  plt.tight_layout()
  plt.show()


def visao_blocos(conexao):
  blocos = _query_df(
    conexao,
    """
    SELECT bloco, SUM(valor_total) AS valor_total
    FROM (
      SELECT p.bloco_economico_pais_origem AS bloco, f.valor_convertido_transacao AS valor_total
      FROM fato_transacoes_internacionais f
      JOIN dim_pais_origem p ON f.sk_pais_origem = p.sk_pais_origem
      UNION ALL
      SELECT p.bloco_economico_pais_destino AS bloco, f.valor_convertido_transacao AS valor_total
      FROM fato_transacoes_internacionais f
      JOIN dim_pais_destino p ON f.sk_pais_destino = p.sk_pais_destino
    ) base
    WHERE bloco IS NOT NULL AND bloco <> ''
    GROUP BY bloco
    ORDER BY valor_total DESC
    """,
  )

  plt.figure(figsize=(12, 6))
  plt.bar(blocos["bloco"], blocos["valor_total"], color="teal")
  plt.title("Valor Financeiro por Bloco Economico")
  plt.xlabel("Bloco Economico")
  plt.ylabel("Valor Total Movimentado")
  _set_value_axis(plt.gca(), blocos["valor_total"], axis="y")
  plt.xticks(rotation=45, ha="right")
  plt.tight_layout()
  plt.show()


def visao_produto_categoria(conexao):
  produtos = _query_df(
    conexao,
    """
    SELECT p.descricao_produto,
           SUM(f.quantidade_transacionada) AS quantidade_total,
           SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_produto p ON f.sk_produto = p.sk_produto
    GROUP BY p.descricao_produto
    ORDER BY valor_total DESC
    LIMIT 10
    """,
  )
  categorias = _query_df(
    conexao,
    """
    SELECT c.descricao_categoria_produto,
           SUM(f.quantidade_transacionada) AS quantidade_total,
           SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_categoria_produto c ON f.sk_categoria_produto = c.sk_categoria_produto
    GROUP BY c.descricao_categoria_produto
    ORDER BY valor_total DESC
    """,
  )

  plt.figure(figsize=(16, 10))

  produtos_total = float(produtos["valor_total"].sum()) if len(produtos) else 1
  categorias_total = float(categorias["quantidade_total"].sum()) if len(categorias) else 1
  produtos["participacao_pct"] = produtos["valor_total"] / produtos_total * 100
  categorias["participacao_pct"] = categorias["quantidade_total"] / categorias_total * 100

  ax1 = plt.subplot(2, 1, 1)
  ax1.barh(produtos["descricao_produto"], produtos["valor_total"], color="slateblue")
  ax1.set_title("Top Produtos por Valor Movimentado")
  ax1.set_xlabel("Valor Total Movimentado")
  ax1.set_ylabel("Produto")
  _set_comparative_axis(ax1, produtos["valor_total"], axis="x")
  ax1.invert_yaxis()
  ax1.grid(axis="x", linestyle="--", alpha=0.4)
  _annotate_barh_values(ax1, produtos, "valor_total")

  ax1_pct = ax1.twiny()
  ax1_pct.set_xlim(0, 100)
  ax1_pct.set_xlabel("Participacao no Top 10 de Produtos (%)")
  ax1_pct.plot(produtos["participacao_pct"], produtos["descricao_produto"], alpha=0)

  ax2 = plt.subplot(2, 1, 2)
  ax2.barh(categorias["descricao_categoria_produto"], categorias["quantidade_total"], color="seagreen")
  ax2.set_title("Categorias por Quantidade Negociada")
  ax2.set_xlabel("Quantidade Total Negociada")
  ax2.set_ylabel("Categoria de Produto")
  _set_comparative_axis(ax2, categorias["quantidade_total"], axis="x")
  ax2.invert_yaxis()
  ax2.grid(axis="x", linestyle="--", alpha=0.4)
  _annotate_barh_values(ax2, categorias, "quantidade_total")

  ax2_pct = ax2.twiny()
  ax2_pct.set_xlim(0, 100)
  ax2_pct.set_xlabel("Participacao por Categoria (%)")
  ax2_pct.plot(categorias["participacao_pct"], categorias["descricao_categoria_produto"], alpha=0)

  plt.tight_layout()
  plt.show()


def visao_cambial(conexao):
  moedas = _query_df(
    conexao,
    """
    SELECT m.descricao_moeda_origem AS moeda,
           AVG(f.taxa_cambio_transacao) AS taxa_media,
           SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_moeda_origem m ON f.sk_moeda_origem = m.sk_moeda_origem
    GROUP BY m.descricao_moeda_origem
    ORDER BY valor_total DESC
    LIMIT 10
    """,
  )
  tempo_cambio = _query_df(
    conexao,
    """
    SELECT t.ano,
           t.mes,
           AVG(f.taxa_cambio_transacao) AS taxa_media,
           SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo
    GROUP BY t.ano, t.mes
    ORDER BY t.ano, t.mes
    """,
  )

  plt.figure(figsize=(14, 12))

  ax1 = plt.subplot(3, 1, 1)
  ax1.bar(moedas["moeda"], moedas["valor_total"], color="crimson", alpha=0.8, label="Valor Total")
  ax1.set_title("Impacto Cambial por Moeda")
  ax1.set_xlabel("Moeda")
  ax1.set_ylabel("Valor Total Movimentado")
  _set_value_axis(ax1, moedas["valor_total"], axis="y")
  max_valor = float(moedas["valor_total"].max()) if len(moedas) else 1.0
  ax1.set_ylim(0, max_valor * 1.35)
  ax1.tick_params(axis="x", rotation=35)
  ax1.grid(axis="y", linestyle="--", alpha=0.4)

  ax1_taxa = ax1.twinx()
  ax1_taxa.plot(
    moedas["moeda"],
    moedas["taxa_media"],
    color="navy",
    marker="o",
    linewidth=2,
    label="Taxa Cambial Media",
  )
  ax1_taxa.set_ylabel("Taxa Cambial Media")

  bars_legend, bars_labels = ax1.get_legend_handles_labels()
  line_legend, line_labels = ax1_taxa.get_legend_handles_labels()
  ax1.legend(
    bars_legend + line_legend,
    bars_labels + line_labels,
    loc="upper right",
    ncol=2,
    frameon=True,
  )

  ax2 = plt.subplot(3, 1, 2)
  labels = tempo_cambio.apply(lambda r: f"{int(r['ano'])}-{int(r['mes']):02d}", axis=1)
  ax2.plot(labels, tempo_cambio["taxa_media"], marker="o", color="royalblue")
  ax2.set_title("Evolucao Mensal da Taxa Cambial Media")
  ax2.set_xlabel("Periodo (Ano-Mes)")
  ax2.set_ylabel("Taxa Cambial Media")
  ax2.tick_params(axis="x", rotation=45)
  ax2.grid(axis="y", linestyle="--", alpha=0.4)

  ax3 = plt.subplot(3, 1, 3)
  ax3.plot(labels, tempo_cambio["valor_total"], marker="o", color="darkorange")
  ax3.set_title("Evolucao Mensal do Valor Total Movimentado")
  ax3.set_xlabel("Periodo (Ano-Mes)")
  ax3.set_ylabel("Valor Total Movimentado")
  _set_value_axis(ax3, tempo_cambio["valor_total"], axis="y")
  ax3.tick_params(axis="x", rotation=45)
  ax3.grid(axis="y", linestyle="--", alpha=0.4)

  plt.subplots_adjust(hspace=0.85, top=0.95, bottom=0.08)
  plt.show()


def visao_executiva(conexao):
  kpis = _query_df(
    conexao,
    """
    SELECT
      SUM(f.valor_convertido_transacao) AS valor_total,
      SUM(f.quantidade_transacionada) AS quantidade_total,
      AVG(f.valor_convertido_transacao) AS ticket_medio,
      COUNT(*) AS total_transacoes
    FROM fato_transacoes_internacionais f
    """,
  ).iloc[0]

  serie_mensal = _query_df(
    conexao,
    """
    SELECT t.ano,
           t.mes,
           SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_tempo t ON f.sk_tempo = t.sk_tempo
    GROUP BY t.ano, t.mes
    ORDER BY t.ano, t.mes
    """,
  )

  top_paises = _query_df(
    conexao,
    """
    SELECT p.nome_pais_destino AS pais, SUM(f.valor_convertido_transacao) AS valor_total
    FROM fato_transacoes_internacionais f
    JOIN dim_pais_destino p ON f.sk_pais_destino = p.sk_pais_destino
    GROUP BY p.nome_pais_destino
    ORDER BY valor_total DESC
    LIMIT 5
    """,
  )
  top_paises["pais"] = top_paises["pais"].replace({"Emirados Arabes Unidos": "Emirados Arabes"})

  serie_mensal["periodo"] = pd.to_datetime(
    serie_mensal["ano"].astype(int).astype(str) + "-" + serie_mensal["mes"].astype(int).astype(str).str.zfill(2) + "-01"
  )
  variacao_pct = 0.0
  ultimo_valor = float(serie_mensal["valor_total"].iloc[-1]) if len(serie_mensal) else 0.0
  if len(serie_mensal) >= 2:
    valor_anterior = float(serie_mensal["valor_total"].iloc[-2])
    if valor_anterior != 0:
      variacao_pct = (ultimo_valor - valor_anterior) / valor_anterior * 100

  total_top5 = float(top_paises["valor_total"].sum()) if len(top_paises) else 1.0
  top_paises["participacao_pct"] = top_paises["valor_total"] / total_top5 * 100

  fig = plt.figure(figsize=(16, 9), facecolor="white")
  fig.suptitle("Resumo Executivo do Comercio Internacional", fontsize=16, fontweight="bold", y=0.98)
  gs = GridSpec(3, 4, figure=fig, height_ratios=[1.0, 1.6, 1.6], hspace=0.75, wspace=0.55)

  card_bg = "#f4f7fb"
  card_edge = "#d8e1ef"
  cards = [
    ("Valor Total", _format_moeda(float(kpis["valor_total"]))),
    ("Quantidade Total", _format_valor_eixo(float(kpis["quantidade_total"]), None)),
    ("Ticket Medio", _format_moeda(float(kpis["ticket_medio"]))),
    ("Total de Transacoes", _format_valor_eixo(float(kpis["total_transacoes"]), None)),
  ]

  for idx, (titulo, valor) in enumerate(cards):
    card_ax = fig.add_subplot(gs[0, idx])
    card_ax.set_facecolor(card_bg)
    for spine in card_ax.spines.values():
      spine.set_visible(True)
      spine.set_color(card_edge)
      spine.set_linewidth(1.1)
    card_ax.set_xticks([])
    card_ax.set_yticks([])
    card_ax.text(0.04, 0.78, titulo, fontsize=10, color="#425466", transform=card_ax.transAxes)
    card_ax.text(0.04, 0.36, valor, fontsize=14, fontweight="bold", color="#0f2742", transform=card_ax.transAxes)

  ax_rank = fig.add_subplot(gs[1:, :2])
  ax_rank.barh(top_paises["pais"], top_paises["valor_total"], color="#ff8f3d", alpha=0.9)
  ax_rank.set_title("Top 5 Paises de Destino", fontsize=12, fontweight="bold")
  ax_rank.set_xlabel("Valor Total Movimentado")
  ax_rank.set_ylabel("Pais")
  _set_comparative_axis(ax_rank, top_paises["valor_total"], axis="x")
  ax_rank.invert_yaxis()
  ax_rank.grid(axis="x", linestyle="--", alpha=0.35)
  for i, row in top_paises.reset_index(drop=True).iterrows():
    label = f"{_format_valor_eixo(row['valor_total'], None)} ({row['participacao_pct']:.1f}%)"
    ax_rank.text(float(row["valor_total"]) * 1.005, i, label, va="center", fontsize=9, color="#2f3b52")

  ax_trend = fig.add_subplot(gs[1:, 2:])
  ax_trend.plot(serie_mensal["periodo"], serie_mensal["valor_total"], marker="o", linewidth=2.3, color="#1f5f8b")
  ax_trend.fill_between(serie_mensal["periodo"], serie_mensal["valor_total"], alpha=0.12, color="#1f5f8b")
  ax_trend.set_title("Tendencia Mensal de Valor", fontsize=12, fontweight="bold")
  ax_trend.set_xlabel("Periodo (Ano-Mes)")
  ax_trend.set_ylabel("Valor Total Movimentado")
  _set_value_axis(ax_trend, serie_mensal["valor_total"], axis="y")
  ax_trend.grid(axis="y", linestyle="--", alpha=0.35)
  ax_trend.xaxis.set_major_locator(mdates.YearLocator())
  ax_trend.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
  ax_trend.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(1, 7)))
  ax_trend.tick_params(axis="x", rotation=0)

  if len(serie_mensal):
    delta_cor = "#1f8b4c" if variacao_pct >= 0 else "#b42318"
    sinal = "+" if variacao_pct >= 0 else ""
    resumo = f"Ultimo mes: {_format_moeda(ultimo_valor)}\nVariacao: {sinal}{variacao_pct:.1f}% vs mes anterior"
    ax_trend.text(
      0.02,
      0.96,
      resumo,
      transform=ax_trend.transAxes,
      va="top",
      fontsize=10,
      color=delta_cor,
      bbox={"facecolor": "white", "edgecolor": "#d9d9d9", "boxstyle": "round,pad=0.35"},
    )

  plt.subplots_adjust(top=0.90, bottom=0.11, left=0.08, right=0.97)
  plt.show()


def _print_menu():
  print("\n=== MENU DE ANALISES BI ===")
  print("1 - Evolucao financeira no tempo (mensal, trimestral, anual)")
  print("2 - Paises que mais movimentam operacoes")
  print("3 - Blocos economicos com maior valor")
  print("4 - Desempenho por produto e categoria")
  print("5 - Impacto da variacao cambial")
  print("6 - Visao executiva consolidada (KPIs)")
  print("0 - Sair")


def main():
  conexao = _connect_dw()
  try:
    while True:
      _print_menu()
      opcao = input("Escolha uma opcao: ").strip()

      if opcao == "1":
        visao_temporal(conexao)
      elif opcao == "2":
        visao_paises(conexao)
      elif opcao == "3":
        visao_blocos(conexao)
      elif opcao == "4":
        visao_produto_categoria(conexao)
      elif opcao == "5":
        visao_cambial(conexao)
      elif opcao == "6":
        visao_executiva(conexao)
      elif opcao == "0":
        print("Encerrando analises.")
        break
      else:
        print("Opcao invalida. Escolha um numero do menu.")
  finally:
    conexao.close()


if __name__ == "__main__":
  main()