"""Gera o histórico do kit que vai na entrega (docs/KIT_CHANGELOG.md) a partir de docs/kit/CHANGELOG.md.

Uso (no scaffold, antes do pip; só biblioteca padrão):
  python3 scripts/kit_history.py [--src docs/kit/CHANGELOG.md] [--out docs/KIT_CHANGELOG.md]

O CHANGELOG do kit é o registro de trabalho entre as tentativas e mistura procedência com anotação interna (medidas
de avaliação, ordens de trabalho). A entrega leva só a procedência: as versões, o que cada uma mudou com a causa
técnica, e as ideias de terceiros com a origem. Cada bloco (item de lista, linha de tabela, parágrafo) com anotação
interna sai inteiro, para nenhuma frase ficar cortada no meio; nos títulos sai só o trecho.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# nota de 6,0 a 10 ("7,25", "(6,5)"); não pega preço, latência nem métrica 0,xx
_GRADE = r"(?<![\d.,$])(?<!US\$ )(?<!R\$ )(?:[6-9],\d{1,2}|10(?:,0)?)(?![\d.,])(?!\s?(?:s|ms|GB|MB|min|%|x|×)\b)"
BANNED = re.compile(
    "|".join([
        r"r[ée]gua", r"\bnotas?\b", r"avaliador", r"avalia[çc](?:ão|ões) (?:cega|simulada|formal)",
        r"corre[çc][ãa]o (?:formal|simulada)", r"\bbench\b", r"\bTOP ?\d", r"\bdono\b", r"tirou 10",
        r"\bmeta\b", r"\bgate em 3 passos\b", r"\bfrentes?\b", r"PLAYBOOK", r"\bpend[êe]ncias?\b", _GRADE,
    ]),
    re.IGNORECASE,
)
# título: "## v5.5.3 (04/11/2026) — rodada 12: texto final limpo" → tira "rodada N:" e o trecho com termo proibido
_ROUND = re.compile(r"\s*rodada \d+:\s*", re.IGNORECASE)


def _blocks(lines: list[str]) -> list[list[str]]:
    """Agrupa em blocos: título, linha de tabela, item de lista (com as linhas de continuação) ou parágrafo."""
    out: list[list[str]] = []
    cur: list[str] = []
    kind = ""

    def flush() -> None:
        nonlocal cur, kind
        if cur:
            out.append(cur)
        cur, kind = [], ""

    for line in lines:
        s = line.strip()
        if not s:
            flush()
            out.append([line])
            continue
        if s.startswith("#") or s.startswith("|"):
            flush()
            out.append([line])
            continue
        if re.match(r"\s*(?:[-*]|\d+\.)\s", line):
            flush()
            cur, kind = [line], "item"
            continue
        if kind == "item" and line.startswith((" ", "\t")):
            cur.append(line)
            continue
        if kind != "para":
            flush()
            kind = "para"
        cur.append(line)
    flush()
    return out


def _heading(line: str) -> str:
    line = _ROUND.sub(" ", line)
    line = re.sub(r"\s*\((?=[^)]*" + _GRADE + r")[^)]*\)", "", line)  # parêntese com nota sai do título
    head, sep, title = line.partition(" — ")
    if sep and BANNED.search(title):
        title = ""
    return (head + (sep + title if title else "")).rstrip()


def render(src: str, version: str = "") -> str:
    kept: list[str] = []
    for block in _blocks(src.splitlines()):
        first = block[0].strip()
        if first.startswith("#"):
            if first.startswith("# "):
                continue  # o título do arquivo do kit é trocado pelo cabeçalho abaixo
            kept.append(_heading(block[0]))
            continue
        if any(BANNED.search(line) for line in block):
            continue
        kept.extend(block)
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
    # seção que ficou só com o título (todos os itens citavam processo): sai também
    body = re.sub(r"(?m)^(#{2,4} [^\n]*)\n+(?=#{2,4} |\Z)", "", body)
    head = ("# Histórico do kit\n\nGerado de `docs/kit/CHANGELOG.md`" + (f" (kit {version})" if version else "")
            + " por `scripts/kit_history.py`: as versões do kit usado no scaffold, o que cada uma mudou e por quê, e "
            "as ideias que vieram de soluções públicas (só a ideia, com a origem; nenhum código copiado). O registro "
            "de trabalho entre as tentativas fica no kit, fora desta entrega.\n")
    return head + "\n" + body + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", type=Path, default=ROOT / "docs" / "kit" / "CHANGELOG.md")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "KIT_CHANGELOG.md")
    ap.add_argument("--version", default="")
    args = ap.parse_args(argv)
    text = render(args.src.read_text(encoding="utf-8"), args.version)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    left = BANNED.findall(text)
    print(f"{args.out}: {len(text.splitlines())} linhas; termos de processo restantes: {len(left)}")
    return 1 if left else 0


if __name__ == "__main__":
    raise SystemExit(main())
