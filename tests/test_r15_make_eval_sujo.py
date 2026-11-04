"""Rodada 15 (ensaio 14: o `make eval` com a calibração sem commit gravou um latest.json `-dirty`, e o ao vivo recusou
DEPOIS, ~5 min perdidos). O gate offline que grava o latest.json padrão e o `--calibrate-gate --apply` recusam na
hora, antes de medir, com árvore suja nos caminhos que o gate lê, e a mensagem diz "COMMIT ANTES"."""
import subprocess

import pytest

from evals import run_evals


def _git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=root, check=True,
                   capture_output=True)


@pytest.fixture
def repo(tmp_path):
    for rel in ("src/app/domain/challenge/__init__.py", "data/sources.json", "evals/cases.jsonl",
                "evals/results/latest.json", "docs/README.md"):
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x\n", encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def test_clean_tree_and_outside_paths_are_not_dirty(repo):
    assert run_evals.dirty_gate_files(repo) == []
    (repo / "evals/results/latest.json").write_text("novo\n", encoding="utf-8")  # resultado: fora
    (repo / "docs/README.md").write_text("novo\n", encoding="utf-8")  # docs: o gate não lê
    assert run_evals.dirty_gate_files(repo) == []


def test_calibration_written_without_commit_is_dirty(repo):
    (repo / "src/app/domain/challenge/__init__.py").write_text("MIN_SCORE = 7.939\n", encoding="utf-8")
    (repo / "data/novo.jsonl").write_text("{}\n", encoding="utf-8")  # arquivo novo também conta
    assert run_evals.dirty_gate_files(repo) == ["src/app/domain/challenge/__init__.py", "data/novo.jsonl"]


def test_no_git_is_not_dirty(tmp_path):
    assert run_evals.dirty_gate_files(tmp_path) == []


def _never_run(*a, **k):
    raise AssertionError("mediu com a árvore suja")


DIRTY = ["src/app/domain/challenge/__init__.py"]


def test_make_eval_refuses_before_measuring(monkeypatch, capsys):
    monkeypatch.delenv(run_evals.ALLOW_DIRTY_GATE, raising=False)
    monkeypatch.setattr(run_evals, "dirty_gate_files", lambda root=None: DIRTY)
    monkeypatch.setattr(run_evals, "run", _never_run)
    assert run_evals.main([]) == run_evals.DIRTY_REFUSED
    out = capsys.readouterr().out
    assert "RECUSADO (gate offline, nada foi medido)" in out and "COMMIT ANTES" in out and DIRTY[0] in out


def test_calibrate_apply_refuses_before_measuring(monkeypatch, capsys):
    monkeypatch.delenv(run_evals.ALLOW_DIRTY_GATE, raising=False)
    monkeypatch.setattr(run_evals, "dirty_gate_files", lambda root=None: DIRTY)
    monkeypatch.setattr(run_evals, "calibrate_gate", _never_run)
    assert run_evals.main(["--calibrate-gate", "--apply"]) == run_evals.DIRTY_REFUSED
    assert "COMMIT ANTES" in capsys.readouterr().out


def test_calibrate_apply_says_commit_before_make_eval(monkeypatch, capsys):
    ci = {"k": 1, "n": 1, "lo": 50.0, "hi": 100.0}
    row = {"threshold": 7.9, "pos_answered": 0.9, "pos_ci": ci, "neg_refused": 0.9, "neg_ci": ci,
           "meets_floor": True, "balanced_acc": 0.9}
    monkeypatch.setattr(run_evals, "dirty_gate_files", lambda root=None: [])
    monkeypatch.setattr(run_evals, "calibrate_gate", lambda: {
        "criterion": "c", "positives": 1, "negatives": 1, "excluded_negatives": [], "table": [row], "best": row,
        "at_current": row, "by_language": {}, "current": 7.9, "current_source": "MIN_SCORE"})
    monkeypatch.setattr(run_evals, "apply_min_score", lambda cal: 0)
    assert run_evals.main(["--calibrate-gate", "--apply"]) == 0
    assert "AGORA: commit da calibração ANTES do make eval" in capsys.readouterr().out


def _fake_run(seen):
    def run(*a, **k):
        seen["ran"] = True
        return {"path": "x", "failures": [], "status": "complete", "passed": True, "rows": []}
    return run


def test_warm_eval_with_out_and_explicit_override_still_measure(monkeypatch, tmp_path):
    monkeypatch.setattr(run_evals, "dirty_gate_files", lambda root=None: DIRTY)
    monkeypatch.setattr(run_evals, "to_markdown", lambda report: "")
    seen: dict = {}
    monkeypatch.setattr(run_evals, "run", _fake_run(seen))
    assert run_evals.main(["--out", str(tmp_path / "warm.json")]) == 0 and seen  # eval aquecido: não é o gate
    seen.clear()
    monkeypatch.setenv(run_evals.ALLOW_DIRTY_GATE, "1")
    assert run_evals.main([]) == 0 and seen
