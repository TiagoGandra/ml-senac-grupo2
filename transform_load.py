# CRISP-DM: preparação de dados fase 3 (ETL - Transform & Load)
import os
import pandas as pd
import numpy as np  

import matplotlib
if not os.environ.get('DISPLAY'):
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder

# Integração com a camada Bronze (Extração)
from extraction import extrair_base

CAMINHO_BRONZE = "data/dfimoveis_raw.csv"
CAMINHO_SILVER = "data/dfimoveis_silver.csv"

def prepararDados(dados):
    """
    CRISP-DM Fase 3 - Transformação
    Limpeza, tratamento e seleção das características estruturais essenciais:
    tipo_imovel, bairro_quadra, area_util, quartos, suites, vagas, valor_condominio.
    """
    print("\n--- Informações iniciais dos dados brutos ---")
    print(dados.info())

    # 1. Deduplicação
    antes = len(dados)
    if "data_coleta" in dados.columns:
        dados.sort_values("data_coleta", ascending=False, inplace=True)
    dados.drop_duplicates(subset=["url_anuncio"] if "url_anuncio" in dados.columns else None, inplace=True)
    print(f"\nDeduplicação: {antes - len(dados)} duplicatas removidas ({antes} -> {len(dados)})")

    # 2. Extração do tipo de imóvel a partir da URL
    dados['tipo_imovel'] = dados['url_anuncio'].str.extract(r'/imovel/([^/-]+)', expand=False)
    dados = dados[dados['tipo_imovel'].isin(['apartamento', 'kitnet', 'casa'])].copy()

    # 3. Tipagem das colunas numéricas e imputações básicas
    for col in ["preco_venda", "area_util", "quartos", "suites", "vagas"]:
        if col in dados.columns:
            dados[col] = pd.to_numeric(dados[col], errors="coerce")

    dados['quartos'] = dados['quartos'].fillna(1.0)
    dados['suites'] = dados['suites'].fillna(0.0)
    dados['vagas'] = dados['vagas'].fillna(0.0)
    dados['valor_condominio'] = pd.to_numeric(dados.get('valor_condominio', 0), errors='coerce').fillna(0.0)

    # 4. Filtro de limites plausíveis de mercado (remoção de outliers extremos)
    dados = dados[dados["preco_venda"].between(50000, 5000000)].copy()
    dados = dados[dados["area_util"].between(15, 1200)].copy()
    dados = dados[dados["valor_condominio"].between(0, 4000)].copy()

    # 4.1 Filtro de consistência de mercado (Preço por m²):
    # Remove anúncios com erros evidentes de digitação ou inconsistências cadastrais grosseiras
    preco_m2 = dados["preco_venda"] / dados["area_util"]
    q_low = preco_m2.quantile(0.015)
    q_high = preco_m2.quantile(0.985)
    qtd_antes_m2 = len(dados)
    dados = dados[preco_m2.between(q_low, q_high)].copy()
    print(f"\nFiltro de consistência de preço/m²: {qtd_antes_m2 - len(dados)} inconsistências removidas (faixa: R$ {q_low:,.2f}/m² a R$ {q_high:,.2f}/m²)")

    # 5. Seleção estrita das características normais/essenciais
    colunas_finais = [
        'preco_venda', 'tipo_imovel', 'bairro_quadra', 
        'area_util', 'quartos', 'suites', 'vagas', 'valor_condominio'
    ]
    dados = dados[colunas_finais].copy()

    # 6. Remoção de eventuais nulos restantes
    dados.dropna(inplace=True)

    # 7. Codificação categórica para modelagem (LabelEncoder)
    lb_tipo = LabelEncoder()
    dados['tipo_imovel'] = lb_tipo.fit_transform(dados['tipo_imovel']) # 0=apartamento, 1=casa, 2=kitnet

    lb_bairro = LabelEncoder()
    dados['bairro_quadra'] = lb_bairro.fit_transform(dados['bairro_quadra'].astype(str))

    print("\n--- Informações após preparação dos dados básicos ---")
    print(dados.info())
    print(dados.head())
    print(f"Dimensões finais (linhas, colunas): {dados.shape}")

    return dados

def salvar_base_silver(dados, caminho_silver=CAMINHO_SILVER):
    """
    CRISP-DM: Fase 3 - Carga (Load) da Camada Silver
    Salva o conjunto de dados tratado em CSV pronto para modelagem.
    """
    os.makedirs(os.path.dirname(caminho_silver), exist_ok=True)
    dados.to_csv(caminho_silver, index=False)
    print(f"\n[LOAD] Base Silver salva com sucesso em '{caminho_silver}' ({len(dados)} registros e {dados.shape[1]} colunas).")

def carregar_base_silver(caminho_silver=CAMINHO_SILVER):
    """
    Carrega o dataset da camada Silver para alimentar a modelagem.
    """
    if not os.path.exists(caminho_silver):
        print(f"\n[AVISO] Base Silver não encontrada em '{caminho_silver}'. Gerando agora via ETL...")
        return executar_transform_load(caminho_silver=caminho_silver)
    
    dados = pd.read_csv(caminho_silver)
    print(f"\n[CARGA SILVER] Base Silver carregada de '{caminho_silver}': {dados.shape[0]} registros e {dados.shape[1]} colunas.")
    return dados

def executar_transform_load(caminho_bronze=CAMINHO_BRONZE, caminho_silver=CAMINHO_SILVER):
    """
    Pipeline completo de Transformação e Carga:
    1. Extrai da Bronze (dfimoveis_raw.csv)
    2. Aplica limpeza básica de características essenciais (prepararDados)
    3. Salva na Silver (dfimoveis_silver.csv)
    """
    print("\n=== Executando Pipeline ETL Simplificado (Bronze -> Silver) ===")
    dados_brutos = extrair_base(caminho_bronze)
    if dados_brutos is None:
        print("Erro: Falha na extração dos dados brutos.")
        return None

    dados_silver = prepararDados(dados_brutos)
    salvar_base_silver(dados_silver, caminho_silver)
    return dados_silver

if __name__ == "__main__":
    dados_processados = executar_transform_load()