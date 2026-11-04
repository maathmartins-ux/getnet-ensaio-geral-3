"""Rodada 15 (lições 9 e 11 do ensaio 14): a página de rotulagem leva adulteradas por padrão e grava o tempo de
leitura de cada situação.

- `--perturb 3` com a fumaça dos oficiais (10 casos, `--n 10`): antes entravam 0 adulteradas em silêncio (toda
  original já estava na amostra real); agora as reais cedem lugar e a página fica com 7 reais + 3 adulteradas.
- O tempo com cada situação na tela vai na ficha (`marks[id].s`) e no texto de "Copiar minhas respostas" (`s=N`);
  a importação grava a coluna `segundos` e o `--report` dá a mediana e as marcações rápidas por pessoa.
- O PLAYBOOK e os prompts do relógio mandam `--perturb 3`.
"""
import json
import re
from pathlib import Path

from kit_docs import needs_kit_docs

from evals import label, perturb
from scripts import label_page

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "scripts" / "templates" / "rotulagem.html"


def _row(i, message, answer, context):
    return {"id": i, "split": "official", "run": 0, "message": message, "answer": answer, "context": context,
            "evidence": [context[2:]], "sources": [{"id": f"doc-{i}", "title": "Fonte",
                                                     "url": f"https://lojadojoao.com.br/{i}"}],
            "source_ids": [f"doc-{i}"], "tool_calls": [], "user_id": "u-ana", "expected_language": "pt",
            "checks": {"numbers": True, "facts": True}}


# "fumaça": só oficiais, todos com número na evidência (numero_trocado plantável em cada um)
ROWS = [_row(f"official-{k:02d}", f"Quanto custa o plano {k}?",
             f"O plano {k} custa R$ {k}9,90 por mês, cobrados na fatura junto com as outras cobranças.",
             f"- Preços: o plano {k} custa R$ {k}9,90 por mês, cobrados na fatura.") for k in range(1, 7)]


def _results(tmp_path):
    res = tmp_path / "results"
    res.mkdir(exist_ok=True)
    (res / "live_official.json").write_text(json.dumps({"rows": ROWS}), encoding="utf-8")
    perturb.build(res, per_type=10, cases={})
    return res


def _back(res):
    return label.unblind([r["id"] for r in label.load_rows(res)] + [r["id"] for r in perturb.load(res)])


def test_perturb_makes_room_when_the_real_sample_takes_every_original(tmp_path, monkeypatch):
    res = _results(tmp_path)
    monkeypatch.setattr(label, "RESULTS", res)
    assert len({r["original_id"] for r in perturb.load(res)}) == len(ROWS)  # todo caso tem adulterada
    info: dict = {}
    got, reasons = label_page.build(len(ROWS), results=res, splits={"official"}, perturb=2, base=tmp_path,
                                    info=info)
    back = _back(res)
    fake = {r["id"]: r for r in perturb.load(res)}
    planted = [fake[back[i["id"]]] for i in got if back[i["id"]] in fake]
    real = [back[i["id"]] for i in got if back[i["id"]] not in fake]
    assert len(got) == len(ROWS) and len(planted) == 2 and len(real) == len(ROWS) - 2  # mesmo total de itens
    assert info == {"reais_pedidas": len(ROWS), "reais": len(ROWS) - 2, "sem_juiz": len(ROWS) - 2}
    assert not {r["original_id"] for r in planted} & set(real)  # nunca ao lado da própria original
    assert set(real) == {r["id"] for r in label.sample(label.load_rows(res), len(ROWS) - 2)}  # a do --export menor
    assert set(reasons) == set(real)


def test_without_perturb_the_real_sample_is_untouched(tmp_path, monkeypatch):
    res = _results(tmp_path)
    monkeypatch.setattr(label, "RESULTS", res)
    info: dict = {}
    got, _ = label_page.build(len(ROWS), results=res, splits={"official"}, base=tmp_path, info=info)
    assert len(got) == len(ROWS) and info == {"reais_pedidas": len(ROWS), "reais": len(ROWS), "sem_juiz": len(ROWS)}


def test_cli_warns_when_real_answers_gave_way(tmp_path, monkeypatch, capsys):
    res = _results(tmp_path)
    monkeypatch.setattr(label, "RESULTS", res)
    monkeypatch.setattr(label, "HERE", tmp_path)
    monkeypatch.setattr(label, "SALT_FILE", tmp_path / "salt.json", raising=False)
    monkeypatch.setattr(label, "VALIDATION_DIR", tmp_path / "validation")
    monkeypatch.setattr(label_page, "_before", lambda: {})
    out = tmp_path / "p.html"
    assert label_page.main(["--n", str(len(ROWS)), "--splits", "official", "--perturb", "3", "--raters", "Ana,Bia",
                            "--out", str(out)]) == 0
    cap = capsys.readouterr()
    printed = json.loads(cap.out)
    assert printed["items"] == len(ROWS) and printed["adulteradas"]["total"] == 3 and printed["reais"] == len(ROWS) - 3
    assert f"{len(ROWS) - 3} reais em vez de {len(ROWS)}" in cap.err


def test_reading_time_goes_from_the_page_to_the_csv_and_the_report(tmp_path):
    res = tmp_path / "results"
    res.mkdir()
    rows = [{"id": f"c{i}", "split": "official", "run": 0, "message": f"pergunta {i}", "answer": f"resposta {i}",
             "checks": {"numbers": True}} for i in range(4)]
    (res / "live_official.json").write_text(json.dumps({"rows": rows}), encoding="utf-8")
    ok = {"v": "pass", "c1": "sim", "c2": "nao", "c3": "sim"}
    dump = tmp_path / "ana.json"  # ficha da página (ArtifactData): marks[id].s em segundos
    dump.write_text(json.dumps([{"data": {"rater": "ana", "marks": {"c0": {**ok, "s": 41}, "c1": {**ok, "s": 9},
                                                                    "c2": {**ok, "s": 63}, "c3": ok}}}]),
                    encoding="utf-8")
    label.import_page(dump, results=res, base=tmp_path)
    got = {r["id"]: r["segundos"] for r in label.read_labels(label.csv_path("ana", tmp_path))}
    assert got == {"c0": "41", "c1": "9", "c2": "63", "c3": ""}  # sem tempo (página antiga): vazio
    # plano B: o texto de "Copiar minhas respostas" traz s=N
    text = "CONFERENCIA abc bia\n" + "\n".join(f"c{i}=pass c1=sim c2=nao c3=sim s={s}"
                                               for i, s in enumerate((5, 12, 30, 8)))
    assert label.import_text(text, results=res, base=tmp_path) == {"bia": 4}
    got = {r["id"]: r["segundos"] for r in label.read_labels(label.csv_path("bia", tmp_path))}
    assert got == {"c0": "5", "c1": "12", "c2": "30", "c3": "8"}
    rep = label.report(results=res, out=tmp_path / "h.json", base=tmp_path)
    t = rep["tempo_por_rotulador"]
    assert t["ana"] == {"itens_com_tempo": 3, "mediana_s": 41, "total_s": 113, "rapidas": 1,
                        "limite_s": label.MIN_READ_S}
    assert t["bia"] == {"itens_com_tempo": 4, "mediana_s": 10.0, "total_s": 55, "rapidas": 3,
                        "limite_s": label.MIN_READ_S}
    assert json.loads((tmp_path / "h.json").read_text(encoding="utf-8"))["tempo_por_rotulador"] == t


def test_report_without_any_time_says_none(tmp_path):
    res = tmp_path / "results"
    res.mkdir()
    (res / "live_official.json").write_text(json.dumps({"rows": [
        {"id": "c0", "split": "official", "run": 0, "message": "p", "answer": "r", "checks": {}}]}), encoding="utf-8")
    label.import_text("CONFERENCIA abc ana\nc0=pass c1=sim c2=nao c3=sim\n", results=res, base=tmp_path)
    assert label.report(results=res, out=tmp_path / "h.json", base=tmp_path)["tempo_por_rotulador"] is None


def test_page_records_time_per_situation_and_exports_it():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "function clockStart(id)" in html and "function clockStop()" in html
    assert '"visibilitychange"' in html  # aba escondida não conta tempo
    assert "s: Math.round(secs[it.id] || 0)" in html  # a ficha grava o tempo da situação
    assert "` s=${m.s ?? \"\"}`" in html  # e o texto de "Copiar minhas respostas" também


@needs_kit_docs
def test_playbook_and_clock_prompts_ask_for_planted_answers():
    for doc in ("PLAYBOOK.md", "V5_PROMPT_M_MONTADO.md", "V5_PROMPT_M.md"):
        text = (ROOT / "docs" / "kit" / doc).read_text(encoding="utf-8")
        cmds = re.findall(r"label_page\.py --n \d+ --splits [^`\n]*", text)
        assert cmds, doc
        assert all("--perturb 3" in c for c in cmds), (doc, cmds)
