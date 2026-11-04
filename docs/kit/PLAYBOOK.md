# Roteiro da tentativa (kit v5.6) — 100% na nuvem, plano até T+48 (10 min de folga), teto T+58, mirando ≥ 9,0 na nossa régua

Escrito a partir da Getnet v4 (34 min do 1º ao último commit, CI verde; lições em [LICOES_V4.md](LICOES_V4.md)),
da V5 (50,8 min, nota estimada 8,2–8,5, não enviada; erros de nota e de tempo em [POSMORTEM_V5.md](POSMORTEM_V5.md))
e da leitura de 28 soluções públicas do mesmo case ([pesquisa/getnet.md](pesquisa/getnet.md),
[pesquisa/formato_swarm.md](pesquisa/formato_swarm.md)). Cada regra abaixo existe porque a falta dela custou nota
ou tempo. O PC só abre o Chrome: nenhum fork, teste ou Docker roda nele.

Prompt da sessão principal pronto para colar: [V5_PROMPT_M.md](V5_PROMPT_M.md). Prompts das frentes:
[PROMPTS.md](PROMPTS.md). Operação pelo Chrome: [CHROME.md](CHROME.md).

**Três fatos que mudam a estratégia** (pesquisa de 01/11/2026):
1. O avaliador da Régua V4 **não roda nada e não assiste ao vídeo** ("Não executei build nem testes", "Vídeo …
   não assistido"). A nota sai do que está ESCRITO e COMMITADO: respostas reais em `docs/DEMO.md`, números em
   `evals/results/`, prova do relógio em `docs/TIMESHEET.md`.
2. Ele pune **atalho em vez de arquitetura** ("resolvem casos por atalho, em vez de pela arquitetura"), resposta
   em pt para pergunta em en, Support que não lê o dado do cliente, HITL que não volta ao fluxo, memória ausente.
3. Nenhuma nota ≥ 9 na Régua V4 foi feita em 60 min. O 9,5 público (nelsondell) perdeu meio ponto em: escala
   presa ao armazenamento, suíte que precisava de rede para começar, factual sem validação humana.

**O que a V5 ensinou sobre o relógio** (pós-morte §3): a frente K foi o caminho crítico (corpus + gold +
escolha do buscador sob 8 subagentes, integrada só no T+18,9); o buscador foi decidido no T+24,9; o primeiro sinal
ao vivo dos oficiais veio no T+31; ~10 min se perderam ANTES do relógio (add_repo negado, ramo padrão errado, tag que
o proxy não envia). A v5.3 tira tudo isso do relógio: kit já no repositório, buscador já escolhido, fumaça ao vivo no
T+12, cortes escritos e 5 min de folga.

**Regra permanente do dono** ([MELHORIA_CONTINUA.md](MELHORIA_CONTINUA.md)): toda rodada mede com o avaliador,
reforça o que ganhou nota, corrige na raiz o que tirou (pesquisando web, git, benches e feedbacks) e registra
antes → depois. Bateria ou avaliação sem hipótese é dinheiro jogado fora.

---

## 0. Antes do relógio (na véspera ou até T−30 min). Nada disto conta no tempo.

| # | O quê | Como saber que está feito |
|---|---|---|
| A0 | **Repositório da tentativa preparado pela sessão maestra** (pós-morte T1): repositório vazio do desafio, público, com o app do Claude com push; `main` com **1 commit** (`chore: repositório (antes do relógio)`, só um README de uma linha); ramo **`kit-fonte`** com o kit v5.4 inteiro (inclusive `docs/kit/`; origem: ramo `kit-v5.4.0` do repositório do kit); **ramo padrão = `main`** conferido no GitHub (Settings → Branches). A sessão do relógio abre NESTE repositório: nenhum `add_repo` dentro do relógio (V5: add_repo negado). | `git ls-remote --symref origin HEAD` → `refs/heads/main`; `git ls-remote --heads origin kit-fonte` com 1 linha |
| A1 | **Ambiente da nuvem com rede** para o site da empresa e para as APIs de dado ao vivo (`olinda.bcb.gov.br`, `geocoding-api.open-meteo.com`, `api.open-meteo.com` e `wttr.in`, a segunda fonte de clima). Menu do ambiente → *Network access*: Full, ou os domínios em *Allowed domains*. | `python scripts/cloud_probe.py --site <url>` sem FALTA (as APIs também como `--site`: a sonda só testa o que recebe) |
| A2 | **Chave do LLM do app** nas variáveis do ambiente: `APP_ANTHROPIC_API_KEY` (nunca no chat). Opcional: juiz de outra família (`JUDGE_PROVIDER=openai_compat`, `JUDGE_BASE_URL`, `JUDGE_MODEL`, `JUDGE_API_KEY`). | sonda: "chave do LLM do app" OK |
| A3 | **Buscador decidido pelo kit** (pós-morte N3/T2): o padrão do kit (`data/retriever.json` / padrões de `config.py`, frente K53) vale no relógio; a K **não** roda `--choose-retriever` para trocar de buscador. A latência foi medida no ensaio com a máquina parada. Modo domínio montado (§2.4): o relógio MEDE no domínio com `--keep-default` (`python -m evals.run_evals --choose-retriever --fast --keep-default --apply`), que grava a tabela medida e mantém o padrão como escolha (04/11: com a bateria ao vivo junto, o p95 do cross deu 2,4 s e o `--apply` puro trocaria para dense+windows) | `kit-fonte` traz o padrão; `data/retriever.json` medido no relógio |
| A4 | **Sonda verde** numa sessão da nuvem no repositório da tentativa: `python scripts/cloud_probe.py --site <url>`. Além da rede e da chave, ela faz `docker pull` da base fixada por digest no Dockerfile (429 = FALTA: puxe antes no script do ambiente ou use espelho com o mesmo digest; sem docker: o `check --docker` roda só no CI), um push de teste num ramo descartável (apagado em seguida) e confere os modelos do buscador no cache | `AMBIENTE PRONTO` (só com tudo verde) |
| A5 | **PC só com o Chrome** (sem app desktop, sem Docker Desktop). | > 3 GB livres |
| A6 | **Orçamento, em DUAS contas separadas.** (1) Plano/créditos do Claude (claude.ai → Configurações → Uso; a tela do dono é em **reais**, limite R$ 130 na v4). (2) **API da Anthropic** (console.anthropic.com → Limits), que paga o eval ao vivo e o juiz (≈ US$ 11 no roteiro do §2). Confira o limite da API ANTES: no ensaio da v5 ele acabou no meio ("regain access on 2026-12-01") e nenhuma rodada ao vivo rodou depois. | os dois limites conferidos; sonda da API sem `aborted_quota` |
| A7 | **Página de conferência testada antes do relógio** (`scripts/label_page.py`, publicada pela maestra com o Artifact tool): dono e 2ª pessoa abrem o link e marcam 2–3 respostas de teste; a maestra lê a coleção `rotulos` e vê as duas fichas. 2ª pessoa ensaia com uma conversa em INGLÊS (V5: kappa 0,054 porque ela leu "idioma" como "devia ser em português"). | duas fichas em `rotulos` |
| A7b | **Dono e 2ª pessoa com as janelas do §2.3 reservadas**: J1 (T+16→T+26, os dois, cada um sozinho: 2 exemplos de treino + 10 respostas às cegas; T+26→T+29, os dois juntos: consenso só das divergências) e J2 (T+34→T+41, só o dono, revisão da análise de erros); modo domínio montado (§2.4): J1 T+8→T+20 com 23 situações, consenso T+20→T+23. Sem a 2ª pessoa, o placar mostra "1 rotulador" como abaixo da referência. | combinado, com a hora de Brasília de cada janela |
| A8 | **Limite da API com folga de US$ 30** | sonda da API sem `aborted_quota` |
| A10 | **Dependências instaladas ANTES do relógio** pelo script de configuração do ambiente da nuvem: cole o arquivo `docs/kit/SETUP_AMBIENTE.sh` INTEIRO em menu do ambiente → Edit → *Setup script* (gerado por `scripts/setup_env.py` a partir de `requirements-dev.lock` + `requirements-hybrid.lock`; `tests/test_setup_env.py` confere que bate com os locks). Ele não lê nada do repositório (no repositório da tentativa os locks só existem no `kit-fonte`): leva os 77 pinos dentro de si, instala com **uv** no python do sistema e baixa os modelos do buscador padrão. Medido numa máquina limpa (venv vazio, cache do uv vazio): 4,9 s, 319 MB. Ensaio 13: o pip de ~530 pacotes passou de 10 min; ensaio 14: a linha tinha só fastembed/onnxruntime/numpy/tokenizers e o pré-voo reprovou. Nunca pip. Sem o script (ensaio geral da rodada 15, máquina nova): o relógio instala o lock com uv em 11 s e os modelos em 53 s, em 2º plano; o script só adianta esse minuto. O pacote do app entra no T+0, depois do scaffold (`uv pip install --system -q --no-deps -e .`, < 1 s). Atenção numa sessão aberta no repositório do kit: o hook de início cria `.venv` (só o lock dev) e o põe à frente do PATH; aí o `python` não vê o que o `--system` instalou: use `/usr/local/bin/python`. A maestra confere com a sessão do relógio aberta: `python -c "import fastembed, onnxruntime, fastapi, pytest"` em segundos | import em segundos |
| A9 | **Modo rápido ligado em TODA sessão** (ordem do dono, 04/11: ensaio e produção; o relógio, as baterias, a maestra e as réguas). Quem liga é o dono, no app, em cada sessão: menu do modelo → modo rápido, ou `/fast` na caixa da sessão. Arquivo não liga: numa sessão da nuvem o Claude Code roda sem terminal e só aceita o modo rápido vindo do app (`fastMode` no `settings.json`, do usuário ou do projeto, cai em `sdk_opt_in_required`). Custa cerca do dobro por token e sai dos créditos de uso do plano (conta 1 do A6). Ensaio de 04/11: a sessão do relógio criada pela maestra (`create_session`) já nasceu com o modo rápido que o app ligou na maestra. A maestra confere cada sessão nova e, se estiver desligado, manda ao dono o link com o lembrete. Ensaio geral da rodada 15 (04/11): a sessão criada pela maestra NASCEU SEM o modo rápido (`flag_settings` ausente; no ensaio 14 tinha nascido com ele): não conte com a herança; logo depois do `create_session`, mande ao dono o link da sessão e peça o `/fast`. | `get_session` da sessão → `external_metadata.flag_settings.fastMode: true` |

---

## 1. Quem faz o quê (orquestração da v4, que funcionou)

A sessão principal (**M**, o regente) faz SPEC, integração, medição e README. As frentes são **subagentes da
própria M** (ferramenta Agent, em segundo plano), cada uma num `git worktree` com branch `fork/<x>`; a M integra
localmente com `scripts/check_ownership.py <x> --base main` e merge `--no-ff`. Não há sessão-irmã nem prompt
colado pelo dono (na v3, sessão criada por outra sessão recusou tarefa; na v4, subagentes não recusaram). A
**maestra** (sessão fora do relógio, §2.2) prepara o repositório, publica as páginas humanas e escreve docs em
ramos `fix/<x>`; ela nunca commita em `main`.

| Frente | Dono de (OWNERSHIP.json) | Entrega | Pronto (v4 → alvo v5.3) |
|---|---|---|---|
| **H** autor cego | `evals/heldout_blind.jsonl` (devolve o JSONL; a M commita sem ler) | 2 × 40 casos que só viram enunciado + SPEC | T+3 → T+12 |
| **R** roteamento | `domain/challenge/flow.py`, prompts router/supervisor/geral, `data/intent_examples.d/r.jsonl`, testes do router/supervisor, **`needs` do domínio** | intent ≥ 90% nos splits do gate; `standalone` no router.md; casos `dependent` | T+4 → T+16 |
| **K** conhecimento | `data/sources.json`, `data/knowledge/**`, glossário, `evals/retrieval.d/**` (com o gold essencial), prompt faq, `docs/SOURCES.md` | corpus por entidade oficial, gold essencial às cegas, Recall@3/MRR do buscador do kit, **`official_check` verde** | T+6 → **T+12** (V5: T+18,9) |
| **T** ferramentas | `domain/challenge/tools.py`, `data/crm/**`, prompt records, `tests/test_tools.py` | leituras + escritas com confirmação; tool devolve totais e datas calculadas (o LLM não soma) | T+4 → T+16 |
| **Q** qualidade e segurança | `evals/cases.d/**`, calibração do juiz, testes HTTP e de guardrail, EVAL_STRATEGY, THREAT_MODEL (com OWASP Agentic ASI01–10) | official-var, memory ≥ 15 (com `standalone`), guardrail ≥ 30, hard, `dependent` | T+6 → T+18 |
| **D** documentação | ARCHITECTURE, OBSERVABILITY, RUNBOOK, ADRs (inclui "considerado e não feito"), PILOT, perguntas da entrevista no README | docs só com o que o código faz | T+5 → T+15 |

O motor (`src/app/*.py`), scripts, runner do eval e fixtures são **congelados** durante o relógio
(`.claude/hooks/ownership_guard.py` recusa a edição; `check_ownership.py` recusa o merge). Exceção: bug de motor
achado pelo eval ao vivo vira commit da M com teste de regressão e o número no commit (v4: 3 correções assim).

---

## 1.9 Trilho de 60 min (ordem do dono, 03/11): o que encurta o relógio sem perder nota

Medido no ensaio de 03/11 (4 CPUs, 15 GB): bateria integral (12 splits, official/memory repeat 3, juiz no mesmo
processo) em **~17 min** com `LIVE_MAX_CONCURRENT=8`; com o juiz, ~20 min; US$ ~13 de conversa + ~8 de juiz.
1. **Fora do relógio:** `pip install` dos locks e `python scripts/fetch_models.py` no script de configuração do
   ambiente da nuvem (não é código entregue; só cache).
2. **Motor sem mudança no relógio:** só domínio (corpus, casos, tools, prompts, glossário), guiado por
   `docs/kit/DOMINIO_GETNET.md`; o domínio NÃO vem pronto.
3. **Paralelo por subagentes:** K (corpus+gold, `gold_questions` gera e ela revisa), R (prompts/router), T (CRM e
   tools), Q (casos); a M integra.
4. **Uma bateria só (o maior ganho):** antes de disparar, `official_check` verde, `check.py` (oficiais com fato),
   `run_evals --calibrate-rerank-gate --apply` e fumaça dos 10 oficiais (~3 min). Bateria às T+20, código congelado.
5. **Hardware (4 CPUs):** concorrência 8, não 12 (o cross-encoder é CPU: 12 conversas = timeout do faq, visto em
   partial/parallel); no máximo 2 processos pesados juntos (bateria, eval offline, build) — o `live_eval.sh` recusa
   com < 6 GB livres. O juiz pode ter mais linhas (`JUDGE_WORKERS`): é só API.
6. **Durante a bateria:** transcrição HITL (`demo_md.py --transcript`, cliente PEDE o atendente e faz um 2º pedido
   no mesmo turno, para provar o plano seguindo depois da resposta humana; de preferência com o dado que só o
   atendente traz: o cliente não sabe qual maquininha, o atendente diz e o modelo chama o records depois dele,
   `human->records` no trace) e página 1 de rotulagem dos primeiros splits gravados; depois, página 2 com
   `--n 20 --suspects 10 --fresh` (parte sorteada: só ela valida o juiz; cada
   página congela o texto rotulado em `evals/validation/`, que se commita com os rótulos). O split `hitl` entra na
   bateria sozinho (workers ≤ 8) e a vitrine é regravada depois dela. Junto com a rodada 1 (mesmo processo ou em paralelo, dentro do teto): ablação do
   replanejamento nas perguntas reais (braço sem o achado: o modelo não recebe `needs`, sem lembrete;
   `run_evals --live --ablate-replan --mode no_needs --split real --repeat 1
   --max-usd 2`, ~US$ 1,5 para 40 casos; com teto menor ela aborta e não compara) e a página com respostas de
   defeito plantado (`evals.perturb` → `evals.judge --perturbed` → `label_page.py --perturb 15`): sem negativos, o
   juiz não se valida contra pessoas.
6b. **Corpus e buscador (K):** `python -m app.ingest` (~1 min, estático) e `python scripts/ingest_render.py` (~3 min,
   Chromium, só as páginas finas; ids existentes ficam). O buscador é o padrão do kit (A3); medir com
   `--choose-retriever --fast` custa ~7–8 min de CPU com a máquina parada (5 configurações, 2 com cross; a 1ª vez
   vetoriza também as janelas) e só vale fora da bateria. Se `dense` passar `dense+windows` no Recall@5, as janelas
   pioraram a ordem no domínio: `--fast --windows` mede o cross com e sem janelas, ou `RAG_WINDOWS=off`.
7. **Fim automático:** `scripts/final.sh` (FAILURE_MODES, TIMESHEET, README, ENTREGA, check) em ~3 min; antes da
   régua, `python -m evals.judge --check` (resumos do juiz × vereditos × rótulos). A M nunca espera
   parada: tudo pesado em 2º plano rastreado.
Meta: entrega em 45–50 min, folga de 10.

---

## 1.10 Modelo e esforço por tarefa (ordem do dono, 04/11)

| Tarefa | Modelo | Esforço |
|---|---|---|
| Sessão principal (M) e código que mexe na nota: roteamento (R), tools (T), correções de causa, motor | Opus | high na principal; medium nas frentes de código |
| Casos (Q), docs (D), held-out (H1/H2), perguntas reais (P), corpus (K) e os 2 rotuladores cegos do gold | Sonnet | medium |
| Conferência mecânica: rodar `fork_check`, contar, ler log, olhar CI | Haiku, ou comando direto (bash) sem agente | low |

A frente K só EXPORTA o pool do gold; a M (dona única: a maestra só confere, §2.2) dispara os 2 rotuladores cegos (Sonnet) assim que o
pool chega: subagente não cria subagente (rodada 12: a K parou com Recall@3/MRR "não medidos").

---

## 2. Linha do tempo (T = commit `chore: scaffold`; **regra dura: nada depois de T+58**)

**Hora sempre pela máquina, nunca de cabeça** (pós-morte T6: a M informava a hora ~3 min adiantada). O relógio vale
pelo commit de scaffold e pelo último commit (T7); tags são opcionais: crie `clock-start`/`clock-end` **localmente**
(`timesheet.py` e `delivery_message.py` leem as tags locais) e tente o push, mas o proxy da nuvem derruba push de tag,
então nunca espere por ele. Em todo relatório ao dono:

```bash
T0=$(git log --format=%ct --grep='^chore: scaffold' | tail -1)
echo "T+$(( ($(date +%s) - T0) / 60 )) min · $(TZ=America/Sao_Paulo date +%H:%M) Brasília"
```

| Quando | Quem | O quê | Saída verificável |
|---|---|---|---|
| T+0 | M | **scaffold a partir de `kit-fonte`** (comandos no V5_PROMPT_M passo 1: `git archive origin/kit-fonte | tar -x -C .` — o `git checkout origin/kit-fonte -- .` é recusado pela trava do modo auto da nuvem (ensaio 13), procedência para `docs/`, `docs/kit/` fora do índice), (se faltar: `uv pip install --system -r requirements-dev.lock -r requirements-hybrid.lock && uv pip install --system --no-deps -e .` em 2º plano, depois do commit), commit `chore: scaffold from entregar-desafio-cronometrado kit v5.4.0`, push de `main` | 1º commit do relógio |
| T+0 | M (2º plano) | (melhor: `python scripts/fetch_models.py --fast` no script de configuração do ambiente da nuvem, antes do relógio; aí este passo só confere o cache) `python scripts/fetch_models.py --fast > var/fetch_models.log 2>&1 &` (modelos do buscador do kit no cache) e `python scripts/preflight.py > var/preflight.log 2>&1 &` (confere ramo padrão `main` e `kit-fonte` consumido ANTES de mexer em arquivo; depois a suíte) | `MODELOS PRONTOS`, `PRÉ-VOO OK` |
| T+0→**T+4** | M | **SPEC dos oficiais primeiro** (o `evals/cases.jsonl` só depois de `esvaziar evals/cases.jsonl` aparecer no `var/preflight.log`, em segundos: o pré-voo esvazia esse arquivo): os 10 casos `official` literais, cada um com `expect.facts` (regex dos fatos de referência, escritas ANTES do código, COM SINÔNIMOS: o mesmo fato dito de outro jeito também passa — ensaio v5.4: "conta digital/Get Conta" reprovava por a regex só aceitar "conta de pagamento"; no T+15 confira cada regex contra as 3 respostas da fumaça) e `expect.entities` (produtos citados); sonda da API (1 caso, `--max-usd 0.2`); commit do pré-voo e commit `spec: oficiais` | `aborted_quota` = PARE e avise o dono |
| **T+4** | M | worktree + subagente **K** (Sonnet, §1.10): só precisa do enunciado, da URL do site e dos casos oficiais | K no ar |
| T+4→T+8 | M | resto da SPEC (taxonomia, desempates, resposta parcial, `standalone`) + casos: replan ≥ 20, dependent ≥ 10, parallel, approval, hitl (formato no DOMINIO_GETNET; um com `expect.after_human`, §3.x), memory ≥ 15 com `expects_fact` e `standalone` (um entre conversas: `earlier_conversations`), cobrindo os seguimentos que derrubaram a V5 ("e a outra?", "and the other terminal?", "how long has it been down?", "e qual foi o valor dela?": demonstrativo = entidade da última resposta) | commit `spec` |
| **T+8** | M | dispara R, T, Q, D (Opus) e H1, H2, P (Sonnet: escrevem só JSONL) | 7 subagentes |
| T+4→**T+12** | K | ingere (páginas de cada entidade oficial + FAQ), perguntas do gold com `origin` geradas em segundos por `python -m evals.gold_questions` (`page` = FAQ do próprio corpus, `official`/`real` = casos e perguntas reais, 20 `no_source`: a K só revisa, não escreve; no nelsondell a metade das páginas saturou e toda a diferença veio da outra), gold essencial às cegas (2 rotuladores, grupos por fato), placar do caminho do agente (Recall@5, MRR@10, rank do 1º gold, por origem), **≥ 15 perguntas sem fonte** (fora do domínio, `relevant: []`) para a separação com × sem fonte (AUC e gap; nelsondell: 82 × 15) e **`python scripts/official_check.py` verde** e `python -m evals.gold_questions --check` = GOLD OK (≤ 8 min) | `fork k: pronto (… official_check N/N, GOLD OK)` |
| **T+12** | M | merge da K **só com `official_check` verde** (condição de merge); logo depois, em 2º plano, o **eval aquecido**: `python -m evals.run_evals --out var/warm.json > var/warm.log 2>&1 &` e a **imagem aquecida**: `python scripts/check.py --warm-image > var/warm_image.log 2>&1 &` (build frio com o buscador do kit ~4 min: pip + modelos; depois só dados e código, segundos). O eval monta o índice do corpus e grava a medida da busca em `var/retrieval_cache.json`; ensaio v5.4: frio, o eval do T+18 levou 580 s e a medida da busca 91 s em cada chamada) | `main` com corpus, `var/warm.json` |
| T+12→T+15 | M (2º plano) | **fumaça ao vivo** só do official, **com o domínio completo (K, R e T já integrados; nunca com o roteador do exemplo)**, repeat 1 (~US$ 0,3; em 2º plano RASTREADO, nunca esperando em 1º plano: ensaio v5.4 travou a M 9 min num `until`): `LIVE_EVAL_ALLOW_STALE_GATE=1 python -m evals.run_evals --live --split official --repeat 1 --max-usd 0.5` (só a fumaça leva a exceção do gate: ela roda antes dele de propósito; o domínio de exemplo continua recusado); completa → commit `evals/results/live_official.json` (a maestra gera a página dela no T+15) | cada oficial reprovado com a causa (fonte, portão, idioma) |
| T+15→T+18 | M | (em paralelo ao gate) causa de cada oficial reprovado na fumaça corrigida no domínio (corpus, glossário, regra), com teste; `official_check` de novo | commits `fix:` com o caso |
| T+8→**T+18** | R, T, Q, D | commits pequenos por item, `fork_check.py <x>` antes de cada um; M integra cada frente ao ficar pronta; H1+H2 → `evals/heldout_blind.jsonl` e P → `evals/real_questions.jsonl` sem ler | `main` verde |
| T+12 (logo após o merge de K, R e T) | M (2º plano) | **gate offline**: `python -m evals.run_evals --calibrate-gate --apply` e `make eval` em 2º plano, assim que R e T entram. **NUNCA é cortado**: é barato, sem LLM, e o ensaio de 04/11 o cortou e entregou gate vermelho (`passed: false`). O `live_eval` recusa gate vermelho ou velho; a rodada 1 só começa com ele verde. Correção do corpus que a fumaça pedir roda EM PARALELO ao gate (não depois) | `latest.json` `passed: true` |
| T+18→T+19 | M | `python scripts/check.py` e `python scripts/official_check.py` (com o eval aquecido do T+12 e o cache da busca: 2–3 min). `make compare` só se a K pedir, em 2º plano. Gate verde → rodada 1 na hora | commit com o gate |
| **T+19→T+31** | M (2º plano) | **rodada 1, bateria integral num processo só**: `scripts/live_eval.sh --max-usd 20` (todos os splits; official e memory repeat 3, o resto 1; o aviso `Estimativa ao vivo` sai antes do 1º gasto e `AVISO: teto` = suba o teto, não corte split). Até 12 conversas ao mesmo tempo (`LIVE_MAX_CONCURRENT`) e o juiz em 8 linhas paralelas (`JUDGE_WORKERS`), julgando cada split ao terminar. **O juiz roda SEM teto** (ordem do dono, 04/11: "o Juiz não precisa ter teto"); o `--max-usd` vale só para as conversas. A **ablação do replan** nas perguntas reais roda JUNTO com a rodada 1 (mesmo processo ou em paralelo, dentro do teto das conversas). **Antes de lançar, NADA pesado rodando** (eval aquecido, `check.py`, build da imagem: cada um ~3 GB; o `live_eval.sh` recusa com < 6 GB livres). Lance com a ferramenta de 2º plano RASTREADA (Bash `run_in_background`) e espere com Monitor/until: `nohup … &` não acorda a sessão. Split que caiu: rode SÓ ele com o MESMO teto por split | `live_*.json` todos `complete`, `judge.json` |
| **T+30** | M (2º plano) | **vídeo gerado por script** (`make video`) em 2º plano, FORA do caminho crítico: não espera a rodada 2 nem bloqueia nada | MP4 |
| T+31→T+33 | M | `evals.failure_modes` (o `live_eval.sh` já o regera) + reprovações do juiz **caso a caso**: corrigir a CAUSA no domínio (corpus, tool, regra, cartão de capacidades), nunca prompt genérico; teste por correção | commits `fix:` com o caso |
| **T+33→T+40** | M (2º plano) | **rodada 2 só dos splits afetados** (official e memory `--repeat 3`; os outros que caíram, repeat 1; afetado = o pedido ao LLM mudou, §3.x) com o juiz sem teto; antes, `cp judge.json judge_r1.json`; depois `python -m evals.judge_diff evals/results/judge_r1.json evals/results/judge.json` → `docs/JUDGE_DIFF.md` | antes × depois |
| T+38→T+41 | M | **dono único do README**: a M preenche os `{{...}}` (§0 leitura do placar, §5, §7) com os números da rodada 1 já fechados e atualiza com a rodada 2 ao chegar; a maestra NÃO escreve rascunho: só revisa (§2.2) | README sem `{{` |
| T+41→T+44 | M | merge dos ramos `fix/rotulos` e `fix/analise` (e correções `fix/<x>` que a maestra mandar); `scripts/demo_md.py`; `check.py --docker --scale` (imagem base já puxada no pré-voo; o TIMESHEET sai do `final.sh`); `scripts/delivery_message.py --repo <url>`; commit de tudo que não é README | `CHECK VERDE` |
| **T+44** | maestra | **lê o README de `main`** e manda à M as frases sem número ou sem prova (e os caminhos/links que não existem) | lista de correções |
| T+44→T+46 | M | aplica as correções da maestra; `git tag clock-end` (local; push opcional); código novo: NÃO. Commit de código depois do T+44 só com `check.py` verde antes | `CHECK VERDE` |
| **T+46→T+48** | M | `make final` (num ensaio que seguiu depois do relógio: `CLOCK_END=<sha> make final`; README sozinho no último commit + push **com retry**; gera `var/ENTREGA_final.md`). Fix depois do `make final` → `make final` de novo: ele é o último passo de verdade. **O plano termina em T+48** | `fill_readme --check` OK |
| T+48→T+52 | M | CI do último commit no GitHub; vermelho → plano B (§4). O `check` roda em 6 jobs paralelos (`core`, `docker` e o replay das gravações em 4 pedaços de tamanho parecido): em fila ele levou 14,7 min no ensaio 13 e 27 min no 14 (replay 1121 s, gate 273 s, docker ~150 s), e o resultado chegava depois do T+59. O ensaio 14 ficou VERMELHO no commit final por ruído entre máquinas (eval offline do CI 2 casos acima do commitado, com o mesmo código): o limiar do portão agora fica entre duas notas e o check tolera até 2 casos por métrica (`MACHINE_TOL_CASES`). Sinal cedo: a maestra dispara a CI à mão (`workflow_dispatch`, ramo `main`) logo depois do commit do gate (~T+20; montado: ~T+9); esse disparo não é cancelado pelos pushes seguintes (ensaio 14: toda CI antes da final foi cancelada) | Actions verde |
| **T+48→T+58** | — | **folga planejada de 10 min** (a rodada 12 usou 52 min de relógio com 5 de folga e cortou rodada 2, vídeo e ablação): só absorve atraso e o CI; nada novo começa aqui. Código novo só até o T+44 | — |
| **T+58** | — | **nada depois** (o dono fixou 60 min redondos como teto absoluto; o kit para em 58). Mensagem ao dono com o placar inteiro | — |

Orçamento da API (conta separada do plano), medido no ensaio v5.3 (11 splits): fumaça ≈ US$ 0,5; rodada 1 ≈ 11 de
conversa + 6 de juiz; rodada 2 ≈ 5 + 2 → **≈ US$ 25; deixe pelo menos US$ 40 livres**. Teto curto aborta split e
split abortado não vai ao juiz (ensaio v5.3: teto 4 para ~5,5 cortou o official em 24 de 30).

**Relatório ao dono a cada ~5 min**: a linha do comando acima + marco atual + adiantado/atrasado em minutos +
próximo passo. Uma linha. O dono acompanha pelo celular.

### 2.1 Cortes decididos antes (se X não fechar até T+Y, segue sem X e declara)

Corte não é falha escondida: cada um vira uma linha em README §7 (limitações) com o motivo e o número que faltou.

| Se não fechar até | Então | Declara |
|---|---|---|
| SPEC dos oficiais no **T+5** | K sai com os 10 enunciados oficiais e as entidades; os `facts` chegam no `spec` do T+8 e a K roda o `official_check` de novo | — |
| K com `official_check` verde no **T+15** | merge da K assim mesmo, com os fatos que falham no texto do commit; a M acrescenta a página que falta em `sources.json` até o T+18; ainda vermelho no T+20 → segue | "official-NN: fato fora do top-5" |
| frente R/T/Q/D pronta no **T+18** | integra o que houver | o que ficou de fora |
| gate ≥ 90% no **T+20** | o gate offline NÃO é cortado (barato): se vermelho, corrige-se a causa; só o retune do limiar é proibido; a rodada 1 espera o gate verde (o `live_eval` recusa gate vermelho) | o gate medido |
| rodada 1 completa no **T+33** | usa os splits que terminaram limpos; official ou memory incompleto roda SÓ ele de novo; o resto fica fora | splits fora da rodada 1 |
| J1 (rótulos às cegas) no **T+26** | a página fica aberta até o T+35 e a importação vai para o T+36, sem rodada de consenso; ninguém até o T+35 → segue | "1 rotulador", "sem rodada de consenso" ou "factual sem validação humana" |
| consenso de J1 no **T+29** | publica só a concordância independente (antes); `depois_do_consenso` fica vazio | "sem rodada de consenso" |
| J2 (revisão da análise de erros) no **T+41** | publica o rascunho do LLM como "não revisado", com o nº de linhas revisadas | "análise de erros revisada em N de M linhas" |
| rodada 2 completa no **T+42** | publica só a rodada 1; JUDGE_DIFF "não medido" | "rodada 2 não medida" |
| vídeo (script em 2º plano desde o T+30) no **T+44** | entrega sem vídeo e sem link de vídeo no README (o `check.py` reprova link sem release) | "sem vídeo" |
| `check.py --docker --scale` no **T+45** | `check.py` sem `--docker --scale` | "imagem e escala não reconferidas no relógio" |
| `make final` começado no **T+47** | `make final` com o que houver; nada novo | — |
| CI verde no **T+55** | `git revert` do último commit de código e `make final` de novo (cabe na folga) | o commit revertido |

### 2.2 Sessão maestra (fora do relógio; nunca commita em `main`) — papel ATIVO

Ordem do dono (04/11): a maestra **não espera ser chamada**. Ela monitora minuto a minuto, captura a falha na hora e
já corrige; entra no processo quando precisa e pega tarefas para si para agilizar. Não conta no relógio, não escreve
o código do produto na `main` e entrega por ramos `fix/<x>`, que a M integra com `merge --no-ff` (V5: zero
conflito); correção pequena e pronta pode ir também por `send_message` à M, com o patch.

**Nomes de ramo da maestra (ensaio 13):** `fix/<x>`, nunca `maestra/<x>`; a mensagem do merge também não leva a palavra
"maestra" (`merge fix/rotulos: rótulos humanos`). As avaliações cegas leram "merge maestra" na linha do tempo do README
como jargão de processo e descontaram. O CI de push ignora ramos `maestra/`, `fix/`, `fork/`, `probe/` e
`dependabot/` (ensaio 14); o `main` dispara a CI a cada push: junte commits (`concurrency` cancela o anterior).

**Monitoramento (laço fixo de T+0 a T+58):** a cada 1–2 min, com `Monitor`/laço (nunca parada em 1º plano):
`docs/kit/tools/vigia.sh <clone> <sha do scaffold>` num `Monitor` (NOVO/PULSO/ALERTA, sem LLM) e, a cada pulso,
o que a sessão do relógio executa AGORA: `get_session` (estado, `fastMode`) e `list_events` com
`kinds=["assistant"]`, `limit` 8 (nunca sem filtro: os subagentes enchem o contexto). Espera em 1º plano há mais
de 60 s (um `until`/`sleep` ou um comando longo sem `run_in_background`) → `interrupt_session` e `send_message`
com o próximo passo (ensaio 14: 4 min travada, mensagens paradas na fila, push só no T+38). Compara com os cortes do §2.1; passou do corte → avisa
a M numa linha (`send_message`). Falha vista (CI vermelho, gate vermelho, split abortado, commit que quebra o check,
sessão parada) → a maestra reproduz num worktree próprio, corrige em `fix/<x>` com teste e manda o ramo (ou o
patch) à M, sem esperar pedido.

| Quando | O quê (tarefa FIXA da maestra) | Saída |
|---|---|---|
| T−30 | A0 (repositório, `kit-fonte`, `main` com 1 commit, ramo padrão), A4 (sonda: `cloud_probe.py` só termina em AMBIENTE PRONTO), A7 (página de teste com as duas pessoas); confere `fastMode` da sessão do relógio (A9) | §0 verde |
| T+0→T+58 | laço de monitoramento acima; vigia o CI de cada push relevante e já prepara o fix do job que quebrar | aviso em ≤ 2 min |
| T+8→T+16 | **confere o gold**: quando o pool chega em `main` (a K só EXPORTA), a M dispara os 2 rotuladores cegos (Sonnet) na hora — dona única; a maestra NUNCA dispara em paralelo (ensaio de 04/11: rotuladores duplicados, custo à toa). Pool em `main` há 3 min sem rotuladores → avisa a M numa linha | gold rotulado até o T+16 |
| **T+12→T+15** | **revisa a fumaça dos oficiais** (`live_official.json`) e aponta a causa de cada reprovado (fonte, portão, idioma, busca) à M, antes de ela abrir o trace | causa por caso |
| **T+15** (modo domínio montado: **~T+7**, assim que a fumaça julgada chega ao `main`, §2.4) | `git pull`; `python scripts/label_page.py --n 20 --splits official,memory --perturb 3 --require-judged --raters <dono>,<2ª pessoa>` (a página serve 2 pessoas: no ensaio 14, Matheus e Bianca, cada um sozinho; os dois nomes entram no `--raters`); publica `var/rotulagem.html` com o Artifact tool e as `capabilities` que o script imprime; manda o link ao dono | link da página de rotulagem (J1) |
| **T+26** (montado: **T+20**, divergências) | lê a coleção `rotulos` (ArtifactData) para `var/rotulos.json`; `python -m evals.label --import-page var/rotulos.json`, `--report` e `--divergences`; manda aos dois `evals/human_divergences.md` | `evals/human_labels.*.csv`; concordância, kappa e AC1 (antes) |
| **T+29** (montado: **T+23**, consenso) | recebe dos dois rotuladores as linhas `id=pass\|fail\|diverge` do consenso; `python -m evals.label --consensus <txt>` e `--report`; commit em `fix/rotulos` | `human_review.json` com antes e depois do consenso |
| **~T+20** (commit do gate no `main`; montado: ~T+9) | **sinal cedo da CI**: dispara a CI à mão no `main` (tool `actions_run_trigger`, `run_workflow`, `workflow_id` = `ci.yml`, `ref` = `main`); esse disparo tem grupo próprio e não é cancelado pelos pushes seguintes. Em ~8 min: as 6 partes do `check` (core, docker, replay 1–4) e os outros 4 jobs; vermelho → causa e correção à M antes do T+40 | CI completa de um commit do relógio |
| **T+31** | página de revisão da análise de erros da rodada 1 (frente E53); link ao dono | link da página de revisão (J2) |
| **T+35** | lê as revisões do dono; grava o resultado para o `FAILURE_MODES.md`; commit em `fix/analise` | ramo `fix/analise` |
| T+38 | avisa a M de que `fix/rotulos` e `fix/analise` estão prontos para o merge | — |
| **T+44** | **revisa o README de `main`** (um dono só: o README é da M; a maestra NÃO rascunha texto nem abre ramo `fix/readme` ou `fix/adr`): aponta cada frase sem número ou sem prova, caminho citado que não existe, link de vídeo sem vídeo, palavra de processo; a M corrige | lista de correções |
| T+48→T+58 | vigia o CI do último commit; vermelho → prepara o `revert` + `make final` e manda à M | CI verde |

### 2.2b Duas maestras (ordem do dono, 04/11, para a rodada 15)

- **Maestra A (operação):** a ÚNICA voz com a sessão do relógio e com o dono; roda o vigia, destrava, publica as
  páginas humanas, integra os ramos `fix/*` e cuida da CI. É a sessão que já acompanha o kit.
- **Maestra B (qualidade):** criada pela Maestra A no T−30 com [V5_PROMPT_MAESTRA_B.md](V5_PROMPT_MAESTRA_B.md);
  trabalha num clone próprio, com 4 tarefas de hora marcada (diagnóstico da fumaça e página de rotulagem de respostas
  julgadas no ~T+7, quando a fumaça julgada chega ao `main`, texto do README no T+30, ensaio do make final no T+38) e entrega só em ramos `fix/*`
  e mensagens à Maestra A. Nunca fala com a sessão do relógio (ensaio 14: mensagens de mais de uma origem empilharam
  na fila de uma sessão travada).
- **Sem orquestrador acima das duas:** o dono decide cortes e o "vai ou não vai"; o vigia automático faz a parte de
  alarme sem custo de LLM. Cada camada a mais acrescenta um salto de mensagem entre a ordem e a execução.
- **Entrelaçadas (diretriz do dono, 04/11 à tarde; vale no ensaio geral e na produção).** Na preparação do kit da
  rodada 15, a A seguiu adiante (lançou sessão, integrou) enquanto a B ainda processava, e os PRs dela ficaram
  vermelhos sem leitura. Desde então:
  1. enquanto a B processa, a A não age no mesmo alvo (kit, repo da tentativa, sessão do relógio): não commita, não
     integra, não lança sessão; lê o estado e espera o `PRONTO` dela;
  2. cada arquivo ou ramo tem uma dona combinada antes (a B: seus `fix/*`/`b/*`; a A: `main` via relógio, integração,
     CLAUDE.md, este §2.2b e as Regras do prompt da B); nenhuma mexe no da outra;
  3. mensagem nova para a B vai na fila (`send_message` com `priority: "later"`), sem interromper o passo dela;
  4. todo achado da B é lido e levado em conta antes do próximo passo; nada vai ao ensaio final nem à produção sem a
     revisão dela;
  5. no relógio, só a A fala com a sessão da tentativa e integra depois do `PRONTO`. Exceção que só faz sentido no
     relógio: bloqueio dele (espera em 1º plano, pré-voo reprovado, CI vermelha, split abortado). A A age na hora,
     porque o relógio não espera, e avisa a B logo depois.

### 2.3 Tempo do dono dentro do relógio (≈ 20 min, em três janelas)

| Janela | Quem | O quê | Duração |
|---|---|---|---|
| antes (T−30) | dono + 2ª pessoa | página de teste (A7), 2–3 respostas cada | 5 min |
| **J1: T+16→T+26** | dono **e** 2ª pessoa, cada um sozinho | **2 exemplos de treino** (a página mostra o gabarito e o porquê; não contam) e **10 respostas às cegas** na página de rotulagem (sem a nota do juiz; ninguém vê a marcação do outro); modo domínio montado (§2.4): 23 situações (20 reais julgadas + 3 adulteradas), T+8→T+20 | ~9 min cada (montado: ~12 min) |
| **J1b: T+26→T+29** | dono **e** 2ª pessoa, juntos (ligação ou mesma sala) | **rodada de consenso**: leem só as situações em que marcaram diferente (`human_divergences.md`, ~20 s cada) e dizem o rótulo combinado, ou `diverge` se continuarem discordando; o dono manda as linhas à maestra. A concordância independente (antes) não muda; o README publica as duas; modo montado: T+20→T+23 | ~3 min |
| **J2: T+34→T+41** | só o dono | **revisão da análise de erros** da rodada 1: confirma ou corrige o passa/falha que o LLM rascunhou em cada linha (o nº de edições é publicado) | ~8 min |
| fora das janelas | dono | lê o relatório de 5 em 5 min; não precisa responder | — |
| T+58 | dono | recebe o placar inteiro e decide se envia (abaixo de 9,5 não se envia) | — |


### 2.4 Modo domínio montado (ordem do dono, 04/11; ensaio 14)

O kit-fonte leva o domínio da tentativa anterior em `docs/kit/dominio/` (gravado por `docs/kit/tools/dominio.py save`).
No T+0 a M o aplica (`python3 docs/kit/tools/dominio.py mount`) e roda o pré-voo com `--mounted`, que não recria o
domínio do exemplo. Vem montado só o que é FONTE (corpus, CRM, casos, gold, prompts, regras, ferramentas, testes e
docs do domínio); o que tem de ser medido ou escrito de novo no relógio NÃO vem: held-out (H1+H2), perguntas reais (P),
rótulos humanos, resultados, gravações, DEMO, FAILURE_MODES, TIMESHEET, RESULTS. A PROCEDENCIA declara de onde o domínio
veio (condição do dono). Sem a SPEC, a K, a R/T/Q/D e o gold: o relógio sobra para medir, corrigir e remedir, com 10+ min
de folga. O modo antigo (domínio escrito no relógio, §2) continua valendo e o prompt dele é o `V5_PROMPT_M.md`; o do
modo montado é o `V5_PROMPT_M_MONTADO.md`.

| Quando | Quem | O quê | Saída |
|---|---|---|---|
| T+0 | M | `git fetch origin kit-fonte && git archive origin/kit-fonte \| tar -x -C .` (nunca `git checkout … -- .`: a trava recusa); `python3 scripts/kit_history.py`; `docs/kit` fora do índice; `python3 docs/kit/tools/dominio.py mount`; commit `chore: scaffold …` e push com retry. **Sem pip antes do commit** (A10: já pré-instalado; se faltar, em 2º plano e sozinho) | 1º commit do relógio |
| T+0→T+5 (2º plano) | M | `python scripts/preflight.py --mounted`; eval aquecido; imagem aquecida; H1+H2 (2 autores cegos Sonnet, 40 cada) e P (40 perguntas reais com link) escritos DE NOVO; **fumaça JULGADA** `LIVE_EVAL_ALLOW_STALE_GATE=1 python -m evals.run_evals --live --splits official,memory --repeat 1 --max-usd 1.5` e logo `LLM_PROVIDER=anthropic python -m evals.judge evals/results/live_official.json evals/results/live_memory.json --max-usd 1.2` (~26 casos; ~US$ 2 com o juiz; sem o `LLM_PROVIDER=anthropic` o juiz recusa), commitada NA HORA (a página de rotulagem precisa de ≥ 20 respostas reais com veredito do juiz) | `PRÉ-VOO OK`, `live_official.json`, `live_memory.json` e `judge.json` no `main` |
| **T+7** | maestra | quando a fumaça JULGADA chega em `main` (official + memory repeat 1 e `evals.judge` sobre elas): publica a página de rotulagem (`--n 20 --splits official,memory --perturb 3 --require-judged --raters Matheus,Bianca`: 20 reais, todas com veredito do juiz sobre o mesmo texto, + 3 adulteradas cegas, 23 itens; a página grava o tempo de cada item e congela texto e veredito, que continuam valendo depois da rodada 1) e manda o link aos dois. Sem veredito o script recusa (sai com 2): ensaio 14, página da fumaça sem juiz, juiz × humano "validado 0" | link J1 |
| T+5→T+9 | M (2º plano) | calibração do portão (commit) → buscador medido no domínio `python -m evals.run_evals --choose-retriever --fast --keep-default --apply` (~2 min, offline; commit do `data/retriever.json`, que o README cita) → gate offline `make eval` verde (nunca cortado) | `data/retriever.json`, `latest.json passed: true` |
| **T+8→T+20** | Matheus e Bianca, cada um sozinho | 2 exemplos de treino + 23 situações às cegas (J1, ~30 s cada) | rótulos na página |
| **T+9→T+21** (depois do gate verde: o ao vivo recusa gate velho) | M (2º plano) | **rodada 1 integral com juiz** (`scripts/live_eval.sh --max-usd 20`; official e memory repeat 3) + ablação do replan junto | `live_*.json` complete, `judge.json` |
| **T+20** | maestra | importa a página e roda `python -m evals.label --import-page`, `--report`, `--divergences`; manda as divergências aos dois. O `--report` dá, por pessoa, quantas das 3 adulteradas ela reprovou (`adulteradas.humano`) e o tempo de leitura (`tempo_por_rotulador`: mediana e marcações abaixo de 20 s); juiz sobre as adulteradas: `LLM_PROVIDER=anthropic python -m evals.judge --validation --max-usd 0.3` (julga os textos congelados da página) | concordância/kappa (antes), adulteradas achadas, tempo |
| **T+20→T+23** | os dois juntos | J1b, consenso só das divergências; a maestra grava com `--consensus` (ramo `fix/rotulos`) | `human_review.json` antes e depois |
| T+21→T+24 | M | falhas caso a caso (`evals.failure_modes`, `reason` do juiz) e correção da CAUSA no domínio, com teste | commits `fix:` com o caso |
| T+24→T+32 | M (2º plano) | **rodada 2 dos splits afetados** (§3.x) com juiz; `cp judge.json judge_r1.json` antes; `python -m evals.judge_diff` ANTES × DEPOIS no código final | `docs/JUDGE_DIFF.md` |
| T+30 | M (2º plano) | `make video`, fora do caminho crítico | MP4 |
| T+32→T+37 | M | README/docs: os textos do domínio já vêm prontos, só se revê o que cita número; `python scripts/check.py --docker --scale` só com docker local (a nuvem não tem: a prova são as 6 partes do `check` na CI do commit final, `core`, `docker` e o replay em 4 pedaços, citadas no README, não um corte); `python scripts/delivery_message.py --repo <url>` | `CHECK VERDE` |
| **T+37** | maestra | revisa o README de `main` (frase sem número/prova, caminho que não existe, jargão de processo) | lista de correções |
| T+38→T+40 | M | correções; `make final` (README sozinho no último commit, push com retry) | `fill_readme --check` OK |
| T+40→T+50 | M / maestra | CI do último commit; vermelho → `revert` do último commit de código e `make final` de novo | Actions verde |
| **T+50→T+58** | — | **folga de 8 min** (plano de 10+ min de folga em relação ao teto de 60); nada novo começa | — |

Regras do modo: (1) eval, gate e check SEMPRE em 2º plano rastreado; (2) a fumaça é commitada ANTES de qualquer outro
passo (ensaio 13: um `make eval` em 1º plano antes do commit atrasou a página do dono ~4 min); (3) um split por vez
nas frentes (nada de laço encadeado dos 4 splits junto com eval aquecido); (4) junte commits: cada push dispara a CI;
(5) ramos auxiliares da maestra `fix/<x>`, merge sem a palavra "maestra"; (6) cortes, em ordem: rodada 2 → vídeo →
consenso (declarados em README §7, como no §2.1; docker/scale não é corte, a CI do commit final prova); gate offline e juiz nunca são cortados.

---

## 3. Regras para todas as frentes e para a M

1. **Motor congelado** durante o relógio (exceção: bug do ao vivo, com teste e número no commit).
2. **Gate nunca desce.** Abaixo de 90%, corrige-se o domínio pela matriz de falhas.
3. **Held-out cego.** O teste de contaminação reprova frase copiada para regra ou exemplo.
4. **Número só de arquivo commitado.** README só por `fill_readme.py`; o check reprova divergência.
5. **README sozinho no último commit** (`make final`). Qualquer commit depois exige rodar de novo (v4: CI
   vermelha 2 vezes por isso).
6. **Nada de exemplo no produto**: nem `example.com` em caso de teste (use domínio fictício próprio).
7. **Comentário e commit só com número medido.**
8. **Atalho não:** nenhuma resposta escrita no código para um cenário; o Support sempre lê o dado do cliente;
   respostas no idioma da pergunta.
9. **Processos:** nunca `pkill -f "<texto do próprio comando>"` (mata o shell); mate por PID:
   `ps -eo pid,args | grep "[r]un_evals"`. Espera longa: Monitor com `until`, nunca `sleep` encadeado.
10. **Rodada ao vivo só vale se terminou limpa.** `status: complete` e `llm_errors` ~0. `degraded` (chamadas perdidas),
    `aborted_quota` (limite da API) e `aborted_*` vão para `.degraded.json`/`.aborted_*.json` e NUNCA substituem um
    resultado completo; não commite nem cite número de rodada assim (a v5 descartou uma por isso).
    **Juiz interrompido** (`judge.json` com `aborted_quota`/`aborted_llm_error`): o parcial fica gravado; com o limite
    da API liberado, `LLM_PROVIDER=anthropic python -m evals.judge <os mesmos live_*.json> --resume --max-usd <teto>` julga só o que faltou (ensaio v5.1: o
    limite acabou no 99º julgamento e, antes desta regra, tudo se perdia).
11. **Mudou o motor, meça num domínio real antes de declarar melhoria.** 487 testes verdes não pegaram 3 regressões
    que o ensaio sobre a v4 achou em 1 hora (`ENSAIO_V5.md`). Use `docs/kit/ENSAIO_V5.md` como roteiro.
12. **venv certa:** o `check.py` recusa se o pacote `app` vier de outro repo (`pip install -e .` no repo atual).
13. **Fato oficial garantido antes do ao vivo** (pós-morte N1). Cada caso oficial traz `expect.facts` (regex sem
    caixa que casa a resposta E o trecho da fonte: número, nome, alternância pt|en, nunca a frase inteira) e
    `expect.entities`. `python scripts/official_check.py` reprova entidade sem trecho ingerido e fato fora do top-5
    do buscador ativo; roda na K antes do merge, na M no T+18 e no `check.py` (gancho da frente E53). Vermelho se corrige no CORPUS (página que falta,
    tabela inteira, glossário), nunca afrouxando a regex depois de ver a busca.
14. **Hora pela máquina e relógio pelo commit** (T6/T7): toda hora citada sai do comando do §2; tags só locais.

---

### 3.x Conferências que as rodadas 11 e 12 acrescentaram (antes da régua)

- `AUTH_SECRET` com 32+ bytes (RFC 7518 §3.2; abaixo disso o PyJWT avisa e `APP_ENV=production` recusa); o `.env`
  de produção leva `OPERATOR_KEYS` (`python -m app.auth operator-key <nome>`) e `METRICS_TOKEN`.
- Depois de `--choose-retriever --apply`: `scripts/fill_readme.py` (o item Retrieval do README é gerado) e
  `pytest tests/test_supply_chain.py` (o `mem_limit` do overlay cabe no buscador escolhido).
- Antes da bateria: `pytest tests/test_router_contamination.py` com o domínio (regra de prompt sem frase de caso).
- Depois do `--import` do gold essencial: conferir `no_agreement` e `back_to_drafts` em
  `evals/essential/report.json`.
- Rejulgamento só com `python -m evals.judge --rejudge-dated` (só pela data); `python -m evals.judge --check` antes
  da régua; `evals/validation/*.json` commitado junto com os rótulos.
- (rodada 12) `APP_ENV=production` recusa `AUTH_MODE=demo`: o `docker-compose.demo.yml` serve só para demonstrar o
  payload literal. Segredo de compose vem do ambiente (`${X:?motivo}`) e o script que sobe gera o valor
  (`tests/test_no_literal_secrets.py`).
- (rodada 12) Comentário de código e prompt sem id de caso: escreva a regra com a medida ("medido ao vivo: ...");
  `tests/test_code_cites_no_eval_case.py` reprova `official-NN` e qualquer id do eval em `src/`, inclusive no domínio.
  Nem menção a quem avalia ("régua") em código, prompt, script ou teste: `tests/test_r12_no_grader_talk.py` varre
  `src/`, `evals/`, `scripts/`, `tests/` e `ops/`; nos docs que o avaliador lê vale o mesmo, sem teste.
- (rodada 12) Caso de HITL em que o plano segue depois do humano: `expect.after_human` (agentes que rodam no turno
  DEPOIS da resposta do atendente); a resposta dele traz o dado que o passo seguinte usa (ex.: o id da venda).
- (rodada 12) Caso de memória entre conversas: `earlier_conversations` (conversas anteriores do mesmo `user_id`,
  cada uma aberta do zero; o turno avaliado vem numa conversa nova e só sabe delas pelo perfil de longo prazo).
- (rodada 12) Mudou contrato, prompt ou cartão (inclusive `LABELS`, descrição ou schema de tool do domínio): regrave
  os splits que passam pelo supervisor e pelos agentes antes de medir. A chave da gravação é o hash do pedido (papel,
  modelo, system, mensagens, tools): o replay acusa "pedido não gravado" e o `check.py` só avisa "regravar", sem
  reprovar. O cache de prompt (`LLM_PROMPT_CACHE`) não muda a chave. Na v5.5.3 mudaram os pedidos do faq, do
  records, do supervisor e do agente geral (cartão, contratos, tools de câmbio e clima, achado no tool_result) e a
  moldura da memória: gravação de antes dela não vale.

## 4. Planos B (o que não é corte de tempo; os cortes estão no §2.1)

| Se… | Então |
|---|---|
| `preflight.py` reprova o repositório (ramo padrão ≠ `main` ou `kit-fonte` ausente/não consumido) | PARE antes da SPEC e avise a maestra numa linha: ela corrige no GitHub; o relógio só conta a partir do scaffold certo |
| API com limite atingido no T+0 | parar: sem LLM o sistema roda no determinístico e o gate semântico não passa; remarcar |
| fumaça do T+12 com oficial em "sem fonte" | `official_check` verde e o ao vivo recusa → é o portão (calibre com pares pt/en, N2), não o corpus; `official_check` vermelho → corpus |
| split ao vivo `aborted_max_usd` | rodar SÓ ele de novo: `run_evals --live --split <s> --max-usd 2 --repeat 3` |
| APIs de clima/câmbio bloqueadas | `LIVE_DATA=off`: as tools `currency_rate` e `weather_forecast` saem do pedido e fica a busca web; declarar `unsupported_numbers` como limite (gravado assim, o replay do CI, com o padrão `on`, avisa "regravar" nos splits com turno `general`: declare junto) |
| modelo do buscador do kit não baixou (`fetch_models` falhou) | `official_check` reprova "buscador caiu"; rode `fetch_models` de novo; no T+15 ainda sem modelo → `RETRIEVER=bm25` declarado e `official_check` nele |
| CI vermelho no T+53 | `git revert` do último commit de código, `make final` de novo (cabe na folga) |
| proxy recusa o push de tag | ignore: tags são locais (T7); o relógio é o commit de scaffold |

---

## 5. O que cada critério da Régua V4 exige (nomes e pesos oficiais) e onde fica a prova

| Critério (peso) | Evidência escrita no repositório | Frente |
|---|---|---|
| Business & Challenge Fit (8%) | `docs/DEMO.md` com as respostas REAIS dos 10 cenários; Support lendo o dado do cliente; `docs/PILOT.md` (shadow → assistido → autônomo); clima/câmbio de API oficial com data | M, D |
| Agentic Reasoning & Orchestration (15%) — inclui o Router | supervisor que observa e replaneja por falha E por achado (todo `needs` das tools vai ao LLM como informação; lembrete só no achado que a regra do domínio liga à pergunta; a tabela insere offline); câmbio e clima por tool que o modelo escolhe (`currency_rate`, `weather_forecast`); split `dependent`; ablação por conclusão (`--mode no_needs`); orçamento por turno (`budget_exhausted`); matriz de confusão do router | R, M |
| Context, Knowledge & RAG (10%) | trechos literais com URL/data/SHA e contexto de seção; Recall@k por trecho e por página; gold por regra; `--compare-retrievers`; portão calibrado (`--apply`) | K |
| Tool & Action Engineering (10%) | JSON Schema estrito, identidade fora do schema, escrita com confirmação e quatro olhos; detector de ação alegada sem execução | T |
| Security & Identity (13%) | JWT, rate limit, guardrails além de regex, PII mascarada; OWASP Agentic ASI01–10 com teste por linha; LGPD (`DELETE /me/conversations/{id}`, retenção) | Q, M |
| Memory, State & Resilience (8%) | split `memory` ao vivo, com caso entre conversas (`earlier_conversations`: perfil de longo prazo feito do livro de fatos); pergunta autônoma (`search_query`); volume persistente; réplica cai e a conversa segue | R, Q |
| Human Oversight & Risk Management (7%) | fila persistida, operador responde e o PLANO retoma no mesmo turno (a resposta volta ao supervisor LLM como passo `human`; caso com `expect.after_human`); risco alto aprovado só com chave pessoal; caso só fecha com prova; ataque não abre caso | T, Q |
| Evaluation & Quality Engineering (14%) | gate no CI + **replay da gravação ao vivo** no CI; pass^3; juiz com canários (e de outra família se houver chave); **validação humana** (`human_review.json`); `FAILURE_MODES.md` | Q, M |
| Observability, Reliability & Cost (6%) | trace_id, `/metrics`, `/ready`, custo por turno resolvido e por intenção (com escrita e leitura do cache de prompt), dashboard Grafana provisionado | M |
| Production Engineering (5%) | CI verde com rede cortada, SBOM e trivy, actions por SHA, overlay endurecido (limites pelo buscador medido; produção não sobe sem `OPERATOR_KEYS` e `METRICS_TOKEN` nem com `AUTH_MODE=demo`), 2 réplicas | M |
| Engineering Judgment (4%) | ADRs com o número que decidiu (inclui "considerado e não feito"); "Perguntas da entrevista, respondidas"; limitações com números; `docs/TIMESHEET.md` | D, M |

Gates da V4 (feedback público): **Critical Security**, **Challenge Fit** ("o núcleo foi implementado no próprio
código"), **Evidence** ("logs de execução real commitados"), **Semantic Quality** ("não comprovado" quando não há
medição de qualidade das respostas). O kit v5 tem um artefato para cada um.

---

## 6. Depois do último commit

Nada no repositório do desafio. Balanço e lições no repositório do kit.

### Senhas de teste do login (kit v5.4)

`POST /auth/login` (usuário + senha → o mesmo JWT do `/chat`) usa só hashes em `var/credentials.json`, fora do git.
Os usuários de teste saem do domínio (`users()` do domínio, se existir; senão os `customers`/`owner` dos registros do
CRM fictício da frente T). Cada ambiente semeia as suas: `python -m app.auth seed-passwords` (na imagem:
`docker compose exec api python -m app.auth seed-passwords`) imprime usuário e senha uma vez e anota em
`var/demo_passwords.txt`. No relógio: depois do merge da T, a M roda o seed uma vez para a demo e o vídeo; o README já
traz o passo "Entrar" para o avaliador semear no clone dele. O token por CLI (`docker compose exec -T api python -m app.auth <usuário>`, de dentro do container: o segredo do host é outro) fica só
como atalho de teste.

### 3.y Roteiro da rodada 13 (lições do ensaio de 60 min, 04/11)

- **Push com retry:** "fatal error in commit_refs" passou na nova tentativa. Todo push do relógio usa o laço de retry
  (3 tentativas, espera crescente); o `make final`/`scripts/final.sh` hoje faz um `git push` simples (confira: se não
  houver retry, é defeito do script, da frente B) e o PLAYBOOK manda repetir à mão até confirmar com `git ls-remote`.
- **Regras da frente de casos (Q):** o gabarito nunca contradiz a SPEC: pedido de registro de OUTRO cliente = "não
  encontrado" pela tool (não `blocked`); aprovação sem humano ("aprove o estorno sem humano") = ação pendente (não
  `blocked`). Exemplos de intenção (`data/intent_examples*.jsonl`) nunca são escritos a partir dos casos; a linha
  offline do guardrail é só informativa (o gate do guardrail é o ao vivo).
- **K parte da lista de entidades dos oficiais** e garante a FAQ de cada uma com o fato: `official_check` exige, por
  entidade, um trecho que a cita e traz um dos `expect.facts` (ensaio: FAQs da Get Smart, Get Conta e Pix faltavam e só
  a fumaça ao vivo do T+20 mostrou).
- **Um dono só dos textos do README:** a sessão do relógio preenche; a maestra só revisa no T+44 (§2.2).
- **Juiz sem teto** (ordem do dono): o `--max-usd` vale só para as conversas.
- **Release do kit com domínio montado:** antes de marcar o kit, a suíte inteira roda também numa cópia do kit
  (`git archive`) com o `src/app/domain/challenge` e os `data/`/`evals/` do último ensaio por cima. Rodada 13: achou
  assim um teste que só passava sem domínio (o CI do relógio ficaria vermelho, como os 2 defeitos do ensaio de 04/11).
- **Pré-voo barra antes do T0:** `cloud_probe.py` (docker pull da base, push de teste, modelos no cache).
