"""Cabeçalho por trecho gerado por modelo pequeno ("do que este trecho trata"), para o índice (contextual retrieval).

  python docs/kit/ensaio14/ctx_headers.py --data data --out var/ctx_headers.json --max-usd 0.10
  python docs/kit/ensaio14/ctx_headers.py --data data --apply var/ctx_headers.json --dest /tmp/data_ctx

Por quê (ensaio 14, official-04): o trecho certo (`sup-pix-09`, critérios para habilitar o Pix: conta Santander e
chave Pix) abre com outra pergunta ("O botão Pix não está disponível…") e o contexto do ingest é o mesmo em todos os
trechos da página ("Arquivos Pix - Getnet › Pix"); com ele ou sem ele, o trecho fica em 7º–10º na pergunta oficial
(MEDIDA_BUSCA_PIX.md). Uma chamada por PÁGINA (a página inteira e os trechos numerados) pede uma frase por trecho com o
assunto que ele responde, só com o que está no trecho. `--apply` grava cópias dos .jsonl com `context` =
"<título> › <frase>" num diretório à parte: o índice usa o `context` com RAG_CONTEXT=on (rag.Doc.head). Nada muda no
corpus do repositório. Custo medido e gravado; para no teto (--max-usd).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

MODEL = "claude-haiku-5-5"
GROUP = 10  # trechos por chamada: página grande inteira de uma vez voltou com a contagem errada
PAGE_CHARS = 12000
PRICE_IN, PRICE_OUT = 0.10 / 1e6, 0.50 / 1e6  # US$ por token do modelo pequeno (prompts < 100 mil tokens)
PROMPT = """Abaixo está uma página de ajuda e os trechos dela, numerados. Para CADA trecho, escreva UMA frase curta
(até 20 palavras), em português, dizendo que pergunta de cliente o trecho responde e o que ele traz (por exemplo:
"requisitos para habilitar o Pix: conta Santander e chave Pix ativa"). Use só o que está no trecho; não invente.
Responda só com um JSON: uma lista de strings, uma por trecho, na mesma ordem.

<pagina titulo="{title}">
{page}
</pagina>

{chunks}"""


def load(data: Path) -> dict[str, list[tuple[Path, dict]]]:
    pages: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    for f in sorted(data.rglob("*.jsonl")):
        if "knowledge" not in f.parts:
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if {"id", "title", "url", "text"} <= row.keys():
                    pages[row["url"]].append((f, row))
    return pages


def generate(data: Path, out: Path, max_usd: float) -> int:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("APP_ANTHROPIC_API_KEY") or os.environ["ANTHROPIC_API_KEY"])
    old = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    headers: dict[str, str] = dict(old.get("headers") or {})  # continua de onde parou: não paga de novo
    spent = float(old.get("spent_usd") or 0.0)
    groups = [(url, [r for _, r in items][i:i + GROUP]) for url, items in load(data).items()
              for i in range(0, len(items), GROUP)]
    pages_text = {url: "\n\n".join(r["text"] for _, r in items)[:PAGE_CHARS] for url, items in load(data).items()}
    for url, rows in groups:
        if all(r["id"] in headers for r in rows):
            continue
        if spent >= max_usd:
            print(f"TETO: US$ {spent:.4f} >= {max_usd}; parei antes de {url}")
            break
        page = pages_text[url]
        chunks = "\n".join(f"[{i + 1}] {r['text'][:1500]}" for i, r in enumerate(rows))
        msg = client.messages.create(model=MODEL, max_tokens=60 * len(rows) + 2000,
                                     output_config={"effort": "low"}, messages=[
            {"role": "user", "content": PROMPT.format(title=rows[0]["title"], page=page, chunks=chunks)}])
        spent += msg.usage.input_tokens * PRICE_IN + msg.usage.output_tokens * PRICE_OUT
        text = "".join(b.text for b in msg.content if b.type == "text").strip()
        text = text[text.find("["): text.rfind("]") + 1]
        try:
            lines = json.loads(text)
        except ValueError:
            print(f"AVISO: resposta ilegível para {url}; sem cabeçalho nesta página")
            continue
        if len(lines) != len(rows):
            print(f"AVISO: {len(lines)} frases para {len(rows)} trechos em {url}; sem cabeçalho nesta página")
            continue
        for r, h in zip(rows, lines, strict=True):
            headers[r["id"]] = " ".join(str(h).split())[:200]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"model": MODEL, "spent_usd": round(spent, 4), "headers": headers}, ensure_ascii=False,
                              indent=1), encoding="utf-8")
    print(f"{len(headers)} cabeçalhos, US$ {spent:.4f} → {out}")
    return 0


def apply(data: Path, headers_file: Path, dest: Path) -> int:
    heads = json.loads(headers_file.read_text(encoding="utf-8"))["headers"]
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(data, dest)
    n = 0
    for f in sorted(dest.rglob("*.jsonl")):
        if "knowledge" not in f.parts:
            continue
        out = []
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if row.get("id") in heads:
                    row["context"] = f"{row['title']} › {heads[row['id']]}"
                    n += 1
                out.append(json.dumps(row, ensure_ascii=False))
        f.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{n} trechos com cabeçalho em {dest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, default=Path("var/ctx_headers.json"))
    ap.add_argument("--max-usd", type=float, default=0.10)
    ap.add_argument("--apply", type=Path, metavar="HEADERS.json")
    ap.add_argument("--dest", type=Path)
    args = ap.parse_args(argv)
    if args.apply:
        return apply(args.data, args.apply, args.dest)
    return generate(args.data, args.out, args.max_usd)


if __name__ == "__main__":
    sys.exit(main())
