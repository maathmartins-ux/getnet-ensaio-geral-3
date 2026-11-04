"""Rodada 15, lição 7 do ensaio 14: o parcial é decidido no MOTOR. Uma linha MISSING só deixa a resposta parcial se
cobre um item que o cliente pediu; MISSING de item vizinho sai do texto mostrado ao cliente e não conta como parcial.
Os dois lados com as frases reais das rodadas do ensaio 14 (official-01, 04, 05, 06; memory-12)."""
import json

import pytest
from fakes import fake_llm, resp, text

from app import agents
from app.agents import Context, missing_items
from app.coverage import drop_neighbor_absence, judge_missing

DOCS = [
    {"id": "alfa", "title": "Plano Alfa", "url": "https://example.com/alfa",
     "text": "O Plano Alfa custa R$ 10 por mês e inclui entrega grátis para capitais."},
    {"id": "beta", "title": "Plano Beta", "url": "https://example.com/beta",
     "text": "O Plano Beta custa R$ 20 por mês e inclui atendimento prioritário."},
    {"id": "antecipa", "title": "Antecipação", "url": "https://example.com/antecipacao",
     "text": "A antecipação de recebíveis adianta o valor das vendas no crédito; o pedido é feito no app."},
]


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    (tmp_path / "kb.jsonl").write_text("\n".join(json.dumps(d, ensure_ascii=False) for d in DOCS), encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))


def ctx(message, language="pt", **facts):
    return Context(text=message, language=language, user_id="u1", conversation_id="c1", intent="faq", facts=facts)


def with_reply(monkeypatch, reply):
    llm, _ = fake_llm([resp("end_turn", text(reply))], effort="medium")
    monkeypatch.setattr(agents, "get_llm", lambda role="agent": llm)


# --- a regra (app.coverage), com as frases reais do ensaio 14 --------------------------------------------------------
@pytest.mark.parametrize("question, missing", [
    ("What's the difference between the Get Clássica and the Get Smart?",
     "I couldn't find the Get Smart's debit and credit rates per brand, so I can't compare its rates with the "
     "Clássica's."),
    ("My card machine won't connect to the internet, what should I do?",
     "The sources don't say what to do if there's still no signal after the test."),
    ("How does receivables advance (antecipação) work with Getnet?", "I didn't find the fee for a standard manual "
                                                                      "advance."),
    ("Como funciona a antecipação de recebíveis?", "taxa da antecipação"),
])
def test_neighbor_items_are_not_asked(question, missing):
    asked, detail = judge_missing([missing], [question])
    assert not asked, detail


@pytest.mark.parametrize("questions, missing", [
    # o que falta É a pergunta: continua parcial
    (["Do I need a bank account to receive my sales via Pix?"],
     "The sources don't say whether a bank account is mandatory."),
    # "custo" pede a taxa (grupo de conceito), mesmo sem a palavra
    (["E tem custo?"], "As fontes não trazem o percentual ou o valor da taxa de antecipação."),
    (["Quanto custam o Plano Alfa e o Plano Gama?"], "preço do Plano Gama"),
    # falta um dos produtos da comparação inteiro: é o assunto pedido
    (["Qual a diferença entre o Plano Alfa e o Plano Zeta?"], "Plano Zeta"),
    # seguimento: o assunto vem da versão autônoma
    (["Como eu resolvo isso?", "Como resolvo a falta de sinal da Get Clássica?"],
     "As fontes não trazem um procedimento específico da Get Clássica para falta de sinal."),
    # sem termo nenhum para comparar: na dúvida, pedido
    (["Qual o prazo?"], "As fontes não trazem."),
])
def test_asked_items_stay_partial(questions, missing):
    asked, detail = judge_missing([missing], questions)
    assert asked, detail


def test_drop_only_the_absence_sentence_of_the_neighbor_item():
    body = ("A Get Smart é Android [1]. A Get Clássica serve para CPF e CNPJ [2]. As fontes não trazem a tabela de "
            "taxas da Get Smart.\nPosso passar para um atendente.")
    out, gone = drop_neighbor_absence(body, ["tabela de taxas da Get Smart"])
    assert gone == ["As fontes não trazem a tabela de taxas da Get Smart."]
    assert out == ("A Get Smart é Android [1]. A Get Clássica serve para CPF e CNPJ [2].\n"
                   "Posso passar para um atendente.")
    same, none = drop_neighbor_absence("It probably does, but the sources don't say so outright.", ["taxa"])
    assert none == [] and same == "It probably does, but the sources don't say so outright."


def test_missing_items_reads_every_marker():
    assert missing_items("Texto [1].\nMISSING: a\n**MISSING:** b.") == ["a", "b"]
    assert missing_items("Texto [1].") == []


# --- no motor (faq_agent) ---------------------------------------------------------------------------------------------
def test_neighbor_missing_is_dropped_and_the_answer_is_complete(corpus, monkeypatch):
    with_reply(monkeypatch, "A antecipação adianta o valor das vendas no crédito e o pedido é feito no app [1]. "
                            "As fontes não trazem a taxa da antecipação.\nMISSING: taxa da antecipação")
    r = agents.faq_agent(ctx("Como funciona a antecipação de recebíveis?"))
    assert r.status == "ok" and r.reason is None
    assert r.facts["missing_dropped"] == ["taxa da antecipação"] and "missing" not in r.facts
    assert "MISSING" not in r.text and "não trazem" not in r.text and "pedido é feito no app" in r.text


def test_asked_missing_stays_partial_and_is_said(corpus, monkeypatch):
    with_reply(monkeypatch, "A antecipação adianta o valor das vendas [1]. As fontes não trazem a taxa.\n"
                            "MISSING: taxa da antecipação")
    r = agents.faq_agent(ctx("Quanto custa a antecipação?"))
    assert r.status == "partial" and r.reason == "partial_coverage" and r.facts["missing"] == "taxa da antecipação"
    assert "não trazem a taxa" in r.text and "missing_dropped" not in r.facts


def test_follow_up_uses_the_standalone_question(corpus, monkeypatch):
    with_reply(monkeypatch, "A antecipação adianta o valor das vendas [1].\nMISSING: taxa da antecipação")
    r = agents.faq_agent(ctx("E tem custo?", standalone="A antecipação de recebíveis tem custo?"))
    assert r.status == "partial" and r.text.endswith("As fontes não trazem: taxa da antecipação.")


def test_one_asked_item_among_neighbors_keeps_it_partial(corpus, monkeypatch):
    with_reply(monkeypatch, "O Plano Alfa custa R$ 10 [1].\nMISSING: horário de entrega\nMISSING: preço do Plano Gama")
    r = agents.faq_agent(ctx("Quanto custam o Plano Alfa e o Plano Gama?"))
    assert r.status == "partial" and "missing_dropped" not in r.facts


def test_not_in_sources_with_citation_stays_partial(corpus, monkeypatch):
    with_reply(monkeypatch, "Alfa: R$ 10 [1]. NOT_IN_SOURCES")  # sem item nomeado: não há o que julgar
    r = agents.faq_agent(ctx("Quanto custa o Plano Alfa e quanto demora a entrega?"))
    assert r.status == "partial"


def test_step_trace_records_the_dropped_items_for_the_eval():
    from app.supervisor import step_view

    r = agents.AgentResult("faq", "ok", text="x", facts={"missing_dropped": ["taxa da antecipação"]})
    assert step_view(r)["missing_dropped"] == ["taxa da antecipação"]
    assert "missing_dropped" not in step_view(agents.AgentResult("faq", "ok", text="x"))
