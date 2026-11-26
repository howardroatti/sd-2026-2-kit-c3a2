"""
API Gateway - porta de entrada unica da plataforma.

JA PRONTO: roteamento para o servico de inferencia e log de requisicoes.
TAREFA 1: autenticacao por JWT.
TAREFA 2: limite de requisicoes por cliente (rate limit).

Rodar: uvicorn servicos.gateway.app:app --port 8000
"""
import os
import time

import requests
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI(title="Gateway - C3.A2")
URL_INFERENCIA = os.getenv("URL_INFERENCIA", "http://localhost:8001")


class Entrada(BaseModel):
    texto: str


@app.middleware("http")
async def registrar(request: Request, call_next):
    inicio = time.time()
    resposta = await call_next(request)
    ms = (time.time() - inicio) * 1000
    print(f"[gateway] {request.method} {request.url.path} "
          f"-> {resposta.status_code} ({ms:.1f}ms)")
    return resposta


@app.get("/saude")
def saude():
    return {"status": "ok"}


@app.post("/predict")
def predict(entrada: Entrada):
    # TAREFA 1: exigir um token JWT valido aqui (401 se ausente/invalido).
    # TAREFA 2: aplicar limite de requisicoes por cliente.
    try:
        r = requests.post(f"{URL_INFERENCIA}/predict",
                          json=entrada.model_dump(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=503,
                            detail=f"servico de inferencia indisponivel: {e}")


# TAREFA 1 (continuacao): rota de login que emite o token.
# @app.post("/login")
# def login(...): ...
