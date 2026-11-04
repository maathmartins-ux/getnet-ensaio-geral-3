"""Rodada 15 (ensaio 14: juiz × humano "validado 0"): a página de rotulagem sai de respostas JULGADAS.

Ensaio 14: a página saiu da fumaça dos oficiais, que o juiz ainda não tinha julgado; as 10 respostas ficaram sem
veredito sobre o mesmo texto e o --report não comparou juiz e pessoas. Agora `--require-judged` recusa (sai com 2)
página com resposta real sem veredito, antes de gravar sal ou conjunto congelado, e o plano do relógio julga a fumaça
(official + memory, ~26 casos) para a página ter ≥ 20 reais julgadas + 3 adulteradas.
"""
import json
import re
from pathlib import Path

import pytest
from kit_docs import needs_kit_docs

from evals import label
from evals.judge import text_sha
from scripts import label_page

ROOT = Path(__file__).resolve().parents[1]


def _rows(n, split):
    return [{"id": f"{split}-{k:02d}", "split": split, "run": 0, "message": f"pergunta {k}",
             "answer": f"resposta {split} {k}", "context": "- x", "checks": {"numbers": True}} for k in range(n)]


def _results(tmp_path, judged: set[str]):
    res = tmp_path / "results"
    res.mkdir()
    rows = {"official": _rows(10, "official"), "memory": _rows(12, "memory")}
    for split, lst in rows.items():
        (res / f"live_{split}.json").write_text(json.dumps({"split": split, "git_sha": "abc", "rows": lst}),
                                                encoding="utf-8")
    verdicts = [{"source": f"live_{r['split']}.json", "id": r["id"], "run": 0, "grounded": True, "helpful": True,
                 "answer_sha": text_sha(r["answer"])} for lst in rows.values() for r in lst if r["id"] in judged]
    (res / "judge.json").write_text(json.dumps({"status": "ran", "model": "m", "prompt_sha": "p",
                                                "verdicts": verdicts}), encoding="utf-8")
    return res, [r for lst in rows.values() for r in lst]


def test_all_judged_page_passes_and_reports_zero_unjudged(tmp_path, monkeypatch):
    res, rows = _results(tmp_path, judged={r for r in (f"official-{k:02d}" for k in range(10))}
                         | {f"memory-{k:02d}" for k in range(12)})
    monkeypatch.setattr(label, "RESULTS", res)
    monkeypatch.setattr(label, "VALIDATION_DIR", tmp_path / "validation")
    info: dict = {}
    got, _ = label_page.build(20, results=res, splits={"official", "memory"}, base=tmp_path, info=info,
                              require_judged=True)
    assert len(got) == 20 and info["sem_juiz"] == 0
    frozen = json.loads(next((tmp_path / "validation").glob("*.json")).read_text(encoding="utf-8"))
    assert all(i["veredito_do_juiz"] is not None for i in frozen["itens"])  # juiz × humano sobre o mesmo texto


def test_unjudged_answer_is_refused_before_anything_is_written(tmp_path, monkeypatch):
    res, _ = _results(tmp_path, judged={f"memory-{k:02d}" for k in range(12)})  # a fumaça dos oficiais sem juiz
    monkeypatch.setattr(label, "RESULTS", res)
    monkeypatch.setattr(label, "VALIDATION_DIR", tmp_path / "validation")
    monkeypatch.setattr(label, "SALT_FILE", tmp_path / "salt.json")
    with pytest.raises(label_page.NotJudged, match="sem veredito do juiz"):
        label_page.build(20, results=res, splits={"official", "memory"}, base=tmp_path, perturb=3,
                         require_judged=True)
    assert not (tmp_path / "validation").exists() and not (tmp_path / "salt.json").exists()
    info: dict = {}  # sem a trava: a página sai e diz quantas ficaram sem juiz
    label_page.build(20, results=res, splits={"official", "memory"}, base=tmp_path, info=info)
    assert info["sem_juiz"] == 10


def test_verdict_of_another_text_does_not_count(tmp_path, monkeypatch):
    res, rows = _results(tmp_path, judged={r["id"] for r in _rows(10, "official")} | {f"memory-{k:02d}"
                                                                                     for k in range(12)})
    data = json.loads((res / "live_official.json").read_text(encoding="utf-8"))
    data["rows"][0]["answer"] = "resposta nova de outra bateria"  # o juiz julgou o texto de antes
    (res / "live_official.json").write_text(json.dumps(data), encoding="utf-8")
    assert label_page.unjudged(label.load_rows(res), res) == ["official-00"]


def test_cli_exits_2_on_unjudged(tmp_path, monkeypatch, capsys):
    res, _ = _results(tmp_path, judged=set())
    monkeypatch.setattr(label, "RESULTS", res)
    monkeypatch.setattr(label, "VALIDATION_DIR", tmp_path / "validation")
    assert label_page.main(["--n", "20", "--splits", "official,memory", "--require-judged", "--raters", "Ana,Bia",
                            "--out", str(tmp_path / "p.html")]) == 2
    assert "sem veredito do juiz" in capsys.readouterr().err and not (tmp_path / "p.html").exists()


@needs_kit_docs
def test_clock_plan_judges_the_smoke_and_asks_for_20_judged_answers():
    for doc in ("PLAYBOOK.md", "V5_PROMPT_M_MONTADO.md", "V5_PROMPT_M.md"):
        text = (ROOT / "docs" / "kit" / doc).read_text(encoding="utf-8")
        cmds = re.findall(r"label_page\.py --n \d+ --splits [^`\n]*", text)
        assert cmds and all("--n 20" in c and "official,memory" in c and "--require-judged" in c and "--perturb 3" in c
                            for c in cmds), (doc, cmds)
    for doc in ("PLAYBOOK.md", "V5_PROMPT_M_MONTADO.md"):
        text = (ROOT / "docs" / "kit" / doc).read_text(encoding="utf-8")
        assert "--live --splits official,memory --repeat 1" in text, doc
        assert "python -m evals.judge evals/results/live_official.json evals/results/live_memory.json" in text, doc
