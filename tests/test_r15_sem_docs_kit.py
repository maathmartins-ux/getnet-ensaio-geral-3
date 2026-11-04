"""Guarda: a suíte passa num repositório SEM docs/kit/, como o main da tentativa (o kit fica no kit-fonte). Ensaio
geral final (rodada 15): a CI de sinal cedo da tentativa deu 8 failed no offline-tests, todos lendo docs/kit/ (o
pré-voo e a cópia local tinham docs/kit no disco e não viram). Roda na cópia só os arquivos de teste que citam o kit
ou docs/: um teste novo que lê docs/kit sem `@needs_kit_docs` reprova aqui, no repo do kit, antes da tentativa."""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from kit_docs import KIT_DOCS

ROOT = Path(__file__).resolve().parents[1]
CITES_KIT = re.compile(r"docs/kit|[\"']kit[\"']|[\"']docs[\"']")


def _repo_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\0") if f and not f.startswith("docs/kit/") and (ROOT / f).is_file()]


@pytest.mark.skipif(not KIT_DOCS.exists(), reason="já é um repositório sem docs/kit (a própria suíte é a prova)")
@pytest.mark.skipif(shutil.which("git") is None, reason="sem git")
def test_suite_passes_without_docs_kit(tmp_path):
    copy = tmp_path / "tentativa"
    for f in _repo_files():
        (copy / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, copy / f)
    targets = sorted(f for f in _repo_files() if re.match(r"tests/test_[^/]+\.py$", f)
                     and f != "tests/test_r15_sem_docs_kit.py"
                     and CITES_KIT.search((ROOT / f).read_text(encoding="utf-8", errors="replace")))
    assert targets, "nenhum teste cita docs/: o filtro quebrou"
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rfE", "-p", "no:cacheprovider", "-p", "no:xdist",
                        *targets], cwd=copy, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONPATH": str(copy / "src")}, timeout=600)
    failed = [line for line in r.stdout.splitlines() if line.startswith(("FAILED ", "ERROR "))]
    assert r.returncode == 0, ("teste lê docs/kit/ sem `@needs_kit_docs` (tests/kit_docs.py): no main da tentativa "
                               "docs/kit não existe e a CI fica vermelha:\n" + "\n".join(failed or r.stdout[-2000:]))
