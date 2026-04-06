import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# 📥 Carregar dados do DW (GOLD)
# ==============================
fato = pd.read_csv("../data/gold/fato_transacoes.csv")
dim_tempo = pd.read_csv("../data/gold/dim_tempo.csv")
dim_pais = pd.read_csv("../data/gold/dim_pais.csv")
dim_produto = pd.read_csv("../data/gold/dim_produto.csv")

# ==============================
# 🔗 JOIN para análise
# ==============================
df = fato.merge(dim_tempo, on="data", how="left") \
         .merge(dim_pais, on="id_pais", how="left") \
         .merge(dim_produto, on="id_produto", how="left")

# ==============================
# 📊 KPIs (painel executivo)
# ==============================
valor_total = df["valor"].sum()
quantidade_total = df["quantidade"].sum()
total_transacoes = df["id_transacao"].count()
ticket_medio = df["valor"].mean()

print("===== KPIs =====")
print(f"Valor Total: {valor_total}")
print(f"Quantidade Total: {quantidade_total}")
print(f"Total de Transações: {total_transacoes}")
print(f"Ticket Médio: {ticket_medio}")

# ==============================
# 📈 1. Evolução das transações
# ==============================
df.groupby("ano")["valor"].sum().plot()

plt.title("Evolução do Valor das Transações")
plt.xlabel("Ano")
plt.ylabel("Valor Total")
plt.show()

# ==============================
# 🌍 2. Top países
# ==============================
df.groupby("nome")["valor"].sum().sort_values(ascending=False).head(10).plot(kind="bar")

plt.title("Top 10 Países por Valor de Transações")
plt.xlabel("País")
plt.ylabel("Valor Total")
plt.xticks(rotation=45)
plt.show()

# ==============================
# 📦 3. Produtos mais vendidos
# ==============================
df.groupby("descricao")["quantidade"].sum().sort_values(ascending=False).head(10).plot(kind="bar")

plt.title("Top 10 Produtos por Quantidade")
plt.xlabel("Produto")
plt.ylabel("Quantidade")
plt.xticks(rotation=45)
plt.show()

# ==============================
# 💰 4. Impacto cambial
# ==============================
df.groupby("ano")[["valor", "valor_convertido"]].sum().plot()

plt.title("Impacto da Variação Cambial")
plt.xlabel("Ano")
plt.ylabel("Valores")
plt.show()