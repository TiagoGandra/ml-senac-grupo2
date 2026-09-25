# CRISP-DM: preparação de dados fase 3
import pandas as pd
import numpy as np  
import pickle # salva o arquivo treinado

# CRISP-DM: análise de dados fase 3 - 123
import matplotlib
matplotlib.use('TkAgg') # rodar gráficos plot no linux
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder # converter coluna string em numerica
from sklearn.model_selection import train_test_split # segregação 70/30 -> treino/teste

# CRISO-DM fase 4
# modelos de inteligencia artificial
# ensemble -> familia de modelos baseado em arvore de decição
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier #MLP -> multi layer perceptor
from sklearn import svm

# CRISO-DM fase 5
from sklearn.metrics import accuracy_score # calcular a acuracia do modelo -> etapa de teste

NOMEARQUIVO = "data/Titanic-Dataset.csv"
NOMEMODELO = "titanic-modelo.pickle"

def carregarDados(nomeArquivo):
    
    dados = None
    try:
        dados = pd.read_csv(nomeArquivo, sep=",")

    except:
        print("Não foi possivel carregar os dados") #importante para não vazar informações importantes ao dar erro
    
    return dados # posso retornar mais de um parametro dados, dados2, dados3 -> passar no máximo até 3

def prepararDados(dados):
    
    # retorna dados básicos sobre o arquivo/dataset carregado
    # qtd colunas, qtd registros não nulos, tipo das colunas
    print(dados.info())
    # atenção ao tipo da coluna

    # 5 primeiros registros do dataset
    print(dados.head())

    # 5 ultimos registros do dataset
    print(dados.tail())

    # o que ganhamos com o head e tail -> procurando se os dados estão formatados direito
    # principalmente dados ponto flutuante(por exemplo, "," no lugar do ".")
    # o tail podemos ver linhas em branco

    # retorna estatistica básicas dos campos do dadaset
    print(dados.describe())
    # importante para ver a simetria, qualidade dos dados, identificação de outliers etc

    # remover os dados duplicados
    #dados = dados.drop_duplicates()
    dados.drop_duplicates(inplace=True) # remover dados duplicados, inplace é para não ter que ficar reatribuindo o dados,
    #assim economiza memoria, pois em algum momento fica os dois em memoria
    # dados duplicados podem ter vindo de JOIN, UNION, CROSS mal feitos do banco de dados
    # curiosidade: melhor banco de dados para armazenar dados para ML -> redshift e grausDB, sempre noSQL

    # remover as colunas
    dados.drop(columns=['Cabin', 'Name', 'PassengerId', 'Ticket'], inplace=True) # remover colunas desnecessárias

    # remove todos os dados nulos
    dados.dropna(inplace=True) # dropamos primeiro cabin porque se rodassemos esse dropna, iria remover a maioria dos dados e
    # deixaria apenas 204 linhas que não tem cabin null

    # decodifica dados categoricos em valores numericos
    lb = LabelEncoder()
    dados['Sex'] = lb.fit_transform(dados['Sex']) # é possivel fazer isso com set também, entender melhor
    dados['Embarked'] = lb.fit_transform(dados['Embarked'])
    # codificamos esses dados (categorizamos) de forma numerica
    print(dados.info())
    print(dados.head())
    print(dados.shape) # retorna uma tupla(imutavel, diferente da lista)
    print(dados.values) # retorna uma lista dentro de outra lista -> ou seja, cria uma matriz

    # mater valores entre 0 e 62 (inclusive)
    # remover os outliers
    dados = dados[dados["Age"].between(0, 60, inclusive="neither")]
    dados = dados[dados["Fare"].between(0, 55, inclusive="neither")]

    return dados

def gerarBoxplot(dados):
    fig, ax = plt.subplots()
    ax.set_ylabel('boxplot variáveis do Titanic')

    for n, col in enumerate(dados.columns):
        if col == 'Age' or col == 'Fare':
            ax.boxplot(dados[col], positions=[n+1])

    plt.title("Boxplot da coluna Age")
    plt.ylabel("Valores")
    plt.show()

def visualizarDados(dados):

    dados['Age'].hist() # aqui podemos analisar que pessoas de mais idades e menos idades possuem menos dados
    # e por isso o modelo pode não performar tão bem para esses casos, por isso temos que balancear
    plt.show()

    dados['Embarked'].hist()
    plt.show()

    gerarBoxplot(dados)

    dados['Survived'].hist() # nosso target, também não está balanceado(devemos balancear: oversampling e poda)
    # se não balancearmos o modelo vai ficar enviesado
    plt.show()

    graficoBarras(dados) # groupby.()

def contarColunas(dados, coluna, valor):
    #dados[coluna] = (dados[coluna] == valor).count
    return None

def graficoBarras(dados):
    fig, ax = plt.subplots()

    #valor0 = dados.loc(dados['Survived', 'Nome'] == 0).count()
    #valor1 = dados[dados['Survived'] == 1].count()

    fruits = ['0', '1']
    counts = [40, 50]
    bar_labels = ['red', 'blue']
    bar_colors = ['tab:red', 'tab:blue']

    ax.bar(fruits, counts, label=bar_labels, color=bar_colors)

    ax.set_ylabel('Coluna Survived')
    ax.set_title('Coluna Survived')
    ax.legend(title='Survived')

    plt.show()

def separarDados(dados):
    print("Separar os dados de treino e teste")

    # separando o objetivo de estratificação [0,1] -- lista 70% e 30%
    Y = dados["Survived"] # variavel dependente/alvo/target
    X = dados.drop(['Survived'],axis=1) # variaveis independentes/feature

    #dadosTreino, dadosTeste = train_test_split(dados, test_size=0.3, train_size=0.7, stratify=Y)
    x_train, x_test, y_train, y_test = train_test_split(X, Y, 
                                                        test_size=0.3,
                                                        train_size=0.7, 
                                                        shuffle=True,  # misturar, aleatoriedade dos dados
                                                        random_state=42, # semente do dado aleatorio
                                                        stratify=Y) # estratificando(oque é estratificar) pelo target

    return x_train, x_test, y_train, y_test # me devolve sempre 4 matrizes

def treinarModelo(x_train, y_train):
    listaModelos = list() # lista dos modelos que vamos treinar, objetos dentro de uma lista, parecido com o que faziamos no orange

    # modelos de IA
    # vamos instanciar os algoritmos, todos são orientados a objetos(tem atributos e métodos) ou seja, são objetos
    listaAlgoritmos = [RandomForestClassifier(n_estimators=100),  # aqui temos os parametros
                       LogisticRegression(max_iter=1000),
                       GaussianNB(),
                       svm.SVC(),
                       GradientBoostingClassifier(n_estimators=100),
                       MLPClassifier(solver='lbfgs', alpha=1e-5, 
                                     hidden_layer_sizes=(15, ), max_iter=1000)] # igual aqui também são os parametros

    # treinar modelos de IA
    for algoritmo in listaAlgoritmos:
        try:
            algoritmo.fit(x_train, y_train) # fit.() encaixa o algoritmo para evitar ficar ter que treinar modelo por mdodelo
            # scikit-learn
            listaModelos.append(algoritmo) 
        except:
            continue

    return listaModelos # lista de modelos treinados

def avaliarListaModelos(listaModelos, x_test, y_test): # test and score do orange
    
    listaPredicoes = list()
    listaAcuracia = list()

    # realiza a predição 
    for modelo in listaModelos:
        y_pred1 = modelo.predict(x_test) # predict.() faça a predição com o dado de teste
        listaPredicoes.append(y_pred1)

    # realiza o calculo da acuracia, com base nas predições do modelo, compara para mim com as predições do especialista
    for predModelo in listaPredicoes:
        listaAcuracia.append(accuracy_score(predModelo, y_test))

    print(listaAcuracia)
    print("Melhor Acurácia: "+str(max(listaAcuracia))) # lista a acuracia dos modelos e pega a com maior acuracia

    # modelo de maior acuracia
    modelo = listaAcuracia.index(max(listaAcuracia))

    return listaModelos[modelo] # devolve o modelo para salvarmos

def salvarModelo(NOMEMODELO, modelo): # save model com pickle
    with open(NOMEMODELO, 'wb') as file: # wb = write binario
        pickle.dump(modelo, file) # dump -> escreva no disco o modelo

def carregarModelo(NOMEMODELO):
    modelo = None
    with open(NOMEMODELO, 'rb') as file: # rb = read binario
        modelo = pickle.load(file) # load -> carrega o modelo
    
    return modelo # e retornamos o modelo

def validacaoModelo(modelo, x_validacao): # predict do orange, recebemos o modelo, pegamos dados novos e prevemos
    y_pred = modelo.predict(x_validacao)

    print("Predição:" + str(y_pred))

NOMEARQUIVO = "data/Titanic-Dataset.csv"

# carregar o conjunto de dados para tretamento - fase 2 do CRISP-DM
dados = carregarDados(NOMEARQUIVO)

if dados is not None:

    # tratamento de dados - fase 3 do CRISP-DM
    dados = prepararDados(dados)

    # visualizar alguns dados de modo gráfico
    visualizarDados(dados)

    # separar os dados de treino e teste
    x_train, x_test, y_train, y_test = separarDados(dados)

    # realizar o treinamento de modelos de IA - Classificacao
    listaModelos = treinarModelo(x_train, y_train)

    # avaliar lista de modelos
    modelo = avaliarListaModelos(listaModelos, x_test, y_test)

    # salvar modelo em formato padronizado
    salvarModelo(NOMEMODELO, modelo)

    # carregar o modelo salvo
    modeloCarregado = carregarModelo(NOMEMODELO)

    # validar o modelo carregado
    x_validacao = x_test # [0,0,0,0,0,0,0] # carregamos o x_test que foi os testes que dropamos o 
    # valor em split, ou seja, não sabemos(algo assim?)
    # mas em produção esse vetor seria uma telinha de entrada de dados, exemplo, [sex(F), age(50),... ---NÃO COLOCAMOS O TARGET---]
    validacaoModelo(modeloCarregado, x_validacao)
