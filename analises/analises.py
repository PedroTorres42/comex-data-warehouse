import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# 📥 Carregar dados do DW
# ==============================
fato = pd.read_csv("../data/gold/fato_transacoes.csv")
dim_tempo = pd.read_csv("../data/gold/dim_tempo.csv")
dim_pais_destino = pd.read_csv("../data/gold/dim_pais_destino.csv")
dim_produto = pd.read_csv("../data/gold/dim_produto.csv")

# ==============================
# 🔗 JOIN (USANDO SK)
# ==============================
df = fato.merge(dim_tempo, on="sk_tempo", how="left") \
         .merge(dim_pais_destino, on="sk_pais_destino", how="left") \
         .merge(dim_produto, on="sk_produto", how="left")

# ==============================
# 📊 KPIs
# ==============================
valor_total = df["valor_convertido"].sum()
quantidade_total = df["quantidade"].sum()
total_transacoes = len(df)
ticket_medio = df["valor_convertido"].mean()

# ==============================
# 🎨 CONFIG DASHBOARD
# ==============================
plt.figure(figsize=(18, 10))
plt.suptitle("🌎 Dashboard - Comércio Exterior", fontsize=18)

# ==============================
# 🧾 KPI VISUAL
# ==============================
plt.subplot(2, 2, 1)
plt.axis("off")

kpi_text = f"""
💰 Valor Total: {valor_total:,.2f}

📦 Quantidade Total: {quantidade_total}

🔢 Total de Transações: {total_transacoes}

🎯 Ticket Médio: {ticket_medio:,.2f}
"""

plt.text(0.1, 0.5, kpi_text, fontsize=14)

# ==============================
# 📈 Evolução Temporal
# ==============================
plt.subplot(2, 2, 2)

df.groupby(["ano", "mes"])["valor_convertido"].sum().unstack().plot(ax=plt.gca())

plt.title("Evolução das Transações")
plt.xlabel("Ano")
plt.ylabel("Valor Convertido")

# ==============================
# 🌍 Top Países Destino
# ==============================
plt.subplot(2, 2, 3)

df.groupby("nome_pais_destino")["valor_convertido"] \
  .sum().sort_values(ascending=False).head(10).plot(kind="bar", ax=plt.gca())

plt.title("Top 10 Países Destino")
plt.xticks(rotation=45)

# ==============================
# 📦 Top Produtos
# ==============================
plt.subplot(2, 2, 4)

df.groupby("descricao_produto")["quantidade"] \
  .sum().sort_values(ascending=False).head(10).plot(kind="bar", ax=plt.gca())

plt.title("Top 10 Produtos")
plt.xticks(rotation=45)

# ==============================
# 🚀 Ajuste e exibição
# ==============================
plt.tight_layout()
plt.show()