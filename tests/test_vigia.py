"""Vigia da Maestra A (docs/kit/tools/vigia.sh): pulso com o T+ certo e alertas de teto, sem LLM (ensaio 14)."""
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VIGIA = ROOT / "docs" / "kit" / "tools" / "vigia.sh"
pytestmark = pytest.mark.skipif(not VIGIA.exists(), reason="docs/kit fica fora da entrega")


def _git(cwd, *args, env=None):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, check=True,
                   capture_output=True, env=env)


def _repo(tmp_path, minutes_ago):
    bare, work = tmp_path / "remote.git", tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    (work / "README.md").write_text("x\n")
    _git(work, "add", "-A")
    stamp = f"@{int(__import__('time').time()) - minutes_ago * 60} +0000"
    env = {**os.environ, "GIT_COMMITTER_DATE": stamp, "GIT_AUTHOR_DATE": stamp}
    _git(work, "commit", "-qm", "chore: scaffold from kit", env=env)
    _git(work, "remote", "add", "origin", str(bare))
    _git(work, "push", "-q", "origin", "main")
    return work


def _once(work):
    out = subprocess.run([str(VIGIA), str(work)], capture_output=True, text=True, timeout=60,
                         env={**os.environ, "VIGIA_ONCE": "1"})
    assert out.returncode == 0, out.stderr
    return out.stdout


def test_pulse_reports_minutes_since_the_scaffold_commit(tmp_path):
    text = _once(_repo(tmp_path, minutes_ago=12))
    assert "PULSO T+12 min" in text and "ALERTA T+50" not in text


def test_ceiling_alerts_fire_after_t50_and_t55(tmp_path):
    text = _once(_repo(tmp_path, minutes_ago=56))
    assert "ALERTA T+50" in text and "ALERTA T+55" in text
