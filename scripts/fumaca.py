"""
Teste de fumaça — executa o fluxo COMPLETO da plataforma de fora para dentro:

  1. /saude                              (gateway no ar)
  2. /predict SEM token                  (deve dar 401 — segurança)
  3. /login                              (emite JWT)
  4. /predict com token                  (caminho síncrono resiliente)
  5. /tarefas + /tarefas/{id}            (caminho assíncrono: fila + worker)
  6. /memoria/busca                      (armazenamento vetorial)

Uso:  python scripts/fumaca.py            (gateway local)
      BASE=https://sua-url.onrender.com python scripts/fumaca.py

Apenas biblioteca padrão (urllib) — roda em qualquer máquina, sem instalar nada.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.getenv("BASE", "http://localhost:8000").rstrip("/")
USUARIO = os.getenv("USUARIO", "aluno")
SENHA = os.getenv("SENHA", "aluno123")
JAEGER_URL = os.getenv("JAEGER_URL", "").rstrip("/")

passos_ok = 0


def requisicao(metodo: str, caminho: str, corpo=None, token=None, *, base=BASE) -> tuple[int, dict]:
    pedido = urllib.request.Request(base + caminho, method=metodo)
    pedido.add_header("Content-Type", "application/json")
    # O User-Agent padrão do urllib é bloqueado por CDNs (ex.: Cloudflare, erro 1010).
    pedido.add_header("User-Agent", "plataforma-ia-fumaca/1.0")
    if token:
        pedido.add_header("Authorization", f"Bearer {token}")
    dados = json.dumps(corpo).encode() if corpo is not None else None
    try:
        with urllib.request.urlopen(pedido, data=dados, timeout=90) as resposta:
            return resposta.status, json.loads(resposta.read().decode() or "{}")
    except urllib.error.HTTPError as erro:
        try:
            return erro.code, json.loads(erro.read().decode() or "{}")
        except Exception:
            return erro.code, {}


def passo(nome: str, condicao: bool, detalhe: str = "") -> None:
    global passos_ok
    estado = "OK " if condicao else "FALHOU"
    print(f"[{estado}] {nome}{(' — ' + detalhe) if detalhe else ''}")
    if not condicao:
        print("\nFalhou no passo: " + nome)
        print("Verifique: docker compose ps && docker compose logs gateway worker")
        sys.exit(1)
    passos_ok += 1


# 1. Gateway no ar
status, corpo = requisicao("GET", "/saude")
passo("1. /saude responde", status == 200 and corpo.get("status") == "ok", str(corpo))

# 2. Sem token -> 401 (autenticação ativa)
status, corpo = requisicao("POST", "/predict", {"texto": "teste sem token"})
passo("2. /predict sem token dá 401", status == 401, f"status={status}")

# 3. Login emite JWT
status, corpo = requisicao("POST", "/login", {"usuario": USUARIO, "senha": SENHA})
token = corpo.get("token", "")
passo("3. /login emite token", status == 200 and len(token) > 20, f"status={status}")

if os.getenv("FALHA_INFERENCIA") == "1":
    for motivo in ("inferência indisponível", "circuito aberto"):
        status, corpo = requisicao("POST", "/predict", {"texto": "teste de falha"}, token)
        passo(f"Fallback: {motivo}", status == 202 and corpo.get("motivo") == motivo)
    sys.exit(0)

# 4. /predict com token (síncrono)
status, corpo = requisicao("POST", "/predict", {"texto": "o atendimento foi excelente"}, token)
passo(
    "4. /predict classificou",
    status == 200 and corpo.get("rotulo") in ("positivo", "negativo"),
    f"status={status} rotulo={corpo.get('rotulo')} confianca={corpo.get('confianca')}",
)

# 5. Caminho assíncrono: /tarefas -> consulta até concluir (fila + worker)
status, corpo = requisicao("POST", "/tarefas", {"texto": "o produto chegou quebrado"}, token)
id_tarefa = corpo.get("id", "")
passo("5a. /tarefas enfileirou (202)", status in (200, 202) and id_tarefa != "", f"status={status} id={id_tarefa}")

resultado = None
limite = time.time() + 60
while time.time() < limite:
    status, corpo = requisicao("GET", f"/tarefas/{id_tarefa}", token=token)
    if status == 200 and corpo.get("status") == "falhou":
        passo("5b. tarefa concluída pelo worker", False, "worker registrou falha")
    if status == 200 and corpo.get("status") == "concluido":
        resultado = corpo
        break
    time.sleep(3)
passo(
    "5b. tarefa concluída pelo worker",
    resultado is not None,
    f"rotulo={resultado.get('rotulo')}" if resultado else "timeout de 60s",
)

# 6. Memória vetorial
status, corpo = requisicao(
    "POST", "/memoria/busca", {"texto": "o produto chegou quebrado", "k": 20}, token
)
passo(
    "6. /memoria/busca encontrou o vetor da tarefa",
    status == 200 and any(item.get("tarefa_id") == id_tarefa for item in corpo.get("resultados", [])),
    f"total={corpo.get('total')}",
)

if JAEGER_URL:
    consulta = urllib.parse.urlencode({"service": "gateway", "operation": "fila.publicar"})
    trace_id = None
    esperado = {"fila.publicar", "worker.processar_tarefa", "inferencia.classificar", "worker.salvar_vetor"}
    for _ in range(15):
        status, corpo = requisicao("GET", f"/api/traces?{consulta}", base=JAEGER_URL)
        for trace in corpo.get("data") or []:
            spans = trace["spans"]
            if not esperado.issubset(span["operationName"] for span in spans):
                continue
            if any(tag["key"] == "tarefa.id" and tag["value"] == id_tarefa
                   for span in spans for tag in span["tags"]):
                trace_id = trace["traceID"]
                break
        if trace_id:
            break
        time.sleep(1)
    passo("7. trace da tarefa confirmado no Jaeger", trace_id is not None, trace_id or "trace ausente")

print(f"\nSucesso: {passos_ok} passos do fluxo completo passaram em {BASE}")
