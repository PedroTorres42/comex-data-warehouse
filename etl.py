#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Orquestrador ETL: Extração → Transformação → Carga
Executa todo o pipeline de dados (Bronze → Silver → Gold)
"""

import sys
import importlib.util
from pathlib import Path

# Configurar base directory
BASE_DIR = Path(__file__).resolve().parent
ETL_DIR = BASE_DIR / "etl"

# ==============================
# 🔄 Funções auxiliares
# ==============================

def executar_modulo(nome_arquivo, descricao):
    """
    Executa um módulo Python do diretório etl/
    
    Args:
        nome_arquivo: Nome do arquivo .py (ex: 'extracao.py')
        descricao: Descrição da etapa (ex: '📥 Extração de dados')
    
    Returns:
        bool: True se sucesso, False se erro
    """
    caminho_arquivo = ETL_DIR / nome_arquivo
    
    if not caminho_arquivo.exists():
        print(f"❌ Erro: {nome_arquivo} não encontrado em {ETL_DIR}")
        return False
    
    print(f"\n{'='*50}")
    print(f"{descricao}")
    print(f"{'='*50}\n")
    
    try:
        # Carregar módulo dinâmico
        spec = importlib.util.spec_from_file_location(
            nome_arquivo.replace('.py', ''),
            caminho_arquivo
        )
        modulo = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = modulo
        spec.loader.exec_module(modulo)
        
        print(f"✅ {descricao} concluída com sucesso!\n")
        return True
        
    except Exception as e:
        print(f"❌ Erro na {descricao}:")
        print(f"   {type(e).__name__}: {str(e)}\n")
        return False

# ==============================
# 🚀 Execução do pipeline
# ==============================

def main():
    """Executa o pipeline completo ETL"""
    
    print("\n" + "="*50)
    print("🔄 INICIANDO PIPELINE ETL")
    print("="*50)
    
    etapas = [
        # ("extracao.py", "📥 Extração de dados"),  # Requer conexão MySQL
        ("transformacao.py", "🔄 Transformação de dados"),
        ("carga_dw.py", "💾 Carga no Data Warehouse"),
    ]
    
    resultados = []
    
    for arquivo, descricao in etapas:
        sucesso = executar_modulo(arquivo, descricao)
        resultados.append((descricao, sucesso))
        
        if not sucesso:
            print(f"⚠️  Pipeline interrompido na etapa: {descricao}")
            break
    
    # Resumo final
    print("\n" + "="*50)
    print("📊 RESUMO DO PIPELINE")
    print("="*50 + "\n")
    
    todas_sucesso = True
    for descricao, sucesso in resultados:
        status = "✅ Sucesso" if sucesso else "❌ Falha"
        print(f"{status} - {descricao}")
        if not sucesso:
            todas_sucesso = False
    
    print("\n" + "="*50)
    if todas_sucesso:
        print("🎉 Pipeline concluído com sucesso!")
        print("📁 Dados disponíveis em:")
        print(f"   Bronze: {BASE_DIR}/data/bronze")
        print(f"   Silver: {BASE_DIR}/data/silver")
        print(f"   Gold:   {BASE_DIR}/data/gold")
        return 0
    else:
        print("❌ Pipeline finalizado com erros")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
