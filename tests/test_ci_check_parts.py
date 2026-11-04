"""A CI roda o check em 3 jobs paralelos (core, replay, docker): em fila ele levava 15–20 min nos ensaios 13 e 14 e o
resultado do último commit chegava depois do T+59. As 3 partes juntas têm de ser o check inteiro, sem etapa perdida
nem repetida, e só o check inteiro reescreve o reports/verify.md."""
import sys
from pathlib import Path

import yaml

from scripts import check

ROOT = Path(__file__).resolve().parents[1]
PARTS = ("core", "replay", "docker")


def _run(monkeypatch, part: str) -> tuple[list[str], bool]:
    names: list[str] = []
    wrote = []

    def fake(name):
        def _f(*_a, **_k):
            names.append(name)
            return (name, True, 0.0, "")
        return _f

    monkeypatch.setattr(check, "step", lambda name, *_a, **_k: fake(name)())
    for fn in ("cited_tests_pass", "committed_eval_is_current", "commit_titles_clean", "no_example_data",
               "officials_have_facts", "replay_gate"):
        monkeypatch.setattr(check, fn, fake(fn))
    monkeypatch.setattr(check, "delivery_doc_checks", lambda: [fake("delivery_doc_checks")()])
    monkeypatch.setattr(check, "docker_steps", lambda *_a, **_k: [fake("docker_steps")()])
    monkeypatch.setattr(check, "image_extras", lambda *_a: "hybrid")
    monkeypatch.setattr(check, "domain_started", lambda: True)
    monkeypatch.setattr(check, "write_verify_report", lambda *_a: wrote.append(True))
    monkeypatch.setattr(sys, "argv", ["check.py", "--docker", "--scale", "--part", part])
    assert check.main() == 0
    return names, bool(wrote)


def test_the_three_parts_are_the_whole_check_without_overlap(monkeypatch):
    whole, wrote_all = _run(monkeypatch, "all")
    parts = {p: _run(monkeypatch, p)[0] for p in PARTS}
    joined = [n for p in PARTS for n in parts[p]]
    assert sorted(joined) == sorted(whole), "etapa perdida ou repetida entre as partes"
    assert len(set(joined)) == len(joined)
    assert parts["replay"] == ["replay_gate"]
    assert "docker_steps" in parts["docker"] and "réplicas (conversa, caso único, queda)" in parts["docker"]
    assert "pytest" in parts["core"] and "eval gate" in parts["core"]
    assert wrote_all


def test_only_the_whole_check_rewrites_verify_report(monkeypatch):
    for p in PARTS:
        assert _run(monkeypatch, p)[1] is False, p


def test_ci_runs_the_three_parts_in_parallel_jobs():
    job = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))["jobs"]["check"]
    assert job["strategy"]["matrix"]["part"] == ["core", "docker", "replay:1/4", "replay:2/4", "replay:3/4",
                                                 "replay:4/4"]
    assert job["strategy"]["fail-fast"] is False  # um vermelho não cancela as outras partes
    runs = [s.get("run", "") for s in job["steps"]]
    assert "python scripts/check.py --docker --scale --part ${{ matrix.part }}" in runs
    leaks = next(s for s in job["steps"] if "gitleaks" in s.get("uses", ""))
    assert leaks.get("if") == "matrix.part == 'core'"  # o histórico inteiro varrido uma vez só


def test_early_signal_run_is_not_cancelled_by_pushes():
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    on = wf.get("on", wf.get(True))  # o PyYAML lê a chave `on` como True
    assert "workflow_dispatch" in on
    assert "github.event_name" in wf["concurrency"]["group"]  # disparo à mão fora do grupo dos pushes
    assert wf["concurrency"]["cancel-in-progress"] is True  # pushes seguidos continuam se cancelando


def test_delivered_code_carries_no_fixed_secret_literal():
    """Prova do kit no getnet-ensaio-geral (04/11): o gitleaks do CI acusou o segredo fixo do smoke de réplicas do
    Postgres (generic-api-key) ao varrer o histórico. Segredo de teste é gerado a cada execução."""
    import re

    pat = re.compile(r'^[A-Z_]*(SECRET|TOKEN|PASSWORD|API_KEY)[A-Z_]*\s*=\s*"[^"]{16,}"', re.M)
    hits = [f"{p.relative_to(ROOT)}" for d in ("scripts", "src", "evals", "ops") for p in (ROOT / d).rglob("*.py")
            if pat.search(p.read_text(encoding="utf-8", errors="ignore"))]
    assert hits == []


def test_replay_shards_cover_every_split_once_and_balance_by_size():
    # tamanhos dos cassetes do ensaio 14 (KB): o replay inteiro levou 1121 s num job só
    sizes = {"memory": 888, "heldout": 698, "real": 329, "official": 268, "replan": 175, "official-var": 174,
             "dependent": 122, "hard": 83, "guardrail": 74, "approval": 51, "parallel": 47, "partial": 41,
             "hitl": 28}
    shards = check.replay_shards(sizes, 4)
    flat = [n for sh in shards for n in sh]
    assert sorted(flat) == sorted(sizes) and len(flat) == len(set(flat))
    loads = [sum(sizes[n] for n in sh) for sh in shards]
    assert max(loads) <= 900  # o maior cassete sozinho manda; nenhum pedaço passa muito dele
    assert check.replay_shards(sizes, 4) == shards  # os jobs paralelos chegam à mesma divisão
    assert check.replay_shards({"a": 1}, 4)[1:] == [[], [], []]


def test_part_argument_accepts_replay_shards_and_refuses_nonsense():
    import argparse

    import pytest

    assert check._part("replay:2/4") == "replay:2/4"
    for bad in ("replay:5/4", "replay:0/4", "tudo", "replay:1"):
        with pytest.raises(argparse.ArgumentTypeError):
            check._part(bad)


def test_run_replay_accepts_several_splits(tmp_path, monkeypatch):
    from evals import run_evals

    cas = tmp_path / "cassettes"
    cas.mkdir()
    for name in ("a", "b", "c"):
        (cas / f"{name}.jsonl").write_text("", encoding="utf-8")
    monkeypatch.setattr(run_evals, "cassettes_dir", lambda: cas)
    monkeypatch.setattr(run_evals, "RESULTS_DIR", tmp_path)  # sem live_<split>.json: cada um vira "grave de novo"
    monkeypatch.setattr(run_evals, "replay_dir", lambda: tmp_path / "replay")
    out = run_evals.run_replay("a,c")
    assert sorted(out["splits"]) == ["a", "c"]


def test_rerank_gate_threshold_sits_between_scores_not_on_one():
    from evals import retrieval_eval

    pos, neg = [-4.98612, -3.2, -1.0], [-6.5, -5.1, -7.0]
    gate = retrieval_eval.calibrate_rerank_gate(pos, neg)
    t = gate["min_rerank"]
    assert t not in pos + neg  # em cima de uma nota, 1e-5 de outra CPU trocava a pergunta de lado
    assert -5.1 < t < -4.98612 and abs(t - (-5.1 + -4.98612) / 2) < 1e-6
    assert gate["pos_answered"] == 1.0 and gate["neg_refused"] == 1.0  # mesma divisão da calibração


def _report(handoff_k, replan_k, n=176):
    return {"metrics": {"ALL": {"handoff_acc": round(100 * handoff_k / n, 1),
                                "ci": {"handoff_acc": {"k": handoff_k, "n": n, "lo": 0, "hi": 0},
                                       "replanned_acc": {"k": replan_k, "n": 20, "lo": 0, "hi": 0}},
                                "replanned_acc": round(100 * replan_k / 20, 1), "p50_ms": 1}}}


def test_committed_eval_tolerates_machine_noise_but_not_stale_evidence(tmp_path, monkeypatch):
    import json

    root = tmp_path
    (root / "evals" / "results").mkdir(parents=True)
    monkeypatch.setattr(check, "ROOT", root)
    fresh = root / "fresh.json"

    def run(old, new):
        (root / "evals" / "results" / "latest.json").write_text(json.dumps(old), encoding="utf-8")
        fresh.write_text(json.dumps(new), encoding="utf-8")
        return check.committed_eval_is_current(fresh)

    _, ok, _, detail = run(_report(159, 11), _report(161, 13))  # ensaio 14: o CI mediu 2 casos a mais
    assert ok and detail.startswith("AVISO")
    _, ok, _, detail = run(_report(150, 11), _report(161, 13))  # 11 casos: evidência velha
    assert not ok and "make readme" in detail
    _, ok, _, _ = run(_report(159, 11), _report(159, 11, n=177))  # n diferente: outro conjunto de casos
    assert not ok


def test_dependabot_prs_run_only_the_light_job():
    jobs = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))["jobs"]
    for name in ("check", "postgres", "retrieval", "supply-chain"):
        assert jobs[name].get("if") == "github.actor != 'dependabot[bot]'", name
    assert "if" not in jobs["offline-tests"]  # o PR do Dependabot ainda é testado


def test_kit_source_branch_does_not_run_ci():
    """O push do kit-fonte (T−30, antes do relógio) disparava uma CI completa de 10 jobs à toa, na mesma fila da CI
    do scaffold (getnet-ensaio-geral-2, 04/11)."""
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    on = wf.get("on", wf.get(True))
    assert "kit-fonte" in on["push"]["branches-ignore"]
