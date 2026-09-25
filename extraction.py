import pandas as pd

def extrair_base(arquivo):
    """
    CRISP-DM: Fase 2 - Compreensão e Extração dos Dados (Camada Bronze).
    Carrega o arquivo CSV bruto e retorna um DataFrame do pandas.
    """
    dados = None
    try:
        dados = pd.read_csv(arquivo)
        print(f"[EXTRAÇÃO] Dados carregados com sucesso de '{arquivo}': {dados.shape[0]} registros e {dados.shape[1]} colunas.")
        return dados  
    except Exception as e:
        print(f"[EXTRAÇÃO] Erro ao extrair a base do arquivo '{arquivo}': {e}")
        return None

if __name__ == "__main__":
    ARQUIVO_BRONZE = "data/dfimoveis_raw.csv"
    dados_brutos = extrair_base(ARQUIVO_BRONZE)
    if dados_brutos is not None:
        print(dados_brutos.head(2))