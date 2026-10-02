import pytest
from bs4 import BeautifulSoup
from src.parser import (
    clean_currency,
    clean_area,
    clean_integer,
    extract_neighborhood,
    extract_iptu_period,
    parse_detail_page
)

def test_clean_currency():
    assert clean_currency("R$ 1.250.000,00") == 1250000.0
    assert clean_currency("1690000,00") == 1690000.0
    assert clean_currency("1.237") == 1237.0
    assert clean_currency("Sob Consulta") is None
    assert clean_currency("") is None

def test_clean_area():
    assert clean_area("87,50 m²") == 87.5
    assert clean_area("110,00 m²") == 110.0
    assert clean_area("127 m²") == 127.0
    assert clean_area("") is None

def test_clean_integer():
    assert clean_integer("3 Quartos") == 3
    assert clean_integer("1 Suíte") == 1
    assert clean_integer("2 vagas") == 2
    assert clean_integer("Sem vaga") is None

def test_extract_neighborhood():
    html = '<div class="info-details"><span itemprop="address">BRASÍLIA - ASA NORTE</span></div>'
    soup = BeautifulSoup(html, "html.parser")
    assert extract_neighborhood(soup) == "Asa Norte"
    
    html2 = '<div class="info-details"><span itemprop="address">NOROESTE</span></div>'
    soup2 = BeautifulSoup(html2, "html.parser")
    assert extract_neighborhood(soup2) == "Noroeste"

def test_extract_iptu_period():
    assert extract_iptu_period("Lindo apto, IPTU mensal no valor de 200.") == "mensal"
    assert extract_iptu_period("IPTU anual de R$ 1200.") == "anual"
    assert extract_iptu_period("Valor do IPTU: R$ 350,00/mês") == "mensal"
    assert extract_iptu_period("Sem IPTU na descrição") is None

def test_parse_detail_page_no_price():
    html = '''
    <input id="id-imovel" value="123">
    <p itemprop="price" content="Sob Consulta">Sob Consulta</p>
    '''
    result = parse_detail_page(html, "http://test.com/123")
    assert result is None

def test_parse_detail_page_valid():
    html = '''
    <input id="id-imovel" value="123">
    <p itemprop="price" content="1500000,00">R$ 1.500.000,00</p>
    <p itemprop="floorSize">100,00 m²</p>
    <div class="info-details">
        <span itemprop="address">BRASÍLIA - ASA SUL</span>
        <div class="room"><span>3 quartos</span></div>
        <div class="suite"><span>1 suíte</span></div>
        <div class="vacancy"><span>2 vagas</span></div>
        <div class="condom"><span>Condomínio R$ 1.000</span></div>
    </div>
    <div class="dados-block"><ul class="details-text"><li>IPTU R$: 500,00</li></ul></div>
    <div class="escondido-text">Descrição completa com IPTU anual incluso.</div>
    <div id="listaDeDetalhesDoImovel"><ul class="feature-itens"><li>Piscina</li><li>Academia</li><li>Academia</li></ul></div>
    '''
    result = parse_detail_page(html, "http://test.com/123")
    assert result is not None
    assert result["preco_venda"] == 1500000.0
    assert result["area_util"] == 100.0
    assert result["quartos"] == 3
    assert result["suites"] == 1
    assert result["vagas"] == 2
    assert result["valor_condominio"] == 1000.0
    assert result["valor_iptu"] == 500.0
    assert result["bairro_quadra"] == "Asa Sul"
    assert result["descricao_texto"] == "Descrição completa com IPTU anual incluso."
    assert result["iptu_periodo"] == "anual"
    assert result["comodidades_lista"] == "Academia, Piscina"
    assert result["id_anuncio"] == "123"
    assert result["url_anuncio"] == "http://test.com/123"
    # data_coleta should be a string (isoformat)
    assert isinstance(result["data_coleta"], str)
