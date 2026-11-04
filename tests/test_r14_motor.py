"""Motor, rodada 14: as falhas do motor que as avaliações cegas do ensaio 13 acharam, com as frases reais como dado.

1. Erro de consulta (`not_found`) nunca vira afirmação sobre a conta ("não achei nenhuma maquininha na sua conta").
2. Fala que retoma outra conversa ("o que falamos da última vez") busca o assunto daquela conversa (perfil).
3. Trecho que se data num ano anterior ao de hoje vai ao redator com o ano e o aviso; o contrato manda usar o novo.
4. Redator que marca MISSING com busca sobrando: o código busca o item que falta e pede a redação com o trecho novo.
"""
import json
import shutil
from datetime import date

from fakes import fake_llm, resp, text, tool_use

from app import agents, domain, memory, pipeline
from app.agents import AgentResult, Context
from app.rag import Doc, Hit
from app.schemas import ChatRequest


def ctx(message: str, intent: str = "faq", language: str = "pt", **facts) -> Context:
    return Context(text=message, language=language, user_id="u1", conversation_id="c1", intent=intent, facts=facts)


# --- 1. not_found não é "a conta não tem" ------------------------------------------------------------------------
# Respostas reais do ensaio 13 (split real): o cliente não estava no cadastro e TODA consulta voltou not_found.
REAL_ANSWERS = [
    "Não encontrei nenhuma maquininha, venda ou recusa na sua conta nos últimos 7 dias. Por isso, com esses dados, não "
    "consigo dizer por que as vendas não foram processadas.\n\nEncaminhei seu caso a um atendente humano, com o "
    "protocolo T-050353f9. A resposta dele vai aparecer nesta conversa.",
    "Não achei nenhuma maquininha na sua conta, e as fontes não trazem um prazo de entrega. Por isso não consigo "
    "informar o prazo nem o status do seu pedido.\n\nEncaminhei seu caso a um atendente humano, protocolo T-a15e09bb.",
    "Para o pagamento por aproximação, o celular precisa ter NFC [6][8].\n\nNão encontrei a causa de funcionar só ao "
    "afastar o celular. Também não achei nenhuma maquininha na sua conta, então não tenho dados dela.",
    "Um Pix recebido pode ficar bloqueado por até 72 horas [1].\n\nNão achei nenhum bloqueio ou valor retido na sua "
    "conta nos últimos 30 dias, nas vendas e na agenda de recebimentos. Por isso não sei dizer qual motivo vale para o "
    "seu caso.",
]


def test_not_found_tool_result_says_what_it_does_not_mean():
    out = agents.explain_tool_error({"ok": False, "error": "not_found"}, "pt")
    assert out["error"] == "not_found" and "NÃO quer dizer que a conta não tem" in out["meaning"]
    assert "does NOT mean" in agents.explain_tool_error({"ok": False, "error": "not_found"}, "en")["meaning"]
    assert "falhou" in agents.explain_tool_error({"ok": False, "error": "TypeError: boom"}, "pt")["meaning"]
    # proposta de escrita, regra de negócio e resultado ok não são falha de consulta: ficam como estão
    for same in ({"ok": False, "needs_confirmation": True, "action_id": "A-1"}, {"ok": True, "data": {"items": []}},
                 {"ok": False, "error": "above_available", "data": {"available": "R$ 10,00"}}):
        assert agents.explain_tool_error(same, "pt") == same


def test_records_with_every_lookup_not_found_answers_with_our_text_not_the_model_claim(monkeypatch):
    llm, msgs = fake_llm([
        resp("tool_use", tool_use("lookup_record", {"record_id": "2001"})),
        resp("end_turn", text("Não achei nenhuma maquininha na sua conta.")),
    ], effort="medium")
    monkeypatch.setattr(agents, "get_llm", lambda role="agent": llm)
    r = agents.records_agent(ctx("Mostre o pedido 2001", "records"))
    assert r.status == "insufficient" and r.reason == "no_data"  # o supervisor segue levando ao humano
    assert r.facts["lookup_failed"] == ["lookup_record:not_found"]
    assert r.text == agents.LOOKUP_FAILED["not_found"]["pt"] and "nenhuma maquininha" not in r.text
    shown = json.loads(msgs.sent[1]["messages"][-1]["content"][0]["content"])
    assert "NÃO quer dizer" in shown["meaning"]


def test_records_with_one_lookup_ok_keeps_the_model_text(monkeypatch):
    llm, _ = fake_llm([
        resp("tool_use", tool_use("lookup_record", {"record_id": "1002"})),
        resp("end_turn", text("O pedido 1002 é o Livro B.")),
    ], effort="medium")
    monkeypatch.setattr(agents, "get_llm", lambda role="agent": llm)
    r = agents.records_agent(ctx("Mostre o pedido 1002", "records"))
    assert r.status == "ok" and r.text == "O pedido 1002 é o Livro B." and "lookup_failed" not in r.facts


def test_final_answer_drops_the_account_absence_sentence_after_failed_lookups():
    failed = ["get_terminals:not_found"]
    for answer in REAL_ANSWERS:
        fixed = agents.without_account_absence(answer, "pt", failed)
        assert "na sua conta" not in fixed.replace(agents.LOOKUP_FAILED["not_found"]["pt"], ""), fixed
        assert fixed.count("Não encontrei esse registro") == 1
    # o resto da resposta fica: protocolo, fonte citada, o que falta
    fixed = agents.without_account_absence(REAL_ANSWERS[0], "pt", failed)
    assert "T-050353f9" in fixed and "Por isso, com esses dados" in fixed
    assert "72 horas [1]" in agents.without_account_absence(REAL_ANSWERS[3], "pt", failed)
    # aplicar de novo não muda nada (o nosso texto não é trocado por ele mesmo)
    assert agents.without_account_absence(fixed, "pt", failed) == fixed
    en = agents.without_account_absence("I found no terminals in your account. A human will reply.", "en", failed)
    assert en.startswith("I couldn't find that record") and "A human will reply." in en
    # sem consulta falha no turno, nada muda
    assert agents.without_account_absence(REAL_ANSWERS[1], "pt", []) == REAL_ANSWERS[1]


def test_pipeline_rewrites_the_supervisor_answer_when_every_lookup_failed(monkeypatch):
    from app import supervisor

    def run(plan, c, confidence=1.0, prior=None):
        out = supervisor.Outcome()
        out.results = [AgentResult("records", "insufficient", text=agents.LOOKUP_FAILED["not_found"]["pt"],
                                   reason="no_data", facts={"lookup_failed": ["get_terminals:not_found"]})]
        out.route = ["records"]
        out.answer = "Não achei nenhuma maquininha na sua conta. Posso encaminhar a um atendente."
        return out

    monkeypatch.setattr(supervisor, "run", run)
    r = pipeline.handle(ChatRequest(message="Minhas maquininhas estão funcionando?"), "u1")
    assert "nenhuma maquininha" not in r.answer and "Não encontrei esse registro" in r.answer
    assert "Posso encaminhar a um atendente." in r.answer


# --- 2. memória entre conversas: o assunto da outra conversa entra na busca -----------------------------------------
CORPUS = [
    {"id": "cred-01", "title": "Crediário", "url": "https://exemplo.test/crediario/",
     "text": "Com o Crediário, a venda pode ser parcelada em até 48x; o prazo máximo e os juros dependem do emissor."},
    {"id": "duv-01", "title": "Dúvidas", "url": "https://exemplo.test/duvidas/",
     "text": "No Parcelado Lojista, o limite é de até 12 parcelas sem juros para o portador do cartão."},
    {"id": "pix-01", "title": "Pix", "url": "https://exemplo.test/pix/",
     "text": "Em Meus Limites você ajusta o limite do Pix por período."},
]


def _corpus(tmp_path, monkeypatch):
    from conftest import KIT_DATA

    data = tmp_path / "data"
    shutil.copytree(KIT_DATA / "data", data)
    (data / "knowledge").mkdir()
    (data / "knowledge" / "base.jsonl").write_text("\n".join(json.dumps(d, ensure_ascii=False) for d in CORPUS),
                                                   encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(data))


def test_refers_back_reads_both_languages():
    for said in ("Remind me which installment limit we talked about last time?", "O que falamos da última vez?",
                 "Na conversa anterior você me disse um prazo, qual era?", "What did you tell me in our last chat?"):
        assert memory.refers_back(said), said
    for said in ("Qual o limite de parcelas do crediário?", "How many installments can I split a sale into?"):
        assert not memory.refers_back(said), said


def test_new_conversation_that_refers_back_searches_the_earlier_topic(tmp_path, monkeypatch):
    _corpus(tmp_path, monkeypatch)
    pipeline.handle(ChatRequest(message="How many installments can I split a sale into with the crediário?"), "u1")
    seen = {}
    real = agents.retrieve

    def spy(*a, **kw):
        seen["recalled"] = kw.get("recalled")
        found = real(*a, **kw)
        seen["queries"], seen["hits"] = found.plan.queries, [h.doc.id for h in found.hits]
        return found

    monkeypatch.setattr(agents, "retrieve", spy)
    r = pipeline.handle(ChatRequest(message="Remind me which installment limit we talked about last time?"), "u1")
    assert "48" in r.answer  # o fato que o sistema deu na outra conversa volta (caminho sem LLM)
    assert seen["recalled"] == ["How many installments can I split a sale into with the crediário?"]
    assert seen["queries"][0] == seen["recalled"][0]  # 1ª busca: o assunto da outra conversa
    assert seen["hits"][0] == "cred-01" and "48" in r.answer  # o fato que o sistema deu antes volta (sem LLM)


def test_same_question_without_the_earlier_conversation_does_not_recall(tmp_path, monkeypatch):
    _corpus(tmp_path, monkeypatch)
    seen = {}
    real = agents.retrieve

    def spy(*a, **kw):
        seen["recalled"] = kw.get("recalled")
        return real(*a, **kw)

    monkeypatch.setattr(agents, "retrieve", spy)
    pipeline.handle(ChatRequest(message="Remind me which installment limit we talked about last time?"), "u2")
    assert not seen.get("recalled")  # sem perfil de outra conversa: nada é inventado


def test_recalled_query_comes_first_and_keeps_the_search_cap():
    class R:
        name = "fake"
        gate = None

        def search(self, query, k=5):
            return []

    found = agents.retrieve("Remind me what we talked about last time", queries=["limite", "parcelas", "x"],
                            recalled=["Qual o limite do crediário?"], retriever=R(), k=5)
    assert found.plan.queries[0] == "Qual o limite do crediário?"
    assert len(found.plan.queries) == 4  # o mesmo teto de antes (a fala + 3 do router): a última cede a vaga


def test_profile_topics_come_from_other_conversations_newest_first():
    profile = memory.Profile()
    profile.add("topic", "Assunto velho", "c-old", 100)
    profile.add("topic", "Assunto novo", "c-new", 200)
    profile.add("topic", "Assunto desta conversa", "c-now", 300)
    assert memory.recalled_topics(profile, exclude="c-now") == ["Assunto novo"]
    assert memory.recalled_topics(profile, exclude="c-now", limit=2) == ["Assunto novo", "Assunto velho"]


# --- 3. fonte velha: o redator vê o ano da página ---
def test_page_dated_in_an_earlier_year_is_tagged_for_the_writer(monkeypatch):
    old = Doc("p1", "Get Clássica", "https://x.test/get-classica/",
              "Taxa única nas principais bandeiras\nSua escolha inteligente para vender mais em 2025:")
    new = Doc("p2", "Todas", "https://x.test/todas/", "Sua escolha inteligente para vender mais em 2026:")
    law = Doc("p3", "Antecipação", "https://x.test/antecipacao/",
              "A partir do dia 7 de junho de 2021, entram em vigor a Resolução 4.734 e a Circular 3.952.")
    today = date(2026, 11, 4)
    assert agents.page_year(old, today) == 2025 and agents.page_year(new, today) == 2026
    assert agents.page_year(law, today) is None  # data solta no texto não data a página
    assert agents.year_tag(old, today) == " [ano da página: 2025, anterior a 2026: pode estar desatualizada]"
    assert agents.year_tag(new, today) == " [ano da página: 2026]" and agents.year_tag(law, today) == ""
    monkeypatch.setattr(agents.clock, "today", lambda: today)
    listing = agents._listing([Hit(old, 1.0), Hit(new, 0.9)])
    assert "[1] Get Clássica (https://x.test/get-classica/) [ano da página: 2025, anterior a 2026" in listing
    assert "[2] Todas (https://x.test/todas/) [ano da página: 2026]:" in listing


def test_faq_contract_says_to_use_the_newest_version_and_not_deny_what_is_there():
    contract = (domain.KIT_PROMPTS / "contract" / "faq.md").read_text(encoding="utf-8")
    assert "a vigente é a mais nova" in contract and "anterior a Y" in contract
    assert "dizer que falta o que está numa passagem é erro" in contract
    records = (domain.KIT_PROMPTS / "contract" / "records.md").read_text(encoding="utf-8")
    assert "Erro de consulta não é dado da conta" in records


# --- 4. MISSING com busca sobrando: o código busca o item -------------------------------------------------------------
class _Retriever:
    name = "fake"
    gate = None

    def __init__(self, by_query):
        self.by_query, self.asked = by_query, []

    def search(self, query, k=5):
        self.asked.append((query, k))
        return [Hit(d, 9.0, bm25=9.0) for d in self.by_query.get(query, [])][:k]


def test_writer_that_marks_missing_without_searching_gets_the_passage(monkeypatch):
    smart = Doc("s1", "Get Smart", "https://x.test/smart/", "A Get Smart é Android e emite nota fiscal.")
    classica = Doc("c1", "Get Clássica", "https://x.test/classica/", "A Get Clássica tem conta e cartão grátis.")
    ret = _Retriever({"Get Clássica features": [classica]})
    first = "A Get Smart é Android [1]. As fontes não descrevem a Get Clássica.\nMISSING: Get Clássica features"
    llm, msgs = fake_llm([resp("end_turn", text("A Get Smart é Android [1]. A Get Clássica tem conta e cartão "
                                                "grátis [2]."))], effort="medium")
    monkeypatch.setattr(agents, "covered_hits", lambda found, **kw: list(found))
    c = ctx("What's the difference?", language="en")
    out, hits, asked = agents._search_missing(c, llm, "sys", "framed", first, [Hit(smart, 9.0)], ret, 5, "en")
    assert asked == ["Get Clássica features"] and [h.doc.id for h in hits] == ["s1", "c1"]
    assert "conta e cartão grátis [2]" in out
    assert ret.asked[0][1] == 6  # k a mais que os já vistos: o teto por página não gasta a vaga com trecho repetido
    assert "Você marcou como faltando: Get Clássica features" in json.dumps(msgs.sent[-1], ensure_ascii=False)


def test_missing_search_without_new_passage_keeps_the_answer():
    smart = Doc("s1", "Get Smart", "https://x.test/smart/", "A Get Smart é Android.")
    first = "A Get Smart é Android [1].\nMISSING: preço"
    out, hits, asked = agents._search_missing(ctx("Quanto custa?"), None, "sys", "framed", first, [Hit(smart, 9.0)],
                                              _Retriever({}), 5, "pt")
    assert out == first and len(hits) == 1 and asked == ["preço"]
    # resposta completa ou NOT_IN_SOURCES inteiro: nada a buscar
    assert agents._search_missing(ctx("x"), None, "s", "f", "Resposta [1].", [], _Retriever({}), 5, "pt")[2] == []
    assert agents._search_missing(ctx("x"), None, "s", "f", "NOT_IN_SOURCES", [], _Retriever({}), 5, "pt")[2] == []



def test_unfilled_page_template_chunk_never_enters_the_index(tmp_path):
    # ensaio 13: o molde da página do produto ("{{recebimento}}", sem dado) subia em 1º na busca do produto
    import json as _json

    from app.rag import load_docs

    rows = [{"id": "p-01", "title": "Get Clássica", "url": "https://x.test/c", "text": "Recebimento em 2 dias."},
            {"id": "p-03", "title": "Get Clássica", "url": "https://x.test/c",
             "text": "Get Clássica {{recebimento}} {{ taxa_debito }}"}]
    (tmp_path / "k.jsonl").write_text("\n".join(_json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    assert [d.id for d in load_docs(tmp_path)] == ["p-01"]
