"""Domínio do desafio: junta flow + tools e guarda o limiar calibrado.

MIN_SCORE sai de `python -m evals.run_evals --calibrate-gate` NO CORPUS DO DESAFIO; troque aqui,
nunca no motor nem no domínio de exemplo (os testes do motor rodam no exemplo).
"""
from __future__ import annotations

from pathlib import Path

from .flow import *  # noqa: F403
from .tools import *  # noqa: F403

# --- portão "sem fonte, sem afirmação" ----------------------------------------------------------------------
# BM25 bruto abaixo disso = sem fonte. O valor do desafio sai de `run_evals --calibrate-gate` e vai para o
# challenge.py (ou COVERAGE_MIN_SCORE no compose). Trocar o padrão do KIT quebrou 14 testes.
# run_evals --calibrate-gate (04/11/2026): responde 80% dos com fonte, recusa 85% dos sem fonte (n=46/20)
MIN_SCORE = 7.396
# Portão pela nota do cross-encoder (só com rerank): None = desligado. O valor do desafio sai de
# `retrieval_eval` (rerank_gate: menor limiar que recusa >= 85% dos sem fonte) e vai para o challenge.
# run_evals --calibrate-rerank-gate (04/11/2026): responde 100% dos com fonte, recusa 100% dos sem fonte (n=46/20)
MIN_RERANK = -4.986

# --- prompts ------------------------------------------------------------------------------------------------
# None = prompts do kit (src/app/prompts). O pré-voo aponta o challenge para src/app/domain/challenge_prompts.
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "challenge_prompts"

