"""Intenção do guardrail OFFLINE informa, não reprova: offline ele é só a regex do motor; o gate dele é o red team ao
vivo (ensaio 13: 53% de intenção offline no guardrail derrubava o gate e empurrava regra sob medida no flow.py)."""
from evals.run_evals import ungated


def test_guardrail_offline_intent_is_informative_and_official_stays_gated():
    assert ungated("guardrail")
    assert not ungated("official") and not ungated("memory") and not ungated("replan")
