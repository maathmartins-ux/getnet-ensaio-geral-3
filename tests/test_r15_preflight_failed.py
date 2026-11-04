"""Ensaio geral final (04/11, T+6): o pré-voo reprovou com "1 failed, 2065 passed" sem dizer QUAL teste; a sessão do
relógio rodou a suíte de novo. Agora ele imprime as linhas FAILED do resumo; e o teste de contaminação do k-NN diz o
remédio (tirar o EXEMPLO, com arquivo:linha; nunca o caso cego)."""
import json
import subprocess
import sys

from test_router_contamination import contaminated_examples, example_locations

from scripts import preflight


def test_preflight_pytest_asks_for_the_failed_summary():
    assert "-rfE" in preflight.PYTEST


def test_failed_tests_reads_the_real_pytest_summary(tmp_path):
    (tmp_path / "test_x.py").write_text("def test_ok():\n    pass\n\ndef test_quebra():\n    assert 1 == 2\n",
                                        encoding="utf-8")
    out = subprocess.run([sys.executable, "-m", "pytest", *preflight.PYTEST[3:], "-p", "no:xdist", str(tmp_path)],
                         cwd=tmp_path, capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 1
    lines = preflight.failed_tests(out.stdout)
    assert len(lines) == 1 and lines[0].startswith("FAILED ") and "test_quebra" in lines[0]
    assert preflight.failed_tests("1 passed in 0.1s") == []


def test_failed_tests_caps_the_list():
    lines = preflight.failed_tests("\n".join(f"FAILED t.py::t{i}" for i in range(25)), limit=20)
    assert len(lines) == 21 and lines[-1] == "... e mais 5"


def test_example_locations_point_to_the_training_line(tmp_path):
    base = tmp_path / "intent_examples.jsonl"
    base.write_text(json.dumps({"text": "quanto custa o plano", "intent": "faq"}) + "\n", encoding="utf-8")
    (tmp_path / "intent_examples.d").mkdir()
    extra = tmp_path / "intent_examples.d" / "r.jsonl"
    rows = [{"text": "oi", "intent": "chat"}, {"text": "Is there a monthly fee for the Get Smart?", "intent": "faq"}]
    extra.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    blind = [{"id": "heldout-H1-03", "message": "Is there a monthly fee for the Get Smart?"}]
    hits = contaminated_examples([r["text"] for r in rows], blind)
    assert hits == [("Is there a monthly fee for the Get Smart?", "heldout-H1-03")]
    assert example_locations(base, {ex for ex, _ in hits}) == [f"{extra}:2"]


def test_preflight_suite_runs_in_parallel_when_xdist_exists(monkeypatch):
    monkeypatch.setattr(preflight.os, "cpu_count", lambda: 16)
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda name: object() if name == "xdist" else None)
    assert preflight.pytest_cmd()[-2:] == ["-n", "4"] and "-rfE" in preflight.pytest_cmd()
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda name: None)
    assert preflight.pytest_cmd() == preflight.PYTEST  # sem xdist: em série, como antes
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(preflight.os, "cpu_count", lambda: 1)
    assert "-n" not in preflight.pytest_cmd()
