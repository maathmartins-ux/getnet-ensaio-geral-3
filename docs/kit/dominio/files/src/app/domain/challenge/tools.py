"""Domínio do desafio — FERRAMENTAS do Customer Support (CRM fictício da Getnet).

Contrato lido pelo motor: TOOLS, ELIGIBLE_STATUS, LABELS, records(), records_offline(), needs_for(). Teste em
tests/test_tools.py. Toda conta sai daqui (totais, contagens, datas de depósito, significado da recusa): o LLM só
copia. "Hoje" é o do negócio (app.clock). Identidade nunca no schema: `user_id` é injetado pelo servidor.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from app import clock
from app.config import data_dir

# --- palavras do domínio (cartão, resposta, aviso do operador) ----------------------------------------------
LABELS = {
    "sem_conexao": {"pt": "sem conexão", "en": "no connection"},
    "sem_sinal": {"pt": "sem sinal", "en": "no signal"},
    "erro_transacao": {"pt": "erro de transação", "en": "transaction error"},
    "today": {"pt": "hoje", "en": "today"},
    "yesterday": {"pt": "ontem", "en": "yesterday"},
    "last_7_days": {"pt": "últimos 7 dias", "en": "last 7 days"},
    "last_30_days": {"pt": "últimos 30 dias", "en": "last 30 days"},
    "30_dias": {"pt": "plano de recebimento em 30 dias", "en": "30-day payout plan"},
    "2_dias": {"pt": "plano de recebimento em 2 dias úteis", "en": "2-business-day payout plan"},
    "credit_plan": {"pt": "plano de recebimento do crédito", "en": "credit payout plan"},
    "reason": {"pt": "motivo", "en": "reason"},
    "period": {"pt": "período", "en": "period"},
    "amount": {"pt": "valor", "en": "amount"},
    "terminal_id": {"pt": "maquininha", "en": "terminal"},
    "request_receivables_advance": {"pt": "antecipação dos recebíveis", "en": "receivables advance"},
    "open_support_ticket": {"pt": "chamado técnico", "en": "support ticket"},
    "get_transactions": {"pt": "consulta de vendas", "en": "sales lookup"},
    "get_settlements": {"pt": "agenda de recebimentos", "en": "settlement schedule"},
    "get_terminals": {"pt": "consulta de maquininhas", "en": "terminal lookup"},
    "pix": "Pix",
    "debito": {"pt": "débito", "en": "debit"},
    "credito": {"pt": "crédito", "en": "credit"},
    "aprovada": {"pt": "aprovada", "en": "approved"},
    "recusada": {"pt": "recusada", "en": "declined"},
    "depositado": {"pt": "depositado", "en": "deposited"},
    "previsto": {"pt": "previsto", "en": "scheduled"},
}

PERIODS = ["today", "yesterday", "last_7_days", "last_30_days"]
DEFAULT_PERIOD = "last_7_days"
_PERIOD = {"type": "string", "enum": PERIODS, "default": DEFAULT_PERIOD,
           "description": "Período: today, yesterday, last_7_days (padrão) ou last_30_days"}
REASONS = ["sem_conexao", "sem_sinal", "erro_transacao"]

# Código de recusa -> significado e o que fazer (calculado aqui, nunca pelo modelo).
DECLINE_CODES = {
    "51": {"pt": "saldo ou limite insuficiente", "en": "insufficient balance or credit limit",
           "action_pt": "o comprador deve falar com o banco emissor ou pagar com outro cartão ou Pix",
           "action_en": "the buyer should contact the card issuer or pay with another card or Pix"},
    "05": {"pt": "não autorizada pelo emissor", "en": "not authorized by the issuer",
           "action_pt": "o comprador deve falar com o banco emissor do cartão; tentar de novo não resolve",
           "action_en": "the buyer should contact the card-issuing bank; retrying will not help"},
    "54": {"pt": "cartão vencido", "en": "expired card",
           "action_pt": "o comprador deve usar um cartão válido", "action_en": "the buyer should use a valid card"},
    "55": {"pt": "senha incorreta", "en": "wrong PIN",
           "action_pt": "o comprador deve digitar a senha correta",
           "action_en": "the buyer should enter the right PIN"},
}
# Prazo de depósito por modalidade, como o site descreve: Pix na hora, débito no dia útil seguinte e crédito no plano
# de recebimento que o lojista escolheu no cadastro. O site oferece receber o crédito "tudo em 2 dias, 30 dias ou mês a
# mês" (FAQ de antecipação) e anuncia "recebimento em 2 dias úteis" com a Get Conta. Cada registro do CRM diz o plano
# (`credit_plan`); sem o campo vale o de 30 dias. "Mês a mês" depende das parcelas e não está neste CRM fictício.
CREDIT_PLANS = {"2_dias": "D+2 úteis", "30_dias": "D+30"}
DEFAULT_CREDIT_PLAN = "30_dias"
SETTLEMENT_RULE = {"pix": "D+0", "debito": "D+1 útil", "credito": CREDIT_PLANS[DEFAULT_CREDIT_PLAN]}


# --- sistema de registro (hoje data/crm/*.json; em produção, a API do CRM com a mesma assinatura) ------------
@lru_cache(maxsize=4)
def _load(folder: str) -> dict:
    out = {}
    for path in sorted(Path(folder).glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        out[rec["owner"]] = rec
    return out


def records() -> dict:
    """{cliente: registro}. Cada registro tem `owner` (auth.known_users lê daqui)."""
    return _load(str(data_dir() / "crm"))


def _client(user_id: str) -> dict | None:
    return records().get(user_id)


def money(cents: int) -> str:
    """R$ 1.234,56 (formato brasileiro, sempre do código)."""
    whole, frac = divmod(int(cents), 100)
    return f"R$ {whole:,}".replace(",", ".") + f",{frac:02d}"


def next_business_day(d: date) -> date:
    """Próximo dia útil (seg a sex) depois de `d`. Feriados não entram neste CRM fictício."""
    d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def credit_plan(user_id: str) -> str:
    """Plano de recebimento do crédito do lojista (`credit_plan` do CRM); valor fora da lista vira o padrão."""
    plan = str((_client(user_id) or {}).get("credit_plan") or DEFAULT_CREDIT_PLAN)
    return plan if plan in CREDIT_PLANS else DEFAULT_CREDIT_PLAN


def deposit_date(method: str, sold: date, plan: str = DEFAULT_CREDIT_PLAN) -> date:
    if method == "pix":
        return sold
    if method == "debito":
        return next_business_day(sold)
    if plan == "2_dias":
        return next_business_day(next_business_day(sold))
    return sold + timedelta(days=30)


def _window(period: str, today: date) -> tuple[date, date]:
    if period == "today":
        return today, today
    if period == "yesterday":
        y = today - timedelta(days=1)
        return y, y
    days = 7 if period == "last_7_days" else 30
    return today - timedelta(days=days - 1), today


def _rows(user_id: str, period: str) -> tuple[list[dict], date, date, date]:
    today = clock.today()
    start, end = _window(period, today)
    rows = []
    for tx in _client(user_id)["transactions"]:
        sold = today - timedelta(days=int(tx["days_ago"]))
        if start <= sold <= end:
            rows.append({**tx, "date": sold})
    rows.sort(key=lambda r: (r["date"], r["time"]))
    return rows, start, end, today


def _relative(d: date, today: date) -> str:
    delta = (today - d).days
    return "today" if delta == 0 else "yesterday" if delta == 1 else f"{delta}_days_ago"


_FAQ_DECLINE = {"agent": "faq", "why": "venda recusada: o que fazer vem do manual de recusas",
                "hint": "código de recusa 51 05 o que fazer"}
# O `why` diz quando o achado vale: lido cru pelo supervisor LLM numa pergunta de recusa, o achado da maquininha
# offline levou o faq a buscar o manual de conexão e a resposta a dizer que ele faltava, sobre algo não perguntado.
_FAQ_OFFLINE = {"agent": "faq", "why": "maquininha offline: se a pergunta é sobre conexão ou sinal, o passo a passo "
                                       "vem do manual de conexão",
                "hint": "maquininha sem conexão chip wi-fi reiniciar"}


# --- tools --------------------------------------------------------------------------------------------------
def get_transactions(user_id: str, period: str = DEFAULT_PERIOD) -> dict:
    if _client(user_id) is None:
        return {"ok": False, "error": "not_found"}
    rows, start, end, today = _rows(user_id, period)
    sales, declines, by_method = [], [], {}
    for r in rows:
        item = {"transaction_id": r["transaction_id"], "date": r["date"].isoformat(),
                "when": _relative(r["date"], today), "time": r["time"], "method": r["method"],
                "amount": money(r["amount_cents"]), "amount_cents": r["amount_cents"], "status": r["status"],
                "terminal_id": r["terminal_id"]}
        if r.get("contestable"):
            item["contestable"] = True
        if r["status"] == "recusada":
            code = DECLINE_CODES.get(r.get("decline_code", ""), {})
            item.update({"decline_code": r.get("decline_code"),
                         "decline_meaning_pt": code.get("pt", "código desconhecido"),
                         "decline_meaning_en": code.get("en", "unknown code"),
                         "what_to_do_pt": code.get("action_pt", "falar com o banco emissor"),
                         "what_to_do_en": code.get("action_en", "contact the card issuer")})
            declines.append(item)
        else:
            sales.append(item)
            m = by_method.setdefault(r["method"], {"count": 0, "total_cents": 0})
            m["count"] += 1
            m["total_cents"] += r["amount_cents"]
    approved = sum(s["amount_cents"] for s in sales)
    declined = sum(d["amount_cents"] for d in declines)
    data = {"period": period, "from": start.isoformat(), "to": end.isoformat(), "today": today.isoformat(),
            "sales": sales, "declines": declines,
            "totals": {"approved_count": len(sales), "approved_total": money(approved),
                       "approved_total_cents": approved, "declined_count": len(declines),
                       "declined_total": money(declined), "declined_total_cents": declined,
                       "by_method": {k: {"count": v["count"], "total": money(v["total_cents"])}
                                     for k, v in by_method.items()}}}
    out = {"ok": True, "data": data}
    if declines:
        out["needs"] = [dict(_FAQ_DECLINE)]
    return out


def get_settlements(user_id: str, period: str = DEFAULT_PERIOD) -> dict:
    """Agenda de recebimentos das vendas APROVADAS do período, com a data de depósito calculada."""
    if _client(user_id) is None:
        return {"ok": False, "error": "not_found"}
    rows, start, end, today = _rows(user_id, period)
    plan = credit_plan(user_id)
    rules = {**SETTLEMENT_RULE, "credito": CREDIT_PLANS[plan]}
    groups: dict[str, dict] = {}
    for r in rows:
        if r["status"] != "aprovada":
            continue
        dep = deposit_date(r["method"], r["date"], plan)
        g = groups.setdefault(r["method"], {"method": r["method"], "rule": rules[r["method"]],
                                            **({"credit_plan": plan} if r["method"] == "credito" else {}),
                                            "count": 0, "total_cents": 0, "items": []})
        g["count"] += 1
        g["total_cents"] += r["amount_cents"]
        g["items"].append({"transaction_id": r["transaction_id"], "sale_date": r["date"].isoformat(),
                           "amount": money(r["amount_cents"]), "deposit_date": dep.isoformat(),
                           "deposit_status": "depositado" if dep <= today else "previsto"})
    schedule = []
    for method in ("pix", "debito", "credito"):
        if method in groups:
            g = groups[method]
            schedule.append({**{k: v for k, v in g.items() if k != "total_cents"}, "total": money(g["total_cents"]),
                             "deposit_dates": sorted({i["deposit_date"] for i in g["items"]})})
    total = sum(g["total_cents"] for g in groups.values())
    pending = sum(r["amount_cents"] for r in rows if r["status"] == "aprovada"
                  and deposit_date(r["method"], r["date"], plan) > today)
    return {"ok": True, "data": {"period": period, "from": start.isoformat(), "to": end.isoformat(),
                                 "today": today.isoformat(), "schedule": schedule,
                                 "totals": {"count": sum(g["count"] for g in groups.values()), "total": money(total),
                                            "already_deposited": money(total - pending),
                                            "still_to_deposit": money(pending)}}}


def get_terminals(user_id: str) -> dict:
    client = _client(user_id)
    if client is None:
        return {"ok": False, "error": "not_found"}
    now = clock.now()
    terminals, offline = [], []
    for term in client["terminals"]:
        last = now - timedelta(minutes=int(term["last_contact_minutes_ago"]))
        item = {"terminal_id": term["terminal_id"], "model": term["model"], "status": term["status"],
                "connection": term["connection"], "signal": term["signal"],
                "last_contact": last.strftime("%Y-%m-%d %H:%M")}
        if term["status"] == "offline":  # campo só quando se aplica (com 0 no online saía "offline há 0 h")
            item["offline_for_hours"] = int(term["last_contact_minutes_ago"]) // 60
            item["issue"] = term.get("issue", "sem_conexao")
            offline.append(term["terminal_id"])
        terminals.append(item)
    out = {"ok": True, "data": {"terminals": terminals, "count": len(terminals),
                                "online_count": len(terminals) - len(offline), "offline_count": len(offline),
                                "offline_ids": offline}}
    if offline:
        out["needs"] = [dict(_FAQ_OFFLINE)]
    return out


def _terminal(user_id: str, terminal_id: str) -> dict | None:
    client = _client(user_id)
    if client is None:
        return None
    wanted = str(terminal_id).strip().upper()
    return next((x for x in client["terminals"] if x["terminal_id"].upper() == wanted), None)


def _ref(prefix: str, *parts: str) -> str:
    return prefix + hashlib.sha1("|".join(parts).encode()).hexdigest()[:6].upper()


def open_support_ticket(user_id: str, terminal_id: str, reason: str) -> dict:
    term = _terminal(user_id, terminal_id)
    if term is None:  # inexistente e de outro cliente: mesma resposta
        return {"ok": False, "error": "not_found"}
    today = clock.today().isoformat()
    ticket = {"ticket_id": _ref("CH", user_id, term["terminal_id"], reason, today),
              "terminal_id": term["terminal_id"], "model": term["model"], "reason": reason, "status": "aberto",
              "opened_on": today}
    return {"ok": True, "data": {**ticket, "before": {"terminal_id": term["terminal_id"], "open_ticket": None},
                                 "after": {"terminal_id": term["terminal_id"], "open_ticket": ticket["ticket_id"]}}}


def available_advance_cents(user_id: str) -> int:
    """Crédito ainda a receber (vendas dos últimos 30 dias): o que pode ser antecipado."""
    rows, _, _, today = _rows(user_id, "last_30_days")
    plan = credit_plan(user_id)
    return sum(r["amount_cents"] for r in rows if r["status"] == "aprovada" and r["method"] == "credito"
               and deposit_date(r["method"], r["date"], plan) > today)


def request_receivables_advance(user_id: str, amount: float) -> dict:
    if _client(user_id) is None:
        return {"ok": False, "error": "not_found"}
    cents = round(float(amount) * 100)
    available = available_advance_cents(user_id)
    if cents > available:
        return {"ok": False, "error": "above_available",
                "data": {"requested": money(cents), "available": money(available)}}
    today = clock.today().isoformat()
    req = {"request_id": _ref("AN", user_id, str(cents), today), "amount": money(cents),
           "available_before": money(available), "status": "solicitada", "requested_on": today}
    return {"ok": True, "data": {**req, "before": {"available": money(available)},
                                 "after": {"available": money(available - cents)}}}


TOOLS = {
    "get_transactions": {
        "description": "Vendas e recusas do cliente autenticado no período, com totais, contagens e o significado "
                       "de cada código de recusa já calculados.", "write": False,
        "input_schema": {"type": "object", "properties": {"period": _PERIOD}, "additionalProperties": False},
        "fn": get_transactions},
    "get_settlements": {
        "description": "Agenda de recebimentos das vendas aprovadas no período por modalidade, com a data de "
                       "depósito calculada (Pix D+0, débito D+1 dia útil, crédito no plano de recebimento do "
                       "lojista: 2 dias úteis ou 30 dias) e os totais.",
        "write": False,
        "input_schema": {"type": "object", "properties": {"period": _PERIOD}, "additionalProperties": False},
        "fn": get_settlements},
    "get_terminals": {
        "description": "Maquininhas do cliente autenticado: status, conexão, sinal, último contato e há quantas "
                       "horas está offline (só quando offline).", "write": False,
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}, "fn": get_terminals},
    "open_support_ticket": {
        "description": "Propõe abrir um chamado técnico para uma maquininha do cliente. Exige confirmação.",
        "write": True,
        "input_schema": {"type": "object", "properties": {
            "terminal_id": {"type": "string", "minLength": 1, "maxLength": 20, "description": "Id da maquininha"},
            "reason": {"type": "string", "enum": REASONS, "description": "Motivo do chamado"}},
            "required": ["terminal_id", "reason"], "additionalProperties": False},
        "fn": open_support_ticket},
    # risco alto: move dinheiro → confirmação do dono E aprovação de um operador (actions.py)
    "request_receivables_advance": {
        "description": "Propõe antecipar recebíveis de crédito no valor pedido (em reais). Exige confirmação do "
                       "cliente e aprovação de um atendente.", "write": True, "risk": "high",
        "input_schema": {"type": "object", "properties": {
            "amount": {"type": "number", "exclusiveMinimum": 0, "description": "Valor em reais (ex.: 500.00)"}},
            "required": ["amount"], "additionalProperties": False},
        "fn": request_receivables_advance},
}
# Ação de escrita -> status do item em que ela faz sentido (nenhuma regra de status neste domínio).
ELIGIBLE_STATUS: dict[str, set[str]] = {}


# --- achados que pedem outro especialista -------------------------------------------------------------------
# A tool já devolve `needs` cru (o supervisor LLM sempre lê). Esta é a REGRA do código: o achado entra no motor de
# tabela quando a pergunta tem sintoma ou pede o que fazer. Junta o `needs` de TODOS os resultados (terminal E venda).
_SYMPTOM = re.compile(r"(conect|connect|sinal|signal|offline|internet|problem|erro|error|recus|declin|resolv|fix|"
                      r"como (eu )?(fa[cç]o|resolvo|volto)|o que (eu )?(posso|devo|fa[cç]o)|what (can|should|do)|"
                      r"how (do|can|to)|steps|passo|down|parou|funcion|working)", re.IGNORECASE)


def tool_needs(evidence: list[str]) -> list[dict]:
    found: list[dict] = []
    for item in evidence:
        try:
            data = json.loads(item)
        except (TypeError, ValueError):
            continue
        for need in (data.get("needs") or []) if isinstance(data, dict) else []:
            if isinstance(need, dict) and need not in found:
                found.append(dict(need))
    return found


def needs_for(result, ctx) -> list[dict]:
    if getattr(result, "agent", None) != "records" or not _SYMPTOM.search(ctx.text or ""):
        return []
    return tool_needs(list(result.evidence or []))


# --- caminho offline do agente records (sem LLM / provedor fora) -------------------------------------------
_TX_ID = re.compile(r"\bTX\d{3,}\b", re.IGNORECASE)
_TERM_ID = re.compile(r"\bT\d{4}[A-Z]?\b", re.IGNORECASE)
_MONEY = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{2}))?")
_ADVANCE = re.compile(r"(antecip|advance)", re.IGNORECASE)
_TICKET = re.compile(r"(chamado|ticket|suporte t[eé]cnico)", re.IGNORECASE)
_TERMINALS = re.compile(r"(maquininha|terminal|m[aá]quina|machine|conect|connect|sinal|signal|offline|online|"
                        r"Get (Cl[aá]ssica|Smart|Mini)|internet)", re.IGNORECASE)
_SETTLE = re.compile(r"(dep[oó]sit|receb|\bcai\b|cair|caem|liquid|settle|paid out|payout|receive)", re.IGNORECASE)
_SALES = re.compile(r"(venda|vendi|recus|declin|sale|sold|transa|faturei|cobran|charge)", re.IGNORECASE)


def _period(text: str) -> str:
    if re.search(r"\b(ontem|yesterday)", text, re.IGNORECASE):
        return "yesterday"
    if re.search(r"\b(hoje|today)\b", text, re.IGNORECASE):
        return "today"
    if re.search(r"(7 dias|semana|7 days|week)", text, re.IGNORECASE):
        return "last_7_days"
    return "last_30_days"  # pergunta sem período: o mais largo que a tool aceita


def _amount(text: str) -> float | None:
    m = _MONEY.search(text)
    if not m:
        return None
    return int(m.group(1).replace(".", "")) + int(m.group(2) or 0) / 100


def _day(iso: str, pt: bool) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%d/%m/%Y") if pt else d.isoformat()


def _label(value: str, pt: bool) -> str:
    v = LABELS.get(value, value)
    return v if isinstance(v, str) else v["pt" if pt else "en"]


def _context_text(ctx) -> str:
    return " ".join([*(m.get("content", "") for m in ctx.history[-4:] if m.get("role") == "user"), ctx.text])


def records_offline(ctx, a):
    """Atendimento determinístico do agente records. `a` = módulo app.agents (AgentResult, run_tool, _t...)."""
    AgentResult, run_tool, t = a.AgentResult, a.run_tool, a._t
    pt = t(ctx, "pt", "en") == "pt"
    text = ctx.text
    calls: list = []
    ev: list[str] = []

    def call(tool: str, args: dict) -> dict:
        result, c = run_tool(tool, args, ctx.user_id, ctx.conversation_id)
        calls.append(c)
        ev.append(json.dumps(result, ensure_ascii=False))
        return result

    def done(msg_pt: str, msg_en: str, facts: dict | None = None, pending=None, needs=None, status="ok"):
        out = AgentResult("records", status, tool_calls=calls, evidence=ev, facts=facts or {},
                          needs=needs or [], text=t(ctx, msg_pt, msg_en))
        if pending:
            out.pending_action = pending
        return out

    if _ADVANCE.search(text):
        amount = _amount(text)
        if amount is None:
            return done("Qual valor você quer antecipar?", "How much do you want to advance?")
        result = call("request_receivables_advance", {"amount": amount})
        cents = round(amount * 100)
        return _proposal(result, done, f"antecipar {money(cents)} dos recebíveis",
                         f"advance {money(cents)} of your receivables")

    if _TICKET.search(text):
        found = _TERM_ID.search(text) or _TERM_ID.search(_context_text(ctx))
        terms = call("get_terminals", {})
        offline = (terms.get("data") or {}).get("offline_ids") or []
        tid = found.group(0).upper() if found else (offline[0] if len(offline) == 1 else None)
        if not tid:
            return done("Para qual maquininha devo abrir o chamado?", "Which terminal should the ticket be for?")
        reason = ("sem_sinal" if re.search(r"(sinal|signal)", text, re.IGNORECASE) else
                  "erro_transacao" if re.search(r"(recus|declin|transa)", text, re.IGNORECASE) else "sem_conexao")
        result = call("open_support_ticket", {"terminal_id": tid, "reason": reason})
        if result.get("error") == "not_found":
            return done(f"Não encontrei a maquininha {tid} na sua conta.",
                        f"I couldn't find terminal {tid} in your account.", {"record_not_found": tid})
        return _proposal(result, done, f"abrir um chamado técnico ({_label(reason, True)}) para a maquininha {tid}",
                         f"open a support ticket ({_label(reason, False)}) for terminal {tid}")

    tx_id = _TX_ID.search(text)
    if _TERMINALS.search(text) and not tx_id and not _SALES.search(text):
        return _terminals_answer(call("get_terminals", {}), done, pt, text)
    if _SETTLE.search(text):
        return _settlements_answer(call("get_settlements", {"period": _period(text)}), done)
    if _SALES.search(text) or tx_id:
        period = "last_30_days" if tx_id else _period(text)
        return _transactions_answer(call("get_transactions", {"period": period}), done, text, tx_id)
    if _TERMINALS.search(text):
        return _terminals_answer(call("get_terminals", {}), done, pt, text)
    return done("Posso consultar suas vendas, recebimentos ou maquininhas. Qual delas?",
                "I can look up your sales, settlements or terminals. Which one?")


def _proposal(result, done, what_pt, what_en):
    if result.get("needs_confirmation"):
        aid = result["action_id"]
        high = result.get("risk") == "high"
        extra_pt = " Depois da sua confirmação, um atendente aprova." if high else ""
        extra_en = " After you confirm, a human agent approves it." if high else ""
        return done(f"Proposta: {what_pt}. Confirme a ação {aid}.{extra_pt} Nada foi feito ainda.",
                    f"Proposal: {what_en}. Confirm action {aid}.{extra_en} Nothing has been done yet.",
                    pending=aid)
    if result.get("error") == "above_limit":
        return done("Esse valor passa do limite permitido para antecipação. Nada foi feito.",
                    "That amount is above the allowed advance limit. Nothing has been done.")
    return done("Não consegui registrar o pedido agora. Nada foi feito.",
                "I couldn't register the request right now. Nothing has been done.", status="error")


def _terminals_answer(result, done, pt, text):
    if not result.get("ok"):
        return done("Não consegui consultar suas maquininhas agora.", "I couldn't look up your terminals now.",
                    status="error")
    data = result["data"]
    parts_pt, parts_en = [], []
    for term in data["terminals"]:
        tid, model, conn = term["terminal_id"], term["model"], term["connection"]
        if term["status"] == "offline":
            h = term["offline_for_hours"]
            parts_pt.append(f"{tid} ({model}) está offline há {h} horas, {_label(term['issue'], True)} "
                            f"(conexão por {conn})")
            parts_en.append(f"{tid} ({model}) has been offline for {h} hours, {_label(term['issue'], False)} "
                            f"(connects via {'SIM chip' if conn == 'chip' else conn})")
        else:
            parts_pt.append(f"{tid} ({model}) está online, conectada por {conn}")
            parts_en.append(f"{tid} ({model}) is online, connected via {conn}")
    facts = {"terminals": {x["terminal_id"]: x["status"] for x in data["terminals"]}, "offline": data["offline_ids"]}
    needs = result.get("needs") or []
    return done("Suas maquininhas: " + "; ".join(parts_pt) + ".", "Your terminals: " + "; ".join(parts_en) + ".",
                facts, needs=needs if _SYMPTOM.search(text) else [])


def _settlements_answer(result, done):
    if not result.get("ok"):
        return done("Não consegui consultar seus recebimentos agora.", "I couldn't look up your settlements now.",
                    status="error")
    data = result["data"]
    if not data["schedule"]:
        return done(f"Não há vendas aprovadas em {_label(data['period'], True)}.",
                    f"There are no approved sales for {_label(data['period'], False)}.", {"period": data["period"]})
    parts_pt, parts_en = [], []
    for g in data["schedule"]:
        dates_pt = ", ".join(_day(d, True) for d in g["deposit_dates"])
        dates_en = ", ".join(_day(d, False) for d in g["deposit_dates"])
        parts_pt.append(f"{_label(g['method'], True)}: {g['total']} ({g['count']} venda(s), {g['rule']}), "
                        f"depósito em {dates_pt}")
        parts_en.append(f"{_label(g['method'], False)}: {g['total']} ({g['count']} sale(s), {g['rule']}), "
                        f"deposit on {dates_en}")
    tot = data["totals"]
    return done(f"Recebimentos das vendas de {_label(data['period'], True)}: " + "; ".join(parts_pt)
                + f". Total {tot['total']}; já depositado {tot['already_deposited']}, "
                  f"a depositar {tot['still_to_deposit']}.",
                f"Settlements for sales from {_label(data['period'], False)}: " + "; ".join(parts_en)
                + f". Total {tot['total']}; already deposited {tot['already_deposited']}, still to be deposited "
                  f"{tot['still_to_deposit']}.",
                {"period": data["period"], "total": tot["total"]})


def _transactions_answer(result, done, text, tx_id):
    if not result.get("ok"):
        return done("Não consegui consultar suas vendas agora.", "I couldn't look up your sales now.", status="error")
    data = result["data"]
    items = data["sales"] + data["declines"]
    needs = result.get("needs") or []
    if tx_id:
        wanted = tx_id.group(0).upper()
        hit = next((i for i in items if i["transaction_id"] == wanted), None)
        if hit is None:  # inexistente e de outro cliente: mesma resposta
            return done(f"Não encontrei a venda {wanted} na sua conta.",
                        f"I couldn't find sale {wanted} in your account.", {"record_not_found": wanted})
        items = [hit]
    else:
        value = _amount(text)
        if value is not None:
            items = [i for i in items if i["amount_cents"] == round(value * 100)] or items
    declines = [i for i in items if i["status"] == "recusada"]
    if re.search(r"(recus|declin)", text, re.IGNORECASE) or (declines and len(items) == len(declines)):
        if not declines:
            return done(f"Não houve vendas recusadas em {_label(data['period'], True)}.",
                        f"There were no declined sales in the {_label(data['period'], False)}.",
                        {"period": data["period"]})
        pt_parts = [f"{d['transaction_id']} ({_label(d['method'], True)}, {d['amount']}): código {d['decline_code']}"
                    f" = {d['decline_meaning_pt']}; {d['what_to_do_pt']}" for d in declines]
        en_parts = [f"{d['transaction_id']} ({_label(d['method'], False)}, {d['amount']}): code {d['decline_code']}"
                    f" = {d['decline_meaning_en']}; {d['what_to_do_en']}" for d in declines]
        return done(f"Vendas recusadas ({len(declines)}): " + " | ".join(pt_parts) + ".",
                    f"Declined sales ({len(declines)}): " + " | ".join(en_parts) + ".",
                    {"declines": [d["transaction_id"] for d in declines]},
                    needs=needs if _SYMPTOM.search(text) else [])
    if tx_id:
        i = items[0]
        return done(f"Venda {i['transaction_id']}: {i['amount']} no {_label(i['method'], True)}, "
                    f"{_label(i['status'], True)} em {_day(i['date'], True)}.",
                    f"Sale {i['transaction_id']}: {i['amount']} by {_label(i['method'], False)}, "
                    f"{_label(i['status'], False)} on {_day(i['date'], False)}.",
                    {"transaction_id": i["transaction_id"]})
    tot = data["totals"]
    by_pt = ", ".join(f"{_label(k, True)} {v['total']} ({v['count']})" for k, v in tot["by_method"].items())
    by_en = ", ".join(f"{_label(k, False)} {v['total']} ({v['count']})" for k, v in tot["by_method"].items())
    return done(f"Vendas aprovadas em {_label(data['period'], True)}: {tot['approved_count']}, total "
                f"{tot['approved_total']} ({by_pt}). Recusadas: {tot['declined_count']}.",
                f"Approved sales for {_label(data['period'], False)}: {tot['approved_count']}, total "
                f"{tot['approved_total']} ({by_en}). Declined: {tot['declined_count']}.",
                {"period": data["period"], "approved_total": tot["approved_total"]})
