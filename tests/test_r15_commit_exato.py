"""Ensaio geral final (rodada 15): o --calibrate-gate --apply e a recusa de árvore suja mandavam `git add -A`, que
commitaria as remoções do pré-voo antes da hora. Agora dizem os arquivos exatos."""
from types import SimpleNamespace

from evals import run_evals


def test_dirty_refusal_names_the_exact_files():
    msg = run_evals.dirty_refusal(["src/app/domain/challenge/__init__.py", "data/a b.jsonl"], "gate offline")
    assert "git add -A" not in msg.replace("nunca `git add -A`", "")
    assert "git add -- src/app/domain/challenge/__init__.py 'data/a b.jsonl' && git commit" in msg


def test_apply_min_score_records_the_file_to_commit(tmp_path, monkeypatch):
    from app import domain

    target = tmp_path / "src" / "app" / "domain" / "challenge" / "__init__.py"
    target.parent.mkdir(parents=True)
    target.write_text("MIN_SCORE = 0.5\n", encoding="utf-8")
    monkeypatch.setattr(domain, "active", lambda: SimpleNamespace(__file__=str(target)))
    monkeypatch.setattr(run_evals, "HERE", tmp_path / "evals")
    cal = {"best": {"threshold": 0.42, "pos_answered": 0.9, "neg_refused": 0.8}, "positives": 10, "negatives": 5}
    assert run_evals.apply_min_score(cal) == 0
    assert cal["applied_to"] == "src/app/domain/challenge/__init__.py"
    assert "MIN_SCORE = 0.42" in target.read_text(encoding="utf-8")


def test_cli_prints_the_exact_add_for_the_calibration():
    import inspect

    src = inspect.getsource(run_evals.main)
    assert "git add -- {shlex.quote(cal.get('applied_to') or DOMAIN_INIT)}" in src
    assert 'git add -A && git commit -m \\"gate' not in src
