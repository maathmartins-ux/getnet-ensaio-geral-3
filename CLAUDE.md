# Instruções permanentes do dono para este kit

Leia e siga `docs/kit/MELHORIA_CONTINUA.md` em toda rodada (ensaio, avaliação, bateria ao vivo, produção):
medir com o avaliador após cada mudança, reforçar os pontos bons, corrigir os ruins na raiz pesquisando (web, git,
benches, feedbacks), registrar antes → depois, e não gastar dinheiro/tokens sem hipótese.

Diretriz 2: toda melhoria entra no kit de produção a cada rodada, de forma recorrente, até bater a meta.
Meta em vigor (última ordem do dono, 03/11 noite): ≥ 9,0 na nossa régua (média de 2 réguas), primeiro no ensaio e
depois no cronometrado de 60 min (8,73 no simulador = 9,5 real do nelsondell). Abaixo disso, não rodar. Ao bater, avisar.
Diretriz 3: rodadas rápidas (errar rápido, corrigir rápido): loop curto por split afetado; bateria integral só no fim do lote.

O texto do dono, palavra por palavra, está no fim de docs/kit/MELHORIA_CONTINUA.md: seguir a partir de agora, em toda sessão.

Ordem do dono (03/11, noite): ensaio ≥ 9,0 na nossa régua (média de 2) → só então ensaio cronometrado de 60 min →
produção só se o cronometrado der ≥ 9,0. Domínio: ordem nova do dono (04/11, ensaio 13) — pode ir montado se não
ferir as regras do desafio (PROCEDENCIA declara, números medidos no relógio, held-out e reais novos e cegos;
MELHORIA_CONTINUA).

Ordem do dono (04/11): modo rápido ligado em toda sessão do ensaio e da produção. Em sessão na nuvem só o app liga
(menu do modelo ou `/fast`); a maestra confere cada sessão nova (`get_session` → `flag_settings.fastMode: true`)
e, se vier desligado, manda o link ao dono com o lembrete (PLAYBOOK, A9).

Diretriz do dono (04/11): a sessão maestra é ATIVA no ensaio e na produção: monitora minuto a minuto (git log de
origin/main e estado da sessão do relógio a cada 1–2 min), captura falha e já corrige, entra no processo quando
precisar e pega tarefas para si para agilizar. Nunca fica passiva esperando dar errado (PLAYBOOK §2.2).
