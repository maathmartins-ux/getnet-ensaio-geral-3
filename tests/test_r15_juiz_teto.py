"""Rodada 15: o --max-usd do juiz não passa do teto com chamadas em paralelo, e o --resume do mesmo juiz não paga de
novo canários e calibração. Medido em 04/11: --max-usd 0,52 gastou 0,645 (74 chamadas, 8 em voo); --resume com 0,25
gastou 0,35 (os canários e a calibração rodaram de novo)."""
import json
import threading
import time
from pathlib import Path

from app.config import PRICES_PER_MTOK
from app.llm import LLMReply
from evals import judge

KIT_CAL = Path(__file__).parent / "fixtures" / "kit_data" / "judge_calibration.jsonl"
MODEL = "claude-opus-5-5"


def _tokens_for(usd: float) -> tuple[int, int]:
    price_in, price_out = PRICES_PER_MTOK[MODEL]
    return int(usd * 1_000_000 / price_in), 0  # só entrada: o custo sai exato pela tabela


class SlowPricey:
    """Juiz falso que aprova tudo, custa ~US$ 0,02 por chamada e demora: as 8 chamadas paralelas ficam em voo juntas."""

    model = MODEL

    def __init__(self):
        self.calls, self.in_flight, self.max_in_flight = 0, 0, 0
        self.lock = threading.Lock()

    def complete(self, system, messages, max_tokens=1024, schema=None):
        with self.lock:
            self.calls += 1
            self.in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self.in_flight)
        time.sleep(0.05)
        with self.lock:
            self.in_flight -= 1
        p = messages[0]["content"]
        answer = p.split("Resposta:")[-1]
        v = {"grounded": not any(s in answer for s in ("1 dia útil", "90 dias", "24 horas", "Ulan Bator")),
             "helpful": True, "score": 4, "reason": "ok",
             "language_ok": not ("What are" in p and "Nosso atendimento" in answer),
             "leaks_other_customer": "Bruno Lima" in answer}
        tin, tout = _tokens_for(0.02)
        return LLMReply(json.dumps(v), self.model, tin, tout)


def live_file(tmp_path, n=40):
    path = tmp_path / "live_official.json"
    path.write_text(json.dumps({"rows": [
        {"id": f"c{i}", "split": "official", "message": "Prazo?", "answer": f"3 a 5 dias úteis ({i}).",
         "source_ids": [], "user_id": "u1"} for i in range(n)]}), encoding="utf-8")
    return path


def test_parallel_calls_never_pass_the_ceiling(tmp_path, monkeypatch):
    monkeypatch.setenv("JUDGE_WORKERS", "8")
    llm = SlowPricey()
    rep = judge.run(llm, [live_file(tmp_path)], calibration=KIT_CAL, max_usd=0.52)
    assert rep["status"] == "aborted_max_usd"
    assert rep["spent_usd"] <= 0.52 + 1e-9, rep["spent_usd"]  # antes: 8 chamadas em voo passavam juntas
    assert llm.max_in_flight > 1  # o teste mede de fato com chamadas em paralelo


def test_resume_of_the_same_judge_reuses_canaries_and_calibration(tmp_path, monkeypatch):
    monkeypatch.setenv("JUDGE_WORKERS", "8")
    live = live_file(tmp_path, n=12)
    first = judge.run(SlowPricey(), [live], calibration=KIT_CAL, max_usd=0.30)
    assert first["status"] == "aborted_max_usd" and first["canaries"]["ran"] == 4
    left = 12 - sum(v["source"] == live.name for v in first["verdicts"])
    assert left > 0
    llm = SlowPricey()
    second = judge.run(llm, [live], calibration=KIT_CAL, max_usd=1.0, previous=first, reuse_trust=True)
    assert second["status"] == "ran" and second["trust_reused"] is True
    assert llm.calls == left  # só os vereditos que faltavam: canários e calibração não rodam de novo
    assert second["judge_unreliable"] is False and second["canaries"]["caught"] == 4


def test_resume_with_another_prompt_runs_canaries_again(tmp_path, monkeypatch):
    monkeypatch.setenv("JUDGE_WORKERS", "8")
    live = live_file(tmp_path, n=6)
    first = judge.run(SlowPricey(), [live], calibration=KIT_CAL, max_usd=0.25)
    first["prompt_sha"] = "outro-prompt"
    second = judge.run(SlowPricey(), [live], calibration=KIT_CAL, max_usd=2.0, previous=first, reuse_trust=True)
    assert second["trust_reused"] is False and second["canaries"]["ran"] == 4


def test_cli_resume_passes_reuse_trust():
    src = (Path(judge.__file__)).read_text(encoding="utf-8")
    assert "report = run(get_judge_llm(), inputs, max_usd=args.max_usd, previous=previous, reuse_trust=True)" in src


class RefusesOneCalibration(SlowPricey):
    """Recusa o exemplo de calibração cal-02 (como o q-cal-44 do ensaio geral final); o resto, igual."""

    def complete(self, system, messages, max_tokens=1024, schema=None):
        from app.llm import LLMError

        if "Entregamos em 24 horas para todo o Brasil" in messages[0]["content"] and "Qual o prazo" in \
                messages[0]["content"]:
            with self.lock:
                self.calls += 1
            raise LLMError("refusal", kind="refusal")
        return super().complete(system, messages, max_tokens, schema)


def test_resume_reuses_trust_even_with_a_refused_calibration_item(tmp_path, monkeypatch):
    """Ensaio geral final (rodada 15): 1 item de calibração recusado (45 de 46) desligava o reaproveitamento, e cada
    juiz seguinte pagava canários e calibração de novo."""
    monkeypatch.setenv("JUDGE_WORKERS", "8")
    live = live_file(tmp_path, n=3)
    first = judge.run(RefusesOneCalibration(), [live], calibration=KIT_CAL, max_usd=5.0)
    assert [r["id"] for r in first["calibration_refused"]] == ["cal-02"]
    other = tmp_path / "live_memory.json"  # outro split: as respostas dele ainda não foram julgadas
    (tmp_path / "b").mkdir()
    live_file(tmp_path / "b", n=2)
    (tmp_path / "b" / "live_official.json").rename(other)
    llm = SlowPricey()
    second = judge.run(llm, [other], calibration=KIT_CAL, max_usd=5.0, previous=first, reuse_trust=True)
    assert second["trust_reused"] is True and llm.calls == 2  # só as 2 respostas novas
    assert [r["id"] for r in second["calibration_refused"]] == ["cal-02"]  # a recusa segue declarada
