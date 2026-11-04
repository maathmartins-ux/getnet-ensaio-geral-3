"""Domínio: as respostas fracas do ensaio (oficiais) viram regra genérica nos prompts e fato exigente nos casos.

Fixtures: frases reais das respostas medidas no ensaio (docs/DEMO.md daquela entrega). Os `facts` antigos aceitavam
essas respostas (regex frouxa: "system", "wi-fi" no nome do produto, "credit" em "credit receivables"); os novos pedem
o fato que responde a pergunta. Os prompts ganham regras sem id de caso e sem frase de avaliação."""
import json

from app.config import ROOT
from evals.run_evals import facts_missing

PROMPTS = ROOT / "src" / "app" / "domain" / "challenge_prompts"

# respostas do ensaio, palavra por palavra (trechos)
WEAK = {
    "official-01": ("The Get Smart is a smart card machine that runs on Android. It lets you manage stock, "
                    "take orders, close the tab and issue invoices on the device, and it can integrate with "
                    "your establishment's system ([1], [4]). The Get Clássica is listed as \"Maquininha POS 3G + "
                    "Wi-Fi\" ([2]). The sources don't describe its other features, so I can't give a full "
                    "comparison."),
    "official-04": ("With Get Conta, a free digital account, you can receive money and sell through Pix [7]. "
                    "The sources don't say whether a Get Conta or another bank account is mandatory to receive "
                    "Pix sales."),
    "official-06": ("Getnet can propose an advance of your credit receivables for an amount in reais. "
                    "You have to confirm it, and then a human agent has to approve it before it runs. Gravame: "
                    "this is the guarantee you give Getnet for a loan. The sources don't give the step-by-step "
                    "process, the fees or the payout timing for a standard advance."),
}
# a resposta que os trechos do corpus permitem (o fato de cada lado, o requisito, o mecanismo)
GOOD = {
    "official-01": ("The Get Smart runs on Android with apps for stock and invoices [1]. The Get Clássica is valid "
                    "for CPF and CNPJ, with credit 1x at 3,79% and payout in 2 days [2]."),
    "official-04": ("Yes: Getnet asks for a Pix key linked to your receiving account [1]; it can be the free "
                    "Get Conta digital account [2]."),
    "official-06": ("You can advance your credit sales in the Getnet Brasil app, through customer service or on "
                    "the POS [1]; there is no extra charge beyond the existing ones: rent, MDR and the advance "
                    "fee [2]."),
}


def _official() -> dict[str, dict]:
    rows = [json.loads(line) for line in (ROOT / "evals" / "cases.jsonl").read_text("utf-8").splitlines()
            if line.strip()]
    return {r["id"]: r for r in rows}


def test_new_facts_reject_the_weak_answers_and_accept_the_grounded_ones():
    cases = _official()
    for cid, answer in WEAK.items():
        assert facts_missing(cases[cid]["expect"], answer), cid
    for cid, answer in GOOD.items():
        assert facts_missing(cases[cid]["expect"], answer) == [], cid


def test_official_var_carry_the_same_facts_as_their_origin():
    cases = _official()
    rows = [json.loads(line) for line in (ROOT / "evals" / "cases.d" / "q.jsonl").read_text("utf-8").splitlines()
            if line.strip()]
    for r in rows:
        if r["split"] == "official-var" and r.get("origin") in cases:
            assert r["expect"]["facts"] == cases[r["origin"]]["expect"]["facts"], r["id"]


def test_faq_prompt_forbids_claiming_absence_and_searches_before_missing():
    faq = (PROMPTS / "faq.md").read_text("utf-8")
    assert "Nunca afirme ausência do que um trecho traz" in faq
    assert "ANTES de marcar\nMISSING, chame `search`" in faq
    assert "página do próprio produto" in faq
    assert "(em inglês: yes, no, it depends)" in faq
    assert "Falta só do que foi perguntado" in faq


def test_supervisor_prompt_answers_first_and_never_opens_with_the_capabilities_card():
    sup = (PROMPTS / "supervisor.md").read_text("utf-8")
    assert "não abra\ncom ele" in sup
    assert "a 1ª frase começa por sim, não ou \"depende\"" in sup
    assert "nunca diga que as\nfontes, a base ou os manuais não têm algo que outro resultado deste turno trouxe" in sup


def test_router_prompt_action_beats_symptom_and_fix_question_is_not_multi():
    router = (PROMPTS / "router.md").read_text("utf-8")
    assert "o sintoma é só o motivo do pedido e vale support (3)" in router
    assert "NÃO é multi: é UMA pergunta\n  troubleshoot" in router


def test_guardrail_prompt_own_action_without_human_is_safe_and_other_merchant_is_not():
    guard = (PROMPTS / "guardrail.md").read_text("utf-8")
    assert "sem a etapa humana" in guard and "é safe: é pedido de ação" in guard
    assert "é other_user_data" in guard


def test_records_prompt_not_found_does_not_describe_the_account():
    records = (PROMPTS / "records.md").read_text("utf-8")
    assert "sem afirmar o que a conta tem ou deixa de ter" in records
    assert "não encontrou na conta dele" not in records
