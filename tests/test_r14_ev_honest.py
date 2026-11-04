"""Rodada 14, avaliação honesta: fato dentro de palavra ou de lista negada não conta, resposta parcial fora da manchete,
juiz confere a frase de ausência contra o contexto, verify.md velho ou vermelho fora da entrega, RESULTS que abre com a
leitura em prosa e o juiz × pessoas refeito no final.sh. As frases e o contexto são os reais de uma bateria ao vivo
(tests/fixtures/r14_ausencia_real.json)."""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from app.llm import LLMReply
from evals import judge
from evals.run_evals import fact_present, facts_missing, partial_answer, resolved_line, resolved_summary
from scripts import check, fill_readme, scorecard

ROOT = Path(__file__).resolve().parents[1]
REAL = json.loads((ROOT / "tests" / "fixtures" / "r14_ausencia_real.json").read_text(encoding="utf-8"))
ITEM = {it["nome"]: it for it in REAL["itens"]}
KIT_CAL = ROOT / "tests" / "fixtures" / "kit_data" / "judge_calibration.jsonl"
BASH = shutil.which("bash")
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


# --- 1. fato: palavra inteira e negação que vale para a lista toda ------------------------------------------------

def test_real_advance_answer_does_not_count_the_fee_fact():
    """A resposta real da antecipação não dá taxa nenhuma; a regex `...|custo|cost` casava em "for CUSTOmers" (e o
    "fees" está na frase de ausência). Antes: facts ok e o caso contado resolvido nas 3 rodadas."""
    it = ITEM["antecipacao"]
    fee = it["facts"][0]
    assert "customers" in it["answer"] and "don't give the step-by-step process, the fees" in it["answer"]
    assert facts_missing({"facts": it["facts"]}, it["answer"]) == [fee]


@pytest.mark.parametrize("text", [
    "The sources don't give the step-by-step process, the fees or the payout timing for a standard advance.",
    "The sources don't give the step-by-step process, the payout timing, and the fees.",
    "The sources don’t give the fees.",  # apóstrofo curvo
    "The sources cover the automatic advance but not the fees or the payout timing.",
    "As fontes não trazem o passo a passo, o prazo de pagamento e as taxas.",
    "As fontes não trazem o passo a passo, o prazo, e as taxas.",
    "As fontes cobrem a antecipação automática, mas não as taxas.",
    "Neither the fee nor the payout date is in the sources.",
])
def test_negation_of_a_list_covers_every_item(text):
    assert not fact_present("taxa|fee|rate|%|custo|cost", text)


@pytest.mark.parametrize("text", [
    "The fee is 1.99% per month.",
    "The sources don't give the timing, and the fee is 2 per month.",  # oração nova, com verbo: afirma a taxa
    "Getnet doesn't charge a fee for Pix.",  # cobrar não é verbo de fonte: afirma
    "A Getnet não cobra taxa no Pix.",
    "Os custos são os do plano.",
])
def test_affirmed_fact_still_counts(text):
    assert fact_present("taxa|fee|rate|%|custo|cost", text)


@pytest.mark.parametrize("pattern, text, want", [
    ("custo|cost", "for customers on the plan", False),
    ("app", "then a human agent has to approve it", False),
    ("app", "pelo app ou pelos apps", True),
    ("antecip", "a antecipação automática", True),  # radical longo escrito para casar o começo
    ("autom[aá]tic", "it runs automatically", True),
    ("cr[eé]dit", "no crédito", True),
    ("pix", "pixel", False),
    ("48", "parcelar em até 48x", True),
    (r"R\$\s*\d", "você vendeu R$ 695,50", True),
    ("79,90", "custa R$ 179,90", False),
])
def test_fact_matches_a_word_not_a_piece_of_another(pattern, text, want):
    assert fact_present(pattern, text) is want


# --- 2. parcial fora da manchete ----------------------------------------------------------------------------------

def _rows():
    partial_steps = ITEM["antecipacao"]["steps"]  # o passo real: faq · partial · partial_coverage
    ok_steps = [{"agent": "faq", "status": "ok"}]
    return [{"id": "c1", "split": "official", "run": n, "checks": {"resolved": True}, "steps": ok_steps}
            for n in range(3)] + \
           [{"id": "c2", "split": "official", "run": n, "checks": {"resolved": True}, "steps": partial_steps}
            for n in range(3)] + \
           [{"id": "c3", "split": "official", "run": 0, "checks": {"resolved": False}, "steps": ok_steps}]


def test_partial_answer_is_counted_apart_from_the_headline():
    assert partial_answer({"steps": ITEM["antecipacao"]["steps"]})
    s = resolved_summary(_rows())["by_split"]["official"]
    assert (s["k"], s["n"], s["rate"]) == (3, 7, round(3 / 7, 4))  # só a completa na manchete
    assert s["partial"] == {"k": 3, "n": 7, "rate": round(3 / 7, 4), "cases": ["c2"]}
    assert s["with_partial"]["k"] == 6 and s["unresolved"] == ["c2", "c3"] and s["pass_hat_k"] == round(1 / 3, 4)
    line = resolved_line({"resolved": resolved_summary(_rows())})
    assert "official **42.9%** completas" in line and "parciais 42.9% (3 de 7: c2), com elas 85.7%" in line
    assert "não resolvidos: c3" in line and "nenhum passo parcial" in line


def test_scoreboard_shows_complete_and_partial_side_by_side(tmp_path):
    (tmp_path / "live_official.json").write_text(json.dumps({"status": "complete", "rows": _rows()}),
                                                 encoding="utf-8")
    got = scorecard.measure(tmp_path)
    assert got["official_resolved"] == round(3 / 7, 4) and got["official_partial"] == round(3 / 7, 4)
    head = scorecard.headline_markdown(tmp_path)
    assert "Oficiais resolvidas por completo" in head and "Oficiais resolvidas só em parte" in head
    assert head.index("por completo") < head.index("só em parte")


# --- 3. juiz: ausência falsa não é fundamentada nem útil -----------------------------------------------------------

def test_absence_sentences_of_the_real_answers_go_to_the_judge():
    comp, adv = ITEM["comparacao_maquininhas"], ITEM["antecipacao"]
    assert judge.absence_sentences(comp["answer"]) == [
        "The sources don't describe its other features, so I can't give a full comparison.",
        "They also don't compare price or fees between the two."]
    assert judge.absence_sentences(adv["answer"]) == [
        "The sources don't give the step-by-step process, the fees or the payout timing for a standard advance."]
    assert judge.absence_sentences("Getnet doesn't charge a fee for Pix. The fee is 2%.") == []


def test_rubric_says_false_absence_is_neither_grounded_nor_helpful():
    assert "false_absence" in judge.SCHEMA["required"] and "false_absence" in judge.VERDICT_FIELDS
    assert "ausência falsa" in judge.SYSTEM and "helpful = false" in judge.SYSTEM
    assert "só é útil quando as fontes de fato não cobrem" in judge.SYSTEM
    v = judge.enforce_absence_rule({"grounded": True, "helpful": True, "false_absence": True, "failure_type": "none"})
    assert (v["grounded"], v["helpful"], v["failure_type"]) == (False, False, "unsupported_claim")
    honest = {"grounded": True, "helpful": True, "false_absence": False, "failure_type": "none"}
    assert judge.enforce_absence_rule(dict(honest)) == honest


class AbsenceJudge:
    """Juiz falso que devolve o erro medido no ensaio: grounded e helpful verdadeiros ("honest about missing
    features") mesmo marcando a ausência como falsa quando o contexto traz a página da Clássica."""

    model = "claude-opus-5-5"

    def __init__(self):
        self.prompts = []

    def complete(self, system, messages, max_tokens=1024, schema=None):
        p = messages[0]["content"]
        self.prompts.append(p)
        answer = p.split("Resposta:")[-1]
        bad = any(s in answer for s in ("1 dia útil", "90 dias", "24 horas", "Ulan Bator"))
        false_absence = "Ficha técnica da Get Clássica" in p and "don't describe its other features" in answer
        return LLMReply(json.dumps({"grounded": not bad, "helpful": True, "score": 4, "reason": "ok",
                                    "language_ok": not ("What are" in p and "Nosso atendimento" in answer),
                                    "leaks_other_customer": "Bruno Lima" in answer, "false_absence": false_absence,
                                    "failure_type": "none"}), self.model)


def test_real_context_with_the_product_page_makes_the_absence_claim_fail(tmp_path):
    comp = ITEM["comparacao_maquininhas"]
    assert "Ficha técnica da Get Clássica" in comp["context"]  # o contexto que o juiz viu TEM a página
    live = tmp_path / "live_official.json"
    live.write_text(json.dumps({"rows": [{"id": "a", "split": "official", "run": 0, "message": comp["message"],
                                          "answer": comp["answer"], "context": comp["context"],
                                          "source_ids": [], "user_id": "u1"}]}), encoding="utf-8")
    fake = AbsenceJudge()
    rep = judge.run(fake, [live], calibration=KIT_CAL)
    v = next(x for x in rep["verdicts"] if x["id"] == "a")
    assert (v["grounded"], v["helpful"], v["false_absence"]) == (False, False, True)
    assert v["failure_type"] == "unsupported_claim"
    prompt = next(p for p in fake.prompts if "Get Smart" in p)
    tail = prompt.split("Frases de ausência da resposta")[1]
    assert "- The sources don't describe its other features, so I can't give a full comparison." in tail


# --- 4. reports/verify.md: só verde e do código final --------------------------------------------------------------

def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV}).stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "README.md").write_text("# P\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "código")
    return repo


def _verify(repo: Path, result: str, sha: str | None = None, dirty: bool = False) -> None:
    sha = sha or _git(repo, "rev-parse", "--short", "HEAD")
    (repo / "reports").mkdir(exist_ok=True)
    (repo / "reports" / "verify.md").write_text(
        f"# Verificação (`scripts/check.py`, sem docker)\n\nCommit `{sha}{'-dirty' if dirty else ''}`, 04/11/2026 "
        f"13:44 UTC. Resultado: **{result}**.\n", encoding="utf-8")


def test_verify_report_must_be_green_and_of_the_final_code(tmp_path):
    repo = _repo(tmp_path)
    assert check.verify_report_problem(repo) is None  # sem verify.md: nada a provar
    _verify(repo, "VERMELHO")  # o do ensaio: commitado vermelho
    assert "VERMELHO" in check.verify_report_problem(repo)
    _verify(repo, "VERDE", dirty=True)
    assert "sem commit" in check.verify_report_problem(repo)
    _verify(repo, "VERDE")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "verify")
    (repo / "README.md").write_text("# P\nnúmeros\n", encoding="utf-8")  # o final.sh só gera README: vale
    assert check.verify_report_problem(repo) is None
    name, ok, _, _ = check.verify_report_current(repo)
    assert ok and "verify.md" in name
    (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")  # código depois do check: não prova
    _git(repo, "commit", "-qam", "fix")
    assert "o código mudou depois (src/app.py)" in check.verify_report_problem(repo)
    _verify(repo, "VERDE", sha="0123456")
    assert "não existe" in check.verify_report_problem(repo)


def test_stale_verify_is_dropped_and_the_removal_goes_in_the_last_commit(tmp_path):
    repo = _repo(tmp_path)
    _verify(repo, "VERMELHO")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "verify vermelho")
    assert "VERMELHO" in check.drop_stale_verify(repo)
    assert not (repo / "reports" / "verify.md").exists()
    assert _git(repo, "diff", "--cached", "--name-status") == "D\treports/verify.md"
    assert check.drop_stale_verify(repo) is None  # já fora: nada a fazer


def test_final_sh_drops_stale_verify_before_the_docs_check_and_commits_it_as_generated():
    final = (ROOT / "scripts" / "final.sh").read_text(encoding="utf-8")
    assert final.index("scripts/check.py --drop-stale-verify") < final.index("scripts/check.py --docs") \
        < final.index("git commit")
    assert {"reports/verify.md", "evals/results/human_review.json"} <= fill_readme.README_ONLY
    assert fill_readme.only_generated(["README.md", "reports/verify.md", "evals/validation/5b18.json"])
    assert not fill_readme.only_generated(["README.md", "src/app/x.py"])
    dirs = re.search(r"^GENERATED_DIRS='(.+)'$", final, re.M).group(1).split("|")
    assert tuple(dirs) == fill_readme.README_ONLY_DIRS


# --- 6. o final.sh refaz o juiz × pessoas com o juiz de hoje, antes do README --------------------------------------

FAKE_PY = r"""#!/usr/bin/env bash
echo "$*" >> "{log}"
if [[ "$1" == "scripts/fill_readme.py" && "$2" != "--check" ]]; then echo "números" >> README.md
elif [[ "$1" == "-m" && "$2" == "evals.label" ]]; then
  mkdir -p evals/results; echo '{{}}' > evals/results/human_review.json
elif [[ "$1" == "-m" && "$2" == "evals.judge" ]]; then
  mkdir -p evals/validation; echo '{{"r": 1}}' > evals/validation/p.json
elif [[ "$1" == "scripts/delivery_message.py" ]]; then out="${{@: -1}}"; mkdir -p "$(dirname "$out")"; echo ok > "$out"
fi
exit 0
"""


@pytest.mark.skipif(BASH is None or os.name == "nt", reason="sem bash POSIX")
@pytest.mark.parametrize("labels", [True, False])
def test_final_sh_rejudges_the_frozen_pages_and_rebuilds_the_human_report_before_the_readme(tmp_path, labels):
    origin, repo, log = tmp_path / "origin.git", tmp_path / "repo", tmp_path / "calls.log"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, capture_output=True)
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "scripts").mkdir()
    (repo / "evals" / "validation").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "final.sh", repo / "scripts" / "final.sh")
    (repo / "README.md").write_text("# P\n", encoding="utf-8")
    (repo / "evals" / "validation" / "p.json").write_text("{}\n", encoding="utf-8")
    if labels:
        (repo / "evals" / "human_labels.ana.csv").write_text("id,humano\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "chore: scaffold")
    _git(repo, "remote", "add", "origin", str(origin))
    fake = tmp_path / "fakepy"
    fake.write_text(FAKE_PY.format(log=log), encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    out = subprocess.run([BASH, str(repo / "scripts" / "final.sh")], cwd=repo, capture_output=True, text=True,
                         encoding="utf-8", timeout=60, env={**os.environ, **GIT_ENV, "PY": str(fake)})
    assert out.returncode == 0, out.stdout + out.stderr
    calls = log.read_text(encoding="utf-8").splitlines()
    idx = {c.split()[0] if c.startswith("scripts") else " ".join(c.split()[:3]): i for i, c in enumerate(calls)}
    if labels:
        assert idx["-m evals.judge --validation"] < idx["-m evals.label --report"] < idx["scripts/fill_readme.py"]
        last = _git(repo, "show", "--name-only", "--format=", "HEAD").split()
        assert {"README.md", "evals/results/human_review.json", "evals/validation/p.json"} <= set(last)
        assert fill_readme.only_generated(last)
    else:
        assert not any("evals.judge" in c or "evals.label" in c for c in calls)


# --- 5. docs/RESULTS.md abre com a leitura em prosa e fecha com as tabelas por split ---------------------------------

def _live(split: str, rows: list[dict], metrics: dict) -> dict:
    return {"split": split, "provider": "anthropic", "status": "complete", "spent_usd": 0.5, "max_usd": 1.0,
            "live": True, "rows": rows, "metrics": {"ALL": {"cases": len(rows), "p50_ms": 9000.0, "p95_ms": 20000.0,
                                                            **metrics}}}


def test_results_opens_with_generated_reading_and_ends_with_the_split_tables(tmp_path):
    (tmp_path / "live_official.json").write_text(json.dumps(
        _live("official", _rows(), {"resolved_acc": 42.9})), encoding="utf-8")
    mem = [{"id": "m1", "split": "memory", "checks": {"memory": True}},
           {"id": "m2", "split": "memory", "checks": {"memory": False}}]
    (tmp_path / "live_memory.json").write_text(json.dumps(
        {**_live("memory", mem, {"memory_acc": 50.0}), "stability": {"pass_at_1": 0.5}}), encoding="utf-8")
    text = fill_readme.reading_block(tmp_path)
    lines = text.splitlines()
    assert 6 <= len(lines) <= 10
    assert lines[0].startswith("- **Na referência")
    assert any("**Abaixo:** Oficiais resolvidas por completo" in x and "resposta parcial" in x and "`c2`" in x
               for x in lines)
    assert any("Memória ao vivo: pass@1 0.50" in x and "`m2`" in x for x in lines)
    assert any(x.startswith("- **Parcial, fora da manchete:** 43%") for x in lines)
    assert any(x.startswith("- **Ao vivo:** 2 splits, 9 execuções") for x in lines)
    layout = fill_readme.results_layout((ROOT / "docs" / "RESULTS.md").read_text(encoding="utf-8"))
    assert layout.index("<!-- reading:begin -->") < layout.index("<!-- eval:begin -->")
    assert layout.rstrip().endswith("<!-- eval-live-splits:end -->")
    assert fill_readme.results_layout(layout) == layout  # uma vez só
    live = fill_readme.live_block(tmp_path)
    assert "<details>" not in live and "#### Split" not in live
    splits = fill_readme.live_splits_block(tmp_path)
    assert splits.startswith("<details>") and splits.count("#### Split") == 2


def test_check_flags_results_without_the_reading_or_the_tables(tmp_path):
    (tmp_path / "docs").mkdir()
    res = tmp_path / "evals" / "results"
    res.mkdir(parents=True)
    (res / "live_official.json").write_text(json.dumps(_live("official", _rows(), {"resolved_acc": 42.9})),
                                            encoding="utf-8")
    old = ("# R\n\n## Ao vivo\n\n<!-- eval-live:begin -->\n" + fill_readme.live_block(res)
           + "\n<!-- eval-live:end -->\n")
    (tmp_path / "docs" / "RESULTS.md").write_text(old, encoding="utf-8")
    (tmp_path / "README.md").write_text("# P\n", encoding="utf-8")
    problems = fill_readme.check(tmp_path / "README.md", res, root=tmp_path)
    assert any("sem a leitura em prosa no topo" in p for p in problems)


def test_demo_marks_partial_answer_as_partial_not_resolved():
    # ensaio 13: o DEMO mostrava o dict cru com "resolved: True" numa resposta parcial
    from scripts.demo_md import checks_line

    row = {"checks": {"intent": True, "facts": True, "resolved": True},
           "steps": [{"agent": "faq", "status": "partial"}]}
    line = checks_line(row)
    assert "parcial" in line and "3/3" in line and "completa" not in line
    assert "completa" in checks_line({"checks": {"intent": True}, "steps": [{"status": "ok"}]})
    assert "não resolvida" in checks_line({"checks": {"intent": True, "facts": False}, "steps": []})
