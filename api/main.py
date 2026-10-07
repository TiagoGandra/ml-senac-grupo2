import pickle
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

RAIZ = Path(__file__).resolve().parent.parent
COLUNAS = ["tipo_imovel", "bairro_quadra", "area_util", "quartos", "suites", "vagas", "valor_condominio"]

recursos = {}


def _carregar(caminho: Path):
    with open(caminho, "rb") as f:
        return pickle.load(f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    recursos["modelo"] = _carregar(RAIZ / "imoveis-modelo.pickle")
    recursos["lb_tipo"] = _carregar(RAIZ / "data" / "lb_tipo.pickle")
    recursos["lb_bairro"] = _carregar(RAIZ / "data" / "lb_bairro.pickle")
    yield
    recursos.clear()


app = FastAPI(title="API de Predição de Preço de Imóveis", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    tipo_imovel: str
    bairro: str
    quartos: int = Field(ge=0)
    suites: int = Field(ge=0)
    vagas: int = Field(ge=0)
    area_util: float = Field(gt=0)
    valor_condominio: Optional[float] = Field(default=None, ge=0)


class PredictResponse(BaseModel):
    preco_previsto: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/options")
def options():
    return {
        "tipos": [str(c) for c in recursos["lb_tipo"].classes_],
        "bairros": [str(c) for c in recursos["lb_bairro"].classes_],
    }


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        tipo = int(recursos["lb_tipo"].transform([req.tipo_imovel])[0])
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Tipo de imóvel desconhecido: {req.tipo_imovel}")
    try:
        bairro = int(recursos["lb_bairro"].transform([req.bairro])[0])
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Bairro desconhecido: {req.bairro}")

    # Condomínio nulo vira 0.0, igual ao ETL (fillna(0.0))
    condominio = req.valor_condominio if req.valor_condominio is not None else 0.0
    x = pd.DataFrame(
        [[tipo, bairro, req.area_util, req.quartos, req.suites, req.vagas, condominio]],
        columns=COLUNAS,
    )
    preco = float(recursos["modelo"].predict(x)[0])
    return PredictResponse(preco_previsto=preco)
