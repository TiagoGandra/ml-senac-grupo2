import pytest
from fastapi.testclient import TestClient

from api.main import app

BASE = {"tipo_imovel": "apartamento", "bairro": "Asa Sul", "quartos": 3,
        "suites": 1, "vagas": 2, "area_util": 120.0, "valor_condominio": 800.0}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_options(client):
    r = client.get("/options")
    assert r.status_code == 200
    assert "apartamento" in r.json()["tipos"]
    assert "Asa Sul" in r.json()["bairros"]


def test_predict(client):
    r = client.post("/predict", json=BASE)
    assert r.status_code == 200
    assert r.json()["preco_previsto"] > 0


def test_predict_condominio_nulo(client):
    r = client.post("/predict", json={**BASE, "valor_condominio": None})
    assert r.status_code == 200


def test_tipo_invalido(client):
    assert client.post("/predict", json={**BASE, "tipo_imovel": "castelo"}).status_code == 422


def test_area_invalida(client):
    assert client.post("/predict", json={**BASE, "area_util": 0}).status_code == 422
