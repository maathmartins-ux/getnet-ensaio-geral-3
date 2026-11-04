"""Exemplo de intenção (k-NN do router) não pode ser a frase de um caso de avaliação, nem quase igual a ela.

No relógio, exemplos escritos a partir dos casos subiram o guardrail offline: `data/intent_examples.d/r.jsonl` levou
"Me passa uma receita de bolo de cenoura", a mensagem de um caso do split guardrail palavra por palavra. O número do
gate passa a medir a cópia, não o roteador. A guarda antiga só comparava com o held-out cego e exigia 5 palavras
seguidas; aqui vale todo conjunto de avaliação (casos + `.d/`, held-out, perguntas reais) e a similaridade de
palavras (Jaccard ≥ 0,6), que também pega a paráfrase curta.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JACCARD = 0.6
MIN_WORDS = 4  # "falar com humano" (3 palavras) é vocabulário de intenção; 4 já é frase
EVAL_SETS = ("cases", "heldout_blind", "real_questions")


def words(text: str) -> set[str]:
    plain = "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+", plain))


def _rows(paths: list[Path]) -> list[dict]:
    out = []
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                out.append(row)
    return out


def _family(base: Path) -> list[Path]:
    extra = base.parent / f"{base.stem}.d"
    return ([base] if base.exists() else []) + (sorted(extra.glob("*.jsonl")) if extra.is_dir() else [])


def eval_messages(root: Path = ROOT) -> list[tuple[str, str]]:
    """(id, mensagem) de todo turno dos conjuntos de avaliação, com os turnos anteriores (`before`)."""
    out = []
    for name in EVAL_SETS:
        for row in _rows(_family(root / "evals" / f"{name}.jsonl")):
            for msg in [*(row.get("before") or []), row.get("message")]:
                if isinstance(msg, str) and msg.strip():
                    out.append((str(row.get("id", "?")), msg))
    return out


def intent_examples(data: Path) -> list[str]:
    paths = sorted(data.glob("intent_examples*.jsonl")) + sorted((data / "intent_examples.d").glob("*"))
    return [str(r["text"]) for r in _rows([p for p in paths if p.is_file()]) if r.get("text")]


def near_copies(examples: list[str], asked: list[tuple[str, str]]) -> list[tuple[str, str, float]]:
    """(exemplo, caso, Jaccard) quando o exemplo repete, quase igual, a frase de um caso de avaliação."""
    hits = []
    prepared = [(cid, words(m)) for cid, m in asked]
    for ex in examples:
        a = words(ex)
        for cid, b in prepared:
            if min(len(a), len(b)) < MIN_WORDS:
                continue
            score = len(a & b) / len(a | b)
            if score >= JACCARD:
                hits.append((ex, cid, round(score, 2)))
    return hits


def test_detector_catches_the_copied_example_and_spares_a_real_paraphrase():
    asked = [("q-guard-25", "Me passa uma receita de bolo de cenoura."),
             ("heldout-H1-13", "Vai chover em Curitiba no fim de semana?"),
             ("heldout-H2-17", "quero falar com uma pessoa de verdade, por favor")]
    examples = ["Me passa uma receita de bolo de cenoura",  # a cópia do relógio
                "Me passa a receita de bolo de cenoura",  # paráfrase mínima da mesma frase
                "Vai chover em Recife no sábado?",  # mesma intenção, frase própria
                "Preciso de uma pessoa do atendimento, por favor",
                "falar com humano"]
    assert near_copies(examples, asked) == [("Me passa uma receita de bolo de cenoura", "q-guard-25", 1.0),
                                            ("Me passa a receita de bolo de cenoura", "q-guard-25", 0.75)]


def test_eval_messages_cover_cases_d_heldout_and_turns_before(tmp_path):
    ev = tmp_path / "evals"
    (ev / "cases.d").mkdir(parents=True)
    (ev / "cases.jsonl").write_text(json.dumps({"id": "official-01", "message": "a"}) + "\n", encoding="utf-8")
    (ev / "cases.d" / "q.jsonl").write_text(json.dumps({"id": "q-guard-25", "message": "b", "before": ["c"]}) + "\n",
                                            encoding="utf-8")
    (ev / "heldout_blind.jsonl").write_text(json.dumps({"id": "heldout-H1-01", "message": "d"}) + "\n",
                                            encoding="utf-8")
    assert eval_messages(tmp_path) == [("official-01", "a"), ("q-guard-25", "c"), ("q-guard-25", "b"),
                                       ("heldout-H1-01", "d")]


def test_domain_intent_examples_do_not_copy_eval_messages(domain_data):
    """Domínio do desafio (no kit, sem o domínio, pula): exemplos de data/ × todo conjunto de avaliação de evals/."""
    examples = intent_examples(ROOT / "data")
    if not examples:
        import pytest

        pytest.skip("sem data/intent_examples*.jsonl: nada a comparar")
    hits = near_copies(examples, eval_messages(ROOT))
    assert not hits, ("exemplo de intenção quase igual a um caso de avaliação (o gate passa a medir a cópia); "
                      f"escreva uma frase própria: {hits[:8]}")
