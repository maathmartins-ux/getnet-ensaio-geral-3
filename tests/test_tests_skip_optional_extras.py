"""Nenhum teste importa direto um pacote que só vem com o extra da busca (numpy, fastembed, onnxruntime...).

O job `offline-tests` da CI instala só a lock de dev: um `import numpy` solto num teste quebra a coleta inteira (no
relógio, a CI da entrega ficou vermelha por um teste novo do motor que importava numpy sem pular; o kit passou verde
porque a máquina do kit tinha o extra). Vale `pytest.importorskip("numpy")` ou o import dentro de
`try/except ImportError`.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# pacotes da requirements-hybrid.lock que a requirements-dev.lock não tem (+ torch, que nenhuma lock traz)
OPTIONAL = {"numpy", "torch", "fastembed", "onnxruntime", "tokenizers", "huggingface_hub", "PIL",
            "sentence_transformers", "py_rust_stemmers", "mmh3", "loguru"}
SKIP_ERRORS = {"ImportError", "ModuleNotFoundError", "Exception"}


def _skipped(body: list[ast.stmt], before: int) -> set[str]:
    """Módulos com `pytest.importorskip("x")` nas instruções do mesmo bloco antes da linha `before`."""
    found = set()
    for stmt in body:
        if stmt.lineno >= before:
            break
        for node in ast.walk(stmt):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "importorskip" and node.args and isinstance(node.args[0], ast.Constant)):
                found.add(str(node.args[0].value).split(".")[0])
    return found


def unguarded_imports(source: str) -> list[tuple[int, str]]:
    """(linha, módulo) de cada import de pacote opcional fora de importorskip e de try/except ImportError."""
    tree = ast.parse(source)
    hits = []

    def visit(body: list[ast.stmt], guarded: bool) -> None:
        for stmt in body:
            names = []
            if isinstance(stmt, ast.Import):
                names = [a.name.split(".")[0] for a in stmt.names]
            elif isinstance(stmt, ast.ImportFrom) and stmt.module and not stmt.level:
                names = [stmt.module.split(".")[0]]
            for name in names:
                if name in OPTIONAL and not guarded and name not in _skipped(body, stmt.lineno):
                    hits.append((stmt.lineno, name))
            if isinstance(stmt, ast.Try):
                catches = {getattr(h.type, "id", None) for h in stmt.handlers} | {
                    getattr(e, "id", None) for h in stmt.handlers if isinstance(h.type, ast.Tuple) for e in h.type.elts}
                visit(stmt.body, guarded or bool(catches & SKIP_ERRORS))
                for h in stmt.handlers:
                    visit(h.body, guarded)
                visit(stmt.orelse + stmt.finalbody, guarded)
                continue
            for field in ("body", "orelse", "finalbody"):
                inner = getattr(stmt, field, None)
                if isinstance(inner, list) and inner and isinstance(inner[0], ast.stmt):
                    visit(inner, guarded)

    visit(tree.body, False)
    return hits


def test_no_test_imports_an_optional_extra_without_skipping():
    files = sorted(p for p in (ROOT / "tests").rglob("*.py") if "fixtures" not in p.parts)
    assert len(files) > 50, "nada varrido"
    bad = [f"{p.relative_to(ROOT)}:{n}: import {mod}" for p in files
           for n, mod in unguarded_imports(p.read_text(encoding="utf-8"))]
    assert not bad, ("teste importa pacote do extra da busca sem pular (o job offline da CI não o tem); use "
                     "`mod = pytest.importorskip(\"mod\")`:\n" + "\n".join(bad))


def test_detector_catches_the_import_that_broke_the_offline_job():
    # o teste do motor que quebrou a CI da entrega, antes e depois da correção
    broken = "def test_percentile_is_numpy_linear():\n    import numpy as np\n    assert np\n"
    fixed = ("import pytest\n\n\ndef test_percentile_is_numpy_linear():\n"
             "    np = pytest.importorskip(\"numpy\")\n    assert np\n")
    assert unguarded_imports(broken) == [(2, "numpy")]
    assert unguarded_imports(fixed) == []
    assert unguarded_imports("from fastembed.rerank import X\nimport torch.nn\n") == [(1, "fastembed"), (2, "torch")]
    guarded = ("import pytest\npytest.importorskip('numpy')\nimport numpy\n"
               "try:\n    import torch\nexcept ImportError:\n    torch = None\n")
    assert unguarded_imports(guarded) == []
    assert unguarded_imports("try:\n    import torch\nexcept ValueError:\n    pass\n") == [(2, "torch")]
