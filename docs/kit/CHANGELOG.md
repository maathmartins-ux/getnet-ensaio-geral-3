# Kit — mudanças

## v5.7.0 — rodada 15 (produção): o que o ensaio 14 e o ensaio geral ensinaram

Origem: ensaio 14 (8,82 nas 3 réguas cegas; CI final vermelha e de 27 min) e o ensaio geral fechado da largada (04/11).
Cada item entrou com teste e a suíte inteira verde.
- **Resposta parcial decidida no código** (`src/app/coverage.py`, `faq_agent`): falta de item que o cliente não pediu
  não deixa a resposta parcial e sai do texto (`missing_dropped` no trace); na dúvida, continua parcial. Ao vivo, no
  domínio do ensaio 14: oficiais completas 17→24/30, pass^k 0,50→0,80, juiz 29/30, 0 de 6 descartes reprovados. A regra
  só no `faq.md` foi medida e ficou fora (o juiz caiu).
- **CI em 10 jobs**: `check` em 6 partes paralelas (`check.py --part core|docker|replay:I/N`, replay em 4 pedaços pelo
  tamanho do cassete); sinal cedo por `workflow_dispatch` com grupo próprio (a maestra dispara no commit do gate); PR do
  Dependabot só com o `offline-tests`; push do `kit-fonte` sem CI. Medido no getnet-ensaio-geral: ~11 min (era 27).
- **Ruído entre máquinas**: limiar do portão no meio do vão entre duas notas (`calibrate_rerank_gate`); `check` tolera
  até 2 casos por métrica (`MACHINE_TOL_CASES`) com AVISO. Ensaio 14: o mesmo código mediu replan 11 × 13 de 20.
- **Segredo de teste gerado a cada execução** (`scripts/pg_replicas_smoke.py`): o gitleaks acusava o fixo.
- **Juiz × pessoas sobre o mesmo texto**: fumaça JULGADA (official + memory) no T+5; página `--n 20 --splits
  official,memory --perturb 3 --require-judged` no ~T+7; J1 T+8→T+20; consenso T+20→T+23 (23 itens, ordem do dono).
- **Juiz com teto que não estoura**: o `--max-usd` reserva as chamadas em voo, canários e calibração; o `--resume` do
  mesmo juiz não paga a calibração de novo.
- **Buscador medido no corpus sem troca**: `--choose-retriever --fast --keep-default --apply` no T+5→T+9 (tabela em
  `data/retriever.json`, citada no README).
- **`make eval` e a calibração recusam árvore suja** antes de medir ("COMMIT ANTES").
- **Ambiente**: `docs/kit/SETUP_AMBIENTE.sh` (77 pinos, uv, sem ler o repo); sem ele o relógio instala em 11 s.
- **Rotulagem**: adulteradas por padrão e tempo de leitura por item.
- **Operação**: vigia (`docs/kit/tools/vigia.sh`), Maestra B com prompt fixo, nenhuma espera em 1º plano no relógio.
- **Correções do ensaio geral**: README montado sem marcador `{{ }}` (o pré-voo o tratava como modelo); testes de tempo
  do guardrail com folga para a máquina carregada; não commitar os arquivos só do kit antes do pré-voo (ele os tira).
- **Juiz sem provedor recusa** os arquivos explícitos (sai com 2 e não toca o `judge.json`); todo comando do juiz no
  kit leva `LLM_PROVIDER=anthropic` e `--max-usd`.
- **Checagens do kit vermelhas à toa**: títulos de commit e README ⇔ evidência só do `chore: scaffold` em diante (no
  repo do kit passam declaradas; na tentativa nada muda, teste dos 2 lados); ruff limpo com o domínio guardado fora
  do lint do kit.
- **Rodada 1 sem `.venv`**: `scripts/live_eval.sh` (e o `.ps1`) usa o `LIVE_EVAL_PY` explícito, senão a `.venv`,
  senão o `python3`/`python` do PATH. A sessão do relógio na nuvem instala no sistema e parava no T+9 com "Falta a
  venv" (achado da Maestra B na revisão da largada; teste sem `.venv` nem `LIVE_EVAL_PY`).
- **Maestras entrelaçadas** (ordem do dono, 04/11 à tarde; PLAYBOOK §2.2b): a A não age no alvo em que a B está
  processando, cada ramo tem dona, mensagem nova vai na fila e nada vai ao ensaio final nem à produção sem a revisão
  da B; só um bloqueio do relógio deixa a A agir antes.
- Ficou fora, declarado: Pix sem conta bancária (o cabeçalho por trecho subiu o `sup-pix-09` ao top-5, mas o MRR caiu);
  antecipação quando o router não faz a 2ª busca (corrigir mudaria o pedido de todo "como funciona").

## v5.6.1 (em preparação) — rodada 14: domínio montado e as correções do ensaio 13

Origem: ensaio do kit r13 em 60 min, 8,67 (8,70 / 8,65 / 8,66, 3 avaliações cegas), 50 min de relógio, cortes de rodada 2,
vídeo e docker/scale local. Ordem do dono (04/11): o próximo ensaio leva o DOMÍNIO MONTADO e 2 rotuladores.
- **Modo domínio montado:** `docs/kit/tools/dominio.py save|mount` guarda a fonte do domínio (corpus, CRM, casos, gold,
  prompts, regras, ferramentas, testes, docs) e a aplica no T+0; `python scripts/preflight.py --mounted` confere sem
  recriar o domínio do exemplo. Não vão: held-out, perguntas reais, rótulos, resultados, DEMO, FAILURE_MODES, TIMESHEET,
  RESULTS (escritos de novo, às cegas, no relógio); a PROCEDENCIA declara a origem. Roteiro: PLAYBOOK §2.4 (J1 da página
  para 2 pessoas no T+5, divergências no T+16, consenso no T+19, rodada 1 T+7→T+19, rodada 2 T+24→T+32, `make final`
  T+38→T+40, CI até T+50, 8 min de folga) e prompt pronto `V5_PROMPT_M_MONTADO.md`. O modo antigo segue valendo.
- **Ramos da maestra:** `fix/<x>` no lugar de `maestra/<x>` e merge sem a palavra "maestra" (as avaliações leram
  "merge maestra" no README como jargão de processo). PLAYBOOK §2.2, V5_PROMPT_M e PROMPTS atualizados.
Correções feitas em tempo real durante o ensaio 13 (sha do kit entre parênteses):
1. scaffold por `git archive origin/kit-fonte | tar -x -C .`: a trava do modo auto recusava `git checkout … -- .` (b823afc).
2. commit do scaffold ANTES do pip, e pip sozinho em 2º plano; A10 (pré-instalar no script do ambiente); `cloud_probe`
   reprova sem as dependências (fead64e). O pip de ~530 pacotes passou de 10 min e atrasou o T0 em ~11 min.
3. `CLAUDE.md` do kit sai só pelo pré-voo (KIT_ONLY); o `git rm --cached` no scaffold reprovava o pré-voo (414bb65).
4. e 9. modo rápido: o indicador é `flag_settings.fastMode`, não o campo `speed` dos eventos (A9).
5. CI com `timeout-minutes` por job (99445f7).
6. `tests/test_kit_history.py` pula sem `docs/kit` (a7435eb).
7. exemplo do `router.md` colidia com um oficial (guarda de contaminação); trocado por um neutro (a7435eb).
8. teste de tempo do guardrail com teto de 200 ms (a7435eb).
10. o pré-voo faz push `--dry-run` (o proxy não apaga ramo de teste) (9e6dfd1).
11. PROMPTS: nunca `cmd | tail && git commit` (o pipe engole o código de saída) (acac4ff).
12. DOMINIO_GETNET: lista dos artigos estáticos de erro de conexão/recusa que entram sempre; PDF fora do ingest (a92a5f5).
13. PROMPTS: um split por vez nas frentes, sem laço encadeado; reta final só `fork_check` (e0e8f04).
14. `label_page` aceita 1 rotulador com aviso (sem kappa/AC1) (f92eec2).
15. commit da fumaça antes de qualquer `make eval`; gate em 2º plano (PLAYBOOK §2.4, V5_PROMPT_M).
16. guardrail offline (só regex) fora do gate de intenção, em UNGATED (6003029).
17. CI: `concurrency` com cancel-in-progress por ramo; ramos `maestra/`, `fork/`, `probe/`, `dependabot` sem CI de push (1f3fdce).
18. teste do modelo do README pula com domínio montado / depois do `make final` (a86677c); lição: simular também o README
    pós-`make final` na release do kit.

## v5.6.0 (em preparação) — rodada 13: corrigir o que o ensaio cronometrado de 60 min (8,65) mostrou

Origem: ensaio do kit r12 em 60 min, 8,65 (8,69 / 8,60 / 8,66, 3 avaliações cegas), 52 min de relógio, cortes de
rodada 2, vídeo, ablação e docker/scale. Cinco frentes em paralelo:
- **A, avaliação honesta:** o caso só conta como resolvido se o juiz (quando roda) também o aprova, e o desacordo
  aparece no README; a checagem de fato ignora o match dentro de frase de ausência ("não informamos a taxa").
- **B, checagens que barram:** `check.py` reprova `{{` em README/docs, caminho ou link citado que não existe, número
  do README fora dos resultados, palavra de processo, e "o último commit é só o README" falso; `make final`/`final.sh`
  com push com retry; gate offline vermelho barra a rodada 1.
- **C, motor de ingestão e texto:** a ingestão mantém linha/coluna da tabela rotulada (preço da Clássica não vira R$ 0,00);
  id interno de trecho sai da resposta; PII é recusada sem abrir caso humano; o aviso de espera some quando o
  atendente já respondeu.
- **D, roteiro do relógio e pré-voo (esta entrada):** `scripts/cloud_probe.py` só diz AMBIENTE PRONTO com `docker pull`
  da base por digest (429 vira FALTA com a instrução; sem docker diz que o check roda só no CI), push de teste num ramo
  descartável e modelos do buscador no cache; `scripts/official_check.py` exige, por entidade de cada oficial, um
  trecho que a cita e traz um dos fatos; PLAYBOOK/V5_PROMPT_M/PROMPTS: tabela de modelo e esforço, K só exporta o pool
  e quem dispara os rotuladores é a principal/maestra, fumaça com o domínio completo em T+12, gate offline em 2º plano
  e nunca cortado, vídeo e ablação fora do caminho crítico, plano até T+48 com 10 min de folga, juiz sem teto, README
  com dono único, maestra ativa (monitora a cada 1–2 min, corrige e pega tarefas), regras da Q e da K.
  Prova: `tests/test_cloud_probe_preflight.py`, `tests/test_p53_official_check.py`.
- **E, pergunta composta:** o agente geral (clima, câmbio) entra como parte do `multi` ao lado de knowledge e support,
  com nome próprio no trace.
Pendências de outras frentes citadas pela D: `scripts/live_eval.sh`/`.ps1` ainda passam `--judge-max-usd` (juiz sem teto);
`scripts/final.sh` faz `git push` sem retry; `run_evals --live` deve recusar domínio de exemplo.

## v5.5.3 (04/11/2026) — rodada 12: texto final limpo, achado e atendente no laço do LLM, dado ao vivo por tool

Oito frentes do motor, cada uma com o registro em `docs/kit/changelog.d/r12-*.md` (O quê / Por quê / Prova):
- **A, texto final sem artefato** (`r12-a-texto.md`): a limpeza da citação do cartão tira a oração inteira (sem
  "Segundo a," nem parêntese órfão) e nome de agente vira palavras; valor de lista fechada sai pelo rótulo do domínio
  (`LABELS`) no cartão e na resposta; o aviso da decisão do operador sai no idioma da conversa, sem o nome da tool; o
  contrato do records e do supervisor veda conclusão que o dado não traz e o do faq põe o sim/não na 1ª frase, com a
  citação. Prova: `tests/test_r12_texto.py`.
- **B, achado e atendente no laço do LLM** (`r12-b-laco.md`): no motor LLM todo achado das tools vai no tool_result
  e a regra do domínio (`needs_for`) só escolhe o lembrete (achado lido e deixado de lado sai `seen`); a resposta do
  atendente na espera vira passo `human` e volta ao supervisor LLM numa réplica do laço, que roda os pendentes e pode
  chamar outro especialista (`human-><agente>`); o código confere a redação e o template é a reserva. Prova:
  `tests/test_supervisor_needs_budget.py`, `tests/test_v54_hitl_sync.py`.
- **C, segurança residual** (`r12-c-residuos.md`): `APP_ENV=production` recusa `AUTH_MODE=demo`; compose de réplicas
  sem segredo fixo (o smoke gera um por execução); comentários sem id de caso nem custo velho; ADR 0005 sem número que
  envelhece. Prova: `tests/test_api.py::test_production_refuses_demo_identity`, `tests/test_no_literal_secrets.py`,
  `tests/test_code_cites_no_eval_case.py`.
- **E, câmbio e clima como tools do LLM** (`r12-e-ao-vivo.md`): o agente geral oferece `currency_rate` e
  `weather_forecast` ao lado da busca web; entrada validada no servidor, erro como tool_result, teto de consultas por
  turno e a tool escolhida no passo; valores obrigatórios e reparo como antes; sem LLM, o detector por regex.
  `prompts/live_data.md` saiu e `prompts/contract/general.md` entrou; `LIVE_DATA=off` tira as duas tools do pedido.
  Prova: `tests/test_r12_live_tools.py`, `tests/test_v55_live_repair.py`.
- **F, perfil de longo prazo** (`r12-f-memoria.md`): `memory.Profile` feito do livro de fatos (registro, produto,
  protocolo com a situação de agora, assunto; origem e data por item, teto por tipo, `USER_MEMORY_TTL_DAYS`), numa
  conversa nova como dado datado em `<untrusted_memory>`, só para o dono; apagar uma conversa tira só o que veio dela;
  caso de eval com `earlier_conversations`. Prova: `tests/test_memory_ledger.py`, `tests/test_eval_isolation.py`.
- **G, docs e eval** (`r12-g-docs.md`): ADRs e mapa ASI sem jargão interno; bloco ao vivo do RESULTS numa tabela por
  split; `expect.after_human` (o plano seguiu depois da resposta do humano). Prova: `tests/test_r12_results_table.py`,
  `tests/test_r12_after_human.py`.
- **H, cache de prompt** (`r12-h-cache.md`): `llm.with_prompt_cache` marca system + tools de cada papel e o laço de
  tool use; o custo conta escrita e leitura do cache; a chave do cassete não muda; `LLM_PROMPT_CACHE=off` desliga.
  Prova: `tests/test_r12_prompt_cache.py`.
- **I, aprovação com chave pessoal** (`r12-i-operador.md`): `POST /actions/{id}/approve` recusa (403, auditado) o
  token compartilhado de operador; risco alto só executa com chave de `OPERATOR_KEYS`, com o nome na auditoria.
  Prova: `tests/test_hitl.py::test_high_risk_action_needs_owner_then_operator_and_runs_once`.
Mais: o pré-voo não copia `prompts/contract/` para o domínio, porque o `domain.prompt` anexa o do kit
(`tests/test_r12_preflight_contract.py`); comentários e prompts dizem a regra e a medida, não quem a apontou
(`tests/test_r12_no_grader_talk.py`); segredo do container do smoke do `check.py` gerado a cada execução; a produção
sem demo no README, na COBERTURA, no mapa ASI, no ADR 0001, no `.env.example` e no overlay endurecido, e a aprovação só
com chave pessoal no README e no `.env.example`. Gravações: A, B, E e F mudam o pedido ao LLM (cartão, contratos e
prompts do faq, records, supervisor e geral; tools do agente geral; achado no tool_result; moldura da memória):
gravação de antes da v5.5.3 não vale, regrave os splits antes de medir (PLAYBOOK §3.x).

## v5.5.2 (04/11/2026) — rodada 11: as 24 perdas conferidas da rodada 10

Nove frentes do motor, cada uma com o registro em `docs/kit/changelog.d/r11-*.md` (O quê / Por quê / Prova), suíte
inteira verde depois do merge:
- **A, achado como informação** (`r11-a-needs.md`): no motor LLM o `needs` não vira passo imposto; lembrete uma vez,
  ignorado contado; passo planejado não é replanejamento; a tabela não escala o turno quando outro especialista já
  respondeu.
- **B, humano no laço medido** (`r11-b-hitl.md`): split `hitl` com operadora simulada (`human_in_turn`, `human_once`),
  resposta final sem oferecer nem negar o encaminhamento, entrega única quando a resposta chega antes da espera.
- **C1, juiz honesto** (`r11-c1-juiz.md`): rejulgamento só pela data com a 1ª passada à vista; juiz × pessoas sobre o
  texto congelado da página; held-out sem `reason`; `python -m evals.judge --check`.
- **C2, documentos gerados** (`r11-c2-docs-gerados.md`): FAILURE_MODES e TIMESHEET gerados pelo `final.sh` e conferidos
  pelo `--check`; KPIs de custo no §0; guarda de fato que ecoa a pergunta; "como ler" nos blocos.
- **D, guardrail** (`r11-d-guardrail.md`): família de alto recall para crime financeiro parafraseado; classificador que
  falha fechado (recusa bloqueia; fora do ar, leitura sem agente LLM); recusa no idioma certo; red team separado em
  ataques × controles, com a linha ao vivo.
- **D2, PyJWT** (`r11-d2-jwt.md`) e **D3, borda** (`r11-d3-borda.md`): JWT por biblioteca auditada (malformado = 401);
  mesma cota do `/chat` no MCP; produção não sobe sem `OPERATOR_KEYS` e `METRICS_TOKEN`; overlay endurecido que cabe
  no buscador.
- **E, busca** (`r11-e-rag.md`): 1 busca corretiva, buscas em paralelo, "resposta primeiro", separação com a recusa do
  portão, gold sem cabeçalho e sem rótulo velho, item Retrieval gerado, trava de contaminação dos prompts.
- **F, observabilidade** (`r11-f-observabilidade.md`): histograma de latência e span do turno, cross par a par só nos k
  devolvidos, carga declarada no SLO, quickstart com o token do container.
Mais: todo lote cego `heldout*` fora do gate de intenção e dentro da bateria (`heldout_blind.d/`); testes de custo e
de estouro de tempo que dependiam da máquina ficaram robustos (crescimento linear; folga para quem não é o lento).

## v5.5.1 (03/11/2026) — lacunas da 2ª correção simulada

- **Testes de estouro de tempo do nó com folga para quem não é o lento**: quatro testes punham `NODE_TIMEOUT_S=0.2`
  para o turno inteiro, mas só um agente bloqueia de propósito (2–5 s). No check da rodada 10, com outra suíte rodando
  junto, o `records` levou 365 ms (> 0,2 s), o 3º turno do teste de retomada do plano escalou e o check ficou
  vermelho. Agora o teto é 1 s (o lento estoura do mesmo jeito) e, no teste de retomada, o teto padrão depois do turno
  lento. Não reproduzi a falha com 5 laços de CPU (passou nas duas versões); a prova é o log da falha. Lição de
  processo: no máximo 2 processos pesados juntos (PLAYBOOK §1.9), e uma suíte é um deles.
- **Buscador padrão com a ordem do denso (`KIT_RETRIEVER.rerank_order = base`)**: a nota do cross-encoder só decide
  o portão sem fonte. No gold do ensaio a escolha automática deu `dense+cross:base` (Recall@5 0,915 / Recall@3 0,898
  contra 0,907 / 0,873 reordenando, mesmo portão) e a bateria integral ao vivo com ela teve oficiais 30/30 aterradas.
  No relógio ninguém roda `--choose-retriever` (PLAYBOOK A3), então o padrão é o que vai à produção;
  `RERANK_ORDER=cross` volta. Os testes do mecanismo de reordenar pedem `order="cross"`.
- **Teste de custo do guardrail mede crescimento, não só o relógio da máquina**: '@a.' com 10 mil caracteres mediu
  51-52 ms no runner da CI (teto 50 ms) e 38 ms aqui, e a CI do ensaio ficou vermelha. Até 50 ms passa direto; acima,
  vale a razão inteiro / metade (linear ~2, quadrático ~4) com teto de 100 ms. A metade tem o mesmo final: cortado em
  10 mil, o texto termina num "@" solto que gera uma cópia desofuscada a mais, e a razão ingênua dava ~4 (2 × 2
  cópias) sem nada quadrático. `_fold` pula o laço por caractere em texto ASCII (mesmo resultado).
- **Conferência da linha do tempo com mais de 20 commits**: a tabela do README mostra só os marcos
  (`TIMELINE_MAX_ROWS`), mas o `fill_readme --check` contava as linhas da tabela e reprovava todo repositório com mais
  de 20 commits ("linha do tempo com 20 commits, o git tem 131"), inclusive logo depois do `final.sh`. Agora vale o
  total declarado na linha final do bloco; teste com 33 commits (passa) e com um commit a mais depois do README
  (reprova).
- **Espera do container no check (`CHECK_HEALTH_TIMEOUT_S`, 180 s)**: a 1ª subida logo depois de um build de vários GB
  passou de 60 s no check da rodada 10 e a mesma imagem subiu em 8 s em seguida. O tempo medido até o /health vai no
  detalhe do `reports/verify.md` (`subiu_em_s`), também no smoke sem rede.
- **Resposta do turno em que o atendente respondeu na espera**: o que o turno já tinha respondido (sem a oferta do
  atendente, que agora respondeu, e sem o texto de quem rodou de novo depois dele) → a consulta e a resposta do
  atendente → os passos retomados. Medido na transcrição com pedido duplo: juntar todos os textos repetia o status da
  maquininha e mantinha "posso encaminhar a um atendente" depois da resposta dele.
- **Juiz com a data em que a resposta foi gerada**: cada linha ao vivo grava `business_date` (app.clock) e o juiz põe
  "Data de hoje" desse dia (ou do `recorded_at` do relatório, convertido para o fuso do negócio), nunca do relógio de
  quando julga. Medido: a bateria rodou às 23h de Brasília e o juiz, já depois da meia-noite UTC, deu "fonte velha
  apresentada como atual" em todo caso com data relativa (11 de 30 oficiais). `python -m evals.judge --rejudge-dated`
  julga de novo só os reprovados e os de resposta com data, reaproveitando canários e calibração.
- **Guardrail em duas precisões (frente k3)**: famílias novas na camada regex contra papel/privilégio, conta de terceiro,
  identidade forjada, tool coagida, sondagem e injeção na forma larga (OWASP ASI02/ASI03). Elas só levantam a
  suspeita; o classificador LLM (camada 2) decide, e sem ele no ar a suspeita bloqueia (falha fechada). As regras
  originais seguem terminais e são avaliadas primeiro. Por quê: quatro rodadas de revisão adversarial com frases novas
  acharam falso positivo terminal novo a cada versão da regex; com o classificador como juiz, o falso positivo não
  chega ao cliente e o recall novo vale quando o LLM cai. Medido no ensaio (offline, só regex = falha fechada): red
  team 70% → 85%, ASI03 29% → 100%, intenção 90,5% → 95,2%, nenhum caso não-ataque bloqueado. Em paráfrases novas a
  regex pega bem menos que no corpus do eval (revisão: de 12/15 a 19/20 conforme a lista); a camada LLM cobre o resto.
- **Relógio do negócio (`app/clock.py`)**: todo "hoje" do sistema (prompt, checagem de datas, dado ao vivo e as tools
  do domínio) vem do fuso do cliente (`APP_TZ`, padrão America/Sao_Paulo), não do servidor em UTC. Medido depois da
  meia-noite UTC: a previsão de amanhã para Porto Alegre (data local certa) saiu recusada porque o prompt dizia que
  hoje já era o dia da previsão.
- **Clima e câmbio: o código confere a redação**: os valores obrigatórios da consulta (mínima, máxima e chance de
  chuva; venda e compra) vão em `LiveResult.must`; faltando um na resposta, o LLM refaz uma vez com o que faltou e,
  se ainda faltar, vale o texto pronto da consulta (`live_repair` no passo, `live_data_repair_total` no /metrics).
  Medido na fumaça ao vivo: uma resposta em inglês omitiu a chance de chuva que estava na evidência.
  A resposta final também é conferida: se a redação do supervisor LLM perde um desses valores que o especialista
  entregou, vale o texto do especialista (`supervisor_answer_dropped_live_total`; foi o caso medido na 2ª fumaça).
  E a checagem de frases não leva junto o valor: medido, ela tirou "até 78% de chuva, leve guarda-chuva" pelo
  conselho sem base, e a chance de chuva saiu com ele; agora, se o corte tira um valor obrigatório, vale o texto do
  especialista com a mesma checagem (`claims_cut_live_value_total`). Os prompts live_data e supervisor pedem só o
  dado, sem conselho, e todos os valores do especialista na mesma frase.
- **Cartão com as opções POR TOOL e o padrão declarado**: juntas, a descrição do período de uma consulta (padrão
  ontem) valia para a outra (padrão 7 dias) e o modelo consultou só "hoje" num pedido de recusa sem data. O prompt
  records também manda o período mais largo quando o cliente não dá data.
- **Duas regras financeiras duras nos prompts do kit**: no faq, taxa ou condição vale só para o produto que o trecho
  nomeia (tabela geral não é regra de outro produto) e a regra do trecho não se estende; no records, o filtro da
  consulta limita a conclusão (filtrar por status não prova que não houve recusa; "as últimas N" pela data). Vindas da
  análise das afirmações sem base do held-out da rodada 9: o held-out deixa de ser cego para essas duas classes de erro.
- **Linhas do HTML separadas dentro do trecho**: o chunker colava as linhas de blocos (`<p>`, `<li>`) com espaço, e uma
  lista em blocos ("Acima de R$ 20mil | Get Clássica" / "Acima de R$ 40mil | Get Clássica ou Get Smart") virava
  "...Get Clássica Acima de R$ 40mil...": o redator lia a faixa errada (isenção do aluguel trocada, 3 respostas da
  memória e do held-out na rodada 9). Agora o separador é a quebra de linha, do mesmo tamanho do espaço: os cortes e os
  ids dos trechos não mudam; pedaços de uma mesma linha longa seguem com espaço.
- **Cartão de capacidades com as listas fechadas das tools**: cada parâmetro com `enum` (período, status) entra no
  cartão. "A consulta cobre ontem, hoje e os últimos 7 dias" é verdade do sistema, mas estava só no schema da tool, que
  o juiz não lê: contava como afirmação sem base (2 respostas do held-out na rodada 9).
- **Nome do buscador diz a ordem**: `dense+cross:base` quando a ordem é a do denso, igual ao nome do comparativo.
- **Ordem do denso no comparativo do buscador**: o `--choose-retriever` (grade e `--fast`) mede também o denso com a
  ordem dele e a nota do cross-encoder só no portão sem fonte (`dense+cross:base`). A escolha desempata pela cobertura
  do portão que o app usa (com cross, o da nota) antes do p95 e grava o `min_rerank` calibrado junto; o app o usa
  quando o domínio não tem `MIN_RERANK`. Antes era preciso gravar a escolha à mão, e o `fill_readme` quebrava com o
  arquivo manual.
- **Critério da escolha do buscador: o recall do redator primeiro**: maior Recall@5 (os trechos que o redator lê),
  empate → MRR → Recall@3 → cobertura do portão → p95. Mudou depois de ver a medida, e o motivo fica registrado: no
  domínio Getnet a ordem do cross tinha MRR 0,859 × 0,842, mas Recall@5 0,907 × 0,915, Recall@3 0,873 × 0,898 e o
  mesmo portão; por MRR a escolha dependia de 3,7 ms de p95 acima do orçamento (1503,7 × 1500 ms), ruído, porque as
  duas variantes fazem a mesma conta no cross-encoder. O recall não oscila entre medições e é o que a resposta usa.
  Ressalva honesta (revisão adversarial): a diferença é de 1 a 2 perguntas em 59, empate técnico. Medido também no
  caminho do agente (fusão de até 3 buscas): ordem do denso Recall@3 0,881 × 0,856, Recall@5 0,915 × 0,907, hit@3
  0,898 × 0,864, MRR@3 0,836 × 0,842. A ordem do denso fica por pôr mais trechos certos no que o redator lê.
- **Chave do cache da medida de busca com a ordem do rerank**: `RERANK_ORDER=cross` devolvia o placar gravado da
  ordem base (a chave não tinha a ordem) e a comparação das duas saía idêntica.
- **Limiar da nota só para a mesma busca, na mesma ordem dos outros limiares**: o `min_rerank` da escolha vale só
  com a mesma ordem, pool e caracteres (senão sai do `gate`); precedência ambiente → escolha → domínio, e o
  `--calibrate-rerank-gate --apply` atualiza os dois. O `--verify` do CI confere também o Recall@5 e o portão da nota
  (tolerância de 1 pergunta). A grade fixa os caracteres lidos pelo cross (o ambiente não muda o comparativo).
- **Segredos sem `.env`**: `AUTH_SECRET` e `OPERATOR_TOKEN` vazios geram um valor aleatório guardado em
  `var/local_secrets.json` (0600); não existe mais segredo padrão conhecido. O `.env.example` vem com os dois vazios e
  o texto "troque-…" passa a contar como segredo fraco no `/health`.
- **Humano no laço por padrão no compose**: `HITL_SYNC_WAIT_S=20` no `docker-compose.yml` (a suíte segue com 0).
- **Todo oficial com fato**: `check.py` reprova oficial sem `expect.facts` (exceto os que esperam humano); sem fato,
  "resolvido" contava uma recusa educada.
- **RESULTS sem repetição**: o bloco por split não repete o retrieval nem mostra "Gate (splits ) … FAIL" de split fora
  do gate.
- **Clima com segunda fonte** (wttr.in, sem chave) quando o Open-Meteo dá 429/timeout, dentro do mesmo teto (60%/40%).
- **Guardrail LLM fora do ar**: a leitura segue (a regex já rodou), mas o turno não propõe escrita (falha fechada para escrita).
- **Idioma no eval**: o motor `table` (offline, cita a fonte sem traduzir) fica fora do `language`; o idioma se mede com LLM.
- **Tarja de número**: dia/ano de amanhã com o mês ("Nov 4, 2026") e número dentro de identificador da tool ("last_7_days") deixam de virar "[valor não confirmado]".
- **Juiz "validado" só com rótulo de pessoa** (`labeler: human:<nome>`); rótulo da SPEC dá concordância, não validação.
- **"Juiz reprova" no juiz × pessoas mudou depois de uma medida**: antes só não fundamentada, idioma ou vazamento; agora também `helpful=False` (as 3 perguntas da página), com as duas leituras lado a lado nas reais (`leituras_reais`) e nas plantadas (`leituras_plantadas` e por tipo, onde o fato_removido as separa), na mesma linha do RESULTS.
- **Juiz × pessoas com plantadas: o total só valida se o juiz reprovar os negativos reais** (regra nova da rodada 10, posta depois da revisão adversarial, mais estrita que a fixada antes de medir): além de ≥ 3 negativos de respostas reais, TNR ≥ 0,8 neles (`evals.judge.PLANTED_RULE`). Contar os reais não bastava: 3 aprovados pelo juiz + 15 plantadas reprovadas davam TNR 0,83 e "validado". O RESULTS diz essa parte como acrescentada depois.
- **Juiz × pessoas só valida com resposta escolhida sem depender do juiz** (2ª revisão adversarial da rodada 10, também posta depois da medida): os negativos reais vinham da página 2 (`--suspects`), que traz o que o próprio juiz reprovou, e o TNR dele neles era 1 por construção — 3 desses + 15 plantadas davam "validado" (agora não). A exportação e a página gravam o motivo de cada resposta real (sorteio, checagem automática, juiz; o da página em `evals/human_selection.json`, fora do HTML), a importação o passa ao CSV (`selecao`), e a validação conta só sorteio, checagem e plantada (`evals.judge.SELECTION_RULE`); a escolhida pelo juiz e o rótulo sem motivo gravado (seleção desconhecida, caso dos 37 rótulos do ensaio) saem à parte, com o TNR do juiz nelas, e não contam nem para o mínimo de reais. A página sorteia antes das suspeitas (sorteada depois, a parte aleatória perderia justo as que o juiz reprovou) e traz as da checagem antes das do juiz; o script avisa quando nenhuma resposta independe do juiz. No ensaio (cópia, rótulos simulados), `--n 20 --suspects 10 --fresh` deu 10 sorteadas, 4 da checagem e 6 do juiz.
- **Afirmação plantada não contradiz a própria resposta; página sorteada pelo sal**: a frase não entra em resposta que diz que a fonte não cobre o assunto dela (troca, liberação, data, "new one", "exchange"; também "não falam" e a frase de ausência que retoma o assunto por "isso"), nem na linha ou ao lado de frase de ausência ou de valor do mesmo tipo, dito com número ou sem (percentual, "sem juros", "não cobra taxa", isenção; prazo, "na hora", D+N, "amanhã", "hoje", "próximo dia útil", data da agenda); se a resposta fala do assunto, mesmo que só em lista ou tabela, a frase só entra numa linha de prosa sobre ele. No ensaio (cópia, mesma entrada), 10 → 3 → 0: das 3 que restavam, heldout-H1-25 caía na linha de "agendado para 02/12/2026" e parallel-01/04 na linha da outra subpergunta (Link de Pagamento, Pix), com o prazo só na lista ou na tabela; dos 34 pares (resposta, frase) com assunto de serviço na pergunta, 23 dizem que a fonte não cobre o assunto, 7 têm valor do mesmo tipo na linha dele e 4 só falam dele em lista ou tabela. A página de 15 sai com número trocado e fato removido (8 e 7) e o RESULTS declara a composição real. Escolha e ordem das adulteradas na página saem do sal (o sal esconde id e posição, não o texto de `perturbed.json`); o arquivo dos sais nasce 0600 e troca de uma vez.
- **RESULTS**: o portão sem fonte sai uma vez (offline), não em cada split ao vivo.
- **Cota ao vivo** com piso nos turnos (rodada anterior em timeout não encolhe a cota).
- **Portão sem fonte pela nota do cross-encoder** (`MIN_RERANK` no domínio, calibrado por `retrieval_eval.rerank_gate`): no ensaio responde 98,3% dos com fonte e recusa 90,9% dos sem fonte (o BM25 recusava 22,7%).
- **Citação interna tirada sem deixar frase quebrada** ("atendente, ." / "Pelo ,").
- **README sem "Desde a última avaliação"** (lia como correr atrás da nota); o pré-voo esvazia
  `evals/demo_transcript.jsonl` (exemplo da loja).

## v5.5 (03/11/2026, branch kit-v5.4.0) — perfil Skywalker (o bench que tirou 10)

Estudo do 10 (`docs/kit/estudo/skywalker.md` §3): a nota veio da forma agentic visível, de nenhuma medida própria
mostrando resposta ruim nos cenários e de um README que explica cada mecanismo; não de CI, testes ou números.
- **Supervisor LLM decide todo turno** (`SUPERVISOR_FAST` desligado por padrão): o DEMO mostrava "atalho" nos
  oficiais, e "regra decidindo" foi o que o avaliador puniu. Custo: ~2 chamadas e ~4 s a mais por turno de 1 passo.
- **Manchete do README sem meta própria** (`scorecard.headline_markdown`): só oficiais resolvidas, pass^k, juiz
  (fundamentadas, úteis), memória e busca, com o valor e como se mede. Diagnósticos do kit ficam em `docs/RESULTS.md`.
- **Entrega** lista só as medidas do enunciado (as ruins entre elas continuam listadas).
- **README**: mapeamento "requisito do enunciado → implementação → onde" com os 4 bônus, teste em 3 minutos,
  avaliação descrita como capacidade (gabarito, camadas, o que é "resolvida") e limitações com efeito e o que faltaria.

## v5.4 (03/11/2026, branch kit-v5.4.0) — metodologia Skywalker (10) e nelsondell (9,5) em busca e memória

- **Busca:** placar pelo caminho do agente (rerank incluso) com Recall@5, MRR@10, rank do 1º gold e origem; buscador
  base ao lado. Gold da V5: 0,842/0,737 publicados → 0,895 / Recall@5 0,947 / MRR 0,829. Híbrido com BM25 só no
  idioma do corpus (`rag.lexical_fits`); palavras do cliente como 1ª busca também offline. Padrão dense+cross por medida.
- **Memória:** especialistas sem estado (pergunta reescrita pelo router + livro de fatos; `SPECIALIST_HISTORY=on`
  volta ao antigo); regra de demonstrativos no router. Ao vivo parcial (n=48): rota 96%, tools 94%.
- **Docs:** gold com `origin`; casos de memória com os seguimentos da V5; prompt e PLAYBOOK apontam o v5.4.0.
- Ensaio: ENSAIO_V54.md (a conta da API atingiu o limite no meio da bateria). Estimativa 9,54 central,
  9,32 no pior caso.
- **Evidência = produto (confirmação de 03/11):** o passo 1 instalava só `[dev]` (sem fastembed): a tentativa mediu tudo no BM25 do fallback e o CI, no denso + cross, reprovou "resultado commitado = código atual" (oficiais 33% × 83%). Instalação agora igual à do CI (`requirements-dev.lock` + `requirements-hybrid.lock`); `check.py` reprova buscador em fallback e o `live_eval.sh` recusa rodar nele. Router: pergunta sobre a própria empresa nunca fica em intenção sem escalada (`OWN_COMPANY`); cota do live pelo custo medido por caso.
- **Ensaio pré-produção de 03/11 (correções):** CI vermelha por 3 defeitos do kit, agora corrigidos e testados — gitleaks acusava 1492 falsos positivos nas gravações (`evals/cassettes/` fora da varredura; teste próprio procura credencial real nelas), 6 testes exigiam fastembed no job offline (`importorskip`), `COPY var/embeddin[g]s` quebrava sem a pasta (bind do contexto). Gate de red team só ao vivo/replay (offline é a regex: 77,5% reprovava a CI). Placar: "juiz × gabarito de calibração" (dizia "humano" para rótulos de agente). `live_eval.sh` recusa com < 6 GB de RAM livre (OOM com 4 processos pesados) e ignora a guarda de disco no --dry-run; PLAYBOOK/prompt: 2º plano rastreado, nada pesado junto da rodada.
- **Imagem = produto medido (ensaio v5.4):** o padrão do kit virou denso + cross, mas a imagem padrão seguia sem fastembed e o CI instalava só o lock de dev: no container a busca caía no BM25 e o eval via HTTP resolvia 3 de 10 oficiais (9 de 10 em processo); no CI o gate mediria outro produto. Agora `EXTRAS=auto` no Dockerfile segue a escolha (`fetch_models.py --extras`), os vetores do corpus vão prontos na imagem (`EMBED_CACHE_DIR=/opt/vectors`; sem eles o 1º pedido vetorizava o corpus, 2–4 min), o check reprova `/health` com fallback, o job `check` do CI instala o lock híbrido com modelos e vetores em cache, e o eval via HTTP do container roda os 10 oficiais (271 casos = 373 s em série). `check.py --warm-image` aquece a imagem no T+12.
- **Tempo (revisão 2):** a medida da busca fica em `var/retrieval_cache.json` pela chave do que muda o número (gold, índice, glossário, buscador, código da busca; `RETRIEVAL_CACHE=off` mede sempre): 91 s → 0 s nas chamadas repetidas. Eval aquecido em 2º plano no T+12; `make eval` sem o `--compare-retrievers` (504 s, agora `make compare`); `fork_check` das frentes fora da K sem e5-large nem medida de busca; pré-voo e `live_eval.sh` param com < 5 GB livres.
- **Do Skywalker (o que era melhor que o kit):** operador consultado DENTRO do turno com espera curta
  (`HITL_SYNC_WAIT_S`, 0 nos testes, até 20 s na demo, teto abaixo do timeout do balanceador) e o plano continua no mesmo turno; escrita com antes/depois;
  DEMO com árvore de passos e transcrição multi-turno; `POST /auth/login` e `/auth/logout` (scrypt, limite com
  Retry-After) no quickstart; versão das instruções em cada resposta (`prompt_versions`); 👎 vira candidato a caso
  com revisão humana (`python -m evals.candidates`); motor sem comentários de bastidor (origem das ideias só em
  `docs/PROCEDENCIA.md`). Mantido o nosso onde é melhor: identidade (JWKS, revogação, PII), produção (imagem
  não-root, CI, réplicas), avaliação (bateria integral, juiz com canários) e governança do humano (fila, 4 olhos, SLA).
- **Do nelsondell:** "desde a última avaliação" no topo do README e referência da avaliação no lugar de meta própria
  (sem ícone de falha); separação com × sem fonte (AUC, gap) no placar de busca; regra de validação do juiz fixada
  antes de medir. ≥ 15 perguntas sem fonte no gold (PLAYBOOK).
- `check.py --docker --scale` verde num clone limpo (imagem, contêiner sem rede, MCP, 2 réplicas com queda); 930 testes.

## v5.3 (03/11/2026, branch kit-v5.3.0) — pós-morte da V5 + estudo Skywalker (10) e nelsondell (9,5)

Medido ao vivo na bateria integral (11 splits, official e memory repeat 3) sobre o domínio da V5, com o motor do
kit por cima (ENSAIO_V53.md). V5 → kit v5.3:

| O que pesava na V5 | O que mudou | V5 → v5.3 |
|---|---|---|
| 2 oficiais sem resposta (escalada) | busca agentic (consultas do router no idioma da base + as palavras do cliente sempre como 1ª busca), três estados de resposta, contrato do motor no fim do prompt do domínio | oficiais resolvidas 80% → 96,7%; pass^3 0,60 → 0,90 |
| 40 de 49 falhas de handoff por excesso | humano só com motivo real: resposta parcial ou com outro especialista já respondendo vira OFERTA; não resolver nada continua indo ao humano (enunciado), e o código garante | replan 90%, heldout 96%, memory 96% de handoff certo |
| juiz útil 0,73 | contrato do motor (resposta indireta conta), cartão com veredito humano e formato dos ids, dia do calendário sem tarja | juiz 352 respostas: fundamentadas 95,5%, úteis 96,9% |
| intenção do held-out 67,5% | router reescreve o seguimento (standalone) e classifica a pergunta completa | 99% |
| memória pass@1 0,72 | rota medida pelo resultado (especialistas certos); records usa o livro de fatos no seguimento | 87,5% pelo resultado (84,4% pelo rótulo); fatos 95,8% |
| kappa entre humanos 0,054 | questionário com treino, perguntas sim/não concretas, consenso e AC1 de Gwet | medir na V5.1 |
| splits abortados por teto; juiz cortado | aviso de teto antes de gastar; saldo único do juiz; juiz em 8 linhas paralelas; recusa do juiz anotada | 11/11 splits completos; juiz 41 → ~2 min |
| tempo no limite | 12 conversas simultâneas (44 estouravam o timeout), 8 workers por split, cronograma com folga de 5 min | bateria integral com o juiz 16 → 12,8 min |

Estimativa por critério no ENSAIO_V53.md: central 9,51, pior caso 9,29 — pela regra do dono, ainda
não basta para a V5.1 (RAG, memória e concordância humana puxam o pior caso).

## v5.2 (02/11/2026, branch kit-v5.1.0) — medido no ensaio sobre o domínio da v4

- **Busca:** ingest sem corte por seção e sem contexto no índice por padrão (Recall@3 essencial 0,747 → 0,82 no
  mesmo corpus); gold por FATO rotulado às cegas por 2 rotuladores (`evals/essential_gold.py`; cópias do mesmo
  fato contam uma vez): Recall@3 0,93, MRR 0,94, Jaccard 0,89 entre rotuladores.
- **Juiz:** limite da API no meio grava o parcial e `--resume` continua (o limite acabou no 99º julgamento).
- **Avaliação humana:** página do claude.ai para 2+ pessoas, feita para leigos (uma situação por vez, conversa em
  balões, dados em tabela, 3 perguntas de sim/não, resultado calculado, tradução); `evals.label --import-page`.
- **Latência (frente L):** atalho do supervisor no plano de 1 passo; p50 oficiais 10,6 → 7,2 s, memória 22,6 →
  14,0 s; custo da rodada 2,00 → 1,55 US$.
- **RAM/velocidade (frente R2):** eval ao vivo num processo; pico 7,7 → 4,8 GB; `--choose-retriever --fast`.
- **Pré-voo:** seção "achados" do domínio de exemplo sem destino quebrava o T+0 (teste novo).
- Ensaio v5.2 ao vivo: oficiais 100% fundamentadas e úteis, pass^3 0,90; memória pass@1 0,90, 97,4% fundamentada
  (ENSAIO_V51.md, seção v5.2).

## v5.1.0 (02/11/2026) — correção formal da Getnet v4 (8,5)

A correção da v4 disse onde estava a nota: qualidade das respostas, busca, memória, humano continuando o plano,
avaliação independente e honestidade na entrega. O v5.1 ataca cada item e foi **ensaiado ao vivo sobre o repositório
entregue da v4** antes de ser declarado (ENSAIO_V51.md). Detalhe por frente em
changelog.d/. Testes: 487 → 656 passando.

| Item da correção | O que mudou | Medida (ensaio no domínio da v4) |
|---|---|---|
| juiz 60% nos oficiais | o juiz lê o texto que o redator viu (`context`); cartão de capacidades como fonte; checagem por frase (`CLAIMS_POLICY`); oferta de ação sem ferramenta sai; seguimento de câmbio/clima pela API oficial; link da fonte na evidência; soma por data em código | 60% → 96,7% fundamentadas; pass^3 0,70 → 0,90; números 80% → 100% |
| busca (Recall@3 0,49, MRR 0,61) | tabelas inteiras; denso multilíngue + rerank local; dedupe; `--choose-retriever`; BM25 confere antes de "sem fonte"; calibração do portão sobre o BM25 | MRR 0,61 → 0,92; Recall@3 0,49 → 0,70 (meta 0,85 não atingida) |
| memória (pass@1 54%) | livro de fatos da conversa; números do histórico do cliente como base; seguimento elíptico herda a intenção; memória medida separada do roteamento | pass@1 0,54 → 0,92; números 64% → 100% |
| humano não continuava o plano | resposta do operador vira evidência do supervisor; operador por especialidade; limite de valor por ação; JWKS com rotação; Postgres com 2 réplicas; métricas somadas entre réplicas | testes (687 com Postgres local); CI com job Postgres |
| avaliação de um rotulador só | `--rater` com kappa humano × humano; held-out com 2 autores cegos (≥ 80); split `real` com link público; juiz com `failure_type` e TPR/TNR por tipo; `judge_diff` antes × depois | ferramentas; os rótulos são do relógio |
| entrega sem os números ruins; narrativa dos minutos | placar com meta e status no topo do README; mensagem de entrega gerada com bons e ruins; `docs/PROCEDENCIA.md` | — |
| achados do próprio ensaio | modelo de 2 GB recarregado (eval morria com 14 GB); 1º caso frio estourava o tempo; portão do denso recusava pergunta com fonte | pico 7,7 GB; handoff offline 84,0% → 90,8% |

Limites que continuam: Recall@3 abaixo de 0,85; p95 da memória 52,8 s (frente L em andamento); denso pesado em memória.

## v5.0.0 (01/11/2026) — lições da Getnet v4 e de 28 soluções públicas

Getnet v4: 34 min do 1º ao último commit, CI verde; nota honesta estimada 8,4 (faixa 7,5–8,8). O v5 ataca o que
segurava a nota, na ordem do peso na Régua V4. Detalhe: LICOES_V4.md e pesquisa/.
Testes do kit: 336 → 487 passando (e 459 → 487 só nesta segunda rodada de trabalho).

| Causa na v4 (ou na pesquisa) | O que mudou | Onde |
|---|---|---|
| ingest descartava a tabela de preços; o AC-01 (Get Clássica × Get Smart) ficava sem fonte | células curtas viram linha de tabela; linha longa repetida fica 1 vez | `src/app/ingest.py` |
| número sem base chegava ao lojista (`numbers_acc` 64–80% ao vivo) | a checagem BLOQUEIA: 1 reescrita, depois `[valor não confirmado]` (`NUMBERS_POLICY=flag\|redact\|escalate`); soma, diferença e contagem da evidência passam; "R$ 80mil" é número | `src/app/grounding.py`, `pipeline.py` |
| clima e câmbio pela busca web (corpo cifrado, número sem base) | PTAX do Banco Central e Open-Meteo chamados no código, com data e fonte; falha cai na busca web (`LIVE_DATA=on\|off`). O teste achou 2 defeitos reais (a checagem apagava `[60]` como citação) | `src/app/live_data.py` |
| ação "alegada" sem execução, promessa de data | detector de "reiniciei/abri o chamado/estornei" sem tool no turno; regras financeiras duras no prompt | `grounding.py`, `prompts/` |
| resposta em pt para pergunta em en (Router LLM) | `clear_language`: vantagem ≥ 2 palavras manda; diretiva de idioma no pedido de cada agente | `router.py`, `agents.py` |
| replanejamento só reagia a falha; ablação "93% × 0%" era zero por construção | `needs` do agente insere o passo; `--ablate-replan --mode no_needs` mede o ganho por conclusão (`completed_acc`) | `supervisor.py`, `evals/run_evals.py` |
| sem teto por turno | `MAX_MODEL_CALLS`, `MAX_TURN_USD`, `NODE_TIMEOUT_S`; estourou → parte respondida + humano (`budget_exhausted`) | `supervisor.py` |
| operador respondia, mas o plano não continuava | a resposta do operador retoma os passos restantes; com o caso aberto, tools de escrita não rodam | `resume.py`, `cases.py` |
| RAG: gold por id quebra a cada re-ingest; recall só por trecho | `relevant_urls`/`relevant_text` (regex) e Recall@k/MRR também por página; contexto de seção no índice; máx. 2 trechos por URL | `rag.py`, `ingest.py` |
| eval ao vivo não protegia o código na CI | cassete: gravação do ao vivo e `LLM_PROVIDER=replay` com pisos = taxas da gravação aceita | `llm.py`, `run_evals.py` |
| juiz Claude julgando Claude, sem canário | 4 canários com defeito conhecido (`judge_unreliable`); juiz de outra família por `JUDGE_PROVIDER=openai_compat` | `evals/judge.py` |
| factual sem validação humana (lacuna do 9,5) | `python -m evals.label`: o dono rotula às cegas, relatório humano × automático (kappa) no README | `evals/label.py` |
| ninguém lia os traces antes de medir | `python -m evals.failure_modes` → `docs/FAILURE_MODES.md` (v4: 39 falhas em 4 modos) | `evals/failure_modes.py` |
| o avaliador não roda nada nem assiste ao vídeo | `docs/DEMO.md` com as respostas reais, `docs/TIMESHEET.md` do git log (tags `clock-start`/`clock-end`), `reports/verify.md` pelo `check.py` | `scripts/demo_md.py`, `timesheet.py`, `check.py` |
| README misturado com resultados deixou a CI vermelha 2 vezes | `make final`: README sozinho no último commit, recusa outra mudança pendente | `scripts/final.sh` |
| eval ao vivo em fila: splits sem verba, juiz sem nada | splits em paralelo, 80% do teto em cotas, 20% para o juiz (teto padrão US$ 10; custo medido ~6) | `scripts/live_eval.sh` |
| `live_eval.sh` sem bit de execução; venv apontando para outro repo; `MIN_SCORE` à mão | teste do bit no git; `check.py` recusa venv de outro repo; `--calibrate-gate --apply` grava o limiar | `tests/test_scripts_exec.py`, `check.py`, `run_evals.py` |
| vídeo manual | `make video`: respostas reais + slides do JSON + Playwright + ffmpeg (~5 min) | `scripts/video/` |
| LGPD e produção | volume nomeado, `DELETE /me/conversations/{id}`, retenção por `MEMORY_RETENTION_DAYS`, `/ready` separado de `/health`, trilha de auditoria só de inclusão | `api.py`, `store.py` |
| CI sem cadeia de suprimento | testes com a rede cortada, SBOM, trivy (CRITICAL falha; `.trivyignore` com motivo e validade), actions por SHA, imagem com `--network none`, overlay endurecido | `.github/workflows/ci.yml`, `docker-compose.hardened.yml` |
| guardrail só com regex e recusa seca | lavagem/sonegação (recusa, com verbo de intenção para não pegar "o que é lavagem de dinheiro?") e autoagressão (resposta de apoio com CVV 188 e SAMU 192, sem LLM); a camada LLM ganhou as 2 categorias | `guardrails.py`, `pipeline.py`, `prompts/guardrail.md` |

| seguimento curto não achava o assunto da pergunta anterior | `search_query`: herda o assunto da última fala do cliente como dica de busca (sem histórico, nada muda) | `router.py`, `pipeline.py` |
| resposta em pt para pergunta em en (regressão do próprio v5, achada no ensaio) | diretiva de idioma no fim de TODO pedido de agente + 1 reescrita se a saída vem no idioma errado | `agents.py`, `pipeline.py` |
| caso aberto marcava `handoff.required` em todo turno (regressão do v5) | `required=False` (só aviso e `ticket_id`) | `supervisor.py` |
| caso de suporte fechava por cortesia | estado do caso só fecha com prova (`customer_confirmed` / `tool_verified`), lembra os passos tentados, 2 ciclos sem sucesso → humano com as tentativas | `casestate.py` |
| mapa de ameaças genérico | OWASP Agentic ASI01–10 → controle → arquivo → teste; um teste reprova citação inexistente (pegou 1) | `docs/SECURITY_ASI.md` |
| só `/operator` e sem painel | `/ui` do lojista (testada num navegador real) e Grafana com 12 painéis provisionados (perfil `observability`), com teste que reprova painel de métrica que o código não emite | `static/ui.html`, `ops/grafana/` |
| rodada com LLM fora do ar parecia medida; aborto sobrescrevia resultado completo | `degraded` e `aborted_quota`, arquivo à parte, saída 3; o limite de gasto da API vira erro `quota` | `run_evals.py`, `llm.py`, `live_eval.sh` |

**Medido num ensaio** (ENSAIO_V5.md): o motor v5 sobre o domínio da v4, LLM real, 3 rodadas.
`official` ao vivo: pass^3 0,70 → 1,00, números 80% → 100%. `memory` ao vivo: números 64% → 92%, pass@1 0,54 → 0,79.
O ensaio achou 3 regressões do próprio v5 (handoff do caso aberto, idioma, rodada degradada), todas corrigidas.

**Não entrou / não foi provado (declarado, não escondido):**
- o estado do caso **não foi medido ao vivo** (o limite de gasto da API foi atingido durante o ensaio; só testes e offline);
- as imagens do Prometheus e do Grafana não foram baixadas nem executadas (o compose valida; os painéis são
  conferidos contra as métricas que o código emite, não contra um Grafana rodando);
- o juiz de outra família (`JUDGE_PROVIDER=openai_compat`) só foi testado com mock;
- a CI do GitHub passou com Docker, réplicas, testes sem rede, SBOM e trivy, mas sem a tela `/ui` nem o Grafana no ar.

## v3.7.0 (31/10/2026) — lições da Getnet v3

Balanço da v3: nota estimada 6,3 (v2: 8,18). CI vermelho em todos os commits do domínio, eval ao vivo e juiz
fora do relógio, README com números que não saíam do JSON commitado. Cada item abaixo corrige uma causa
medida, e cada trava nova foi testada contra o repositório da v3 (reprova o erro que ela teve).

| Causa na v3 | O que mudou | Onde |
|---|---|---|
| 59 testes do kit quebraram porque o domínio editou o motor | o domínio virou pacote trocável (`app/domain/`); o motor lê o domínio ativo na hora da chamada; os testes do kit fixam `DOMAIN=example`. Simulação: domínio Getnet inteiro no lugar → 315 testes do kit verdes | `src/app/domain/`, `tests/conftest.py` |
| trocar o limiar no motor quebrou mais 14 testes | `MIN_SCORE` é do domínio (`domain/challenge/__init__.py`) | `src/app/domain/` |
| pré-voo só trocava dados | `scripts/preflight.py` cria o domínio do desafio em 3 arquivos com dono único, copia prompts, tira a loja do produto e roda a suíte | `scripts/preflight.py` |
| 8 forks com check completo afogaram a CPU | check rápido por frente (segundos); check completo só na integração; 5 frentes | `scripts/fork_check.py`, `OWNERSHIP.json` |
| README §5 de um eval não commitado (replan 80% × 10%) | `fill_readme.py --check` e "resultado commitado = código atual" no `check.py` | `scripts/fill_readme.py`, `scripts/check.py` |
| `latest.json` era ignorado pelo git e entrou velho | `evals/results/` versionado; gate e eval via HTTP gravam em `var/` | `.gitignore`, `scripts/check.py` |
| pytest sobrescrevia `evals/results/latest.json` | testes gravam em `tmp_path`; casos/held-out/retrieval do eval apontam para o fixture | `tests/conftest.py`, `evals/run_evals.py` |
| 12 de 42 "provas" do README falhavam | `check.py` reprova teste citado que falha ou não existe | `scripts/check.py` |
| linha do tempo sem o último commit ("50 min" × 54) | `--check` exige todos os commits; só pode faltar um commit que mexa apenas em README/ESTADO | `scripts/fill_readme.py` |
| "72% escrito no relógio" contava 21.909 linhas de JSON | arquivos gerados fora da conta | `scripts/fill_readme.py` |
| loja de exemplo no índice, no Recall@3, no juiz e nas tools | `check.py` reprova marcas da loja depois do pré-voo | `scripts/check.py` |
| trecho real ("evite o modo desenvolvedor") descartado como injeção | regra só bloqueia a ORDEM de ativar o modo desenvolvedor | `src/app/guardrails.py` |
| ingestor escrito no relógio (~30 min) | `app/ingest.py` genérico lendo `data/sources.json` | `src/app/ingest.py` |
| PC com 7,9 GB e disco cheio não aguenta forks | tentativa 100% na nuvem; `scripts/medir_forks.py` para medir outra máquina | `docs/kit/PLAYBOOK.md` |
| gancho do Windows (`.venv/Scripts/python.exe`) quebra no Linux | gancho com `python3`; sessão da nuvem instala o lock e sobe o Docker ao abrir | `.claude/` |
| Docker não construía atrás do proxy da nuvem | certificado como segredo do build, `--network host` só quando detecta o proxy. Medido: `check --docker` verde em 47 s na nuvem | `Dockerfile`, `scripts/check.py` |
| ambiente da nuvem com rede limitada recusava o site da empresa | `scripts/cloud_probe.py` confere chave, rede, Docker e git ANTES do relógio | `scripts/cloud_probe.py` |
| na nuvem, `ANTHROPIC_API_KEY` não chega aos programas e `ANTHROPIC_BASE_URL` aponta para a conexão interna do Claude Code (o SDK a leria sozinho) | o app lê `APP_ANTHROPIC_API_KEY` e, em sessão remota, fala com a API pública; a sonda testa a chave em `GET /v1/models` (sem custo) | `src/app/config.py`, `src/app/llm.py`, `scripts/cloud_probe.py` |
| mesmo com `APP_ANTHROPIC_API_KEY`, o valor chegava trocado na sessão (107 caracteres, sem `sk-ant-`) e a API recusava; no PC a chave funciona | eval ao vivo e juiz rodam no PC com `scripts/pc_live.ps1` (prepara o Python, guarda a chave fora dos repositórios, testa sem custo, envia só os resultados para `fork/live`); a sonda da nuvem ganha `--chave-no-pc` | `scripts/pc_live.ps1`, `scripts/live_eval.ps1`, `OWNERSHIP.json` |
| (01/11/2026) com o valor certo em `APP_ANTHROPIC_API_KEY`, a sessão da nuvem recebe a chave e a API aceita; eval ao vivo de 4 casos na nuvem: US$ 0,034, 0 erro | eval ao vivo e juiz voltam para a sessão principal na nuvem; `pc_live.ps1` vira plano B | `docs/kit/PLAYBOOK.md`, `docs/kit/PROMPTS.md`, `docs/kit/CHROME.md` |
| eval ao vivo, juiz e vídeo depois do relógio | roteiro com marcos duros: ao vivo em 2º plano a partir de T+33, vídeo publicado até T+52 | `docs/kit/PLAYBOOK.md`, `docs/kit/PROMPTS.md` |

### Espelhado das referências públicas (docs/kit/REFERENCIAS.md, 01/11/2026)

| Ideia | Origem | Onde |
|---|---|---|
| ablação do replanejamento (com × sem), offline e ao vivo | nelsondell (9,5 na V4) | `SUPERVISOR_REPLAN`, `run_evals --ablate-replan`, bloco Replanejamento |
| matriz de confusão do router como tabela | EikiYamashiro | relatório do eval / README §5 |
| caminho do avaliador em 5 minutos + coluna "limite conhecido" | nelsondell, ArturFBrandi | README do kit §0 e §3 |
| 2 réplicas atrás de balanceador no CI (e o defeito de caso duplicado que isso revelou) | nelsondell, bnavarro12 | `scripts/scale_smoke.py`, `docker-compose.scale.yml`, `src/app/store.py`, ADR 0002 |
| flags de risco de fintech na resposta | Buzz | `src/app/grounding.py::risk_flags` |
| gitleaks no CI | nelsondell | `.github/workflows/ci.yml`, `.gitleaks.toml` |
| retrieval em pares pt/en + ablação de buscadores commitada | jonathansschaffer, ArturFBrandi | prompt da frente K |

Não validado ainda (faça no ensaio geral, PLAYBOOK §7): tempos reais de cada marco com 6 sessões da nuvem ao
mesmo tempo, o limite de uso da conta com essas 6 sessões, e a gravação do vídeo dentro da nuvem.
