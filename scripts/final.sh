#!/usr/bin/env bash
# Último commit da entrega: README (e ESTADO.md) e os docs gerados, SOZINHOS no commit, e push.
#
# A linha do tempo do README conta os commits, então o README precisa ser o ÚLTIMO e o único arquivo do último
# commit: misturado com evals/results num commit seguido de outro, a CI fica vermelha ("linha do tempo com 36
# commits, o git tem 37"). Qualquer commit depois disto exige rodar este script de novo.
#
# Uso: scripts/final.sh                       # recusa se houver outra mudança sem commit
#      scripts/final.sh --clock-end <sha>     # TIMESHEET com o relógio fechando nesse commit (o resto: pós-relógio)
#      CLOCK_END=<sha> make final             # o mesmo pelo make
# --clock-end: o proxy da nuvem derruba o push de tag, então a tag clock-end não chega ao GitHub; sem ele, o relógio
# do TIMESHEET fecha no último commit (o certo no relógio de verdade; num ensaio que seguiu depois, declare o fim).
set -euo pipefail
CLOCK_END="${CLOCK_END:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --clock-end) CLOCK_END="${2:?--clock-end precisa do sha do commit que fecha o relógio}"; shift 2 ;;
    *) echo "opção desconhecida: $1 (uso: scripts/final.sh [--clock-end <sha>])" >&2; exit 64 ;;
  esac
done
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PY:-python}"
# os arquivos que o fill_readme gera (fill_readme.README_ONLY): a tabela da PROCEDENCIA conta as linhas do git e muda
# a cada commit (gerada fora deste passo, fica um commit atrás e a CI compara com a versão velha); FAILURE_MODES e
# TIMESHEET saem daqui também (rodada 10: gerados à mão, ficaram velhos e contradiziam o placar)
# + o relatório do check e o juiz × pessoas que este passo refaz (fill_readme.README_ONLY e README_ONLY_DIRS)
GENERATED='README\.md|ESTADO\.md|docs/RESULTS\.md|docs/PROCEDENCIA\.md|docs/SECURITY_ASI\.md|docs/ENTREGA\.md|docs/FAILURE_MODES\.md|docs/TIMESHEET\.md|reports/verify\.md|evals/results/human_review\.json'
GENERATED_DIRS='evals/validation/'
dirty="$(git status --porcelain --untracked-files=no | grep -v -E " ((${GENERATED})|(${GENERATED_DIRS})[^ ]+)$" || true)"
if [[ -n "$dirty" ]]; then
  echo "Commite antes o que não é README/ESTADO/docs gerados (o README tem de ser o último commit):"; echo "$dirty"; exit 1
fi
# análise de erros dos MESMOS live_*.json commitados (o fill_readme --check reprova se divergir); sem eval ao vivo,
# não há o que analisar e o script segue
"$PY" -m evals.failure_modes || echo "   docs/FAILURE_MODES.md não gerado (motivo acima); o --check do fim reprova se ficou velho"
# prova do relógio do git log, antes do último commit (o --check tolera só ele)
"$PY" scripts/timesheet.py ${CLOCK_END:+--clock-end "$CLOCK_END"}
# juiz × pessoas com o juiz de HOJE, antes do README: a conferência humana importada no meio do relógio ficava com o
# juiz daquela hora e, depois que a bateria reescrevia o judge.json, a CI do último commit reprovava ("human_review.json
# não é o que o --report dá hoje") e o juiz × pessoas saía com n = 1 de 9. O --validation julga o texto congelado das
# páginas (só o que este juiz ainda não julgou; sem chave, pula) e o --report refaz o human_review.json.
if compgen -G "evals/human_labels*.csv" > /dev/null; then
  "$PY" -m evals.judge --validation --max-usd "${VALIDATION_MAX_USD:-2}"
  "$PY" -m evals.label --report
fi
# --final: este passo faz o commit só do README, então o topo pode dizer isso (o --check confere no HEAD)
"$PY" scripts/fill_readme.py --final
# a mensagem de entrega commitada sai com os números deste commit (gerada no T+44 ela ficava velha: memória e relógio)
if [[ -f docs/ENTREGA.md ]]; then
  REPO_URL="$(git remote get-url origin 2>/dev/null | sed -E 's#^git@github.com:#https://github.com/#; s#\.git$##; s#https://[^@/]*@#https://#')"
  "$PY" scripts/delivery_message.py --repo "${REPO_URL:-<url do repo>}" --out docs/ENTREGA.md > /dev/null && git add docs/ENTREGA.md
fi
# reports/verify.md VERMELHO ou de outro código sai da entrega (a CI do último commit é a prova): refazer o check
# aqui custaria ~3,5 min de relógio e poderia travar o último commit; o verde do mesmo código fica
"$PY" scripts/check.py --drop-stale-verify
git add README.md
for f in ESTADO.md docs/RESULTS.md docs/PROCEDENCIA.md docs/SECURITY_ASI.md docs/FAILURE_MODES.md docs/TIMESHEET.md reports/verify.md evals/results/human_review.json; do
  [[ -f "$f" ]] && git add "$f"
done
[[ -d evals/validation ]] && git add evals/validation
# o que reprova uma entrega (marcador {{...}}, arquivo citado que não existe, palavra de processo, número de outra
# entrega) para AQUI, antes do commit e do push, com a lista do que corrigir (no kit, sem domínio, não confere nada)
if ! "$PY" scripts/check.py --docs; then
  echo "Corrija os docs acima, commite o que não é gerado e rode scripts/final.sh de novo (nada foi commitado)." >&2
  exit 1
fi
if git diff --cached --quiet; then echo "README já está em dia com o git log."; else
  git commit -q -m "readme: números e linha do tempo (fill_readme, último passo)"
fi
"$PY" scripts/fill_readme.py --check
# o push pela nuvem às vezes cai ("fatal error in commit_refs") e passa na tentativa seguinte: até 4 novas tentativas
# com espera crescente (2/4/8/16 s; PUSH_WAITS troca a espera, o teste usa 0)
push_retry() {
  local waits=(${PUSH_WAITS:-2 4 8 16}) i=0
  until git push -q origin HEAD; do
    if (( i >= ${#waits[@]} )); then
      echo "push recusado $((i + 1)) vezes: confira a rede/credencial e rode só 'git push origin HEAD'" >&2
      return 1
    fi
    echo "push falhou; nova tentativa em ${waits[$i]} s" >&2
    sleep "${waits[$i]}"
    i=$((i + 1))
  done
}
push_retry
# A mensagem que vai ao dono sai DEPOIS do último commit (o relógio dela conta até ele); fora do git (não cria commit).
mkdir -p var
REPO_URL="$(git remote get-url origin 2>/dev/null | sed -E 's#^git@github.com:#https://github.com/#; s#\.git$##; s#https://[^@/]*@#https://#')"
"$PY" scripts/delivery_message.py --repo "${REPO_URL:-<url do repo>}" --out var/ENTREGA_final.md > /dev/null \
  && echo "Mensagem ao dono (relógio até o último commit): var/ENTREGA_final.md"
echo "OK: último commit $(git log -1 --format='%h %aI') enviado. Confira a CI na aba Actions."
