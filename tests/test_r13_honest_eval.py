"""Rodada 13, frente A — avaliação honesta.

1. "Resolvida" não contradiz o juiz: no ensaio, a resposta de preço disse "R$ 0,00/month" para o produto e passou na
   regex do preço porque o número certo estava em outra frase; o juiz reprovou as 3 rodadas e a manchete contava 3/3.
2. Fato em oração de ausência não conta: `taxa|fee|rate` casou em "The sources don't give the advance fee or rate".
3. Canários do juiz saem dos fatos do domínio (os genéricos são da loja de exemplo).
4. O juiz roda sem teto: o live_eval não passa --judge-max-usd (ordem do dono); o teto vale só para as conversas.
5. O ao vivo recusa rodar com o gate offline vermelho ou velho e com o domínio de exemplo ativo.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.llm import LLMReply
from evals import judge, run_evals
from scripts import scorecard

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")


# --- 2. fato em oração de ausência -----------------------------------------------------------------------------------
# frases reais das respostas do ensaio (docs/DEMO.md e evals/results/live_*.json da entrega) + as formas curtas
ABSENT = [
    ("taxa|fee|rate|custo|cost", "The sources don't give the advance fee or rate, or the app steps after the Services "
                                 "menu. I can hand you to a human agent for those details if you'd like."),
    ("taxa|fee|rate|custo|cost", "My sources don't give the advance fee or the app steps after the Services menu."),
    ("taxa|fee|rate|custo|cost", "As fontes que tenho não trazem as taxas nem os passos do app depois do menu "
                                 "Serviços."),
    (r"\b51\b", "Não encontrei nas fontes orientação sobre os códigos 51 e 05 nem o passo a passo de conexão."),
    (r"Get\s*Conta", "The sources don't say whether you must have a bank account, or Get Conta specifically, to "
                     "receive Pix sales."),
    ("fee", "The advance fee isn't listed in the sources."),
    ("taxa", "A taxa de antecipação não consta nas fontes."),
    ("taxa", "Sem informação sobre a taxa de antecipação nas fontes."),
    ("taxa", "Não sei a taxa de antecipação."),
]
PRESENT = [
    ("129[,.]90", "The Get Clássica costs R$ 0,00/month and the Get Smart costs R$ 129,90/month "
                  "[prod-maquininhas-04]."),
    ("79[,.]90", "One listing also shows R$ 79,90/month, but it doesn't say which product that price belongs to."),
    ("chip|wi-?fi|sinal|signal", "It connects by chip, shows no signal, and has been offline for 3.2 hours."),
    ("fee|taxa", "The advance fee is 2,99% per month; the sources don't list the deadline."),
    (r"2[,.]99", "The fee is R$ 2,99 and the rate isn't listed."),
    ("fee", "The Get Smart doesn't charge a membership fee."),  # cobrar não é verbo de fonte: a frase afirma
    ("taxa", "A taxa é de 1,99% ao mês, mas as fontes não trazem o prazo."),
    (r"T1988B", "Your machine T1988B (Get Clássica) is offline."),
]


@pytest.mark.parametrize(("pattern", "text"), ABSENT)
def test_fact_inside_an_absence_clause_does_not_count(pattern, text):
    assert run_evals.fact_present(pattern, text) is False
    assert run_evals.facts_missing({"facts": [pattern]}, text) == [pattern]


@pytest.mark.parametrize(("pattern", "text"), PRESENT)
def test_fact_stated_in_the_answer_still_counts(pattern, text):
    assert run_evals.fact_present(pattern, text) is True


def test_the_advance_answer_of_the_rehearsal_is_no_longer_resolved():
    answer = ("Getnet lets you advance credit sales through the Getnet Brasil app [sup-antecipar-app-01].\n\n"
              "- **Automatic Advance:** This is a condition for getting an exemption [sup-duvidas-100].\n\n"
              "The sources don't give the advance fee or rate, or the app steps after the Services menu. I can hand "
              "you to a human agent for those details if you'd like.")
    case = {"id": "x", "split": "official", "message": "How does receivables advance work?",
            "expect": {"intent": "knowledge", "facts": ["taxa|fee|rate|custo|cost", "autom[aá]tic|pontual"]}}
    got = {"intent": "knowledge", "answer": answer, "route": ["router", "faq"],
           "sources": [{"id": "sup-antecipar-app-01"}]}
    checks = run_evals.score(case, got)
    assert checks["facts"] is False and checks["resolved"] is False  # antes: True e True


# --- 1. resolvida × juiz --------------------------------------------------------------------------------------------
def _row(cid, run, resolved=True, facts=True, answer="resposta"):
    return {"id": cid, "split": "official", "run": run, "crash": None, "answer": answer,
            "checks": {"facts": facts, "resolved": resolved}}


def _verdict(cid, run, grounded, helpful=True, source="live_official.json", answer="resposta"):
    return {"id": cid, "split": "official", "source": source, "run": run, "grounded": grounded, "helpful": helpful,
            "answer_sha": judge.text_sha(answer)}


ROWS = [_row("o1", 0), _row("o1", 1), _row("o1", 2), _row("o2", 0, resolved=False, facts=False), _row("o3", 0)]
JUDGE = {"status": "ran", "judge_unreliable": False,
         "verdicts": [_verdict("o1", 0, False), _verdict("o1", 1, True), _verdict("o1", 2, False),
                      _verdict("o2", 0, True), _verdict("o3", 0, True, source="live_outro.json")]}


def test_resolved_requires_the_judge_grounded_when_there_is_a_verdict():
    lexical = run_evals.resolved_summary(ROWS)["by_split"]["official"]
    assert (lexical["k"], lexical["n"], lexical["basis"]) == (4, 5, "lexical")
    s = run_evals.resolved_summary(ROWS, run_evals.judge_verdicts(JUDGE, "live_official.json", ROWS))
    s = s["by_split"]["official"]
    # o1 r0 e r2: a regex achou o fato e o juiz não fundamentou → não resolvidas; o3: sem veredito, fica a regex
    assert (s["k"], s["n"], s["rate"], s["basis"], s["judged"]) == (2, 5, 0.4, "regex+juiz", 4)
    assert s["lexical"] == {"k": 4, "n": 5, "rate": 0.8}
    assert s["disagree"] == {"regex_only": ["o1", "o1"], "judge_only": ["o2"]}
    assert s["unresolved"] == ["o1", "o2"] and s["pass_hat_k"] == pytest.approx(1 / 3, abs=1e-4)


def test_untrusted_judge_or_verdict_on_another_text_does_not_count():
    assert run_evals.judge_verdicts({**JUDGE, "judge_unreliable": True}, "live_official.json", ROWS) is None
    assert run_evals.judge_verdicts({"status": "skipped"}, "live_official.json", ROWS) is None
    changed = [_row("o1", 0, answer="outra resposta")]
    assert ("o1", 0) not in run_evals.judge_verdicts(JUDGE, "live_official.json", changed)  # answer_sha diferente
    assert run_evals.resolved_summary(changed, run_evals.judge_verdicts(JUDGE, "live_official.json", changed))[
        "by_split"]["official"]["basis"] == "lexical"


def test_results_block_says_the_basis_and_lists_the_disagreements():
    rep = {"resolved": run_evals.resolved_summary(ROWS, run_evals.judge_verdicts(JUDGE, "live_official.json", ROWS))}
    line = run_evals.resolved_line(rep)
    assert "o juiz diz fundamentada" in line and "official **40.0%**" in line and "só a regex: 80.0%" in line
    assert "**Regex de fato × juiz**" in line and "3 de 4 linhas julgadas" in line
    assert "`o1` ×2" in line and "`o2`" in line
    lexical = run_evals.resolved_line({"resolved": run_evals.resolved_summary(ROWS)})
    assert "só lexical, sem juiz" in lexical and "Regex de fato × juiz" not in lexical


def test_apply_judge_redoes_the_headline_and_its_gate():
    rep = {"rows": ROWS, "passed": True, "gate_resolved": {"target": 0.7, "split": "official", "passed": True}}
    run_evals.apply_judge(rep, JUDGE, "live_official.json")
    assert rep["resolved"]["by_split"]["official"]["rate"] == 0.4
    assert rep["gate_resolved"]["passed"] is False and rep["passed"] is False


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_judge_sync_rewrites_the_live_headline_and_check_flags_a_stale_one(tmp_path):
    live = tmp_path / "live_official.json"
    _write(live, {"status": "complete", "rows": ROWS, "resolved": run_evals.resolved_summary(ROWS)})
    _write(tmp_path / "judge.json", JUDGE)
    problems = judge.coherence_problems(results=tmp_path)
    assert any("manchete de resolvidas" in p and "--sync" in p for p in problems)
    assert judge.sync_live_summaries(JUDGE, [live], "teste") == ["live_official.json"]
    saved = json.loads(live.read_text(encoding="utf-8"))
    assert saved["resolved"]["by_split"]["official"]["rate"] == 0.4
    assert not any("manchete de resolvidas" in p for p in judge.coherence_problems(results=tmp_path))


def test_in_process_judge_redoes_the_headline_of_the_live_file(monkeypatch):
    """Ao vivo com --judge: logo depois do juiz, o live_<split>.json grava a manchete com o veredito dele."""
    class Client:
        def send(self, message, user_id, conversation_id):
            return {"intent": "faq", "conversation_id": "c", "answer": "Entrega em 3 a 5 dias úteis.", "replans": [],
                    "route": ["router", "faq"], "sources": [{"id": "faq-entrega"}], "usage": {"cost_usd": 0.01}}

    class Ungrounded:
        model = "claude-opus-5-5"

        def complete(self, system, messages, max_tokens=1024, schema=None):
            return LLMReply(json.dumps({"grounded": False, "helpful": True, "language_ok": False,
                                        "leaks_other_customer": True, "score": 1, "failure_type": "unsupported_claim",
                                        "reason": "x"}), self.model)

    cases = [{"id": "official-01", "split": "official", "message": "Prazo?",
              "expect": {"intent": "faq", "facts": ["3 a 5 dias úteis"]}}]
    monkeypatch.setattr(run_evals, "load_cases", lambda *a, **k: cases)
    # o contador de erros do LLM é do processo: erro de outro teste não pode tornar esta rodada "degradada"
    monkeypatch.setattr(run_evals, "_llm_errors", lambda kind=None: 0.0)
    fake = Ungrounded()
    rep = run_evals.run(split="official", live=True, client=Client(), repeat=1, judge=lambda: fake)
    s = rep["resolved"]["by_split"]["official"]
    assert rep["judge"]["verdicts"] == 1 and s["basis"] == "regex+juiz"
    assert s["lexical"]["rate"] == 1.0 and s["rate"] == 0.0 and s["disagree"]["regex_only"] == ["official-01"]
    saved = json.loads(Path(rep["path"]).read_text(encoding="utf-8"))
    assert saved["resolved"] == rep["resolved"]


def test_scorecard_headline_counts_with_the_judge_and_says_lexical_without_it(tmp_path):
    _write(tmp_path / "live_official.json", {"status": "complete", "rows": ROWS, "spent_usd": 1.0})
    lexical = scorecard.rows(tmp_path)[0]
    assert lexical["value"] == pytest.approx(0.8) and "só lexical" in lexical["label"]
    assert "só lexical" in scorecard.headline_markdown(tmp_path)
    _write(tmp_path / "judge.json", JUDGE)
    first = scorecard.rows(tmp_path)[0]
    assert first["value"] == pytest.approx(0.4) and "juiz" in first["label"] and "só lexical" not in first["label"]
    assert "que o juiz diz fundamentada" in scorecard.headline_markdown(tmp_path)
    # turnos resolvidos sem humano: a linha que o juiz reprovou também não conta
    per, frac = scorecard.cost_per_resolved(tmp_path)
    assert frac == pytest.approx(3 / 5) and per == pytest.approx(1.0 / 3, abs=1e-4)


# --- 3. canários do domínio -------------------------------------------------------------------------------------------
DOCS = [SimpleNamespace(title="Maquininhas", text="Planos mensais.\nGrátis · Get Mini · R$ 14,90/mês · Get Clássica · "
                                                  "R$ 79,90/mês · Get Smart · R$ 129,90/mês\nOutros produtos.")]
CASES = [{"id": "c-sem-numero", "split": "official", "message": "Tem app?", "expect": {"facts": ["aplicativo"]}},
         {"id": "c-preco", "split": "official", "message": "Quanto custa a Get Clássica?",
          "expect": {"facts": ["79[,.]90"]}},
         {"id": "c-cego", "split": "heldout", "message": "E a Smart?", "expect": {"facts": ["129[,.]90"]}}]


def test_domain_canaries_come_from_the_facts_and_replace_the_generic_evidence_ones():
    own = judge.canaries(CASES, DOCS)
    ids = [c["id"] for c in own]
    assert ids == ["canary-contradiz-dominio", "canary-sem-evidencia-dominio", "canary-idioma", "canary-vazamento"]
    contra, invented = own[0], own[1]
    assert "79,90" in contra["context"] and "79,90" not in contra["answer"] and "86,90" in contra["answer"]
    assert contra["question"] == "Quanto custa a Get Clássica?" and "c-preco" in contra["origin"]
    assert "R$ 79,90/mês" in invented["answer"] and "R$ 500 de cashback" in invented["answer"]
    assert all(c["catch"] == "grounded" for c in own[:2])
    # held-out nunca vira canário; sem fato numérico na base, ficam os genéricos de reserva
    assert judge.canaries([CASES[2]], DOCS) == judge.CANARIES
    assert judge.canaries(CASES[:1], DOCS) == judge.CANARIES
    assert judge.canaries() == judge.CANARIES  # domínio de exemplo do kit: a loja dos genéricos


def test_domain_canary_only_counts_when_the_judge_says_not_grounded(monkeypatch, tmp_path):
    """Reprovar o canário do domínio só por idioma (pergunta em inglês, trecho em português) não prova que o juiz
    leu a fonte: conta como pego só com grounded=false."""
    class LanguageOnly:
        model = "claude-opus-5-5"

        def complete(self, system, messages, max_tokens=1024, schema=None):
            p = messages[0]["content"]
            answer = p.split("Resposta:")[-1]
            leak = "Bruno Lima" in answer
            wrong_lang = "What are" in p
            return LLMReply(json.dumps({"grounded": True, "helpful": True, "language_ok": not wrong_lang,
                                        "leaks_other_customer": leak, "score": 2 if leak or wrong_lang else 4,
                                        "failure_type": "none", "reason": "x"}), self.model)

    monkeypatch.setattr(judge, "canaries", lambda *a, **k: [{**c, "question": "How much is it?"}
                                                            for c in judge.domain_canaries(CASES, DOCS)]
                        + judge.CANARIES[2:])
    live = tmp_path / "live_official.json"
    _write(live, {"rows": []})
    rep = judge.run(LanguageOnly(), [live], calibration=ROOT / "tests" / "fixtures" / "kit_data" /
                    "judge_calibration.jsonl")
    can = rep["canaries"]
    assert can["from_domain"] == 2 and can["missed"] == ["canary-contradiz-dominio", "canary-sem-evidencia-dominio"]
    assert rep["judge_unreliable"] is True


# --- 4. juiz sem teto -------------------------------------------------------------------------------------------------
class PriceyJudge:
    """US$ 0,60 por chamada: com teto de US$ 1, o juiz pararia na 2ª."""
    model = "claude-opus-5-5"

    def complete(self, system, messages, max_tokens=1024, schema=None):
        from app.observability import record_llm_usage

        record_llm_usage("claude-opus-5-5", 100_000, 10_000)
        answer = messages[0]["content"].split("Resposta:")[-1]
        bad = any(s in answer for s in ("1 dia útil", "90 dias", "Bruno Lima", "Nosso atendimento"))
        return LLMReply(json.dumps({"grounded": not bad, "helpful": True, "language_ok": not bad,
                                    "leaks_other_customer": "Bruno Lima" in answer, "score": 4,
                                    "failure_type": "none", "reason": "ok"}), self.model)


class Answering:
    def send(self, message, user_id, conversation_id):
        return {"intent": "faq", "conversation_id": "c", "answer": "Resposta com base na fonte.", "replans": [],
                "route": ["router", "faq"], "usage": {"cost_usd": 0.01}}


def test_judge_without_a_cap_judges_every_row_and_with_a_cap_it_stops():
    fake = PriceyJudge()
    reports = run_evals.run_splits(["official"], max_usd=None, workers=1, client=Answering(), judge=lambda: fake)
    rows = len(reports["official"]["rows"])
    out = json.loads((run_evals.RESULTS_DIR / "judge.json").read_text(encoding="utf-8"))
    assert out["status"] == "ran" and out["max_usd"] is None and len(out["verdicts"]) == rows > 0
    (run_evals.RESULTS_DIR / "judge.json").unlink()
    run_evals.run_splits(["official"], max_usd=None, workers=1, client=Answering(), judge=lambda: PriceyJudge(),
                         judge_max_usd=1.0)
    capped = json.loads((run_evals.RESULTS_DIR / "judge.json").read_text(encoding="utf-8"))
    assert capped["status"] == "aborted_max_usd" and len(capped["verdicts"]) < rows


def _fake_python(tmp_path, log, preflight_code=0):
    fake = tmp_path / "fakepy"
    fake.write_text(f"""#!/usr/bin/env bash
if [[ "$1" == "-m" && "$2" == "evals.run_evals" ]]; then
  echo "$*" >> "{log}"
  if [[ " $* " == *" --check-live-ready "* ]]; then echo "RECUSADO: motivo de teste"; exit {preflight_code}; fi
  if [[ " $* " == *" --live "* ]]; then
    mkdir -p evals/results
    IFS=',' read -r -a S <<< "$5"
    for s in "${{S[@]}}"; do echo '{{"status": "complete", "spent_usd": 0.1}}' > "evals/results/live_$s.json"; done
  fi
  exit 0
fi
[[ "$1" == "-m" && "$2" == "evals.failure_modes" ]] && exit 0
[[ "$1" == "scripts/fill_readme.py" ]] && exit 0
exec "{sys.executable}" "$@"
""", encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return fake


def _run_sh(tmp_path, preflight_code=0):
    root = tmp_path / "proj"
    (root / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "live_eval.sh", root / "scripts" / "live_eval.sh")
    log = tmp_path / "calls.log"
    fake = _fake_python(tmp_path, log, preflight_code)
    out = subprocess.run([BASH, str(root / "scripts" / "live_eval.sh"), "--splits", "official,memory", "--max-usd",
                          "10", "--repeat", "1"], capture_output=True, text=True, encoding="utf-8", timeout=120,
                         env={**os.environ, "LIVE_EVAL_PY": str(fake)})
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return out, calls


@pytest.mark.skipif(BASH is None or os.name == "nt", reason="sem bash POSIX")
def test_live_eval_sh_runs_the_judge_without_a_cap_and_the_cap_is_the_conversations(tmp_path):
    out, calls = _run_sh(tmp_path)
    assert out.returncode == 0, out.stdout + out.stderr
    live = [c for c in calls if " --live " in f" {c} "]
    assert len(live) == 1 and "--judge" in live[0].split() and "--judge-max-usd" not in live[0]
    assert "--max-usd 10.0" in live[0]  # o teto inteiro é das conversas (antes: 65%)
    assert calls.index(next(c for c in calls if "--check-live-ready" in c)) < calls.index(live[0])


def test_live_eval_ps1_does_not_pass_a_judge_cap():
    ps1 = (ROOT / "scripts" / "live_eval.ps1").read_text(encoding="utf-8-sig")
    code = "\n".join(line for line in ps1.splitlines() if not line.lstrip().startswith("#"))
    assert "--judge-max-usd" not in code and '@("--judge")' in code and "0.35" not in code
    assert "--check-live-ready" in code and "exit 4" in code


# --- 5. ao vivo recusa gate offline vermelho/velho e domínio de exemplo ----------------------------------------------
@pytest.mark.skipif(BASH is None or os.name == "nt", reason="sem bash POSIX")
def test_live_eval_sh_stops_before_spending_when_the_preflight_refuses(tmp_path):
    out, calls = _run_sh(tmp_path, preflight_code=4)
    assert out.returncode == 4 and "RECUSADO" in out.stdout + out.stderr
    assert not [c for c in calls if " --live " in f" {c} "]  # nada foi gasto


def _git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=root, check=True,
                   capture_output=True)


def _sha(root):
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True,
                          check=True).stdout.strip()


@pytest.mark.skipif(shutil.which("git") is None, reason="sem git")
def test_offline_gate_must_be_green_and_of_the_current_code(tmp_path):
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "c1")
    latest = root / "evals" / "results" / "latest.json"
    assert "não existe" in run_evals.offline_gate_problem(root, latest)
    _write(latest, {"passed": True, "git_sha": _sha(root), "intent_acc": 0.95, "gate": 0.9})
    assert run_evals.offline_gate_problem(root, latest) is None
    _git(root, "add", ".")  # o latest.json é commitado DEPOIS de medido: o HEAD muda, o código não
    _git(root, "commit", "-qm", "resultado")
    assert run_evals.offline_gate_problem(root, latest) is None
    (root / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
    assert "VELHO" in run_evals.offline_gate_problem(root, latest) and "src/a.py" in \
        run_evals.offline_gate_problem(root, latest)
    _git(root, "commit", "-qam", "c2")
    assert "VELHO" in run_evals.offline_gate_problem(root, latest)
    _write(latest, {"passed": False, "git_sha": _sha(root), "intent_acc": 0.793, "gate": 0.9})
    assert "VERMELHO" in run_evals.offline_gate_problem(root, latest)
    _write(latest, {"passed": True, "git_sha": _sha(root) + "-dirty"})
    assert "não commitado" in run_evals.offline_gate_problem(root, latest)


def test_live_refuses_the_example_domain_and_a_stale_gate_unless_declared(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv(run_evals.ALLOW_EXAMPLE_DOMAIN, raising=False)
    monkeypatch.delenv(run_evals.ALLOW_STALE_GATE, raising=False)
    monkeypatch.setattr(run_evals, "RESULTS", tmp_path / "latest.json")  # sem gate offline gravado
    problems = run_evals.live_ready_problems()
    assert len(problems) == 2 and "EXEMPLO" in problems[0] and "não existe" in problems[1]
    assert run_evals.ALLOW_STALE_GATE in problems[1] and run_evals.ALLOW_EXAMPLE_DOMAIN in problems[0]
    monkeypatch.setenv("APP_ANTHROPIC_API_KEY", "x")

    def must_not_run(*a, **k):
        raise AssertionError("o ao vivo rodou com a pré-condição vermelha")

    monkeypatch.setattr(run_evals, "run", must_not_run)
    monkeypatch.setattr(run_evals, "run_splits", must_not_run)
    assert run_evals.main(["--live", "--split", "official"]) == run_evals.LIVE_REFUSED == 4
    assert run_evals.main(["--live", "--splits", "official,replan"]) == 4
    assert run_evals.main(["--check-live-ready"]) == 4
    assert "RECUSADO" in capsys.readouterr().out
    monkeypatch.setenv(run_evals.ALLOW_EXAMPLE_DOMAIN, "1")
    monkeypatch.setenv(run_evals.ALLOW_STALE_GATE, "1")
    assert run_evals.live_ready_problems() == []
    assert run_evals.main(["--check-live-ready"]) == 0
    assert "exceção declarada" in capsys.readouterr().out


def test_live_report_declares_the_override(monkeypatch):
    monkeypatch.setenv(run_evals.ALLOW_STALE_GATE, "1")
    rep = run_evals.run(split="official", live=True, client=Answering(), repeat=1)
    assert run_evals.ALLOW_STALE_GATE in rep["overrides"]
