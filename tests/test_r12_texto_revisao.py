"""Limpeza da resposta final: os 5 achados confirmados da revisão adversarial da rodada 12 (área texto).

Regra: a limpeza nunca apaga conteúdo legítimo; na dúvida, o texto fica e sai só o código interno. Os casos vêm dos
testes de reprodução dos revisores; os marcados "gravado" são texto que o LLM escreveu nas baterias (r10/r11).
"""
import pytest

from app import capabilities
from app.pipeline import NO_ANSWER, _scrub_internal


# --- 1. (alta) a palavra antes da citação só sai quando de fato a introduz ---------------------------------------
@pytest.mark.parametrize("language, raw, clean", [
    # gravado: dependent-07 e real-31 (respostas finais da rodada 10); o pronome "uma" sumia ("de cada.")
    ("pt", "Posso consultar os últimos 7 dias para ver se houve recusas e qual foi o código de cada uma "
           "[policy:capabilities].",
     "Posso consultar os últimos 7 dias para ver se houve recusas e qual foi o código de cada uma."),
    ("pt", "- Consultar suas vendas recusadas dos últimos 7 dias, com o código de recusa de cada uma "
           "[policy:capabilities].",
     "- Consultar suas vendas recusadas dos últimos 7 dias, com o código de recusa de cada uma."),
    ("pt", "Se quiser, posso propor um [policy:capabilities].", "Se quiser, posso propor um."),
    ("pt", "Quer que eu abra um [policy:capabilities]?", "Quer que eu abra um?"),
    # inglês: "do"/"no" são verbo e negação (casavam com as contrações do português); "in"/"on" no fim são partícula
    ("en", "Deciding the dispute isn't something I can do [policy:capabilities].",
     "Deciding the dispute isn't something I can do."),
    ("en", "That isn't something I can do [policy:capabilities].", "That isn't something I can do."),
    ("en", "No [policy:capabilities]. A human agent decides disputes.", "No. A human agent decides disputes."),
    ("en", "The answer is no [policy:capabilities].", "The answer is no."),
    ("en", "You have to be logged in [policy:capabilities].", "You have to be logged in."),
    ("en", "Make sure the terminal is turned on [policy:capabilities].", "Make sure the terminal is turned on."),
    ("en", "You have to be logged in per [policy:capabilities].", "You have to be logged in."),
    # a abertura de verdade continua saindo
    ("pt", "Segundo a [policy:capabilities], a antecipação é uma ação de risco alto.",
     "A antecipação é uma ação de risco alto."),
    ("en", "From [policy:capabilities], I can look up your recent declines.", "I can look up your recent declines."),
    ("en", "Nothing runs, under [policy:capabilities], until you confirm.", "Nothing runs until you confirm."),
])
def test_lead_strip_never_eats_a_word_of_the_sentence(language, raw, clean):
    assert _scrub_internal(raw, language) == clean


# --- 2. (média) a frase curta que responde fica; a que só apontava a citação sai -----------------------------------
@pytest.mark.parametrize("language, raw, clean", [
    ("pt", "15 minutos conforme [policy:capabilities].", "15 minutos."),
    ("pt", "A proposta vale pouco tempo. 15 minutos conforme [policy:capabilities].",
     "A proposta vale pouco tempo. 15 minutos."),
    ("en", "15 minutes per [policy:capabilities].", "15 minutes."),
    ("pt", "R$ 50 segundo [policy:capabilities].", "R$ 50."),
    ("pt", "Posso abrir o chamado. Requer confirmação conforme [policy:capabilities].",
     "Posso abrir o chamado. Requer confirmação."),
    ("en", "I can open it. Confirmation required per [policy:capabilities].",
     "I can open it. Confirmation required."),
    # o número fica mesmo na frase que aponta
    ("pt", "Os 3 planos estão em [policy:capabilities].", "Os 3 planos estão."),
])
def test_short_answer_sentence_is_not_dropped(language, raw, clean):
    assert _scrub_internal(raw, language) == clean


@pytest.mark.parametrize("language, raw, clean", [
    # gravado: real-11 (resposta final da rodada 10) dava "Essa política de ações está."
    ("pt", "Posso fazer isso depois que você confirmar. Essa política de ações está em [policy:capabilities].",
     "Posso fazer isso depois que você confirmar."),
    # gravado: real-39 (texto do agente, rodada 10) dava "...são só."; sai só a oração que apontava
    ("pt", "Também não posso propor uma ação para isso, porque as ações disponíveis são só as de "
           "[policy:capabilities].\n\nO que posso fazer:",
     "Também não posso propor uma ação para isso.\n\nO que posso fazer:"),
    ("pt", "Não posso fazer isso porque as ações disponíveis são só as de [policy:capabilities].",
     "Não posso fazer isso."),
    ("pt", "Os detalhes de crédito e débito estão em [policy:capabilities]. Posso ajudar?", "Posso ajudar?"),
    ("pt", "Nada é executado antes da sua confirmação, conforme descrito em [policy:capabilities].",
     "Nada é executado antes da sua confirmação."),
    ("pt", "Nada é executado conforme descrito em [policy:capabilities].", "Nada é executado."),
    ("pt", "Isso vale. Mais detalhes em [policy:capabilities].", "Isso vale."),
    ("pt", "Isso vale. Se quiser, mais detalhes em [policy:capabilities].", "Isso vale."),
    ("pt", "Você pode ver [policy:capabilities]. Depois disso, confirme.", "Depois disso, confirme."),
    ("en", "Done. The details are listed in the [policy:capabilities].", "Done."),
    ("en", "Done. You can see the details in [policy:capabilities].", "Done."),
    ("en", "I can open it. For more details, see [policy:capabilities].", "I can open it."),
])
def test_pointer_sentence_is_not_left_without_its_object(language, raw, clean):
    assert _scrub_internal(raw, language) == clean


def test_answer_with_content_never_becomes_no_answer():
    for language, raw in (("pt", "15 minutos conforme [policy:capabilities]."),
                          ("en", "15 minutes per [policy:capabilities]."),
                          ("en", "No [policy:capabilities].")):
        assert _scrub_internal(raw, language) != NO_ANSWER[language]
    assert _scrub_internal("Veja [policy:capabilities].", "pt") == NO_ANSWER["pt"]  # só apontava


# --- 3. (baixa) o separador que não abria a citação fica ------------------------------------------------------------
@pytest.mark.parametrize("language, raw, clean", [
    ("pt", "Não, segundo o [policy:capabilities], a decisão é de um atendente humano.",
     "Não, a decisão é de um atendente humano."),
    ("pt", "Sim, conforme o [policy:capabilities], você pode antecipar.", "Sim, você pode antecipar."),
    ("pt", "Você confirma a proposta; conforme [policy:capabilities], ela expira em 15 minutos.",
     "Você confirma a proposta; ela expira em 15 minutos."),
    ("en", "No, according to [policy:capabilities], a human agent decides that.", "No, a human agent decides that."),
    ("en", "Yes, per [policy:capabilities], you can cancel.", "Yes, you can cancel."),
    ("en", "No — per [policy:capabilities], the assistant can't decide disputes.",
     "No — the assistant can't decide disputes."),
    # o aposto de verdade continua saindo com o par de vírgulas
    ("pt", "A antecipação, segundo a [policy:capabilities], precisa de aprovação.",
     "A antecipação precisa de aprovação."),
    ("pt", "A proposta expira em 15 minutos, conforme [policy:capabilities], e depois some.",
     "A proposta expira em 15 minutos e depois some."),
])
def test_separator_that_is_not_part_of_the_insertion_stays(language, raw, clean):
    assert _scrub_internal(raw, language) == clean


# --- 4. (baixa) lista, rótulo, citação em bloco e negrito ----------------------------------------------------------
@pytest.mark.parametrize("raw, clean", [
    ("Fontes:\n- [sup-duvidas-06]\n- [policy:capabilities]", "Fontes:\n- [sup-duvidas-06]"),
    ("1. [policy:capabilities]\n2. Confirme.", "2. Confirme."),
    ("- Veja [policy:capabilities].\n- Aguarde.", "- Aguarde."),
    ("- Antecipar.\n- Veja [policy:capabilities].\n- Aguarde.", "- Antecipar.\n- Aguarde."),
    ("Isso vale.\n\nFonte: [policy:capabilities]\n\nDepois, confirme.", "Isso vale.\n\nDepois, confirme."),
    # cabeçalho de lista não é rótulo de fonte: fica, sem a citação
    ("Próximos passos: [policy:capabilities]\n1. Confirme a proposta.\n2. Aguarde.",
     "Próximos passos:\n1. Confirme a proposta.\n2. Aguarde."),
    ("**Conforme [policy:capabilities]**, a proposta expira.", "A proposta expira."),
    ("A proposta expira em 15 minutos **[policy:capabilities]**.", "A proposta expira em 15 minutos."),
    ("> Conforme [policy:capabilities], nada é executado.", "> Nada é executado."),
])
def test_list_header_survives_and_no_bare_marker_is_left(raw, clean):
    assert _scrub_internal(raw, "pt") == clean


# --- 5. (baixa) sem citação, nada muda: a limpeza de parênteses é só no ponto do corte -----------------------------
@pytest.mark.parametrize("text", [
    "No SDK, chame `pos.init()` antes de `pos.pay()`.",
    "Use a fórmula f() = 0 (ver o manual).",
    "O emoticon :( . é triste",
    "Olá , tudo bem ?",
])
def test_text_without_citation_keeps_empty_parentheses(monkeypatch, text):
    monkeypatch.setattr(capabilities, "_tools", lambda: {})
    assert _scrub_internal(text, "pt") == text


def test_parentheses_elsewhere_survive_the_cut_of_a_citation(monkeypatch):
    monkeypatch.setattr(capabilities, "_tools", lambda: {})
    assert _scrub_internal("Chame `pos.init()` antes de pagar (conforme [policy:capabilities]).", "pt") == (
        "Chame `pos.init()` antes de pagar.")
    assert _scrub_internal("O chamado só é aberto depois que você confirmar (conforme [policy:capabilities].", "pt") \
        == "O chamado só é aberto depois que você confirmar."
