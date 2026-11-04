"""Domínio montado (ordem do dono, 04/11): o mount aplica a fonte do domínio, não traz o que é medido de novo e a
PROCEDENCIA declara a origem; o pré-voo --mounted não recria nem esvazia o domínio."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "docs" / "kit" / "tools" / "dominio.py"
pytestmark = pytest.mark.skipif(not TOOL.exists(), reason="sem docs/kit/ (entrega)")


def _tool():
    spec = importlib.util.spec_from_file_location("dominio", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_blind_sets_and_measurements_never_travel():
    d = _tool()
    for rel in ("evals/heldout_blind.jsonl", "evals/real_questions.jsonl", "evals/cases.d/real.jsonl",
                "evals/results/live_official.json", "evals/cassettes/x.json", "docs/DEMO.md", "docs/TIMESHEET.md",
                "docs/PROCEDENCIA.md", "evals/human_labels.matheus.csv", "reports/verify.md"):
        assert not d._kept(rel), rel
    for rel in ("src/app/domain/challenge/flow.py", "data/knowledge/produtos/pix.jsonl", "evals/cases.d/q.jsonl",
                "evals/essential/report.json", "docs/SPEC.md", "tests/test_domain_router.py"):
        assert d._kept(rel), rel


def test_mount_declares_the_origin_in_procedencia(tmp_path, monkeypatch):
    d = _tool()
    store = tmp_path / "store"
    (store / "files" / "docs").mkdir(parents=True)
    (store / "files" / "docs" / "SPEC.md").write_text("spec", encoding="utf-8")
    (store / "MANIFEST.json").write_text(json.dumps({"source": "https://x/r", "commit": "abc1234def",
                                                     "saved_at": "2026-11-04", "files": ["docs/SPEC.md"]}))
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "PROCEDENCIA.md").write_text("# P\n\n## 1. O kit e a sua história\n", encoding="utf-8")
    monkeypatch.setattr(d, "STORE", store)
    assert d.mount(root) == ["docs/SPEC.md"]
    text = (root / "docs" / "PROCEDENCIA.md").read_text(encoding="utf-8")
    assert "Domínio montado antes do relógio" in text and "abc1234" in text
    assert text.index("Domínio montado") < text.index("## 1. O kit")
    d.mount(root)  # de novo: o bloco é trocado, nunca duplicado
    assert (root / "docs" / "PROCEDENCIA.md").read_text(encoding="utf-8").count(d.BLOCK_BEGIN) == 1



def test_mounted_readme_has_no_template_marker():
    """Ensaio geral da rodada 15: um `{{RODADA_2_E_VIDEO}}` no README montado fez o teste do README (e o pré-voo)
    tratá-lo como o modelo do kit e esperar o exemplo do domínio de exemplo: PRÉ-VOO FALHOU na largada."""
    from pathlib import Path

    readme = Path(__file__).resolve().parents[1] / "docs" / "kit" / "dominio" / "files" / "README.md"
    if not readme.exists():
        import pytest

        pytest.skip("sem docs/kit (fora da entrega)")
    assert "{{" not in readme.read_text(encoding="utf-8")
