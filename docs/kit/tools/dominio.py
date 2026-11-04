"""Domínio montado (ordem do dono, 04/11): guarda o domínio de uma tentativa e o aplica no T+0 da seguinte.

  python docs/kit/tools/dominio.py save <repo da tentativa> <commit>   # maestra, antes do relógio: grava
                                                                       # docs/kit/dominio/ (arquivos + MANIFEST)
  python docs/kit/tools/dominio.py mount                               # sessão do relógio, no T+0 (depois do
                                                                       # git archive do kit-fonte)

Vai junto o que é FONTE do domínio (corpus, CRM, casos, gold de busca, prompts, regras, ferramentas, testes e docs
do domínio). NÃO vai o que tem de ser medido ou escrito de novo no relógio: resultados, gravações, held-out e
perguntas reais (autores cegos novos), rótulos humanos, DEMO, FAILURE_MODES, TIMESHEET, RESULTS e PROCEDENCIA
(geradas). O `mount` escreve na PROCEDENCIA de onde o domínio veio (declarar é a condição do dono).
Fica em docs/kit/ (fora da entrega): só a preparação usa.
"""
from __future__ import annotations

import fnmatch
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STORE = ROOT / "docs" / "kit" / "dominio"

KEEP = [
    "src/app/domain/challenge/*", "src/app/domain/challenge_prompts/*",
    "data/knowledge/**", "data/crm/*", "data/glossary.json", "data/sources.json", "data/sample.jsonl",
    "data/intent_examples.jsonl", "data/intent_examples.d/*",
    "evals/cases.jsonl", "evals/cases.d/*", "evals/retrieval.jsonl", "evals/retrieval.d/*",
    "evals/retrieval.drafts/official.jsonl", "evals/essential/*",
    "evals/judge_calibration.jsonl", "evals/judge_calibration.d/*",
    "tests/test_domain_*.py", "tests/test_tools.py",
    "README.md", "docs/SPEC.md", "docs/ARCHITECTURE.md", "docs/EVAL_STRATEGY.md", "docs/OBSERVABILITY.md",
    "docs/RUNBOOK.md", "docs/SECURITY_ASI.md", "docs/SOURCES.md", "docs/THREAT_MODEL.md", "docs/VIDEO_SCRIPT.md",
    "docs/COBERTURA.md", "docs/adr/*",
]
# escritos de novo no relógio, por autores cegos novos: nunca vêm da tentativa anterior
NEVER = ["evals/cases.d/real.jsonl", "evals/heldout_blind.jsonl", "evals/real_questions.jsonl"]
# exemplo da loja que o pré-voo apagaria (o mount faz o mesmo, porque o pré-voo --mounted não mexe no domínio)
EXAMPLE_GONE = ["data/records.json"]
BLOCK_BEGIN, BLOCK_END = "<!-- dominio-montado:begin -->", "<!-- dominio-montado:end -->"


def _kept(rel: str) -> bool:
    return rel not in NEVER and any(fnmatch.fnmatch(rel, pat) for pat in KEEP)


def save(repo: Path, commit: str) -> dict:
    files = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", commit],
                           capture_output=True, text=True, check=True).stdout.split()
    kept = sorted(f for f in files if _kept(f))
    dest = STORE / "files"
    if dest.exists():
        shutil.rmtree(dest)
    for rel in kept:
        blob = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rel}"], capture_output=True, check=True)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(blob.stdout)
    url = subprocess.run(["git", "-C", str(repo), "remote", "get-url", "origin"], capture_output=True,
                         text=True).stdout.strip()
    manifest = {"source": url, "commit": commit, "saved_at": time.strftime("%Y-%m-%d"), "files": kept}
    (STORE / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def procedencia_block(manifest: dict) -> str:
    return (f"{BLOCK_BEGIN}\n**Domínio montado antes do relógio.** O corpus, o CRM simulado, os casos de avaliação, "
            f"o gold de busca, os prompts e as regras do domínio e os docs do domínio vieram prontos da tentativa "
            f"cronometrada anterior deste mesmo desafio ({manifest['source']}, commit `{manifest['commit'][:7]}`, "
            f"{manifest['saved_at']}). No relógio desta entrega: held-out e perguntas reais escritos de novo por "
            f"autores cegos, todas as medições (offline, ao vivo, juiz), a conferência humana, as correções e esta "
            f"documentação.\n{BLOCK_END}")


def mount(root: Path = ROOT) -> list[str]:
    manifest = json.loads((STORE / "MANIFEST.json").read_text(encoding="utf-8"))
    src = STORE / "files"
    for rel in manifest["files"]:
        out = root / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / rel, out)
    for rel in EXAMPLE_GONE:
        (root / rel).unlink(missing_ok=True)
    proc = root / "docs" / "PROCEDENCIA.md"
    text = proc.read_text(encoding="utf-8")
    block = procedencia_block(manifest)
    if BLOCK_BEGIN in text:
        head, _, rest = text.partition(BLOCK_BEGIN)
        text = head + block + rest.partition(BLOCK_END)[2]
    else:
        anchor = "## 1. O kit e a sua história"
        text = text.replace(anchor, block + "\n\n" + anchor, 1) if anchor in text else text + "\n\n" + block + "\n"
    proc.write_text(text, encoding="utf-8")
    return manifest["files"]


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "save" and len(sys.argv) == 4:
        m = save(Path(sys.argv[2]), sys.argv[3])
        print(f"domínio guardado: {len(m['files'])} arquivos de {m['source']} @ {m['commit'][:7]}")
    elif len(sys.argv) == 2 and sys.argv[1] == "mount":
        print(f"domínio montado: {len(mount())} arquivos; PROCEDENCIA declara a origem")
    else:
        sys.exit(__doc__)
