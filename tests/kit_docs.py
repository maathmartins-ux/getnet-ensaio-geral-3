"""Testes que leem docs/kit/ (playbook, prompts, SETUP_AMBIENTE.sh): no repositório da tentativa o kit fica no
kit-fonte, fora do main (o scaffold tira docs/kit do índice). Sem esta marca, a CI da tentativa ficava vermelha
(ensaio geral final, rodada 15: 8 failed no job offline-tests). Use `@needs_kit_docs` só no teste que lê docs/kit."""
from pathlib import Path

import pytest

KIT_DOCS = Path(__file__).resolve().parents[1] / "docs" / "kit"

needs_kit_docs = pytest.mark.skipif(not (KIT_DOCS / "PLAYBOOK.md").exists(),
                                    reason="docs/kit fora do repositório da tentativa (fica no kit-fonte)")
