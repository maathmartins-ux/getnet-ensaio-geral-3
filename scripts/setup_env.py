"""Gera o script de configuração do ambiente da nuvem (PLAYBOOK §0, A10): docs/kit/SETUP_AMBIENTE.sh.

  python scripts/setup_env.py            # regrava docs/kit/SETUP_AMBIENTE.sh a partir dos locks
  python scripts/setup_env.py --check    # sai com 1 se o arquivo não bate com os locks (o teste faz o mesmo)

Por quê (ensaio 14, lição 4): a linha passada ao dono tinha só fastembed/onnxruntime/numpy/tokenizers; faltou o lock
inteiro (fastapi, pytest, ruff…), o pré-voo reprovou e o relógio teve de instalar. E o script de configuração roda
ANTES de a sessão ter o kit: no repositório da tentativa, o `main` só tem o README (A0) e os locks só existem no ramo
`kit-fonte`. Por isso o script gerado não lê arquivo nenhum do repositório: leva os pinos dos dois locks
(requirements-dev.lock + requirements-hybrid.lock, os mesmos do `uv pip install -r … -r …` do prompt do relógio)
dentro de si, instala com uv (o pip levou ~10 min nos ensaios 13 e 14; o uv resolve o mesmo lock em segundos) e
baixa os modelos do buscador padrão (os mesmos de scripts/fetch_models.py) para o cache do fastembed.
O pacote do app (`-e .`) não entra: ele só existe depois do scaffold; o passo 1 do prompt do relógio o instala sem
dependências (< 1 s).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCKS = ("requirements-dev.lock", "requirements-hybrid.lock")
OUT = ROOT / "docs" / "kit" / "SETUP_AMBIENTE.sh"
LOCK_FILE = "/tmp/kit-requirements.txt"
# o que o pré-voo e a fumaça importam logo no T+0 (o script falha alto se faltar algum)
IMPORTS = ("fastembed", "onnxruntime", "numpy", "tokenizers", "fastapi", "anthropic", "pytest", "xdist")
PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==(\S+)(\s*;.*)?$")


def pins(root: Path = ROOT) -> list[str]:
    """As linhas de requisito dos dois locks (sem comentários), unidas e em ordem; o mesmo pacote com versão ou
    marcador diferente nos dois é erro (o uv recusaria no meio do script de configuração)."""
    seen: dict[str, str] = {}
    for name in LOCKS:
        for raw in (root / name).read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = PIN.match(line)
            if not m:
                raise ValueError(f"{name}: linha que não é pino exato: {line!r}")
            key = m.group(1).lower().replace("_", "-")
            norm = re.sub(r"\s*;\s*", " ; ", line)
            if seen.get(key, norm) != norm:
                raise ValueError(f"{key}: {seen[key]!r} × {norm!r} nos locks")
            seen[key] = norm
    return [seen[k] for k in sorted(seen)]


def render(root: Path = ROOT) -> str:
    sys.path.insert(0, str(root / "scripts"))
    import fetch_models  # mesmos modelos do buscador padrão do kit (config.py / fetch_models.py)

    embed, cross = fetch_models.DEFAULT_EMBED, fetch_models.DEFAULT_CROSS
    body = "\n".join(pins(root))
    checks = ", ".join(IMPORTS)
    return f"""#!/usr/bin/env bash
# Script de configuração do ambiente da nuvem (PLAYBOOK §0, A10). Cole TUDO em: menu do ambiente → Edit → Setup script.
# GERADO por scripts/setup_env.py a partir de {' + '.join(LOCKS)} (não edite à mão; o teste
# tests/test_setup_env.py confere que bate com os locks). Não lê nada do repositório: no repositório da tentativa os
# locks só existem no ramo kit-fonte. Instala com uv (segundos; o pip levou ~10 min) no python do sistema.
set -euo pipefail
UV="$(command -v uv || true)"; [ -n "$UV" ] || UV=/root/.local/bin/uv
if [ ! -x "$UV" ]; then python3 -m pip install -q uv && UV="$(command -v uv)"; fi
cat > {LOCK_FILE} <<'KIT_LOCK'
{body}
KIT_LOCK
"$UV" pip install --system -q -r {LOCK_FILE}
python3 -c "import {checks}; print('dependencias do kit OK')"
# modelos do buscador padrão (~2,8 GB) no cache do fastembed; falha de rede aqui não derruba o ambiente: o relógio
# baixa no 1º eval (scripts/fetch_models.py)
python3 - <<'KIT_MODELS' || echo "AVISO: modelos do buscador não baixados; o 1º eval baixa"
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
TextEmbedding("{embed}")
TextCrossEncoder("{cross}")
print("modelos do buscador OK")
KIT_MODELS
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="só confere; sai com 1 se o arquivo estiver velho")
    args = ap.parse_args(argv)
    text = render()
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("SETUP_AMBIENTE.sh em dia com os locks" if ok else
              "SETUP_AMBIENTE.sh VELHO: rode python scripts/setup_env.py")
        return 0 if ok else 1
    OUT.write_text(text, encoding="utf-8")
    print(f"{OUT.name}: {len(pins())} pinos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
