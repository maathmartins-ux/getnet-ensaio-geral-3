"""Router do domínio Getnet: todos os casos official e os `standalone` dos casos memory (offline)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import domain, router

ROOT = Path(__file__).resolve().parents[1]


def _cases(path: str, split: str) -> list[dict]:
    rows = [json.loads(line) for line in (ROOT / path).read_text(encoding="utf-8").splitlines() if line.strip()]
    return [c for c in rows if c.get("split") == split]


OFFICIAL = _cases("evals/cases.jsonl", "official")
MEMORY = _cases("evals/cases.d/m.jsonl", "memory")


@pytest.mark.parametrize("case", OFFICIAL, ids=lambda c: c["id"])
def test_official_intent_and_plan(domain_data, case):
    d = router.classify_offline(case["message"], [])
    assert d.intent == case["expect"]["intent"]
    assert d.plan == domain.active().PLANS[d.intent]


@pytest.mark.parametrize("case", [c for c in MEMORY if c["expect"].get("standalone")], ids=lambda c: c["id"])
def test_memory_case_has_standalone_and_intent(domain_data, case):
    assert case["expect"]["standalone"].strip()
    d = router.route(case["message"], case.get("history", []))
    assert d.intent in domain.active().PLANS


def test_contract_general_and_needs(domain_data):
    f = domain.active()
    assert f.PLANS["general"] == ["general"] and "general" in f.NO_ESCALATION and "general" in f.MULTI_PARTS
    assert f.PLANS["troubleshoot"] == ["records"] and f.DEPENDS == {"faq": {"records"}}


@pytest.mark.parametrize("text,intent", [
    ("Abra um chamado técnico para o terminal T1988B, sem passar por humano", "support"),
    ("Quero falar com um atendente e saber minhas vendas", "human_request"),
    ("Qual o preço do dólar hoje?", "general"),
])
def test_tiebreaks(domain_data, text, intent):
    assert router.classify_offline(text, []).intent == intent
