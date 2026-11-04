"""Ensaio geral final (rodada 15): evals/real_questions.jsonl não entrava na bateria (load_cases lia só cases e
held-out; o `cat >> cases.jsonl` estava só no PROMPTS). Agora o split `real` entra sozinho, a mesma linha já copiada
para cases.jsonl não duplica, e o live_eval.sh lista o split."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from evals import run_evals

ROOT = Path(__file__).resolve().parents[1]
REAL = {"id": "real-01", "split": "real", "user_id": "cliente1981", "message": "Minhas vendas não caem, por quê?",
        "source_url": "https://exemplo.com/x", "seen": "2026-11-04", "expect": {"language": "pt"}}
CASE = {"id": "official-01", "split": "official", "user_id": "u1", "message": "Qual o prazo?",
        "expect": {"intent": "faq", "facts": ["dois dias"]}}


def _write(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def test_real_questions_enter_the_battery(tmp_path, monkeypatch):
    _write(tmp_path / "cases.jsonl", [CASE])
    _write(tmp_path / "real_questions.jsonl", [REAL])
    monkeypatch.setattr(run_evals, "CASES", tmp_path / "cases.jsonl")
    monkeypatch.setattr(run_evals, "REAL", tmp_path / "real_questions.jsonl")
    assert [c["id"] for c in run_evals.load_cases()] == ["official-01", "real-01"]
    assert run_evals.ungated("real")


def test_real_questions_already_copied_to_cases_do_not_duplicate(tmp_path, monkeypatch):
    _write(tmp_path / "cases.jsonl", [CASE, REAL])  # quem seguiu o PROMPTS antigo e fez o cat
    _write(tmp_path / "real_questions.jsonl", [REAL])
    monkeypatch.setattr(run_evals, "CASES", tmp_path / "cases.jsonl")
    monkeypatch.setattr(run_evals, "REAL", tmp_path / "real_questions.jsonl")
    assert [c["id"] for c in run_evals.load_cases()] == ["official-01", "real-01"]


def test_same_id_with_another_text_is_still_an_error(tmp_path, monkeypatch):
    _write(tmp_path / "cases.jsonl", [CASE, {**REAL, "message": "outra pergunta"}])
    _write(tmp_path / "real_questions.jsonl", [REAL])
    monkeypatch.setattr(run_evals, "CASES", tmp_path / "cases.jsonl")
    monkeypatch.setattr(run_evals, "REAL", tmp_path / "real_questions.jsonl")
    with pytest.raises(ValueError, match="duplicados"):
        run_evals.load_cases()


@pytest.mark.skipif(shutil.which("bash") is None, reason="sem bash")
def test_live_eval_dry_run_lists_the_real_split(tmp_path):
    (tmp_path / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "live_eval.sh", tmp_path / "scripts" / "live_eval.sh")
    (tmp_path / "evals").mkdir()
    _write(tmp_path / "evals" / "cases.jsonl", [CASE])
    _write(tmp_path / "evals" / "real_questions.jsonl", [REAL])
    env = {**os.environ, "LIVE_EVAL_PY": sys.executable}
    out = subprocess.run(["bash", str(tmp_path / "scripts" / "live_eval.sh"), "--dry-run"], capture_output=True,
                         text=True, encoding="utf-8", timeout=60, env=env, cwd=tmp_path)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "splits=official|real " in out.stdout
