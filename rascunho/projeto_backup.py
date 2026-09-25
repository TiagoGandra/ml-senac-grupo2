# CRISP-DM: preparação de dados fase 3
import os
import pandas as pd
import numpy as np  
import pickle # salva o arquivo treinado

# CRISP-DM: análise de dados fase 3
import matplotlib
# Configura o backend do matplotlib (se não houver DISPLAY gráfico, usa Agg)
if not os.environ.get('DISPLAY'):
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder # converter coluna string/categórica em numérica
from sklearn.model_selection import train_test_split # segregação 70/30 -> treino/teste

# CRISP-DM fase 4
# modelos para regressão(estimar valor de preço da venda)
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor

# CRISP-DM fase 5
# Métricas de avaliação para problemas de Regressão
# R² (coeficiente de determinação), MAE (erro médio absoluto) e RMSE (raiz do erro quadrático médio)
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from extraction import extrair_base

NOMEARQUIVO = "data/dfimoveis_raw.csv"
NOMEMODELO = "imoveis-modelo.pickle"

def prepararDados(dados):
    
    # retorna dados básicos sobre o arquivo/dataset carregado
    # qtd colunas, qtd registros não nulos, tipo das colunas
    print("\n--- Informações iniciais dos dados ---")
    print(dados.info())
    # atenção ao tipo da coluna

    # 5 primeiros registros do dataset
    print("\n5 Primeiros registros:")
    print(dados.head())

    # 5 ultimos registros do dataset
    print("\n5 Últimos registros:")
    print(dados.tail())

    # o que ganhamos com o head e tail -> procurando se os dados estão formatados direito
    # principalmente dados ponto flutuante(por exemplo, "," no lugar do ".")
    # no tail podemos ver linhas em branco

    # retorna estatística básicas dos campos do dataset
    print("\nEstatísticas descritivas básicas:")
    print(dados.describe())
    # importante para ver a simetria, qualidade dos dados, identificação de outliers etc

    # 1. Deduplicação dos dados
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

    # 5. Remoção de colunas que não agregam ao modelo:
    colunas_remover = [
        'id_anuncio', 'data_coleta', 'url_anuncio', 'descricao_texto',
        'iptu_periodo', 'valor_condominio', 'valor_iptu', 'comodidades_lista'
    ]
    dados.drop(columns=[col for col in colunas_remover if col in dados.columns], inplace=True)

    # 6. Remover eventuais dados nulos restantes
    dados.dropna(inplace=True)

    # 7. Remoção de outliers (preço e área útil)
    dados = dados[dados["preco_venda"].between(50000, 25000000)]
    dados = dados[dados["area_util"].between(15, 1500)]

    # 8. Decodifica dados categóricos em valores numéricos (LabelEncoder)
    lb_tipo = LabelEncoder()
    dados['tipo_imovel'] = lb_tipo.fit_transform(dados['tipo_imovel'])

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

def separarDados(dados):
    print("\n--- Separar os dados de treino e teste ---")

    # Separando o objetivo (Target) e variáveis independentes (Features)
    Y = dados["preco_venda"] # variável dependente/alvo/target contínua
    X = dados.drop(columns=['preco_venda']) # variáveis independentes/features

    x_train, x_test, y_train, y_test = train_test_split(
        X, Y, 
        test_size=0.3,
        train_size=0.7, 
        shuffle=True,     
        random_state=42 
    )

    print(f"Tamanho do treino (70%): {x_train.shape[0]} registros")
    print(f"Tamanho do teste (30%): {x_test.shape[0]} registros")

    return x_train, x_test, y_train, y_test # me devolve 4 matrizes

def treinarModelo(x_train, y_train):
    listaModelos = list() # lista dos modelos que vamos treinar, objetos dentro de uma lista, parecido com o Orange

    # Modelos de Inteligência Artificial para REGRESSÃO
    # Instanciamos os algoritmos regressores correspondentes:
    listaAlgoritmos = [
        RandomForestRegressor(n_estimators=100, random_state=42),   # Ensemble baseado em floresta aleatória
        GradientBoostingRegressor(n_estimators=100, random_state=42), # Ensemble com boosting de gradiente
        LinearRegression(),                                         # Regressão linear clássica
        DecisionTreeRegressor(random_state=42),                     # Árvore de decisão para regressão
        KNeighborsRegressor(n_neighbors=5),                         # Vizinhos mais próximos (KNN)
        Ridge(alpha=1.0)                                            # Regressão linear com regularização L2
    ]

    print("\n--- Treinando os Modelos de Regressão ---")
    # treinar modelos de IA
    for algoritmo in listaAlgoritmos:
        nome_algoritmo = algoritmo.__class__.__name__
        try:
            print(f"Treinando {nome_algoritmo}...")
            algoritmo.fit(x_train, y_train) # fit() treina/ajusta o algoritmo aos dados de treino
            listaModelos.append(algoritmo) 
        except Exception as e:
            print(f"Erro ao treinar {nome_algoritmo}: {e}")
            continue

    return listaModelos # lista de modelos treinados

def avaliarListaModelos(listaModelos, x_test, y_test): # test and score do Orange
    
    listaPredicoes = list()
    listaScoresR2 = list()

    print("\n--- Avaliação dos Modelos de Regressão (Test & Score) ---")
    print(f"{'Modelo':<28} | {'R² Score':<10} | {'MAE (R$)':<18} | {'RMSE (R$)':<18}")
    print("-" * 80)

    # realiza a predição e calcula as métricas para cada modelo
    for modelo in listaModelos:
        y_pred = modelo.predict(x_test) # predict() realiza a predição com os dados de teste
        listaPredicoes.append(y_pred)

        # Métricas de regressão:
        # R² (Coeficiente de Determinação): variação explicada pelo modelo (quanto mais próximo de 1.0, melhor)
        r2 = r2_score(y_test, y_pred)
        # MAE: Erro Médio Absoluto (em Reais)
        mae = mean_absolute_error(y_test, y_pred)
        # RMSE: Raiz do Erro Quadrático Médio (em Reais)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        listaScoresR2.append(r2)
        nome_modelo = modelo.__class__.__name__
        print(f"{nome_modelo:<28} | {r2:<10.4f} | R$ {mae:<15,.2f} | R$ {rmse:<15,.2f}")

    print("-" * 80)
    melhor_indice = listaScoresR2.index(max(listaScoresR2))
    melhor_modelo = listaModelos[melhor_indice]
    print(f"Melhor Modelo Selecionado: {melhor_modelo.__class__.__name__} com R² = {max(listaScoresR2):.4f}")

    return melhor_modelo # devolve o modelo de melhor performance para salvarmos

def salvarModelo(NOMEMODELO, modelo): # save model com pickle
    with open(NOMEMODELO, 'wb') as file: # wb = write binário
        pickle.dump(modelo, file) # dump -> escreve no disco o modelo treinado
    print(f"\nModelo salvo com sucesso no arquivo: '{NOMEMODELO}'")

def carregarModelo(NOMEMODELO):
    modelo = None
    with open(NOMEMODELO, 'rb') as file: # rb = read binário
        modelo = pickle.load(file) # load -> carrega o modelo
    print(f"Modelo carregado com sucesso do arquivo: '{NOMEMODELO}'")
    return modelo # e retornamos o modelo

def validacaoModelo(modelo, x_validacao, y_validacao=None): # predict do Orange: pegamos dados novos e prevemos
    print("\n--- Validação / Predição do Modelo ---")
    y_pred = modelo.predict(x_validacao)

    print("Valores preditos:")
    for i in range(len(y_pred)):
        pred_formatado = f"R$ {y_pred[i]:,.2f}"
        if y_validacao is not None:
            real_val = y_validacao.iloc[i] if hasattr(y_validacao, 'iloc') else y_validacao[i]
            real_formatado = f"R$ {real_val:,.2f}"
            diff = y_pred[i] - real_val
            diff_formatado = f"R$ {diff:,.2f}"
            print(f"Exemplo {i+1} -> Preço Previsto: {pred_formatado} | Preço Real: {real_formatado} | Diferença: {diff_formatado}")
        else:
            print(f"Exemplo {i+1} -> Preço Previsto: {pred_formatado}")

# carregar o conjunto de dados para tratamento - fase 2 do CRISP-DM
dados = extrair_base(NOMEARQUIVO)

if dados is not None:

    # tratamento de dados - fase 3 do CRISP-DM
    dados = prepararDados(dados)

    # visualizar alguns dados de modo gráfico
    visualizarDados(dados)

    # separar os dados de treino e teste
    x_train, x_test, y_train, y_test = separarDados(dados)

    # realizar o treinamento de modelos de IA - Regressão
    listaModelos = treinarModelo(x_train, y_train)

    # avaliar lista de modelos (Test & Score)
    modelo = avaliarListaModelos(listaModelos, x_test, y_test)

    # salvar modelo em formato padronizado (pickle)
    salvarModelo(NOMEMODELO, modelo)

    # carregar o modelo salvo
    modeloCarregado = carregarModelo(NOMEMODELO)

    # validar o modelo carregado em uma amostra de teste (primeiras 5 amostras)
    # em produção esse vetor seria uma entrada de dados (formulário, API, etc.) sem a coluna target
    x_validacao = x_test.head(5)
    y_validacao = y_test.head(5)
    validacaoModelo(modeloCarregado, x_validacao, y_validacao)
