#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar o Data Warehouse no MySQL e carregar dados do CSV
Uso: python criar_mysql_dw.py
"""

import mysql.connector
from mysql.connector import errorcode
import pandas as pd
import os
from pathlib import Path
import sys

# ==============================
# ⚙️ Configurações
# ==============================

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = "comex_dw"

BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = BASE_DIR / "data" / "gold"
DW_DIR = BASE_DIR / "dw"

# ==============================
# 🔄 Funções
# ==============================

def conectar_mysql():
    """Conecta ao MySQL"""
    try:
        conexao = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print(f"✅ Conectado ao MySQL em {DB_HOST}:{DB_PORT}")
        return conexao
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("❌ Erro: Usuário ou senha incorretos")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("❌ Erro: Banco de dados não existe")
        else:
            print(f"❌ Erro ao conectar: {err}")
        sys.exit(1)

def criar_schema(conexao):
    """Cria o schema (banco + tabelas)"""
    cursor = conexao.cursor()
    
    try:
        print("\n📋 Criando schema do Data Warehouse...")
        
        schema_path = DW_DIR / "criar_dw.sql"
        if not schema_path.exists():
            print(f"❌ Erro: schema não encontrado em {schema_path}")
            return False

        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()

        # Permite parametrizar o nome do banco via variável de ambiente.
        sql = sql.replace("comex_dw", DB_NAME)

        for _ in cursor.execute(sql, multi=True):
            pass
        
        conexao.commit()
        print("✅ Schema criado com sucesso!")
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Erro ao criar schema: {err}")
        conexao.rollback()
        return False
    finally:
        cursor.close()

def carregar_dados(conexao):
    """Carrega dados do CSV para as dimensões e fato"""
    cursor = conexao.cursor()
    
    try:
        print("\n📊 Carregando dados no Data Warehouse...\n")
        
        # Lista de arquivos e suas tabelas
        tabelas = {
            "dim_tempo.csv": "dim_tempo",
            "dim_pais_origem.csv": "dim_pais_origem",
            "dim_pais_destino.csv": "dim_pais_destino",
            "dim_produto.csv": "dim_produto",
            "dim_categoria_produto.csv": "dim_categoria_produto",
            "dim_moeda_origem.csv": "dim_moeda_origem",
            "dim_moeda_destino.csv": "dim_moeda_destino",
            "dim_tipo_transacao.csv": "dim_tipo_transacao",
            "dim_transporte.csv": "dim_transporte",
            "fato_transacoes_internacionais.csv": "fato_transacoes_internacionais",
        }
        
        for arquivo, tabela in tabelas.items():
            caminho = GOLD_DIR / arquivo
            
            if not caminho.exists():
                print(f"⚠️  Arquivo não encontrado: {arquivo}, pulando...")
                continue
            
            try:
                df = pd.read_csv(caminho)
                registros = len(df)
                
                # Inserir dados linha por linha (seguro para FK)
                for _, row in df.iterrows():
                    colunas = ', '.join(f"`{col}`" for col in df.columns)
                    placeholders = ', '.join(['%s'] * len(df.columns))
                    sql = f"INSERT INTO {tabela} ({colunas}) VALUES ({placeholders})"
                    
                    valores = tuple(
                        None if pd.isna(v) else v 
                        for v in row.values
                    )
                    
                    cursor.execute(sql, valores)
                
                conexao.commit()
                print(f"✅ {tabela:40} - {registros:6} registros carregados")
                
            except Exception as e:
                print(f"❌ Erro ao carregar {arquivo}: {e}")
                conexao.rollback()
        
        print("\n✅ Dados carregados com sucesso!")
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Erro ao carregar dados: {err}")
        conexao.rollback()
        return False
    finally:
        cursor.close()

def validar_criacao(conexao):
    """Valida a criação do DW"""
    cursor = conexao.cursor()
    
    try:
        print("\n📋 Validando estrutura do Data Warehouse...\n")
        
        cursor.execute(f"USE {DB_NAME}")
        cursor.execute("SHOW TABLES")
        
        tabelas = [row[0] for row in cursor.fetchall()]
        
        print(f"Banco: {DB_NAME}")
        print(f"Total de tabelas: {len(tabelas)}\n")
        
        for tabela in sorted(tabelas):
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            quantidade = cursor.fetchone()[0]
            print(f"  • {tabela:40} - {quantidade:8} registros")
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Erro na validação: {err}")
        return False
    finally:
        cursor.close()

# ==============================
# 🚀 Execução Principal
# ==============================

def main():
    """Executa o pipeline completo"""
    
    print("\n" + "="*60)
    print("🏗️  CRIADOR DE DATA WAREHOUSE - MYSQL")
    print("="*60)
    
    # Conectar
    conexao = conectar_mysql()
    
    # Criar schema
    if not criar_schema(conexao):
        conexao.close()
        sys.exit(1)
    
    # Selecionar banco
    conexao.database = DB_NAME
    
    # Carregar dados
    if not carregar_dados(conexao):
        conexao.close()
        sys.exit(1)
    
    # Validar
    if not validar_criacao(conexao):
        conexao.close()
        sys.exit(1)
    
    conexao.close()
    
    print("\n" + "="*60)
    print("🎉 Data Warehouse criado e carregado com sucesso!")
    print("="*60)
    print(f"\n📍 Banco: mysql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"📊 Dimensões + Fato carregadas")
    print(f"📈 Pronto para análises!\n")

if __name__ == "__main__":
    main()
