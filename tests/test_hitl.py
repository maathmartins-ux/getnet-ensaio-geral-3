"""Supervisão humana de produção: o HITL retoma o plano, o caso tem SLA e a ação pendente tem prazo.

- resposta do operador → o assistente escreve na hora a próxima mensagem ao cliente a partir dela (retomada);
- ação de risco alto: confirmação do dono E aprovação do operador (quatro olhos); executa uma vez só;
- ação pendente expira (ACTION_TTL_MIN); caso aberto com SLA vencido sobe de prioridade uma vez;
- duas respostas simultâneas ao mesmo caso: uma vence.
"""
import hashlib
import threading

import pytest
from fakes import fake_llm, resp, text
from fastapi.testclient import TestClient

from app import actions, resume
from app.api import app
from app.auth import issue_token
from app.store import get_store

client = TestClient(app)
OP = {"X-Operator-Token": "test-operator"}
ANA = {"X-Operator-Token": "chave-pessoal-da-ana"}  # OPERATOR_KEYS do fixture `personal_key`


@pytest.fixture
def personal_key(monkeypatch):
    """Chave pessoal da Ana ao lado do token compartilhado (migração: os dois valem) — só ela aprova risco alto."""
    monkeypatch.setenv("OPERATOR_KEYS", "ana:" + hashlib.sha256(b"chave-pessoal-da-ana").hexdigest())
    monkeypatch.setenv("OPERATOR_SHARED_TOKEN", "on")


def auth(user="u1"):
    return {"Authorization": f"Bearer {issue_token(user)}"}


def chat(message, conv=None, user="u1"):
    return client.post("/chat", json={"message": message, "conversation_id": conv}, headers=auth(user)).json()


# --- retomada --------------------------------------------------------------------------------------
def test_operator_reply_resumes_the_conversation_immediately():
    r0 = chat("Quero falar com um atendente")
    ticket, conv = r0["handoff"]["ticket_id"], r0["conversation_id"]
    r = client.post(f"/handoffs/{ticket}/reply", json={"answer": "Seu limite de antecipação é R$ 5.000,00."},
                    headers=OP).json()
    assert r["ticket"]["status"] == "answered" and r["ticket"]["answered_by"] == "admin"
    assert "5.000,00" in r["resumed"]["answer"]
    msgs = client.get(f"/conversations/{conv}", headers=auth()).json()["messages"]
    assert [m["role"] for m in msgs][-2:] == ["human_agent", "assistant"]  # sem esperar o próximo turno
    assert msgs[-1]["intent"] == "resumed"


def test_resume_with_llm_treats_human_answer_as_authority(monkeypatch):
    llm, msgs = fake_llm([resp("end_turn", text("O atendente confirmou: limite de R$ 5.000,00."))], effort="medium")
    monkeypatch.setattr(resume, "get_llm", lambda role="agent": llm)
    r0 = chat("Quero falar com um atendente")
    out = client.post(f"/handoffs/{r0['handoff']['ticket_id']}/reply",
                      json={"answer": "Limite de R$ 5.000,00."}, headers=OP).json()
    sent = msgs.sent[0]
    assert "Limite de R$ 5.000,00." in sent["messages"][-1]["content"] and "autoridade" in sent["system"]
    assert out["resumed"]["answer"].startswith("O atendente confirmou") and out["resumed"]["unsupported_numbers"] == []


def test_resumed_message_gets_the_same_cleanup_as_the_final_answer(monkeypatch):
    """A redação da retomada passa pela limpeza da resposta final do turno (antes, só pela máscara de PII): a citação
    do cartão sai com a oração dela e o nome de agente vira palavras, na resposta e no histórico."""
    llm, _ = fake_llm([resp("end_turn", text(
        "Segundo a [policy:capabilities], a antecipação precisa da sua confirmação. "
        "O atendente consultou o records_agent e confirmou o limite de R$ 5.000,00."))], effort="medium")
    monkeypatch.setattr(resume, "get_llm", lambda role="agent": llm)
    r0 = chat("Quero falar com um atendente")
    out = client.post(f"/handoffs/{r0['handoff']['ticket_id']}/reply",
                      json={"answer": "Limite de R$ 5.000,00."}, headers=OP).json()
    answer = out["resumed"]["answer"]
    assert answer == ("A antecipação precisa da sua confirmação. "
                      "O atendente consultou os dados da sua conta e confirmou o limite de R$ 5.000,00.")
    msgs = client.get(f"/conversations/{r0['conversation_id']}", headers=auth()).json()["messages"]
    assert msgs[-1]["content"] == answer  # o turno seguinte relê o texto limpo, não o código


def test_resumed_step_text_gets_the_same_cleanup(monkeypatch):
    """O texto do passo retomado depois do humano (sem LLM: o template e o faq) também sai sem código interno."""
    from app import cases, supervisor
    from app.agents import AgentResult, Context

    monkeypatch.setitem(supervisor.AGENTS, "faq", lambda ctx: AgentResult(
        "faq", "ok", text="Conforme [policy:capabilities], o prazo de entrega é de 2 dias úteis, segundo o faq_agent.",
        evidence=["O prazo de entrega é de 2 dias úteis."]))
    r0 = chat("Quero falar com um atendente")
    ticket, conv = r0["handoff"]["ticket_id"], r0["conversation_id"]
    cases.save_pending(ticket, Context(text="Qual o prazo de entrega?", language="pt", user_id="u1",
                                       conversation_id=conv, intent="faq"), ["faq"])
    resumed = client.post(f"/handoffs/{ticket}/reply", json={"answer": "Verifiquei o seu pedido."},
                          headers=OP).json()["resumed"]
    assert resumed["resumed_steps"] == ["faq"] and resumed["engine"] == "template"
    assert resumed["answer"] == ("Resposta do atendente: Verifiquei o seu pedido.\n\n"
                                 "O prazo de entrega é de 2 dias úteis, segundo a base de conhecimento.")


def test_resume_imports_the_cleanup_without_an_import_cycle():
    """resume.py importa a limpeza de pipeline só na hora da retomada: pipeline → supervisor → resume (tardio) não
    vira ciclo, e resume continua importável sozinho, antes de pipeline."""
    import os
    import subprocess
    import sys

    from app.config import ROOT

    code = ("import sys, app.resume as r; assert 'app.pipeline' not in sys.modules; "
            "print(r._scrub('Veja o faq_agent [policy:capabilities].', 'pt'))")
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "DOMAIN": "example"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60, env=env, cwd=ROOT,
                         check=True)
    assert out.stdout.strip() == "Veja a base de conhecimento."


def test_two_simultaneous_replies_only_one_wins():
    ticket = chat("Quero falar com um atendente")["handoff"]["ticket_id"]
    codes = []

    def answer(i):
        codes.append(client.post(f"/handoffs/{ticket}/reply", json={"answer": f"resposta {i}"}, headers=OP).status_code)

    threads = [threading.Thread(target=answer, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(codes) == [200, 404, 404, 404]


# --- aprovação de quatro olhos ---------------------------------------------------------------------------
def test_high_risk_action_needs_owner_then_operator_and_runs_once(personal_key):
    r = chat("Quero o estorno do pedido 1001")
    aid = r["pending_action"]
    assert aid and "Nada foi feito" in r["answer"]
    owner = client.post(f"/actions/{aid}/confirm", headers=auth()).json()
    assert owner["awaiting_operator"] is True and owner["ticket_id"]
    assert get_store().get_action(aid)["status"] == "awaiting_operator"  # dono confirmou, ainda não executou
    queue = client.get("/handoffs", headers=OP).json()
    assert any(t["kind"] == "approval" and t["action_id"] == aid for t in queue)

    assert client.post(f"/actions/{aid}/approve", headers={"X-Operator-Token": "errado"}).status_code == 403
    # o token compartilhado não aprova risco alto: a aprovação tem dono (chave pessoal) na auditoria
    assert client.post(f"/actions/{aid}/approve", headers=OP).status_code == 403
    assert get_store().get_action(aid)["status"] == "awaiting_operator"
    done = client.post(f"/actions/{aid}/approve", headers=ANA).json()
    assert done["result"]["ok"] is True and done["action"]["approved_by"] == "ana"
    assert client.post(f"/actions/{aid}/approve", headers=ANA).status_code == 409  # executa uma vez só
    conv = r["conversation_id"]
    last = client.get(f"/conversations/{conv}", headers=auth()).json()["messages"][-1]
    assert last["role"] == "assistant" and "aprovad" in last["content"].lower()


def test_rejected_high_risk_action_runs_nothing(personal_key):
    aid = chat("Quero o estorno do pedido 1001")["pending_action"]
    client.post(f"/actions/{aid}/confirm", headers=auth())
    out = client.post(f"/actions/{aid}/reject", json={"answer": "Fora da política."}, headers=OP).json()
    assert out["action"]["status"] == "rejected" and out["result"] is None
    assert client.post(f"/actions/{aid}/approve", headers=ANA).status_code == 409


def test_normal_write_action_still_runs_on_owner_confirmation():
    aid = chat("Quero cancelar o pedido 1001")["pending_action"]
    assert client.post(f"/actions/{aid}/confirm", headers=auth()).json()["ok"] is True


# --- TTL e SLA ------------------------------------------------------------------------------------------
def test_pending_action_expires(monkeypatch):
    aid = chat("Quero cancelar o pedido 1001")["pending_action"]
    real = actions.time.time
    monkeypatch.setattr(actions.time, "time", lambda: real() + 16 * 60)  # TTL padrão: 15 min
    r = client.post(f"/actions/{aid}/confirm", headers=auth())
    assert r.status_code == 410 and get_store().get_action(aid)["status"] == "expired"


def test_overdue_case_is_escalated_once():
    ticket = chat("Quero falar com um atendente")["handoff"]["ticket_id"]
    store = get_store()
    assert store.escalate_overdue() == []  # ainda no prazo
    due = store.get_ticket(ticket)["due_at"]
    first = client.post("/handoffs/sla-check", params={"now": due + 1}, headers=OP).json()
    assert [t["id"] for t in first["escalated"]] == [ticket]
    assert store.get_ticket(ticket)["priority"] == "high" and store.get_ticket(ticket)["escalation_level"] == 1
    assert client.post("/handoffs/sla-check", params={"now": due + 2}, headers=OP).json()["escalated"] == []


def test_a_personal_key_named_admin_is_reserved(monkeypatch):
    """"admin" é o nome do token compartilhado: uma chave pessoal com esse nome seria lida como ele (sem dono na
    auditoria e sem aprovar risco alto). Ela fica de fora da configuração e a produção acusa."""
    from app import api
    from app.config import operator_keys, operator_keys_reserved

    monkeypatch.setenv("OPERATOR_KEYS", "admin:" + hashlib.sha256(b"k").hexdigest() + ",ana:"
                       + hashlib.sha256(b"chave-pessoal-da-ana").hexdigest())
    assert set(operator_keys()) == {"ana"} and operator_keys_reserved()
    assert "OPERATOR_KEYS com o nome reservado admin" in api.production_gaps()
    from app import auth
    assert auth.main(["operator-key", "admin"]) == 2
