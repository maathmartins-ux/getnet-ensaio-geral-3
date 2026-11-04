"""R13-E: pergunta composta com parte geral (clima, câmbio) e outra do negócio roda as DUAS partes.

No ensaio de 60 min (rodada 12) o agente geral só rodava quando a intenção do turno inteiro era `general` e o passo
dele saía `faq` no trace: "Qual a taxa do credito parcelado e vai chover em Salvador hoje?" foi ao faq duas vezes, sem
fonte para o clima, e escalou; "vai chover em Curitiba sabado? ah e mostra minhas vendas de ontem" ignorou o clima.
Aqui o domínio de exemplo declara o agente geral (`general` em MULTI_PARTS) e a regra de clima do router: a parte
geral entra no `multi` como agente próprio (`general`), em paralelo com o outro, nos dois motores; sozinho, o geral
continua igual (só o nome do passo muda); a parte geral nunca escala.
"""
import json
import re

import pytest
from fakes import fake_llm, resp, text, tool_use

from app import agents, live_data, router, supervisor
from app.agents import AgentResult, Context
from app.schemas import ChatRequest, Source

COMPOSITE = "Qual a taxa do credito parcelado e vai chover em Salvador hoje?"  # a frase do held-out do ensaio
GEO = {"results": [{"name": "Salvador", "admin1": "Bahia", "country": "Brasil", "latitude": -12.97,
                    "longitude": -38.5, "timezone": "America/Bahia"}]}
FORECAST = {"daily": {"time": ["2026-11-04"], "temperature_2m_max": [30.2], "temperature_2m_min": [24.1],
                      "precipitation_probability_max": [70], "weather_code": [61]}}


@pytest.fixture
def general_domain(monkeypatch):
    """O domínio de exemplo com agente geral, como o desafio declara: intenção `general` (plano antigo ["faq"], que o
    motor troca pelo agente geral), `general` em MULTI_PARTS, NO_ESCALATION e a regra de clima/câmbio do router."""
    from app.domain import example

    rules = example.clause_intent

    def clause_intent(text_, history, r):
        if live_data.is_weather(text_) or live_data.currency_of(text_):
            return "general"
        if re.search(r"\b(taxa|cr[eé]dito|parcelad\w*)\b", text_, re.IGNORECASE):  # produto do desafio: base
            return "faq"
        return rules(text_, history, r)

    monkeypatch.setattr(example, "PLANS", {**example.PLANS, "general": ["faq"]})
    monkeypatch.setattr(example, "MULTI_PARTS", {"faq", "records", "general"})
    monkeypatch.setattr(example, "NO_ESCALATION", {"general"})
    monkeypatch.setattr(example, "clause_intent", clause_intent)
    monkeypatch.setattr(example, "DISAMBIGUATION", {"ask_words": ["qual", "quanto", "vai chover"]}, raising=False)
    monkeypatch.setenv("LIVE_DATA", "on")
    monkeypatch.setattr(live_data, "_get_json", lambda url, params: GEO if url == live_data.GEOCODING else FORECAST)
    return example


def ctx(text_, intent="multi", **facts):
    c = Context(text=text_, language="pt", user_id="u1", conversation_id="c-r13e", intent=intent)
    c.facts.update(facts)
    return c


# --- router: a parte geral entra no multi -------------------------------------------------------------------------
def test_rules_route_the_composite_to_both_parts(general_domain):
    d = router.classify_offline(COMPOSITE, [])
    assert (d.intent, d.plan) == ("multi", ["faq", "general"])
    d = router.classify_offline("vai chover em Curitiba sabado? ah e mostra meu pedido 1002", [])
    assert (d.intent, d.plan) == ("multi", ["records", "general"])
    # o multi do negócio segue igual, e o geral sozinho segue geral
    assert router.classify_offline("Qual o prazo de entrega? E o meu pedido 1002?", []).plan == ["faq", "records"]
    alone = router.classify_offline("Vai chover em Salvador hoje?", [])
    assert alone.intent == "general"


def test_without_general_in_multi_parts_nothing_changes(monkeypatch):
    """Domínio que não declara o agente geral (o exemplo como está): a pergunta composta segue como antes."""
    assert router.classify_offline(COMPOSITE, []).plan == ["faq"]
    assert [t["name"] for t in supervisor.tools_for()] == ["faq_agent", "records_agent", "escalation_agent"]
    assert "general" not in router.schema()["properties"]["plan"]["items"]["enum"]


def test_llm_router_multi_without_general_gets_the_general_step(general_domain, monkeypatch):
    """Router LLM disse multi com o plano do negócio só: as regras do domínio veem a parte geral e ela entra."""
    raw = {"standalone": COMPOSITE, "search_queries": ["taxa crédito parcelado"], "intent": "multi",
           "plan": ["faq", "records"], "language": "pt", "confidence": 0.9}
    llm, msgs = fake_llm([resp("end_turn", text(json.dumps(raw)))])
    monkeypatch.setattr(router, "get_llm", lambda role="router": llm)
    decision = router.route(COMPOSITE, [])
    assert decision.intent == "multi" and decision.plan == ["faq", "records", "general"]
    schema = msgs.sent[0]["output_config"]["format"]["schema"]["properties"]["plan"]
    assert "general" in schema["items"]["enum"] and "general" in schema["description"]


# --- motor de tabela (sem LLM): as duas partes rodam, em paralelo ------------------------------------------------
def test_table_engine_answers_both_parts_with_the_general_step_named(general_domain):
    from app.pipeline import handle

    got = handle(ChatRequest(message="Qual o prazo de entrega? E vai chover em Salvador hoje?"), "u1", True)
    assert got.intent == "multi" and got.route == ["router", "faq", "general"]
    assert [s["agent"] for s in got.steps] == ["faq", "general"]
    assert not got.handoff.required and "escalation" not in got.route
    assert "Salvador" in got.answer and "70" in got.answer  # a chance de chuva da consulta ao vivo
    assert got.sources and any("open-meteo" in s.url for s in got.sources)
    general = next(s for s in got.steps if s["agent"] == "general")
    assert general["decided_by"] == "router" and general["status"] == "ok"


def test_the_general_part_never_escalates_but_the_other_part_still_does(general_domain, monkeypatch):
    monkeypatch.setitem(supervisor.AGENTS, "faq", lambda c: AgentResult("faq", "ok", text="Prazo: 5 dias [doc-1].",
                                                                         sources=[Source(id="doc-1", title="t",
                                                                                         url="u")]))
    monkeypatch.setitem(supervisor.AGENTS, "general", lambda c: AgentResult("general", "error", reason="exception:X"))
    out = supervisor.run(["faq", "general"], ctx(COMPOSITE))
    assert out.route == ["faq", "general"] and not out.replans  # falha da parte geral: sem FALLBACK para o humano
    # a parte do negócio sem fonte segue a regra de sempre: outro especialista respondeu parte → oferta do humano
    monkeypatch.setitem(supervisor.AGENTS, "faq", lambda c: AgentResult("faq", "insufficient", reason="no_source"))
    monkeypatch.setitem(supervisor.AGENTS, "general", lambda c: AgentResult("general", "ok", text="Chuva: 70%."))
    out = supervisor.run(["faq", "general"], ctx(COMPOSITE))
    assert out.route == ["faq", "general"] and out.results[1].text.endswith(supervisor.OFFER_HUMAN["pt"])
    # sozinha, a parte do negócio sem fonte vai ao humano (FALLBACK do faq), como antes
    out = supervisor.run(["faq"], ctx("Qual a taxa do credito parcelado?", intent="faq"))
    assert out.route == ["faq", "escalation"] and out.replans == ["faq:no_source->escalation"]


# --- motor LLM (LLM falso): o supervisor chama o geral na mesma resposta que o faq ----------------------------------
def test_llm_supervisor_calls_the_general_agent_in_parallel_for_its_part(general_domain, monkeypatch):
    monkeypatch.setenv("SUPERVISOR_FAST", "off")
    seen: dict = {}

    def faq(c):
        seen["faq_ask"] = c.facts["ask"]["faq"]
        return AgentResult("faq", "ok", text="O crédito parcelado tem taxa de 3,49% [doc-1].",
                           sources=[Source(id="doc-1", title="Taxas", url="https://x/taxas")], evidence=["3,49%"])

    monkeypatch.setitem(supervisor.AGENTS, "faq", faq)
    weather = ("Hoje em Salvador: mínima de 24,1 °C, máxima de 30,2 °C e 70% de chance de chuva (Open-Meteo, "
               "04/11/2026).")
    agent, agent_msgs = fake_llm([resp("tool_use", tool_use("weather_forecast", {"city": "Salvador"})),
                                  resp("end_turn", text(weather))])
    monkeypatch.setattr(agents, "get_llm", lambda role="agent": agent)
    final = f"O crédito parcelado tem taxa de 3,49% [doc-1]. {weather}"
    sup, sup_msgs = fake_llm([
        resp("tool_use", tool_use("faq_agent", {"query": "taxa do crédito parcelado"}, "t1"),
             tool_use("general_agent", {"query": "vai chover em Salvador hoje?"}, "t2")),
        resp("end_turn", text(final))])
    monkeypatch.setattr(supervisor, "get_llm", lambda role="supervisor": sup)
    out = supervisor.run(["faq", "general"], ctx(COMPOSITE))
    assert "general_agent" in [t["name"] for t in sup_msgs.sent[0]["tools"]]
    assert out.route == ["faq", "general"] and not out.replans  # os dois do plano, na mesma volta
    assert [supervisor.step_view(r)["agent"] for r in out.results] == ["faq", "general"]
    assert all(supervisor.step_view(r)["decided_by"] == "llm" for r in out.results)
    assert seen["faq_ask"] == "taxa do crédito parcelado"
    # o modelo do agente geral recebeu só a parte dele
    assert "Parte que cabe a você: vai chover em Salvador hoje?" in agent_msgs.sent[0]["messages"][-1]["content"]
    assert out.results[1].text == weather and out.answer == final
    assert agents.live_missing(out.answer, out.results[1].live_must, "pt") == []


def test_general_alone_is_unchanged_but_named_general(general_domain, monkeypatch):
    """Turno só geral: o plano antigo ["faq"] e a tool faq_agent viram o agente geral; resposta igual à de antes."""
    monkeypatch.setenv("SUPERVISOR_FAST", "off")
    out = supervisor.run(["faq"], ctx("Vai chover em Salvador hoje?", intent="general"))  # sem LLM: a tabela
    assert out.route == ["general"] and out.results[0].agent == "general"
    assert "Salvador" in out.results[0].text and "70" in out.results[0].text
    weather = "Hoje em Salvador: mínima de 24,1 °C, máxima de 30,2 °C e 70% de chance de chuva."
    agent, agent_msgs = fake_llm([resp("tool_use", tool_use("weather_forecast", {"city": "Salvador"})),
                                  resp("end_turn", text(weather))])
    monkeypatch.setattr(agents, "get_llm", lambda role="agent": agent)
    sup, _ = fake_llm([resp("tool_use", tool_use("faq_agent", {"query": "chuva em Salvador"})),
                       resp("end_turn", text(weather))])
    monkeypatch.setattr(supervisor, "get_llm", lambda role="supervisor": sup)
    out = supervisor.run(["faq"], ctx("Vai chover em Salvador hoje?", intent="general"))
    assert out.route == ["general"] and supervisor.step_view(out.results[0])["agent"] == "general"
    # a mensagem inteira é do geral: vai sem o recorte de parte
    assert agent_msgs.sent[0]["messages"][-1]["content"].startswith("Vai chover em Salvador hoje?")


def test_faq_agent_called_directly_on_a_general_turn_answers_as_general(monkeypatch):
    monkeypatch.setenv("LIVE_DATA", "off")
    r = agents.faq_agent(ctx("Quanto está o dólar hoje?", intent="general"))
    assert r.agent == "general" and r.status == "ok"
    assert agents.AGENTS["general"] is agents.general_agent
    assert router.GENERAL == agents.GENERAL == supervisor.GENERAL


# --- placar de agente esperado: gravação antiga com o geral como faq ------------------------------------------------
def test_scoreboard_accepts_faq_as_the_general_step_of_old_recordings():
    from evals import run_evals

    case = {"expect": {"intent": "general", "handoff": False, "agents": ["general"]}}
    old = {"intent": "general", "route": ["router", "faq"], "handoff": {"required": False}, "answer": "x"}
    new = {"intent": "general", "route": ["router", "general"], "handoff": {"required": False}, "answer": "x"}
    assert run_evals.score(case, old)["handoff_outcome"] and run_evals.score(case, new)["handoff_outcome"]
    legacy_case = {"expect": {"intent": "general", "handoff": False, "agents": ["faq"]}}
    assert run_evals.score(legacy_case, new)["handoff_outcome"]
    # no multi, faq é a base de conhecimento: não vale pelo geral
    multi = {"expect": {"intent": "multi", "handoff": False, "agents": ["general"]}}
    got = {"intent": "multi", "route": ["router", "faq"], "handoff": {"required": False}, "answer": "x"}
    assert not run_evals.score(multi, got)["handoff_outcome"]
