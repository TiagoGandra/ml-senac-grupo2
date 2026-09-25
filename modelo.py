# CRISP-DM: Fases 4, 5 e 6 - Modelagem, Avaliação e Implantação/Predição
import os
import pickle
import pandas as pd
import numpy as np  

from sklearn.model_selection import train_test_split # segregação 70/30 -> treino/teste

# CRISP-DM fase 4: Modelos de Inteligência Artificial para REGRESSÃO
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor

# CRISP-DM fase 5: Métricas de Avaliação de Regressão
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Importa a função de carga da base Silver do módulo transform_load
from transform_load import carregar_base_silver, CAMINHO_SILVER

NOMEMODELO = "imoveis-modelo.pickle"

def separarDados(dados):
    """
    CRISP-DM: Preparação final para modelagem - Divisão em treino (70%) e teste (30%).
    """
    print("\n--- Separar os dados de treino e teste ---")

    # Separando o objetivo (Target de Regressão) e variáveis independentes (Features)
    Y = dados["preco_venda"] # variável dependente/alvo/target contínua (preço em R$)
    X = dados.drop(columns=['preco_venda']) # variáveis independentes/features

    # Em problemas de regressão (alvo contínuo), NÃO usamos stratify=Y,
    # pois a estratificação é aplicável apenas a classes discretas (classificação).
    x_train, x_test, y_train, y_test = train_test_split(
        X, Y, 
        test_size=0.3,
        train_size=0.7, 
        shuffle=True,      # misturar, aleatoriedade dos dados
        random_state=42    # semente do dado aleatório (reprodutibilidade)
    )

    print(f"Tamanho do treino (70%): {x_train.shape[0]} registros")
    print(f"Tamanho do teste (30%): {x_test.shape[0]} registros")

    return x_train, x_test, y_train, y_test # devolve as 4 matrizes

def treinarModelo(x_train, y_train):
    """
    CRISP-DM: Fase 4 - Modelagem
    Treina múltiplos algoritmos de regressão supervisionada.
    """
    listaModelos = list()

    listaAlgoritmos = [
        RandomForestRegressor(n_estimators=100, random_state=42),   # Ensemble baseado em floresta aleatória
        GradientBoostingRegressor(n_estimators=100, random_state=42), # Ensemble com boosting de gradiente
        LinearRegression(),                                         # Regressão linear clássica
        DecisionTreeRegressor(random_state=42),                     # Árvore de decisão para regressão
        KNeighborsRegressor(n_neighbors=5),                         # Vizinhos mais próximos (KNN)
        Ridge(alpha=1.0)                                            # Regressão linear com regularização L2
    ]

    print("\n--- Treinando os Modelos de Regressão ---")
    for algoritmo in listaAlgoritmos:
        nome_algoritmo = algoritmo.__class__.__name__
        try:
            print(f"Treinando {nome_algoritmo}...")
            algoritmo.fit(x_train, y_train) # fit() treina/ajusta o algoritmo aos dados de treino
            listaModelos.append(algoritmo) 
        except Exception as e:
            print(f"Erro ao treinar {nome_algoritmo}: {e}")
            continue

    return listaModelos

def avaliarListaModelos(listaModelos, x_test, y_test):
    """
    CRISP-DM: Fase 5 - Avaliação (Test & Score)
    Calcula R², MAE e RMSE para cada modelo no conjunto de teste e elege o melhor.
    """
    listaPredicoes = list()
    listaScoresR2 = list()

    print("\n--- Avaliação dos Modelos de Regressão (Test & Score) ---")
    print(f"{'Modelo':<28} | {'R² Score':<10} | {'MAE (R$)':<18} | {'RMSE (R$)':<18}")
    print("-" * 80)

    for modelo in listaModelos:
        y_pred = modelo.predict(x_test)
        listaPredicoes.append(y_pred)

        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        listaScoresR2.append(r2)
        nome_modelo = modelo.__class__.__name__
        print(f"{nome_modelo:<28} | {r2:<10.4f} | R$ {mae:<15,.2f} | R$ {rmse:<15,.2f}")

    print("-" * 80)
    melhor_indice = listaScoresR2.index(max(listaScoresR2))
    melhor_modelo = listaModelos[melhor_indice]
    print(f"Melhor Modelo Selecionado: {melhor_modelo.__class__.__name__} com R² = {max(listaScoresR2):.4f}")

    return melhor_modelo

def salvarModelo(nomeModelo, modelo):
    """
    Salva o melhor modelo treinado em formato binário (pickle).
    """
    with open(nomeModelo, 'wb') as file:
        pickle.dump(modelo, file)
    print(f"\nModelo salvo com sucesso no arquivo: '{nomeModelo}'")

def carregarModelo(nomeModelo):
    """
    Carrega o modelo do disco para inferência.
    """
    modelo = None
    with open(nomeModelo, 'rb') as file:
        modelo = pickle.load(file)
    print(f"Modelo carregado com sucesso do arquivo: '{nomeModelo}'")
    return modelo

def validacaoModelo(modelo, x_validacao, y_validacao=None):
    """
    CRISP-DM: Fase 6 - Validação prática / Simulação de inferência em produção.
    """
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

if __name__ == "__main__":
    # 1. Carrega a base Silver (se não existir, o carregar_base_silver gera via ETL automaticamente)
    dados = carregar_base_silver(CAMINHO_SILVER)

    if dados is not None:
        # 2. Separação de treino e teste
        x_train, x_test, y_train, y_test = separarDados(dados)

        # 3. Treinamento dos modelos de Machine Learning (Fase 4)
        listaModelos = treinarModelo(x_train, y_train)

        # 4. Avaliação e seleção do melhor modelo (Fase 5)
        melhorModelo = avaliarListaModelos(listaModelos, x_test, y_test)

        # 5. Salva o melhor modelo treinado
        salvarModelo(NOMEMODELO, melhorModelo)

        # 6. Carrega o modelo salvo do disco
        modeloCarregado = carregarModelo(NOMEMODELO)

        # 7. Validação em amostras de teste (Fase 6)
        x_validacao = x_test.head(5)
        y_validacao = y_test.head(5)
        validacaoModelo(modeloCarregado, x_validacao, y_validacao)
