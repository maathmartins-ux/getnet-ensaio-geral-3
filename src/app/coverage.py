"""Parcial decidido no motor: o que falta só torna a resposta parcial se é um item que o cliente PEDIU.

Ensaio 14 (lição 7): os oficiais 01, 05 e 06 saíram "partial" porque o redator marcou `MISSING` de um item vizinho
que ninguém pediu ("a tabela de taxas da Get Smart" numa pergunta de diferença; "o que fazer se o teste falhar" num
passo a passo; "a taxa da antecipação" num "como funciona"). O prompt já proibia e o modelo não obedeceu (a correção
só no prompt subiu as completas de 17 para 19 de 30, e o juiz caiu). Aqui a regra é do código e é conservadora:

- termos do que falta = palavras de conteúdo (claims.content_words), sem o vocabulário de ausência ("as fontes não
  trazem", "I couldn't find") e sem o ASSUNTO da pergunta ("como funciona X", "diferença entre A e B": X, A e B);
- termos da pergunta = palavras de conteúdo da pergunta, da versão autônoma e da parte que coube ao agente, com o
  glossário do domínio (pt↔en) e grupos de conceito genéricos (custo/taxa/fee; precisa/obrigatório; prazo/quando);
- é item PEDIDO se algum termo do que falta (radical de 5 letras) está nos termos da pergunta, ou se o que falta é
  só o assunto (o produto inteiro que a comparação pede); é VIZINHO só se não sobra termo em comum nenhum.

Na dúvida (sem termo nenhum para comparar), fica pedido: a resposta continua parcial e a falta continua dita.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Iterable

from .claims import content_words, fold, states_absence, stem

# o vocabulário das frases de ausência não é o item que falta
ABSENCE_WORDS = frozenset(fold(w) for w in (
    "sources", "source", "fontes", "fonte", "passage", "passages", "trecho", "trechos", "passagens", "data", "dados",
    "say", "says", "said", "give", "gives", "show", "shows", "cover", "covers", "mention", "mentions", "find", "found",
    "couldn", "didn", "doesn", "don", "can", "cannot", "outright", "explicit", "explicitly", "specific", "exact",
    "trazem", "traz", "dizem", "diz", "mostram", "mostra", "cobrem", "encontrei", "achei", "achar", "consegui",
    "informam", "informa", "apareceu", "aparece", "nenhum", "nenhuma", "também", "tambem", "also", "either",
    "whether", "what", "which", "who", "how", "there", "here", "sobre", "about", "info", "information",
    "informação", "informacao", "detalhe", "detalhes", "details", "detailed", "full", "completa", "completo",
    "manuals", "manual", "manuais", "page", "pages", "página", "pagina", "páginas", "paginas", "site",
))

# grupos de conceito genéricos (não do domínio): pedir um é pedir os outros
CONCEPTS = tuple(frozenset(fold(w) for w in group) for group in (
    ("custo", "custos", "custa", "preço", "preco", "preços", "valor", "valores", "taxa", "taxas", "tarifa",
     "tarifas", "cobra", "cobrança", "cobranca", "percentual", "cost", "costs", "price", "prices", "fee", "fees",
     "rate", "rates", "charge", "charges", "pricing", "pay", "pays", "paga", "pagar", "interest", "juros"),
    ("precisa", "preciso", "precisar", "necessário", "necessario", "obrigatório", "obrigatorio", "obrigatória",
     "exige", "exigido", "requisito", "requisitos", "need", "needs", "required", "require", "requires", "mandatory",
     "requirement", "requirements", "elegibilidade", "eligibility"),
    ("prazo", "prazos", "quando", "tempo", "demora", "dias", "deadline", "when", "long", "time", "days", "timing"),
))

# o assunto da pergunta (o que ela descreve ou compara) não é atributo pedido
_SUBJECT = (
    re.compile(r"\bhow\s+(?:does|do|is|are)\s+(?P<s>.+?)\s+work", re.I),
    re.compile(r"\bcomo\s+funcion\w*\s+(?P<s>.+?)(?:[?.!]|$)", re.I),
    re.compile(r"\bdiferen\w*\s+(?:entre|between)\s+(?P<s>.+?)(?:[?.!]|$)", re.I),
    re.compile(r"\bdifference\s+between\s+(?P<s>.+?)(?:[?.!]|$)", re.I),
    re.compile(r"\b(?:what|o\s+que)\s+(?:is|é|e)\s+(?P<s>.+?)(?:[?.!]|$)", re.I),
)


def _key(word: str) -> str:
    w = word.removesuffix("'s")
    if len(w) > 4 and w.endswith("s"):
        w = w[:-1]
    return stem(w)


def _terms(text: str) -> set[str]:
    return {_key(w) for w in content_words(text) if fold(w) not in ABSENCE_WORDS}


def subject_terms(question: str) -> set[str]:
    out: set[str] = set()
    for rx in _SUBJECT:
        for m in rx.finditer(question):
            out |= _terms(m.group("s"))
    return out


def question_terms(texts: Iterable[str], expand: Callable[[str], str] | None = None) -> set[str]:
    """Termos do que o cliente pediu (pergunta, versão autônoma, parte do agente), com glossário e conceitos."""
    out: set[str] = set()
    for t in texts:
        if t:
            out |= _terms(expand(t) if expand else t)
    for group in CONCEPTS:
        keys = {_key(w) for w in group}
        if out & keys:
            out |= keys
    return out


def is_asked(missing: str, asked: set[str], subject: set[str]) -> bool:
    """O item que falta foi pedido? Conservador: na dúvida, sim (a resposta continua parcial)."""
    terms = _terms(missing)
    if not terms:
        return True
    rest = terms - subject
    if not rest:  # falta o próprio assunto (um dos produtos da comparação, inteiro): é pedido
        return True
    return bool(rest & (asked - subject))


def judge_missing(items: list[str], questions: Iterable[str], expand: Callable[[str], str] | None = None
                  ) -> tuple[bool, list[dict]]:
    """(algum item é pedido, [{item, pedido, termos em comum}]) para a lista do que falta."""
    qs = [q for q in questions if q]
    subject = set().union(*(subject_terms(q) for q in qs)) if qs else set()
    asked = question_terms(qs, expand)
    out = []
    for item in items:
        ok = is_asked(item, asked, subject)
        out.append({"item": item, "pedido": ok,
                    "em_comum": sorted((_terms(item) - subject) & (asked - subject)),
                    "assunto": sorted(_terms(item) & subject)})
    return any(d["pedido"] for d in out), out


_SENT = re.compile(r"(?<=[.!?])\s+")


def drop_neighbor_absence(text: str, items: list[str]) -> tuple[str, list[str]]:
    """Tira do texto mostrado ao cliente as frases de ausência que falam dos itens vizinhos `items` (já julgados não
    pedidos): frase com `states_absence` e algum termo em comum com um deles. Frase de ausência sem termo em comum
    (ou só com pronome) fica. Devolve (texto, frases tiradas); linha que fica vazia sai, o resto não muda."""
    gone_terms = set().union(*(_terms(i) for i in items)) if items else set()
    dropped: list[str] = []
    lines = []
    for line in text.split("\n"):
        parts = _SENT.split(line)
        keep = [p for p in parts if not (p.strip() and states_absence(p) and _terms(p) & gone_terms)]
        dropped += [p.strip() for p in parts if p not in keep]
        if keep == parts:
            lines.append(line)
        elif any(x.strip() for x in keep):
            lines.append(" ".join(x for x in keep if x.strip()))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip(), dropped
