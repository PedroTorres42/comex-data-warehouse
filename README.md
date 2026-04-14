# comex-data-warehouse

Projeto acadêmico de Data Warehouse para comércio internacional, com pipeline completo de ETL e camada de análises em Python.

## Visão Geral do Processo

O fluxo do projeto segue 4 etapas:

1. Extração (`etl/extracao.py`)

- Conecta no banco de origem.
- Extrai tabelas transacionais.
- Salva os dados brutos em CSV na camada bronze (`data/bronze/`).

2. Transformação (`etl/transformacao.py`)

- Carrega arquivos da camada bronze.
- Limpa e padroniza dados.
- Constrói dimensões e fato no modelo estrela em memória.

3. Carga (`etl/carga_dw.py`)

- Conecta no banco do DW.
- Cria/recria o schema com base em `dw/modelo_estrela.sql`.
- Insere dimensões e tabela fato.

4. Análises (`analises/analises.py`)

- Conecta no DW.
- Exibe menu interativo de gráficos e visões analíticas.

Também existe um orquestrador principal (`main.py`) que executa o pipeline completo em sequência.

## Estrutura do Projeto

```text
main.py
etl/
	extracao.py
	transformacao.py
	carga_dw.py
analises/
	analises.py
dw/
	modelo_estrela.sql
data/
	bronze/
```

## Pré-requisitos

- Python 3.10+ (recomendado)
- Acesso ao banco de origem (extração)
- Acesso ao banco de destino (DW)

## Instalação (sem uv)

1. Criar ambiente virtual:

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS (bash/zsh):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instalar dependências:

```bash
pip install -r requirements.txt
```

## Configuração de Ambiente

Crie um arquivo `.env` na raiz com as variáveis abaixo.

### Banco de extração

- `EXTRACAO_DB_HOST`
- `EXTRACAO_DB_PORT`
- `EXTRACAO_DB_USER`
- `EXTRACAO_DB_PASSWORD`
- `EXTRACAO_DB_NAME`
- `EXTRACAO_DB_SSL_CA` (opcional)

### Banco de Data Warehouse

- `DW_DB_SERVICE_URI`

Exemplo de URI:

```text
mysql://usuario:senha@host:3306/nome_do_banco
```

## Como Rodar

### Pipeline completo (extração + transformação + carga + análise)

```bash
python main.py
```

### Pipeline com análise automática específica

```bash
python main.py --analise-opcao 6
```

Opções de análise: `1` a `6`.

Sem `--analise-opcao`, o `main.py` abre a análise em modo interativo e aguarda sua digitação.

### Abrir menu interativo de análise no final do pipeline

```bash
python main.py --analise-interativa
```

### Rodar etapas isoladas

```bash
python etl/extracao.py
python etl/transformacao.py
python etl/carga_dw.py
python analises/analises.py
```

### Carga incremental no banco de origem (sem recriar tabelas)

Para inserir novos dados a partir de CSV no banco de origem sem `DROP TABLE`:

```bash
python etl/carga_origem_incremental.py
```

Opções úteis:

```bash
# apenas inserir novos (ignora duplicados)
python etl/carga_origem_incremental.py --mode insert-ignore

# processar só algumas tabelas
python etl/carga_origem_incremental.py --tables cambios transacoes

# usar outro diretório de CSV (ex.: amostras)
python etl/carga_origem_incremental.py --csv-dir data/bronze_sample
```

## Exemplo de inserção segura no CSV(transacoes.csv)

```csv
100001,2,1,5,1,125000.50,80,1,1
```

## Observações

- A carga do DW recria tabelas do modelo estrela antes de inserir dados.
- Se faltar variável no `.env`, os scripts interrompem com mensagem de validação.
