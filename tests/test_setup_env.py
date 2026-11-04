"""A10 (ensaio 14, lição 4): o script de configuração do ambiente da nuvem leva o lock INTEIRO, com uv, sem ler nada
do repositório (no repositório da tentativa os locks só existem no ramo kit-fonte), e o PLAYBOOK aponta para ele."""
import re
import subprocess
import sys
from pathlib import Path

from kit_docs import needs_kit_docs

from scripts import fetch_models, setup_env

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs" / "kit" / "SETUP_AMBIENTE.sh"


def _lock_pins(name):
    out = set()
    for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(re.sub(r"\s*;\s*", " ; ", line))
    return out


def _script_pins():
    text = SCRIPT.read_text(encoding="utf-8")
    block = text.split("<<'KIT_LOCK'\n", 1)[1].split("\nKIT_LOCK\n", 1)[0]
    return set(block.splitlines())


@needs_kit_docs
def test_setup_script_is_up_to_date_with_the_locks():
    assert SCRIPT.read_text(encoding="utf-8") == setup_env.render(), "rode: python scripts/setup_env.py"


@needs_kit_docs
def test_setup_script_carries_every_pin_of_both_locks_and_nothing_else():
    want = _lock_pins("requirements-dev.lock") | _lock_pins("requirements-hybrid.lock")
    got = _script_pins()
    assert got == want
    for pkg in ("fastapi", "pytest", "pytest-xdist", "ruff", "fastembed", "onnxruntime", "numpy", "tokenizers"):
        assert any(p.startswith(f"{pkg}==") for p in got), pkg  # o que faltou no ensaio 14


@needs_kit_docs
def test_setup_script_reads_nothing_from_the_repository_and_uses_uv():
    text = SCRIPT.read_text(encoding="utf-8")
    body = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    assert "-r requirements" not in body and "scripts/" not in body.split("KIT_MODELS")[0]
    assert '"$UV" pip install --system -q -r /tmp/kit-requirements.txt' in body
    assert "pip install -r" not in body  # nunca o pip para o lock (~10 min)
    assert f'TextEmbedding("{fetch_models.DEFAULT_EMBED}")' in body
    assert f'TextCrossEncoder("{fetch_models.DEFAULT_CROSS}")' in body


@needs_kit_docs
def test_setup_script_is_valid_bash():
    assert subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True).returncode == 0


def test_check_flag_reports_a_stale_file(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_env, "OUT", tmp_path / "s.sh")
    assert setup_env.main(["--check"]) == 1
    assert setup_env.main([]) == 0
    assert setup_env.main(["--check"]) == 0


@needs_kit_docs
def test_playbook_a10_points_to_the_generated_script():
    playbook = (ROOT / "docs" / "kit" / "PLAYBOOK.md").read_text(encoding="utf-8")
    a10 = next(line for line in playbook.splitlines() if line.startswith("| A10 |"))
    assert "docs/kit/SETUP_AMBIENTE.sh" in a10 and "scripts/setup_env.py" in a10


def test_conflicting_pins_are_refused(tmp_path):
    (tmp_path / "requirements-dev.lock").write_text("numpy==2.0.0\n", encoding="utf-8")
    (tmp_path / "requirements-hybrid.lock").write_text("numpy==2.1.0\n", encoding="utf-8")
    try:
        setup_env.pins(tmp_path)
    except ValueError as exc:
        assert "numpy" in str(exc)
    else:
        raise AssertionError("pinos em conflito passaram")


if __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-q", __file__]))
