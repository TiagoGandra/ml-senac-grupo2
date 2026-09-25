# CRISP-DM: preparação de dados fase 3 (ETL - Transform & Load)
import os
import pandas as pd
import numpy as np  

# CRISP-DM: análise exploratória de dados fase 3
import matplotlib
# Configura o backend do matplotlib (se não houver DISPLAY gráfico, usa Agg)
if not os.environ.get('DISPLAY'):
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder # converter coluna string/categórica em numérica

# Integração com a camada Bronze (Extração)
from extraction import extrair_base

# Definição dos caminhos das camadas Bronze e Silver
CAMINHO_BRONZE = "data/dfimoveis_raw.csv"
CAMINHO_SILVER = "data/dfimoveis_silver.csv"

def prepararDados(dados):
    """
    Realiza a limpeza, tratamento, engenharia de features e codificação dos dados brutos.
    """
    print("\n--- Informações iniciais dos dados brutos ---")
    print(dados.info())
    print("\n5 Primeiros registros:")
    print(dados.head())
    print("\nEstatísticas descritivas básicas:")
    print(dados.describe())

    # 1. Deduplicação dos dados (caso o crawler tenha coletado o mesmo imóvel em datas diferentes)
    antes = len(dados)
    if "data_coleta" in dados.columns:
        dados.sort_values("data_coleta", ascending=False, inplace=True)
    dados.drop_duplicates(subset=["url_anuncio"] if "url_anuncio" in dados.columns else None, inplace=True)
    print(f"\nDeduplicação: {antes - len(dados)} duplicatas removidas ({antes} -> {len(dados)})")

    # 2. Extração da coluna tipo_imovel a partir da url_anuncio (logo após /imovel/)
    # O dataset contém 3 tipos principais: apartamento, kitnet e casa
    dados['tipo_imovel'] = dados['url_anuncio'].str.extract(r'/imovel/([^/-]+)', expand=False)
    # Filtra apenas os 3 tipos esperados no projeto
    dados = dados[dados['tipo_imovel'].isin(['apartamento', 'kitnet', 'casa'])].copy()
    print("\nDistribuição por Tipo de Imóvel:")
    print(dados['tipo_imovel'].value_counts())

    # 3. Tipagem das colunas numéricas
    for col in ["preco_venda", "area_util", "quartos", "suites", "vagas"]:
        if col in dados.columns:
            dados[col] = pd.to_numeric(dados[col], errors="coerce")

    # 4. Feature engineering: número de comodidades a partir de comodidades_lista
    if "comodidades_lista" in dados.columns:
        dados['qtd_comodidades'] = dados['comodidades_lista'].fillna('').apply(
            lambda x: len(str(x).split(',')) if str(x).strip() else 0
        )

    # 5. Remoção de colunas que não agregam ao modelo ou possuem excesso de nulos:
    colunas_remover = [
        'id_anuncio', 'data_coleta', 'url_anuncio', 'descricao_texto',
        'iptu_periodo', 'valor_condominio', 'comodidades_lista'
    ]
    dados.drop(columns=[col for col in colunas_remover if col in dados.columns], inplace=True)

    # 5.5 inserir valores na coluna valor_iptu
    iptu_estimado = dados["preco_venda"] * 0.003
    dados["valor_iptu"] = dados["valor_iptu"].fillna(iptu_estimado)

    # 6. Remover eventuais dados nulos restantes
    dados.dropna(inplace=True)

    # 7. Remoção de outliers (preço e área útil)
    # Nota: se desejar focar até 5 milhões para maior homogeneidade e R² maior, ajuste preco_max=5000000
    dados = dados[dados["preco_venda"].between(50000, 5000000)]
    dados = dados[dados["area_util"].between(15, 1500)]

    # 8. Decodifica dados categóricos em valores numéricos (LabelEncoder)
    lb_tipo = LabelEncoder()
    dados['tipo_imovel'] = lb_tipo.fit_transform(dados['tipo_imovel']) # apartamento=0, casa=1, kitnet=2

    lb_bairro = LabelEncoder()
    dados['bairro_quadra'] = lb_bairro.fit_transform(dados['bairro_quadra'])

    print("\n--- Informações após preparação dos dados ---")
    print(dados.info())
    print(dados.head())
    print(f"Dimensões finais (linhas, colunas): {dados.shape}")

    return dados

def gerarBoxplot(dados):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Boxplot da Área Útil
    axes[0].boxplot(dados['area_util'])
    axes[0].set_title("Boxplot da Área Útil (m²)")
    axes[0].set_ylabel("Área (m²)")

    # Boxplot do Preço de Venda em Milhões de R$
    axes[1].boxplot(dados['preco_venda'] / 1e6)
    axes[1].set_title("Boxplot do Preço de Venda (Milhões de R$)")
    axes[1].set_ylabel("Valor (Milhões de R$)")

    plt.tight_layout()
    plt.show()

def graficoBarras(dados):
    fig, ax = plt.subplots(figsize=(8, 5))

    # Contagem de registros por tipo de imóvel
    contagem = dados['tipo_imovel'].value_counts().sort_index()
    nomes_tipos = ['Apartamento', 'Casa', 'Kitnet'] if len(contagem) == 3 else [str(i) for i in contagem.index]
    cores = ['tab:blue', 'tab:green', 'tab:orange']

    ax.bar(nomes_tipos, contagem.values, color=cores[:len(contagem)])
    ax.set_ylabel('Quantidade de Imóveis')
    ax.set_title('Distribuição por Tipo de Imóvel (apartamento, casa, kitnet)')

    for i, v in enumerate(contagem.values):
        ax.text(i, v + 40, str(v), ha='center', fontweight='bold')

    plt.tight_layout()
    plt.show()

def visualizarDados(dados):
    print("\nGerando visualizações gráficas...")
    try:
        # Histograma do target (preco_venda em Milhões de R$)
        plt.figure(figsize=(8, 4))
        (dados['preco_venda'] / 1e6).hist(bins=30, edgecolor='black', color='steelblue')
        plt.title("Distribuição do Preço de Venda (Milhões de R$)")
        plt.xlabel("Preço de Venda (Milhões de R$)")
        plt.ylabel("Frequência")
        plt.tight_layout()
        plt.show()

        # Histograma da área útil
        plt.figure(figsize=(8, 4))
        dados['area_util'].hist(bins=30, edgecolor='black', color='coral')
        plt.title("Distribuição da Área Útil (m²)")
        plt.xlabel("Área Útil (m²)")
        plt.ylabel("Frequência")
        plt.tight_layout()
        plt.show()

        # Boxplots para visualização de dispersão
        gerarBoxplot(dados)

        # Gráfico de barras da nova coluna tipo_imovel
        graficoBarras(dados)
    except Exception as e:
        print(f"Aviso: Não foi possível renderizar gráficos na tela ({e}). O fluxo do pipeline continuará normalmente.")

def salvar_base_silver(dados, caminho_silver=CAMINHO_SILVER):
    """
    CRISP-DM: Fase 3 - Carga (Load) da Camada Silver
    Salva o conjunto de dados tratado em um novo arquivo CSV pronto para modelagem.
    """
    os.makedirs(os.path.dirname(caminho_silver), exist_ok=True)
    dados.to_csv(caminho_silver, index=False)
    print(f"\n[LOAD] Base Silver salva com sucesso em '{caminho_silver}' ({len(dados)} registros e {dados.shape[1]} colunas).")

def carregar_base_silver(caminho_silver=CAMINHO_SILVER):
    """
    Carrega o dataset da camada Silver para alimentar a modelagem de Machine Learning.
    Se o arquivo ainda não existir, executa o pipeline de transformação para criá-lo.
    """
    if not os.path.exists(caminho_silver):
        print(f"\n[AVISO] Base Silver não encontrada em '{caminho_silver}'. Gerando agora via ETL...")
        return executar_transform_load(caminho_silver=caminho_silver)
    
    dados = pd.read_csv(caminho_silver)
    print(f"\n[CARGA SILVER] Base Silver carregada de '{caminho_silver}': {dados.shape[0]} registros e {dados.shape[1]} colunas.")
    return dados

def executar_transform_load(caminho_bronze=CAMINHO_BRONZE, caminho_silver=CAMINHO_SILVER, visualizar=False):
    """
    Pipeline completo de Transformação e Carga:
    1. Extrai da Bronze (dfimoveis_raw.csv)
    2. Aplica as regras de negócio e tratamento (prepararDados)
    3. Opcionalmente gera gráficos (visualizarDados)
    4. Salva na Silver (dfimoveis_silver.csv)
    """
    print("\n=== Executando Pipeline ETL (Bronze -> Silver) ===")
    
    # 1. Extração
    dados_brutos = extrair_base(caminho_bronze)
    if dados_brutos is None:
        print("Erro: Falha na extração dos dados brutos.")
        return None

    # 2. Transformação
    dados_silver = prepararDados(dados_brutos)

    # 3. Visualização (se solicitada)
    if visualizar:
        visualizarDados(dados_silver)

    # 4. Carga (Load) na camada Silver
    salvar_base_silver(dados_silver, caminho_silver)

    return dados_silver

if __name__ == "__main__":
    # Executa a transformação e salva a base Silver com visualizações
    dados_processados = executar_transform_load(visualizar=True)