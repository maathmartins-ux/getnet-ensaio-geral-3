"""Supervisor do domínio Getnet: replan (sem fonte → humano), dependent (records + faq) e partial (não escala)."""
from __future__ import annotations

from app import domain


def _prompt() -> str:
    return domain.prompt("supervisor.md")


def test_replan_fallback_goes_to_human(domain_data):
    f = domain.active()
    assert f.FALLBACK["faq"] == "escalation" and f.FALLBACK["records"] == "escalation"
    assert "escalation" in f.ALLOWED["faq"] and f.ALLOWED["escalation"] == set()


def test_dependent_faq_waits_for_records_and_needs_is_followed(domain_data):
    f = domain.active()
    assert "faq" in f.ALLOWED["records"] and f.DEPENDS["faq"] == {"records"}
    assert "`needs`" in _prompt()


def test_partial_is_an_answer_not_a_handoff(domain_data):
    p = _prompt()
    assert "partial" in p and "não caso humano" in p


def test_general_never_escalates(domain_data):
    f = domain.active()
    assert "general" in f.NO_ESCALATION and "escalation" not in f.ALLOWED["general"]
