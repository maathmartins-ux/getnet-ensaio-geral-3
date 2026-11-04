"""Re-pontua, SEM LLM, respostas ao vivo gravadas com a regra do parcial no motor (app.coverage, b/parcial-motor).

  PYTHONPATH=src python docs/kit/ensaio14/rescore_parcial.py --before before.json \\
      --run r14=live_official.json,judge.json --run faq=faq_official.json,faq_judge.json [--out relatorio.md]

`before.json` = {id do caso: [turnos anteriores do cliente]} (run_evals.load_cases do domínio que gerou as respostas).
A linha gravada não guarda o item do MISSING (a linha sai do texto); guarda o texto final, com a frase de ausência do
redator ou a do motor ("The sources don't cover: x."). Então os itens do que falta são as frases de ausência
(claims.states_absence) da resposta, e as perguntas são a mensagem e os turnos anteriores do caso (no motor ao vivo
entram a versão autônoma e a parte do agente; aqui, os turnos, que pedem mais e deixam a regra mais conservadora).
Linha parcial vira completa só se ela tem frase de ausência e NENHUMA é de item pedido. Resolvida segue a regra de
sempre (run_evals.resolved_summary: regex de fato + `grounded` do juiz sobre o texto gravado).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

from app.claims import states_absence
from app.coverage import judge_missing
from evals.run_evals import judge_verdicts, partial_answer, resolved_summary

_SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def absence_items(answer: str) -> list[str]:
    return [s.strip() for s in _SENT.split(answer or "") if s.strip() and states_absence(s)]


def rescore(rows: list[dict], before: dict[str, list[str]]) -> tuple[list[dict], list[dict]]:
    """(linhas com o status re-decidido, [decisão de cada linha parcial])."""
    out, log = [], []
    for r in rows:
        r = copy.deepcopy(r)
        if partial_answer(r):
            items = absence_items(r.get("answer", ""))
            questions = [r.get("message") or "", *before.get(r["id"], [])]
            asked, detail = judge_missing(items, questions) if items else (True, [])
            log.append({"id": r["id"], "run": r.get("run", 0), "pergunta": r.get("message"), "vira_ok": not asked,
                        "sem_frase_de_ausencia": not items, "itens": detail})
            if not asked:
                for st in r.get("steps") or []:
                    if (st or {}).get("status") == "partial":
                        st["status"] = "ok"
        out.append(r)
    return out, log


def table(name: str, before_sum: dict, after_sum: dict) -> list[str]:
    lines = [f"### {name}", "", "| split | completas | parciais | pass^k | completas + parciais |",
             "|---|---:|---:|---:|---:|"]
    for split in sorted(before_sum["by_split"]):
        a, b = before_sum["by_split"][split], after_sum["by_split"][split]
        lines.append(f"| {split} | {a['k']}/{a['n']} → **{b['k']}/{b['n']}** | {a['partial']['k']} → "
                     f"**{b['partial']['k']}** | {a['pass_hat_k']} → **{b['pass_hat_k']}** | "
                     f"{a['with_partial']['k']} → {b['with_partial']['k']} |")
    lines += ["", "| caso | completas antes → depois | parciais antes → depois |", "|---|---:|---:|"]
    for split in sorted(before_sum["by_split"]):
        ca, cb = before_sum["by_split"][split]["cases"], after_sum["by_split"][split]["cases"]
        for i in sorted(ca):
            if ca[i] != cb[i] or ca[i]["partial"]:
                lines.append(f"| {i} | {ca[i]['resolved']}/{ca[i]['runs']} → {cb[i]['resolved']}/{cb[i]['runs']} | "
                             f"{ca[i]['partial']} → {cb[i]['partial']} |")
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--run", action="append", required=True, metavar="NOME=LIVE.json,JUDGE.json")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    before = json.loads(args.before.read_text(encoding="utf-8"))
    md = ["# Parcial no motor: re-pontuação sem LLM das respostas gravadas", ""]
    report = {}
    for spec in args.run:
        name, _, files = spec.partition("=")
        live_path, judge_path = (Path(p) for p in files.split(","))
        live = json.loads(live_path.read_text(encoding="utf-8"))
        judge = json.loads(judge_path.read_text(encoding="utf-8"))
        rows = live["rows"]
        # o judge.json guarda a fonte como live_<split>.json; o arquivo copiado pode ter outro nome
        source = f"live_{live['split']}.json"
        verdicts = judge_verdicts(judge, source, rows)
        new_rows, log = rescore(rows, before)
        a, b = resolved_summary(rows, verdicts), resolved_summary(new_rows, verdicts)
        report[name] = {"antes": a, "depois": b, "decisoes": log}
        md += table(f"{name} ({live_path.name}, juiz: {judge_path.name}, {live.get('git_sha')})", a, b) + [""]
        md += ["Cada frase de ausência das respostas parciais, com a decisão:", "",
               "| caso | rodada | decisão | frase de ausência (o que falta) | termos em comum com a pergunta |",
               "|---|---:|---|---|---|"]
        for d in log:
            verdict = "**vira completa**" if d["vira_ok"] else ("parcial (sem frase)" if d["sem_frase_de_ausencia"]
                                                                else "parcial")
            for it in d["itens"] or [{"item": "—", "pedido": True, "em_comum": []}]:
                mark = "pedido" if it["pedido"] else "vizinho"
                lines_item = it["item"].replace("|", "/")
                md.append(f"| {d['id']} | {d['run']} | {verdict} | ({mark}) {lines_item} | "
                          f"{', '.join(it['em_comum']) or '—'} |")
        md.append("")
    text = "\n".join(md)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
        args.out.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
