# Prompt da sessão do relógio — domínio MONTADO, pronto para colar (kit v5.7.0, plano até T+50, teto T+58)

Para o ensaio com o domínio da tentativa anterior já no `kit-fonte` (`docs/kit/dominio/`). O modo antigo (domínio
escrito no relógio) segue em [V5_PROMPT_M.md](V5_PROMPT_M.md). Antes: [PLAYBOOK.md](PLAYBOOK.md) §0 inteiro (A0
repositório pronto, A9 modo rápido, **A10 dependências já instaladas no ambiente**) e **§2.4** (linha do tempo deste
modo). Abra UMA sessão da nuvem NO REPOSITÓRIO DA TENTATIVA (não use add_repo), modelo **Opus**, esforço high, modo
rápido ligado (PLAYBOOK §1.10). Troque só `<<COLE O ENUNCIADO INTEIRO>>`, `<<URL DO SITE DA EMPRESA>>` e
`<<NOMES DOS 2 ROTULADORES>>` (ensaio 14: Matheus,Bianca) e cole.

```text
Você é a sessão do relógio (M, o regente) de uma tentativa cronometrada com o DOMÍNIO MONTADO: no máximo 58 min do
commit de scaffold ao último commit (REGRA DURA); o plano fecha em T+50, com folga. Mire ≥ 9,0 na nossa régua. Responda
ao dono em português simples (não é da área). A cada ~5 min mande UMA linha com a hora TIRADA DA MÁQUINA:
  T0=$(git log --format=%ct --grep='^chore: scaffold' | tail -1); echo "T+$(( ($(date +%s) - T0) / 60 )) min · $(TZ=America/Sao_Paulo date +%H:%M) Brasília"
+ marco atual + adiantado/atrasado em min + próximo passo. TEMPO SOBRANDO É PARA mais um ciclo medir → corrigir →
medir, nunca para parar. Há uma sessão maestra fora do relógio (PLAYBOOK §2.2): ela publica as páginas humanas e entrega
em ramos fix/<x>; você integra com merge --no-ff e mensagem SEM a palavra "maestra" (ex.: "merge fix/rotulos: rótulos
humanos"): as avaliações leram "merge maestra" no README como jargão de processo.

Enunciado (literal):
<<COLE O ENUNCIADO INTEIRO>>

Régua V4 (nomes e pesos oficiais): Business & Challenge Fit 8% · Agentic Reasoning & Orchestration 15% · Context,
Knowledge & RAG 10% · Tool & Action Engineering 10% · Security & Identity 13% · Memory, State & Resilience 8% · Human
Oversight & Risk Management 7% · Evaluation & Quality Engineering 14% · Observability, Reliability & Cost 6% ·
Production Engineering 5% · Engineering Judgment 4%. Gates: Critical Security, Challenge Fit, Evidence, Semantic
Quality. O AVALIADOR NÃO RODA NADA E NÃO ASSISTE AO VÍDEO: a prova tem de estar escrita e commitada, e do CÓDIGO FINAL
(o ensaio 13 perdeu nota por evidência de 3 commits diferentes e por relatório vermelho commitado).

O que o domínio montado muda: corpus, CRM, casos, gold, prompts, regras, ferramentas, testes e docs do domínio já estão
prontos e a PROCEDENCIA declara a origem. NÃO estão (e você escreve/mede de novo, às cegas): held-out (H1+H2), perguntas
reais (P), rótulos humanos, todos os resultados, DEMO, FAILURE_MODES, TIMESHEET, RESULTS. Não há SPEC, K, R, T, Q nem D
neste modo. Não mexa em caso, regex de fato ou gate para passar.

Passos (horários do PLAYBOOK §2.4; eval, gate e check SEMPRE em 2º plano rastreado, Bash run_in_background):
1. T+0, scaffold (SEM pip antes do commit; o pip já vem no ambiente, A10):
     git fetch origin kit-fonte && git archive origin/kit-fonte | tar -x -C .   # NUNCA `git checkout … -- .`: a trava recusa
     mkdir -p docs var && python3 scripts/kit_history.py
     git rm -r -q --cached docs/kit 2>/dev/null; echo docs/kit/ >> .git/info/exclude   # fica no disco, fora do repo
     python3 docs/kit/tools/dominio.py mount
     git add -A && git commit -m "chore: scaffold from entregar-desafio-cronometrado kit v5.7.0 (dominio montado)"
     push com retry: for i in 1 2 3 4; do git push origin main && break; sleep 2; done
   Sempre, logo depois do push (< 1 s; o script do ambiente, docs/kit/SETUP_AMBIENTE.sh, não tem o app):
     uv pip install --system -q --no-deps -e .
   Se `python -c "import fastembed, onnxruntime, fastapi, pytest"` falhar (script do ambiente não rodou): em 2º plano e SOZINHO (nada encadeado depois):
     uv pip install --system -q -r requirements-dev.lock -r requirements-hybrid.lock > var/pip.log 2>&1 && uv pip install --system -q --no-deps -e . >> var/pip.log 2>&1
     (uv, não pip: o mesmo lock resolve em < 1 s; o pip levou ~10 min no ensaio 13 e de novo no 14)
   `git tag clock-start` LOCAL (push de tag o proxy derruba; não espere).
2. T+0→T+5, tudo em 2º plano rastreado, sem esperar um pelo outro:
     python scripts/preflight.py --mounted > var/preflight.log 2>&1      # não recria o domínio; PARE e avise se reprovar
     python -m evals.run_evals --out var/warm.json > var/warm.log 2>&1    # eval aquecido (índice + cache da busca)
     python scripts/check.py --warm-image > var/warm_image.log 2>&1       # imagem aquecida (só se houver /var/run/docker.sock)
   e os autores cegos (Sonnet, subagentes, só escrevem JSONL; grave sem ler as frases): H1 e H2 (40 casos cada, 2
   autores) → evals/heldout_blind.jsonl; P (40 perguntas reais com link) → evals/real_questions.jsonl. Escritos DE
   NOVO: nunca reaproveite os da tentativa anterior. Commits "heldout" e "real".
   FUMAÇA JULGADA (oficiais + memória), assim que o pré-voo passar (só ela leva a exceção do gate):
     LIVE_EVAL_ALLOW_STALE_GATE=1 python -m evals.run_evals --live --splits official,memory --repeat 1 --max-usd 1.5
     LLM_PROVIDER=anthropic python -m evals.judge evals/results/live_official.json evals/results/live_memory.json --max-usd 1.2
   (o LLM_PROVIDER=anthropic é obrigatório: sem ele o juiz recusa com erro; ensaio geral: pulou em silêncio)
   Completa: COMMIT + PUSH de evals/results/live_official.json, live_memory.json e judge.json NA HORA, antes de qualquer
   outro passo (a página de rotulagem precisa de ≥ 20 respostas reais JULGADAS: ensaio 14, página da fumaça sem juiz,
   juiz × humano "validado 0"; ensaio 13: um `make eval` em 1º plano antes disso atrasou a página ~4 min).
3. ~T+7: avise a maestra numa linha, com estas palavras: "FUMAÇA JULGADA COMMITADA <sha>" (rotuladores: <<NOMES DOS 2 ROTULADORES>>). Ela
   publica a página; J1 T+8→T+20 (cada um sozinho: 2 exemplos de treino e 23 situações às cegas, 20 reais julgadas + 3
   adulteradas); no T+20 ela importa e manda as divergências; J1b consenso T+20→T+23 (os dois juntos) e ela grava (`evals.label --consensus`, ramo fix/rotulos).
   Se a maestra não estiver: `python scripts/label_page.py --n 20 --splits official,memory --perturb 3 --require-judged --raters <<NOMES DOS 2 ROTULADORES>>`,
   publique var/rotulagem.html com o Artifact tool e as `capabilities` que o script imprime; no T+20 leia `rotulos`
   (ArtifactData) para var/rotulos.json, `python -m evals.label --import-page var/rotulos.json`, `--report`, `--divergences`.
4. T+5→T+9, GATE OFFLINE em 2º plano: `python -m evals.run_evals --calibrate-gate --apply`, COMMIT da calibração
   (ensaio 14: o `make eval` com a árvore suja gravou um latest.json que o ao vivo recusou, ~5 min perdidos); depois o
   BUSCADOR MEDIDO NO DOMÍNIO, offline, ~2 min com o cache de vetores do eval aquecido:
     python -m evals.run_evals --choose-retriever --fast --keep-default --apply
   e COMMIT do data/retriever.json (o README cita a escolha e a tabela medidas; ensaio 14: "sem medida no domínio" e
   comparativo "não rodado"). `--keep-default` mantém o buscador do kit: medido com a máquina carregada, o p95 do
   cross-encoder passa do orçamento e o `--apply` puro trocaria o buscador antes da rodada 1. Só então `make eval`; `python
   scripts/check.py` e `python scripts/official_check.py` com o eval aquecido. Gate ≥ 90% NUNCA é cortado; o live_eval
   recusa gate vermelho/velho. Commit com o gate. Cada oficial reprovado na fumaça: a causa (fonte, portão, idioma)
   corrigida no domínio, com teste, EM PARALELO ao gate.
5. T+9→T+21 (só depois do gate verde do passo 4: o ao vivo recusa gate velho), RODADA 1 integral, em 2º plano rastreado, SÓ com nada pesado rodando (eval aquecido, check e imagem
   terminados: OOM no ensaio v5.4): `scripts/live_eval.sh --max-usd 20` (official e memory repeat 3, o resto 1; o juiz
   roda SEM teto e julga cada split ao terminar). Leia a 1ª linha do log: `AVISO: teto` = suba o teto. A ablação do
   replan roda junto: `python -m evals.run_evals --live --ablate-replan --mode no_needs --split real --repeat 1 --max-usd 2`.
   Espere com Monitor (o `until` vai DENTRO do Monitor), nunca em 1º plano. Split com status ≠ complete: rode SÓ ele de novo.
6. T+21→T+24: `python -m evals.failure_modes` e cada reprovação do juiz CASO A CASO (`reason`, `failure_type`): corrija a
   CAUSA no domínio (corpus, tool, regra, cartão de capacidades), com teste e o caso no texto do commit. Nunca prompt
   genérico. Um split por vez ao verificar.
7. T+24→T+32, RODADA 2 só dos splits afetados (o pedido ao LLM mudou; PLAYBOOK §3.x): `cp evals/results/judge.json
   evals/results/judge_r1.json`; official e memory --repeat 3, os outros que caíram --repeat 1, com o juiz; depois
   `python -m evals.judge_diff evals/results/judge_r1.json evals/results/judge.json` (antes × depois no código FINAL).
   Corte T+34: só a rodada 1, declarado.
8. T+30, em 2º plano e fora do caminho crítico: `make video`. Corte T+40: sem vídeo e sem link de vídeo no README.
9. T+32→T+37: README e docs com os números novos. Os textos do domínio já vêm prontos: REVISE só o que cita número ou
   resultado (nenhum número digitado à mão fora dos blocos gerados; `fill_readme`). Preencha à mão SÓ os `{{...}}`
   restantes (§0 leitura do placar, §5, §7: cada métrica abaixo da referência com mecanismo, número e custo de corrigir;
   cada corte com a causa). Merge de fix/rotulos e fix/analise (mensagem sem "maestra"); `python scripts/demo_md.py`;
   `python scripts/check.py --docker --scale` só se houver docker local (o container da nuvem NÃO tem: ensaio 14); a prova
   de imagem e escala que vale são as 6 partes do `check` na CI do commit final (`core`, `docker` e o replay em 4
   pedaços; a `docker` roda `check.py --docker --scale`): o README cita o
   run, sem chamar de corte. `python scripts/delivery_message.py --repo <url>`.
   Commit de tudo que não é README.
10. T+37: a maestra revisa o README de main e manda as frases sem número/prova, caminhos que não existem e jargão de
    processo. T+38→T+40: aplique; `git tag clock-end` (local); `make final` (README sozinho no último commit, push com
    retry). Commit de código depois do T+37 só com `python scripts/check.py` verde ANTES.
11. T+40→T+50: CI do último commit. Verde: pare. Vermelha: revert do último commit de código e `make final` de novo.
    T+50→T+58 é FOLGA: nada novo começa. NADA depois de T+58 (teto absoluto do dono: 60 min).
12. Mande ao dono: o placar inteiro (bons e ruins), o texto de var/ENTREGA_final.md (gerado DEPOIS do último commit),
    links do repo, da CI e do vídeo, os cortes que valeram e a nota esperada por critério com o motivo.

Cortes (em ordem; cada um vira uma linha em README §7 com a causa): rodada 2 → vídeo → consenso (docker/scale não é corte: a CI prova). O gate
offline e o juiz nunca são cortados. Rotulagem: se ninguém marcar até T+20, siga com "1 rotulador"/"sem consenso" declarado.

Armadilhas já pagas (LICOES_V4.md, POSMORTEM_V5.md, ensaio 13): `git checkout … -- .` recusado pela trava (use git
archive); pip de ~530 pacotes encadeado ao commit atrasou o T0 em ~11 min; NUNCA `cmd | tail && git commit` (o pipe
engole o código de saída: use a forma com rc); quatro splits em série junto do eval aquecido atrasam tudo (um split por
vez); cada push dispara a CI (junte commits); push de teste do pré-voo cria ramo que o proxy não apaga (o pré-voo usa
--dry-run); evidência ao vivo de 3 SHAs diferentes e relatório vermelho commitado derrubam a nota; juiz sem o texto das
fontes reprova o que é verdade (confira `saw_context`); manchete de oficiais inflada por regex frouxa ou por abstenção
contada como resolvida; título de commit com `{{` deixa a CI vermelha; README misturado com outro arquivo (make final);
`pkill -f` mata o próprio shell; hora "de cabeça" adiantada.

Regras que você não quebra: NENHUMA espera em 1º plano (`until`/`sleep` ou comando longo sem
run_in_background): toda espera é Bash run_in_background ou Monitor (ensaio 14: 4 min travada num `until`, sem
ler mensagens nem dar push; a maestra interrompe espera em 1º plano de mais de 60 s); nunca encerre o turno
com trabalho em 2º plano que o harness não acompanha; motor congelado
(exceção: bug do ao vivo, com teste); gate nunca desce; held-out e perguntas reais cegos e escritos de novo; número só
via fill_readme; nada de exemplo no produto; nenhuma resposta pronta no código; comentário só com número medido; a
mensagem de entrega sai com os números ruins, os cortes e a procedência (o domínio veio montado: declarado na
PROCEDENCIA). Gasto: pare se a API passar de US$ 30.
```
