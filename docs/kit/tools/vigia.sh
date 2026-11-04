#!/usr/bin/env bash
# Vigia da Maestra A (rodada 15): roda no Monitor da maestra, uma linha por evento, sem LLM.
#   docs/kit/tools/vigia.sh <clone do repo da tentativa> [sha do scaffold]
# Emite: NOVO <ramo> <sha> (commit novo em qualquer ramo), PULSO T+N a cada 2 min, ALERTA quando o main fica
# SEM_COMMIT_MIN minutos (padrão 6) sem commit novo, e ALERTA de teto em T+50 e T+55.
# Cada ALERTA de "sem commit" manda a maestra olhar o que a sessão do relógio executa AGORA (get_session e
# list_events com kinds=["assistant"], limit 8): espera em 1º plano há mais de 60 s → interrupt_session e
# send_message com o próximo passo. Ensaio 14: a sessão do relógio ficou 4 min num `until` em 1º plano, sem ler
# mensagens nem dar push, e a maestra só viu pelo git no T+38.
# VIGIA_ONCE=1: uma volta só (teste).
set -uo pipefail
REPO="${1:?uso: vigia.sh <clone> [sha do scaffold]}"
cd "$REPO" || exit 2
SEM_COMMIT_MIN="${SEM_COMMIT_MIN:-6}"
T0_SHA="${2:-}"
t0() {
  if [ -n "$T0_SHA" ]; then git log -1 --format=%ct "$T0_SHA" 2>/dev/null; return; fi
  git log --all --format=%ct --grep='^chore: scaffold' 2>/dev/null | tail -1
}
prev=$(git ls-remote origin 2>/dev/null | sort)
last_main=$(echo "$prev" | awk '$2=="refs/heads/main"{print $1}')
last_change=$(date +%s); n=0; warned50=0; warned55=0
while true; do
  cur=$(git ls-remote origin 2>/dev/null | sort)
  if [ -n "$cur" ] && [ "$cur" != "$prev" ]; then
    comm -13 <(echo "$prev") <(echo "$cur") | while read -r s r; do echo "NOVO ${r#refs/heads/} ${s:0:7}"; done
    prev=$cur
  fi
  main=$(echo "$cur" | awk '$2=="refs/heads/main"{print $1}')
  now=$(date +%s)
  if [ -n "$main" ] && [ "$main" != "$last_main" ]; then last_main=$main; last_change=$now; fi
  T0=$(git fetch -q origin main 2>/dev/null; t0)
  T=$([ -n "$T0" ] && echo $(( (now - T0) / 60 )) || echo "?")
  n=$((n + 1))
  [ $((n % 2)) -eq 0 ] || [ "${VIGIA_ONCE:-0}" = "1" ] && \
    echo "PULSO T+$T min · $(TZ=America/Sao_Paulo date +%H:%M) · main ${main:0:7}"
  idle=$(( (now - last_change) / 60 ))
  if [ "$idle" -ge "$SEM_COMMIT_MIN" ] && [ $((idle % SEM_COMMIT_MIN)) -eq 0 ]; then
    echo "ALERTA ${idle} min sem commit no main: confira o que a sessão do relógio executa agora (get_session + list_events assistant 8); espera em 1º plano > 60 s → interrupt_session e send_message"
  fi
  if [ "$T" != "?" ] && [ "$T" -ge 50 ] && [ "$warned50" = 0 ]; then
    warned50=1; echo "ALERTA T+50: último commit até T+59; nada novo começa"
  fi
  if [ "$T" != "?" ] && [ "$T" -ge 55 ] && [ "$warned55" = 0 ]; then
    warned55=1; echo "ALERTA T+55: só o make final e a CI; nenhum commit de código"
  fi
  [ "${VIGIA_ONCE:-0}" = "1" ] && exit 0
  sleep 60
done
