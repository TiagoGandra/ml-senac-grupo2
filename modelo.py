# CRISP-DM: Fases 4, 5 e 6 - Modelagem, Avaliação e Implantação/Predição
import os
import pickle
import pandas as pd
import numpy as np  

import matplotlib
if not os.environ.get('DISPLAY'):
    matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split

# CRISP-DM Fase 4: Modelos de Machine Learning para Regressão
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor

# CRISP-DM Fase 5: Métricas de Avaliação
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Importa a carga da base Silver do pipeline ETL
from transform_load import carregar_base_silver, CAMINHO_SILVER

NOMEMODELO = "imoveis-modelo.pickle"
ARQUIVO_GRAFICO = "grafico_real_vs_predito.png"
ARQUIVO_MEDIA_BAIRRO = "data/media_m2_bairro.pickle"
CAMINHO_LB_BAIRRO = "data/lb_bairro.pickle"

def separarDados(dados):
    """
    CRISP-DM: Divisão em treino (70%) e teste (30%).
    """
    print("\n--- Separar os dados de treino e teste ---")
    Y = dados["preco_venda"]
    X = dados.drop(columns=['preco_venda'])

    x_train, x_test, y_train, y_test = train_test_split(
        X, Y, 
        test_size=0.3,
        train_size=0.7, 
        shuffle=True, 
        random_state=42
    )

    print(f"Tamanho do treino (70%): {x_train.shape[0]} registros")
    print(f"Tamanho do teste (30%): {x_test.shape[0]} registros")

    return x_train, x_test, y_train, y_test

def aplicar_target_encoding_bairro(x_train, y_train, x_test, caminho_pickle=ARQUIVO_MEDIA_BAIRRO):
    """
    CRISP-DM Fase 4: Engenharia de Features sem Data Leakage (Zero Target Leakage).
    Calcula a métrica de preço/m² médio por bairro estritamente sobre o conjunto de treino (70%)
    e a projeta sobre treino e teste. Persiste os parâmetros para uso em inferência futura.
    """
    preco_m2_treino = y_train / x_train['area_util']
    mapa_bairro = preco_m2_treino.groupby(x_train['bairro_quadra']).mean().to_dict()
    media_global = float(preco_m2_treino.mean())

    os.makedirs(os.path.dirname(caminho_pickle), exist_ok=True)
    with open(caminho_pickle, "wb") as f:
        pickle.dump({"mapa": mapa_bairro, "media_global": media_global}, f)
    print(f"\n[ENGENHARIA DE FEATURES] Preço médio por m² calculado para {len(mapa_bairro)} bairros no treino.")
    print(f"Artefato salvo em '{caminho_pickle}' (Média global de fallback: R$ {media_global:,.2f}/m²).")

    x_train_feat = x_train.copy()
    x_test_feat = x_test.copy()

    x_train_feat['preco_m2_bairro'] = x_train_feat['bairro_quadra'].map(mapa_bairro).fillna(media_global)
    x_test_feat['preco_m2_bairro'] = x_test_feat['bairro_quadra'].map(mapa_bairro).fillna(media_global)

    return x_train_feat, x_test_feat

def treinarModelo(x_train, y_train):
    """
    CRISP-DM Fase 4: Treinamento dos Algoritmos de Regressão.
    """
    listaAlgoritmos = [
        RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        GradientBoostingRegressor(n_estimators=100, random_state=42),
        LinearRegression(),
        DecisionTreeRegressor(random_state=42),
        KNeighborsRegressor(n_neighbors=5),
        Ridge(alpha=1.0)
    ]

    listaModelos = []
    print("\n--- Treinando os Modelos de Regressão ---")
    for algoritmo in listaAlgoritmos:
        nome = algoritmo.__class__.__name__
        try:
            print(f"Treinando {nome}...")
            algoritmo.fit(x_train, y_train)
            listaModelos.append(algoritmo)
        except Exception as e:
            print(f"Erro ao treinar {nome}: {e}")

    return listaModelos

def avaliarListaModelos(listaModelos, x_test, y_test):
    """
    CRISP-DM Fase 5: Avaliação dos Modelos (Test & Score) e Seleção do Melhor.
    """
    print("\n--- Avaliação dos Modelos de Regressão (Test & Score) ---")
    print(f"{'Modelo':<28} | {'R² Score':<10} | {'MAE (R$)':<18} | {'RMSE (R$)':<18}")
    print("-" * 80)

    melhor_modelo = None
    melhor_r2 = -float("inf")

    for modelo in listaModelos:
        y_pred = modelo.predict(x_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        nome = modelo.__class__.__name__
        print(f"{nome:<28} | {r2:<10.4f} | R$ {mae:<15,.2f} | R$ {rmse:<15,.2f}")

        if r2 > melhor_r2:
            melhor_r2 = r2
            melhor_modelo = modelo

    print("-" * 80)
    print(f"Melhor Modelo Selecionado: {melhor_modelo.__class__.__name__} com R² = {melhor_r2:.4f}")
    return melhor_modelo

def avaliarPorBairro(modelo, x_test, y_test, caminho_lb_bairro=CAMINHO_LB_BAIRRO):
    """
    CRISP-DM Fase 5: Métrica Diagnóstica por Bairro.
    Avalia o desempenho do modelo segmentado regionalmente no conjunto de teste,
    calculando a quantidade de amostras, MAE (R$), erro mediano percentual (MdAPE)
    e percentual de predições dentro da margem de tolerância de +/- 15%.
    """
    print("\n--- Avaliação Diagnóstica de Desempenho por Bairro (Test Set) ---")
    if not os.path.exists(caminho_lb_bairro):
        print(f"Aviso: Encoder de bairros '{caminho_lb_bairro}' não encontrado para decodificação.")
        return

    with open(caminho_lb_bairro, "rb") as f:
        lb_bairro = pickle.load(f)

    y_pred = modelo.predict(x_test)
    df_diag = x_test.copy()
    df_diag['real'] = y_test.values
    df_diag['pred'] = y_pred
    df_diag['erro_abs'] = np.abs(df_diag['real'] - df_diag['pred'])
    df_diag['erro_pct'] = (df_diag['erro_abs'] / df_diag['real']) * 100
    df_diag['acerto_15pct'] = df_diag['erro_pct'] <= 15.0
    df_diag['nome_bairro'] = lb_bairro.inverse_transform(df_diag['bairro_quadra'])

    resumo_bairro = df_diag.groupby('nome_bairro').agg(
        qtd=('real', 'count'),
        mae=('erro_abs', 'mean'),
        mdape=('erro_pct', 'median'),
        acuracia_15pct=('acerto_15pct', lambda x: (x.sum() / len(x)) * 100)
    ).sort_values('qtd', ascending=False)

    print(f"{'Bairro':<24} | {'Amostras':<8} | {'MAE (R$)':<16} | {'Erro Mediano %':<15} | {'Acurácia ±15%':<14}")
    print("-" * 88)
    for nome, row in resumo_bairro.iterrows():
        print(f"{nome:<24} | {int(row['qtd']):<8} | R$ {row['mae']:<13,.2f} | {row['mdape']:<14.2f}% | {row['acuracia_15pct']:<13.1f}%")
    print("-" * 88)

def salvarModelo(nomeModelo, modelo):
    """
    CRISP-DM Fase 6: Salva o melhor modelo em formato pickle.
    """
    with open(nomeModelo, 'wb') as file:
        pickle.dump(modelo, file)
    print(f"\nModelo salvo com sucesso no arquivo: '{nomeModelo}'")

def carregarModelo(nomeModelo):
    """
    Carrega o modelo salvo em disco para inferência.
    """
    with open(nomeModelo, 'rb') as file:
        modelo = pickle.load(file)
    print(f"Modelo carregado com sucesso do arquivo: '{nomeModelo}'")
    return modelo

def validacaoModelo(modelo, x_validacao, y_validacao=None, caminho_lb_bairro=CAMINHO_LB_BAIRRO):
    """
    CRISP-DM Fase 6: Validação prática / Simulação de predição em novas amostras.
    Inclui verificação de domínio de bairros treinados.
    """
    print("\n--- Validação / Predição do Modelo ---")
    
    # Verificação de bairros conhecidos
    if os.path.exists(caminho_lb_bairro):
        with open(caminho_lb_bairro, "rb") as f:
            lb_bairro = pickle.load(f)
        bairros_validos_codigos = set(range(len(lb_bairro.classes_)))
        if 'bairro_quadra' in x_validacao.columns:
            for b in x_validacao['bairro_quadra'].unique():
                if b not in bairros_validos_codigos:
                    print(f"[ALERTA DE DOMÍNIO] Bairro com código '{b}' não foi contemplado no treinamento! Predição sujeita a incerteza.")

    y_pred = modelo.predict(x_validacao)

    print("Valores preditos:")
    for i in range(len(y_pred)):
        pred_formatado = f"R$ {y_pred[i]:,.2f}"
        if y_validacao is not None:
            real_val = y_validacao.iloc[i] if hasattr(y_validacao, 'iloc') else y_validacao[i]
            diff = y_pred[i] - real_val
            diff_pct = (diff / real_val) * 100
            print(f"Exemplo {i+1} -> Preço Previsto: {pred_formatado} | Preço Real: R$ {real_val:,.2f} | Diferença: R$ {diff:,.2f} ({diff_pct:+.1f}%)")
        else:
            print(f"Exemplo {i+1} -> Preço Previsto: {pred_formatado}")

def graficoRealVsPredito(y_test, y_pred, nome_modelo="RandomForestRegressor"):
    """
    CRISP-DM Fase 5: Gráfico de Dispersão Preço Real vs Preço Previsto.
    Compara as predições do modelo com a linha de referência ideal (y = x).
    Salva a imagem para uso na apresentação e exibe caso haja interface gráfica.
    """
    plt.figure(figsize=(7, 7))

    # Converte os valores para Milhões de R$ para melhor legibilidade nos eixos
    y_test_milhoes = y_test / 1e6
    y_pred_milhoes = y_pred / 1e6

    plt.scatter(y_test_milhoes, y_pred_milhoes, alpha=0.4, color='teal', edgecolors='none', s=25)
    plt.xlabel("Preço Real (Milhões de R$)", fontsize=12)
    plt.ylabel("Preço Previsto (Milhões de R$)", fontsize=12)
    plt.title(f"Preço Real vs Previsto ({nome_modelo})", fontsize=14, pad=12)

    # Linha diagonal ideal de 45 graus (y = x)
    min_val = min(y_test_milhoes.min(), y_pred_milhoes.min())
    max_val = max(y_test_milhoes.max(), y_pred_milhoes.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label="Previsão Ideal (y = x)")

    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=11)
    plt.tight_layout()

    plt.savefig(ARQUIVO_GRAFICO, dpi=300)
    print(f"\nGráfico salvo com sucesso no arquivo: '{ARQUIVO_GRAFICO}'")
    if os.environ.get('DISPLAY') and matplotlib.get_backend().lower() != 'agg':
        plt.show()
    plt.close()

if __name__ == "__main__":
    dados = carregar_base_silver(CAMINHO_SILVER)

    if dados is not None:
        x_train, x_test, y_train, y_test = separarDados(dados)

        # CRISP-DM Fase 4: Engenharia de Features (Média de Preço/m² por Bairro sem Data Leakage)
        x_train_feat, x_test_feat = aplicar_target_encoding_bairro(x_train, y_train, x_test)

        listaModelos = treinarModelo(x_train_feat, y_train)
        melhorModelo = avaliarListaModelos(listaModelos, x_test_feat, y_test)
        salvarModelo(NOMEMODELO, melhorModelo)
        modeloCarregado = carregarModelo(NOMEMODELO)

        # Validação prática nas 5 primeiras amostras de teste
        validacaoModelo(modeloCarregado, x_test_feat.head(5), y_test.head(5))

        # CRISP-DM Fase 5: Avaliação Diagnóstica Segmentada por Bairro
        avaliarPorBairro(modeloCarregado, x_test_feat, y_test)

        # Gráfico de Dispersão: Preço Real vs Preço Previsto
        y_pred_test = modeloCarregado.predict(x_test_feat)
        graficoRealVsPredito(y_test, y_pred_test, melhorModelo.__class__.__name__)
