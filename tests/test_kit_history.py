"""A entrega leva o histórico do kit sem anotação interna (scripts/kit_history.py): versões, mudanças, ideias.
"""
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# docs/kit/ fica fora da entrega (o scaffold o tira do índice): na entrega e na CI dela estes testes não têm o que ler
# (ensaio 13: sem isto, 2 falhas certas na CI da entrega)
pytestmark = pytest.mark.skipif(not (ROOT / "docs" / "kit" / "CHANGELOG.md").exists(),
                                reason="sem docs/kit/ (entrega): o histórico já foi gerado no scaffold")
spec = importlib.util.spec_from_file_location("kit_history", ROOT / "scripts" / "kit_history.py")
kh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kh)


def test_real_changelog_comes_out_clean_and_keeps_versions():
    src = (ROOT / "docs" / "kit" / "CHANGELOG.md").read_text(encoding="utf-8")
    out = kh.render(src, "vX")
    assert kh.BANNED.findall(out) == []
    for word in ("r\u00e9gua", "nota estimada", "avaliador", "tirou 10", "dono"):
        assert word not in out.lower()
    versions_src = re.findall(r"(?m)^## (v[\d.]+)", src)
    versions_out = re.findall(r"(?m)^## (v[\d.]+)", out)
    assert versions_src and versions_out == versions_src  # nenhuma versão some
    assert "| Ideia | Origem | Onde |" in out  # a procedência das ideias de terceiros fica


def test_block_with_grade_goes_whole_and_metrics_stay():
    src = ("# CHANGELOG\n\n## v1.0 (01/01/2026) — rodada 3: busca nova (7,25)\n\n"
           "- **Busca:** Recall@3 0,85 e p50 7,2 s; custo US$ 6,5.\n"
           "- **Balanço:** nota estimada 8,4 na\n  r\u00e9gua, faixa 7,5–8,8.\n"
           "- **Outro:** o avaliador puniu\n  regra decidindo.\n")
    out = kh.render(src)
    assert "Recall@3 0,85" in out and "7,2 s" in out and "US$ 6,5" in out
    assert "Balanço" not in out and "faixa" not in out and "puniu" not in out and "regra decidindo" not in out
    assert "## v1.0 (01/01/2026) — busca nova" in out and "rodada 3" not in out and "7,25" not in out


def test_scaffold_uses_the_generator_not_a_raw_copy():
    prompt = (ROOT / "docs" / "kit" / "V5_PROMPT_M.md").read_text(encoding="utf-8")
    assert "scripts/kit_history.py" in prompt
    assert "cp docs/kit/CHANGELOG.md" not in prompt and "changelog.d docs/" not in prompt
    # o CLAUDE.md da preparação do kit sai pelo pré-voo (KIT_ONLY), não no scaffold: tirá-lo antes reprova o pré-voo
    # ("kit-fonte não consumido"), visto no ensaio 13
    assert "--cached --ignore-unmatch CLAUDE.md" not in prompt
