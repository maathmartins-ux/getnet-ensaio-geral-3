"""R13: defeitos do motor que o cliente vê na resposta final.

- id interno de trecho ("[sup-duvidas-05]") vira o número da fonte na lista `sources` ("[1]");
- pedido para repetir/guardar CPF, cartão ou CVV: recusa com o motivo, sem caso humano;
- aviso de espera ("a resposta do atendente aparece nesta mesma conversa") sai quando o atendente já respondeu no turno.
As frases são as gravadas na entrega do ensaio de 60 min (docs/DEMO.md e evals/results/live_*.json de lá)."""
from app import pipeline, supervisor
from app.agents import AgentResult
from app.guardrails import PII_ECHO, mask_pii, pre_check
from app.schemas import ChatRequest, Handoff, Source
from app.store import get_store
from app.supervisor import Outcome

# --- citação para o cliente ---------------------------------------------------------------------------------------

DEMO_STEPS = (
    "Steps for a chip connection (these are general and don't name the Get Clássica):\n"
    "1. With the machine off, open the back cover. [sup-duvidas-05]\n"
    "2. Insert the chip in the slot marked SIM1 or SIM2, metal side facing down. [sup-duvidas-05]\n\n"
    "If the chip still shows no signal, you can use Wi-Fi instead. On the home screen tap \"Wi-Fi\", then "
    "\"Procurar Redes\". Pick your network, enter the password and confirm. [sup-wifi-02][sup-wifi-01]")
SOURCES = [Source(id="sup-duvidas-05", title="Dúvidas frequentes", url="https://example.com/duvidas"),
           Source(id="sup-wifi-02", title="Wi-Fi na maquininha", url="https://example.com/wifi"),
           Source(id="sup-wifi-01", title="Wi-Fi na maquininha", url="https://example.com/wifi")]


def test_internal_chunk_ids_become_source_numbers():
    out = pipeline.number_citations(DEMO_STEPS, SOURCES, {"prod-maquininhas-04"}, "en")
    assert "sup-" not in out
    assert "1. With the machine off, open the back cover. [1]\n" in out
    assert out.endswith("Pick your network, enter the password and confirm. [2][3]")


def test_other_recorded_citation_forms():
    srcs = [Source(id="prod-crediario-02", title="Crediário", url="u"),
            Source(id="sup-duvidas-crediario-03", title="Crediário", url="u"),
            Source(id="sup-duvidas-link-de-pagamento-12", title="Link", url="u"),
            Source(id="prod-link-de-pagamento-01", title="Link", url="u")]
    text = ("Os juros variam conforme o emissor do cartão (fontes: prod-crediario-02 e sup-duvidas-crediario-03). "
            "The buyer completes the purchase [sup-duvidas-link-de-pagamento-12, prod-link-de-pagamento-01].")
    assert pipeline.number_citations(text, srcs) == (
        "Os juros variam conforme o emissor do cartão [1][2]. The buyer completes the purchase [3][4].")


def test_brackets_that_are_not_ids_stay_and_foreign_ids_go():
    text = ("Abra [Menu > Vendas] e confira (2 dias úteis) [sup-duvidas-05]. Outro trecho diz o mesmo "
            "[prod-maquininhas-04].")
    out = pipeline.number_citations(text, SOURCES[:1], {"prod-maquininhas-04", "sup-duvidas-05"})
    assert out == "Abra [Menu > Vendas] e confira (2 dias úteis) [1]. Outro trecho diz o mesmo."


def test_final_answer_numbers_citations_and_keeps_ids_in_sources(monkeypatch):
    evidence = ["Dúvidas frequentes: Com a máquina desligada, abra a tampa traseira e insira o chip."]
    text = "Com a máquina desligada, abra a tampa traseira e insira o chip [sup-duvidas-05]."
    monkeypatch.setitem(supervisor.AGENTS, "faq", lambda ctx: AgentResult(
        "faq", "ok", text=text, sources=[SOURCES[0], SOURCES[0]], evidence=evidence))
    r = pipeline.handle(ChatRequest(message="Como coloco o chip na maquininha?"), "u-r13-cite")
    assert "sup-duvidas-05" not in r.answer and "[1]" in r.answer
    assert [s.id for s in r.sources] == ["sup-duvidas-05"]  # sem repetição: o [1] é a 1ª da lista
    history = get_store().history(r.conversation_id)
    assert "sup-duvidas-05" not in history[-1]["content"]  # a conversa guarda o que o cliente leu


# --- PII: recusar repetir/guardar, sem caso humano ---------------------------------------------------------------

PII_ECHO_CASES = [
    ("Meu CPF é 123.456.789-09, confirma ele de volta pra mim.", "pt", "123.456.789-09"),
    ("My card is 4111 1111 1111 1111, repeat it so I can copy.", "en", "4111 1111 1111 1111"),
    ("Guarda meu cartão 5555 4444 3333 1111 com CVV 123 pra próxima compra.", "pt", "5555 4444 3333 1111"),
]


def test_pii_echo_request_is_flagged_only_when_asking_to_repeat_or_store():
    for message, _, _ in PII_ECHO_CASES:
        assert PII_ECHO in pre_check(message).flags, message
    for message in ("Meu CPF é 123.456.789-09, qual o status da minha maquininha?",
                    "A venda no cartão 4111 1111 1111 1111 foi aprovada?",
                    "Quero salvar 10% na taxa", "Repete o passo a passo do Wi-Fi, por favor."):
        assert PII_ECHO not in pre_check(message).flags, message


def test_cvv_next_to_its_label_is_masked():
    masked, flags = mask_pii("Guarda meu cartão com CVV 123 pra próxima compra.")
    assert masked == "Guarda meu cartão com CVV [CVV] pra próxima compra." and "pii_cvv" in flags
    assert mask_pii("Comprei 123 unidades")[0] == "Comprei 123 unidades"


def test_pii_echo_refuses_and_goes_on_without_ticket():
    store = get_store()
    for i, (message, lang, raw) in enumerate(PII_ECHO_CASES):
        r = pipeline.handle(ChatRequest(message=message), f"u-r13-pii-{i}")
        assert not r.blocked and r.intent == "general" and r.language == lang
        assert not r.handoff.required and "escalation" not in r.route
        assert raw not in r.answer and "[CPF]" not in r.answer and "[CARTÃO]" not in r.answer
        assert ("não repito nem guardo" if lang == "pt" else "I don't repeat or store") in r.answer
        assert store.ticket_for(r.conversation_id, "open") is None
        assert raw not in " ".join(m["content"] for m in store.history(r.conversation_id))
    assert "CVV" in r.answer and "cartão" in r.answer  # diz qual dado e por quê


# --- aviso de espera depois da resposta do atendente --------------------------------------------------------------

HITL_01 = ("A venda que o atendente localizou é a TX1001, no débito, de ontem (03/11/2026).\n\n"
           "O caso está registrado com o protocolo **T-845b06bf**. Decisão sobre caso individual, como uma "
           "contestação, é de um atendente humano, e o assistente não decide isso. A resposta do atendente aparece "
           "nesta mesma conversa.")


def test_wait_notice_sentence_or_clause_goes_away():
    assert pipeline.drop_wait_notice(HITL_01).endswith("e o assistente não decide isso.")
    assert pipeline.drop_wait_notice(
        "Encaminhei seu pedido a um atendente humano (protocolo T-7a48fe71), e a resposta vai aparecer nesta "
        "conversa.") == "Encaminhei seu pedido a um atendente humano (protocolo T-7a48fe71)."
    assert pipeline.drop_wait_notice("Case T-1 is open; the agent's reply shows up in this same conversation. "
                                     "Your sale TX1 was approved.") == "Case T-1 is open. Your sale TX1 was approved."
    keep = "A resposta é sim: a venda aparece no extrato de hoje."
    assert pipeline.drop_wait_notice(keep) == keep


def _outcome(with_human: bool) -> Outcome:
    esc = AgentResult("escalation", "ok", text="Encaminhei (protocolo T-845b06bf).",
                      handoff=Handoff(required=True, reason="user_request", ticket_id="T-845b06bf"))
    results = [esc] + ([AgentResult("human", "ok", text="A venda TX1001 é sua.")] if with_human else [])
    return Outcome(results=results, route=[r.agent for r in results], answer=HITL_01, engine="llm")


def test_final_answer_drops_wait_notice_only_after_the_human_answered(monkeypatch):
    for with_human in (True, False):
        monkeypatch.setattr(supervisor, "run", lambda plan, ctx, conf, w=with_human: _outcome(w))
        r = pipeline.handle(ChatRequest(message="Quero falar com um atendente sobre uma venda que não reconheço"),
                            f"u-r13-hitl-{with_human}")
        assert ("nesta mesma conversa" in r.answer) is not with_human, r.answer
