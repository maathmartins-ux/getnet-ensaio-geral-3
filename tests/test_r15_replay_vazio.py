"""Ensaio geral final (rodada 15): os 4 pedaços do replay passaram em 0–1 s, sem nenhum cassete, em silêncio. O replay
do commit final não pode passar vazio: resultado ao vivo commitado sem o cassete que ele gravou reprova; replay que
não gera o resumo reprova; sem nenhuma gravação ao vivo, passa declarado."""
import json

from scripts import check


def _live(root, split, cassette):
    d = root / "evals" / "results"
    d.mkdir(parents=True, exist_ok=True)
    rec = {"split": split, "status": "complete", "cassette": {"file": cassette, "floors": {"intent_acc": 100}}}
    (d / f"live_{split}.json").write_text(json.dumps(rec), encoding="utf-8")


def test_live_result_without_its_cassette_fails(tmp_path, monkeypatch):
    _live(tmp_path, "official", "evals/cassettes/official.jsonl")
    monkeypatch.setattr(check.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("não roda")))
    name, ok, _, detail = check.replay_gate(tmp_path)
    assert not ok and "live_official.json → evals/cassettes/official.jsonl" in detail and "commite" in detail
    assert not check.replay_gate(tmp_path, shard=(1, 4))[1]
    assert "commite" not in check.replay_gate(tmp_path, shard=(2, 4))[3]  # só o 1º pedaço avisa


def test_nothing_recorded_passes_declared(tmp_path):
    name, ok, _, detail = check.replay_gate(tmp_path)
    assert ok and "nada a fazer" in detail


def test_replay_that_writes_no_summary_fails(tmp_path, monkeypatch):
    (tmp_path / "evals" / "cassettes").mkdir(parents=True)
    (tmp_path / "evals" / "cassettes" / "official.jsonl").write_text("{}", encoding="utf-8")
    _live(tmp_path, "official", "evals/cassettes/official.jsonl")
    stale = tmp_path / "var" / "replay" / "replay.json"
    stale.parent.mkdir(parents=True)
    stale.write_text(json.dumps({"splits": {}, "passed": True}), encoding="utf-8")  # de outra execução

    class Crash:
        stdout, stderr, returncode = "", "Traceback: ImportError x", 1

    monkeypatch.setattr(check.subprocess, "run", lambda *a, **k: Crash())
    name, ok, _, detail = check.replay_gate(tmp_path)
    assert not ok and "não gerou" in detail and "ImportError" in detail


def test_replay_reason_fails(tmp_path, monkeypatch):
    (tmp_path / "evals" / "cassettes").mkdir(parents=True)
    (tmp_path / "evals" / "cassettes" / "x.jsonl").write_text("{}", encoding="utf-8")

    def fake_run(*a, **k):
        (tmp_path / "var" / "replay").mkdir(parents=True, exist_ok=True)
        (tmp_path / "var" / "replay" / "replay.json").write_text(json.dumps(
            {"splits": {}, "passed": False, "reason": "nenhum cassete em evals/cassettes: grave com --live"}))

    monkeypatch.setattr(check.subprocess, "run", fake_run)
    assert not check.replay_gate(tmp_path)[1]
