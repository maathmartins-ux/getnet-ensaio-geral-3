"""Tools do Customer Support (domínio do desafio): contas no código, isolamento, schema e caminho offline."""
from __future__ import annotations

import json
from datetime import date, datetime

import pytest

from app import actions, agents, clock
from app.domain.challenge import tools as T

WED = date(2026, 11, 4)  # quarta-feira: ontem = terça
SAT = date(2026, 11, 7)  # sábado: ontem = sexta (débito cai na segunda)


@pytest.fixture
def crm(domain_data, monkeypatch):
    T._load.cache_clear()
    monkeypatch.setattr(clock, "today", lambda: WED)
    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 11, 4, 15, 0))
    yield
    T._load.cache_clear()


def _ctx(text, lang="pt", user="cliente1988", history=None):
    return agents.Context(text=text, language=lang, user_id=user, conversation_id="c-tools", intent="records",
                          history=history or [])


def test_nomes_congelados_schema_fechado_sem_identidade(crm):
    assert set(T.TOOLS) == {"get_transactions", "get_settlements", "get_terminals", "open_support_ticket",
                            "request_receivables_advance"}
    for name, tool in T.TOOLS.items():
        schema = tool["input_schema"]
        assert schema["additionalProperties"] is False, name
        assert not {"user_id", "owner", "merchant_id"} & set(schema["properties"]), name
    assert T.TOOLS["open_support_ticket"]["write"] and "risk" not in T.TOOLS["open_support_ticket"]
    assert T.TOOLS["request_receivables_advance"]["risk"] == "high"
    for name in ("get_transactions", "get_settlements"):
        period = T.TOOLS[name]["input_schema"]["properties"]["period"]
        assert period["enum"] == ["today", "yesterday", "last_7_days", "last_30_days"]
        assert period["default"] == "last_7_days"
    assert not {"lookup_record", "cancel_record", "refund_record"} & set(T.TOOLS)


def test_labels_pt_en():
    assert T.LABELS["sem_sinal"] == {"pt": "sem sinal", "en": "no signal"}
    assert T.LABELS["last_7_days"]["pt"] == "últimos 7 dias"
    assert T.LABELS["request_receivables_advance"]["en"] == "receivables advance"


def test_transacoes_totais_e_recusas_calculados(crm):
    out = T.get_transactions("cliente1988", "yesterday")
    tot = out["data"]["totals"]
    assert tot["approved_count"] == 3 and tot["approved_total"] == "R$ 695,50"
    assert set(tot["by_method"]) == {"pix", "debito", "credito"}
    assert any(s["transaction_id"] == "TX1002" and s["amount"] == "R$ 480,00" for s in out["data"]["sales"])
    assert "needs" not in out  # sem recusa ontem
    today = T.get_transactions("cliente1988", "today")
    dec = {d["transaction_id"]: d for d in today["data"]["declines"]}
    assert dec["TX1007"]["decline_code"] == "51" and dec["TX1007"]["amount"] == "R$ 210,00"
    assert "insuficiente" in dec["TX1007"]["decline_meaning_pt"]
    assert dec["TX1008"]["decline_code"] == "05" and "issuer" in dec["TX1008"]["decline_meaning_en"]
    assert today["needs"][0]["agent"] == "faq"
    week = T.get_transactions("cliente1988")
    assert any(s.get("contestable") for s in week["data"]["sales"] if s["transaction_id"] == "TX1006")


def test_depositos_pix_d0_debito_d1_util_credito_d30(crm, monkeypatch):
    sched = {g["method"]: g for g in T.get_settlements("cliente1988", "yesterday")["data"]["schedule"]}
    assert sched["pix"]["deposit_dates"] == ["2026-11-03"]
    assert sched["debito"]["deposit_dates"] == ["2026-11-04"]
    assert sched["credito"]["deposit_dates"] == ["2026-12-03"] and sched["credito"]["total"] == "R$ 480,00"
    monkeypatch.setattr(clock, "today", lambda: SAT)  # venda de sexta no débito cai na segunda
    friday = {g["method"]: g for g in T.get_settlements("cliente1988", "yesterday")["data"]["schedule"]}
    assert friday["debito"]["deposit_dates"] == ["2026-11-09"]


def test_credito_segue_o_plano_de_recebimento_do_lojista_como_no_site(crm, monkeypatch):
    """O site oferece receber o crédito em 2 dias úteis ou em 30 dias (ou mês a mês); o prazo do crédito sai do plano
    do lojista no CRM, não de uma regra fixa. O plano vai no resultado, para a resposta dizer de onde vem a data."""
    sched = {g["method"]: g for g in T.get_settlements("cliente1988", "yesterday")["data"]["schedule"]}
    assert sched["credito"]["credit_plan"] == "30_dias" and sched["credito"]["rule"] == "D+30"
    assert "credit_plan" not in sched["pix"] and "credit_plan" not in sched["debito"]
    assert T.LABELS["30_dias"]["en"] == "30-day payout plan"
    rec = {**T.records()["cliente1988"], "credit_plan": "2_dias"}
    monkeypatch.setattr(T, "_client", lambda uid: rec if uid == "cliente1988" else None)
    fast = {g["method"]: g for g in T.get_settlements("cliente1988", "yesterday")["data"]["schedule"]}
    assert fast["credito"]["deposit_dates"] == ["2026-11-05"] and fast["credito"]["rule"] == "D+2 úteis"  # ter → qui
    assert T.available_advance_cents("cliente1988") < 48000 + 15000  # menos crédito a receber no plano curto
    rec["credit_plan"] = "plano_inventado"
    assert T.credit_plan("cliente1988") == "30_dias"
    assert "2 dias úteis ou 30 dias" in T.TOOLS["get_settlements"]["description"]


def test_terminais_offline_for_hours_so_quando_offline(crm):
    out = T.get_terminals("cliente1988")
    terms = {x["terminal_id"]: x for x in out["data"]["terminals"]}
    assert terms["T1988A"]["model"] == "Get Smart" and terms["T1988A"]["connection"] == "wi-fi"
    assert "offline_for_hours" not in terms["T1988A"]
    assert terms["T1988B"]["status"] == "offline" and terms["T1988B"]["offline_for_hours"] == 5
    assert terms["T1988B"]["connection"] == "chip" and terms["T1988B"]["issue"] == "sem_sinal"
    assert out["needs"] == [T._FAQ_OFFLINE]
    assert "needs" not in T.get_terminals("cliente2024")


def test_outro_cliente_e_inexistente_sao_indistinguiveis(crm):
    other = T.open_support_ticket("cliente2024", "T1988B", "sem_sinal")
    missing = T.open_support_ticket("cliente2024", "T9999Z", "sem_sinal")
    assert other == missing == {"ok": False, "error": "not_found"}
    assert all(t["terminal_id"].startswith("T2024") for t in T.get_terminals("cliente2024")["data"]["terminals"])
    assert "cliente2024" in T.records() and "cliente1988" in T.records()


def test_escritas_viram_proposta_no_servidor(crm):
    res, _ = actions.run_tool("open_support_ticket", {"terminal_id": "T1988B", "reason": "sem_sinal"},
                              "cliente1988", "c-w")
    assert res.get("needs_confirmation") and res["action_id"]
    res, _ = actions.run_tool("request_receivables_advance", {"amount": 300.0}, "cliente1988", "c-w")
    assert res.get("needs_confirmation") and res["risk"] == "high"
    bad, _ = actions.run_tool("get_terminals", {"user_id": "cliente2024", "x": 1}, "cliente1988", "c-w")
    assert bad["error"] == "invalid_args"


def test_antecipacao_limitada_ao_credito_a_receber(crm):
    assert T.available_advance_cents("cliente1988") == 63000
    assert T.request_receivables_advance("cliente1988", 500.0)["ok"]
    assert T.request_receivables_advance("cliente1988", 1000.0)["error"] == "above_available"


def test_offline_terminais_em_frase_com_needs(crm):
    r = T.records_offline(_ctx("Which of my terminals is offline and how do I fix it?", "en"), agents)
    assert "T1988B" in r.text and "offline for 5 hours" in r.text and "no signal" in r.text
    assert r.needs and r.needs[0]["agent"] == "faq"
    pt = T.records_offline(_ctx("Qual das minhas maquininhas está offline?"), agents)
    assert "está offline há 5 horas" in pt.text and "sem sinal" in pt.text


def test_offline_recusas_e_deposito(crm):
    r = T.records_offline(_ctx("Tive vendas recusadas: quais foram e o que eu posso fazer?"), agents)
    assert "TX1007" in r.text and "código 51" in r.text and "código 05" in r.text and r.needs
    en = T.records_offline(_ctx("When will the money from yesterday's sales be deposited?", "en"), agents)
    assert "R$ 480,00" in en.text and "2026-12-03" in en.text and "2026-11-04" in en.text
    one = T.records_offline(_ctx("Por que a venda de R$ 210,00 foi recusada?"), agents)
    assert "TX1007" in one.text and "TX1008" not in one.text


def test_offline_escrita_e_isolamento(crm):
    r = T.records_offline(_ctx("Abra um chamado técnico para a minha maquininha T1988B que está sem sinal"), agents)
    assert r.pending_action and "Nada foi feito" in r.text
    adv = T.records_offline(_ctx("Please request an advance of R$ 300,00 on my receivables", "en"), agents)
    assert adv.pending_action and "R$ 300,00" in adv.text and "human agent" in adv.text
    other = T.records_offline(_ctx("Qual o valor da venda TX1002?", user="cliente2024"), agents)
    assert "Não encontrei" in other.text and "480" not in other.text


def test_needs_for_junta_todos_os_resultados(crm):
    ev = [json.dumps(T.get_terminals("cliente1988")), json.dumps(T.get_transactions("cliente1988", "today"))]
    result = agents.AgentResult("records", "ok", evidence=ev)
    found = T.needs_for(result, _ctx("Minha maquininha dá erro e não conecta"))
    assert [n["hint"] for n in found] == [T._FAQ_OFFLINE["hint"], T._FAQ_DECLINE["hint"]]
    assert T.needs_for(result, _ctx("Quanto vendi ontem?")) == []
