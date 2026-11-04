"""Rodada 15 (ensaio 14: o README dizia "sem medida no domínio" e o comparativo de buscadores "não rodado").

O relógio mede o buscador no domínio (`--choose-retriever --fast --keep-default --apply`, offline, ~2 min com o cache
de vetores quente) e grava data/retriever.json, que o README cita. `--keep-default` mantém o padrão do kit como
escolha: medido em 04/11 com a bateria ao vivo rodando junto, o p95 do cross-encoder deu 2,4 s (> 1,5 s) e o
`--apply` puro trocaria o buscador para dense+windows no meio da entrega (portão 94%/95% em vez de 100%/100%).
"""
import argparse
import json
from pathlib import Path

from kit_docs import needs_kit_docs

from app.config import KIT_RETRIEVER
from evals import retrieval_eval as rv
from scripts import fill_readme

ROOT = Path(__file__).resolve().parents[1]


def _res(config, p95, recall5, mrr, gate_ok=True, rerank=False):
    gate = {"min_score": 7.9, "min_cosine": 0.84, "pos_answered": 0.94, "neg_refused": 0.95 if gate_ok else 0.5,
            "meets_floor": gate_ok, "positives": 46, "negatives": 19, "neg_refusal_min": 0.85}
    out = {"cases": 46, "recall@3": recall5 - 0.04, "recall@5": recall5, "mrr": mrr, "hit@3": 0.93, "ndcg@3": 0.88,
           "latency_ms": {"p50": p95 / 3, "p95": p95, "mean": p95 / 2}, "memory_mb": 1500.0, "gate": gate,
           "config": dict(config)}
    if rerank:
        out["rerank_gate"] = {"min_rerank": -4.986, "pos_answered": 1.0, "neg_refused": 1.0, "meets_floor": True,
                              "positives": 46, "negatives": 19, "neg_refusal_min": 0.85, "enough": True}
    return out


DENSE_W = {"retriever": "dense", "embed_model": KIT_RETRIEVER["embed_model"], "windows": True}
# a medida de 04/11 com a máquina carregada: o padrão (cross:base) fora do orçamento de latência
RESULTS = {"bm25": _res({"retriever": "bm25"}, 0.6, 0.877, 0.801),
           "dense+windows": _res(DENSE_W, 86.6, 0.924, 0.909),
           rv.config_name(dict(KIT_RETRIEVER)): _res(KIT_RETRIEVER, 2401.7, 0.924, 0.909, rerank=True)}


def test_loaded_machine_would_swap_the_retriever_without_keep_default():
    assert rv.choose(RESULTS)["name"] == "dense+windows"  # o defeito: a carga troca o buscador


def test_keep_default_records_the_kit_default_with_the_gate_of_this_measurement():
    picked = rv.keep_default(RESULTS)
    assert picked["name"] == rv.config_name(dict(KIT_RETRIEVER))
    assert {k: v for k, v in picked["config"].items() if k != "gate"} == dict(KIT_RETRIEVER)
    assert picked["config"]["gate"]["min_rerank"] == -4.986 and picked["reason"] == rv.KEEP_DEFAULT_REASON


def test_keep_default_refuses_when_the_default_was_not_measured_or_its_gate_fails():
    assert rv.keep_default({k: v for k, v in RESULTS.items() if k != rv.config_name(dict(KIT_RETRIEVER))}) is None
    bad = {**RESULTS, rv.config_name(dict(KIT_RETRIEVER)): _res(KIT_RETRIEVER, 900, 0.9, 0.9, gate_ok=False)}
    assert rv.keep_default(bad) is None


def test_cli_with_reuse_writes_the_choice_and_the_readme_cites_it(tmp_path, monkeypatch, capsys):
    data, results = tmp_path / "data", tmp_path / "results"
    data.mkdir()
    results.mkdir()
    (results / "retrieval_compare.json").write_text(json.dumps({
        "recorded_at": "2026-11-04T16:57:31+00:00", "gold": "retrieval.jsonl",
        "results": RESULTS, "diff_vs_baseline": {}}), encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(data))
    monkeypatch.setattr(rv, "FAST_CONFIGS", tuple(r["config"] for r in RESULTS.values()))
    args = argparse.Namespace(verify=False, latency_budget_ms=None, ram_budget_mb=None, fast=True, windows=False,
                              reuse=True, keep_default=True, apply=True, gold=None, embed_models=None,
                              rerank_models=None, rerank_pools=None)
    assert rv.choose_cli(args, tmp_path / "gold.jsonl", results, "abc1234") == 0
    out = capsys.readouterr().out
    assert "AVISO: no orçamento de agora a escolha seria dense+windows" in out
    rec = json.loads((data / "retriever.json").read_text(encoding="utf-8"))
    assert rec["chosen"] == rv.config_name(dict(KIT_RETRIEVER)) and rec["git_sha"] == "abc1234"
    block = fill_readme.retriever_block(results, data)
    assert "frase gerada de `data/retriever.json`" in block and "sem medida no domínio" not in block
    assert "Não rodado" not in fill_readme.retrieval_block(results, data)


def test_cli_without_keep_default_still_picks_by_budget(tmp_path, monkeypatch):
    data, results = tmp_path / "data", tmp_path / "results"
    data.mkdir()
    results.mkdir()
    (results / "retrieval_compare.json").write_text(json.dumps({
        "recorded_at": "x", "gold": "g", "results": RESULTS, "diff_vs_baseline": {}}), encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(data))
    monkeypatch.setattr(rv, "FAST_CONFIGS", tuple(r["config"] for r in RESULTS.values()))
    args = argparse.Namespace(verify=False, latency_budget_ms=None, ram_budget_mb=None, fast=True, windows=False,
                              reuse=True, apply=True, gold=None, embed_models=None, rerank_models=None,
                              rerank_pools=None)
    assert rv.choose_cli(args, tmp_path / "g.jsonl", results, None) == 0
    assert json.loads((data / "retriever.json").read_text(encoding="utf-8"))["chosen"] == "dense+windows"


CMD = "python -m evals.run_evals --choose-retriever --fast --keep-default --apply"


@needs_kit_docs
def test_clock_plan_measures_the_retriever_after_the_gate_calibration_and_before_make_eval():
    prompt = (ROOT / "docs" / "kit" / "V5_PROMPT_M_MONTADO.md").read_text(encoding="utf-8")
    step4 = prompt.split("\n4. ", 1)[1].split("\n5. ", 1)[0]
    assert CMD in step4
    assert step4.index("--calibrate-gate --apply") < step4.index(CMD) < step4.index("Só então `make eval`")
    playbook = (ROOT / "docs" / "kit" / "PLAYBOOK.md").read_text(encoding="utf-8")
    assert CMD in playbook
    a3 = next(line for line in playbook.splitlines() if line.startswith("| A3 |"))
    assert "--keep-default" in a3
