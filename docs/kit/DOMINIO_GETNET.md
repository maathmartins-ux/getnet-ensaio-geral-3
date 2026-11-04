# Checklist do domínio Getnet (lições dos ensaios de 03 e 04/11; só ideias, nada de código ou texto pronto)

O domínio NÃO vai pré-montado no kit (ordem do dono). Este checklist diz o que montar no relógio e o que já se sabe
que o avaliador cobra; cada item aponta o passo do kit que automatiza ou confere.

## Corpus e busca (frente K)
- Páginas oficiais de produto (maquininhas, Pix, Link de Pagamento, crediário, antecipação, Get Conta) e a central
  de dúvidas (`/duvidas/`). Página de produto que monta o texto por JavaScript (no ensaio, pagamentos-pelo-whatsapp,
  0 trechos no HTML estático) entra pela 2ª passada do `scripts/ingest_render.py`, que renderiza só as páginas finas.
- A central de ajuda (get-ajuda) é índice montado por JavaScript: o índice e as categorias, mesmo renderizados, só
  têm títulos e links (no ensaio, get-ajuda e get-ajuda-reserva-financeira deram 0 trechos); os artigos
  `/get-ajuda-<categoria>/<artigo>/` têm o texto no HTML estático. Descubra os artigos pelo índice renderizado (o
  render do `scripts/ingest_render.py`: `node scripts/render_page.js <url>` dá o HTML depois do JavaScript) e ponha
  os artigos em `sources.json`, em vez de ingerir o índice, que dá 0 trechos.
- **Artigos que entram SEMPRE** (HTML estático, achados no ensaio 13; a K de lá não os ingeriu e o official-05
  ficou só com o manual indireto): maquininha que não conecta (official-05) →
  `https://site.getnet.com.br/get-ajuda-erros-maquininha/erro-adq-1-84/` (problema de conexão),
  `.../erro-adq-1-19/` (erro de conexão), `.../erro-adq-1-18/` (erro de comunicação), `.../erro-adq-4-30/` (falha na
  comunicação), `.../erro-adq-1-87/` (registro do chip), e o índice `https://site.getnet.com.br/get-ajuda-erros-maquininha/`
  só para descobrir os outros; venda recusada (official-08) →
  `https://site.getnet.com.br/get-ajuda-gestao-de-vendas/quais-possiveis-status-das-minhas-vendas/` ("Negada" = não
  autorizada pelo emissor/bandeira) e `.../get-ajuda-erros-maquininha/erro-adq-4-23/` (falha na transação). A tabela
  de códigos do emissor (ABECS) e os manuais (Wi-Fi, chip, "Teste de Conexão") são PDF
  (`/wp-content/uploads/2021/02/tabela-WS_final.pdf`, `/wp-content/uploads/2024/01/Manul_GetClassica.pdf`,
  `/wp-content/uploads/2025/09/Manul-GetSmart.pdf`): o `app/ingest.py` não lê PDF; se o oficial precisar deles, o
  texto relevante vai como página de conhecimento com a URL de origem.
- Glossário pt→en com as perguntas em inglês dos oficiais: "bank account" → Get Conta, "card machine" → maquininha,
  "receivables advance" → antecipação. Conferir com `retrieve()` que a página certa sobe no top-5.
- Portão sem fonte: `python -m evals.run_evals --calibrate-rerank-gate --apply` (grava `MIN_RERANK`); gold com
  ≥ 15 perguntas sem fonte, senão o limiar é indicativo.
- Abrir cada URL de `data/sources.json` e conferir que o título é o do produto: no ensaio, o slug `antecipacao`
  era a FAQ da Reserva Financeira (o site redireciona `/antecipacao/`), e o official-06 saiu parcial nas 3 rodadas.
- Gold de busca: o gerador tira cabeçalhos, banners e telas do site (`gold_questions.GENERIC`); depois do
  `--import`, conferir `no_agreement` e `back_to_drafts` em `evals/essential/report.json`.
- Depois de mudar o buscador ou o cross-encoder, recalibrar o portão (a nota do int8 dependia do lote; agora é
  par a par, e o limiar do ensaio mudou de -5,50 para -4,99).
- Buscador: no relógio vale o padrão do kit (PLAYBOOK A3), `dense+windows+cross:base` desde a rodada 12 (janelas por
  trecho: o cartão da Get Clássica dentro do prod-taxas-02 entra no top-5 do redator do official-01; antes ficava em
  12º–18º; a nota do rerank só decide o portão). `--choose-retriever --fast` mede 5 configurações (~7–8 min de CPU,
  máquina parada; a 1ª vez vetoriza também as janelas) e só roda fora da bateria; o README cita a tabela gerada, nunca número à mão.

## Oficiais (SPEC, T+0→T+4)
- Todo oficial com `expect.facts` (o `check.py` reprova sem): clima `°C`, depósito com os valores do CRM, euro `PTAX`
  e `R$`, recusa com os códigos 51 e 05, Pix com a Get Conta. Fato frouxo infla a manchete: a régua cobra.
- "resolvido" já reprova resposta que abre com abstenção; o prompt manda a 1ª frase responder.
- Todo caso oficial e de memória tem ao menos um fato que a pergunta não traz (o `load_cases` recusa o eco: o
  official-10 passava só repetindo "WhatsApp" e "Payment Link"). Comparação de produtos pede um fato de cada
  produto (o official-01 pedia os recursos da Get Clássica e o caso não tinha esse fato).

## Prompts do domínio (frente R)
- Tabela de faixa de faturamento ("acima de R$ X mil por mês") é isenção do aluguel, nunca preço nem limite.
- Pergunta sobre a própria empresa nunca fica em `general` (guarda `OWN_COMPANY`).
- Fora do escopo (receita, curiosidade) não responde conteúdo: o prompt `general` do kit já recusa.
- Duas perguntas sobre o MESMO produto = knowledge, não multi (exemplos rotulados no router).
- Clima e câmbio nunca escalam; clima tem segunda fonte (wttr.in) no kit.
- Desafio com agente geral: declare `general` em MULTI_PARTS (além de PLANS e NO_ESCALATION): a pergunta composta
  (clima/câmbio + produto ou conta) roda as duas partes em paralelo, com o passo `general` no trace; o `combine` do
  exemplo conta 2+ partes do negócio (não volte a `MULTI_PARTS <= partes`, que com `general` ali desfaz o multi).
- O `general.md` do domínio lista `currency_rate`, `weather_forecast` e `web_search` (cópia do kit, feita pelo
  pré-voo); o contrato do motor (`prompts/contract/general.md`) vai no fim e manda chamar as duas e trazer
  mínima/máxima/chuva e compra/venda. `live_data.md` não é mais lido. O `domain.prompt` só anexa o contrato a prompt
  do domínio sem "Regras do motor" no texto: não cole o contrato no prompt do domínio (o do kit deixaria de entrar).
- Comentário e prompt do domínio sem id de caso: a guarda (`tests/test_code_cites_no_eval_case.py`) lê os ids de
  `evals/cases.jsonl` e `cases.d/` e reprova a citação em `src/` (no ensaio, um comentário do `flow.py` citava 3 ids).
- Seguimento curto que pergunta ESTADO ou DADO de um terminal/transação (está online?, há quanto tempo?, e o outro?)
  é support mesmo depois de um troubleshoot; a regra "herda a intenção" sem essa exceção fazia o modelo alternar o
  rótulo (memória com 4 casos instáveis só pelo rótulo, resposta certa).
- Regra de domínio no prompt é genérica: sem frase de caso de avaliação, sem marca e sem fato embutido
  (`tests/test_router_contamination.py::test_domain_prompts_do_not_copy_eval_questions` reprova 5 palavras
  seguidas de pergunta de avaliação; no ensaio, a regra do "do I need a bank account?" caiu nele).
- Troubleshoot: plano só `["records"]`; o manual (faq) vem do achado (`needs`) e é o supervisor LLM que decide
  chamá-lo (o supervisor.md do domínio mantém "se o resultado pedir outro especialista (`needs`), chame-o").
  Passo que o plano do router já tem não conta como replanejamento.

## CRM e tools (frente T)
- Dois clientes de teste; depósito Pix D+0, débito D+1 útil, crédito D+30; recusas com código e significado
  calculados no código; terminal com sinal e último contato. Schema validado no servidor (kit).
- `needs_for` é a regra do código sobre o achado: no motor de tabela só entra o que ela devolver (junte o `needs` de
  TODOS os resultados de tool, terminal E transação, não só o do 1º: no official-08 a dica de recusa se perdia); no
  motor LLM ela só escolhe o achado que ganha o lembrete, e o modelo recebe sempre o `needs` das tools (achado que
  importa ao modelo mesmo fora da regra vai no `needs` da tool).
- Declare `LABELS` no domínio (tools.py): sem_conexao → sem conexão / no connection; sem_sinal → sem sinal / no
  signal; erro_transacao → erro de transação / transaction error; last_7_days → últimos 7 dias / last 7 days;
  yesterday → ontem / yesterday; today → hoje / today; reason → motivo / reason; period → período / period;
  request_receivables_advance → antecipação dos recebíveis / receivables advance; open_support_ticket → chamado
  técnico / support ticket. Sem `LABELS`, o valor sai só sem '_': sem acento e em português num turno em inglês.
  Formato `{valor: "palavras"}` ou `{valor: {"pt": ..., "en": ...}}`; vale no cartão, na resposta e no aviso da
  decisão do operador (`app/capabilities.py`).
- Campo só quando se aplica: `offline_for_hours` só com terminal offline (com 0 no terminal online, o LLM
  escreveu "offline há 0 hora" na vitrine e em 2 respostas da bateria).
- Toda tool com período tem enum E padrão (o cartão de capacidades mostra as opções e o padrão de cada uma); sem
  padrão, o supervisor escolheu o período mais curto e o depósito do oficial sumiu. Pergunta sem período = o mais
  largo que a tool aceita.
- "Hoje" sempre do relógio do negócio (`app.clock`, `APP_TZ`, padrão America/Sao_Paulo) nas tools do domínio: a
  bateria perto da meia-noite de Brasília já é o dia seguinte em UTC.
- Clima e câmbio: os valores obrigatórios (mínima, máxima, chance de chuva; venda e compra) saem do código
  (`LiveResult.must`); o prompt do domínio não pede para resumir a chuva junto do conselho do guarda-chuva (o corte de
  afirmações tirava a frase inteira).

## Evidência que a régua lê (fim do relógio)
- Bateria ao vivo integral UMA vez no código final (nada de commits misturados): `scripts/live_eval.sh`.
- Ablação do replanejamento (`--ablate-replan --mode no_needs --split real`) DEPOIS da bateria e no mesmo commit:
  os vereditos vão para `judge_ablation_*.json` e a linha do RESULTS conta dos arquivos de veredito; smoke e ablação
  nunca regravam os cassetes do CI.
- Juiz com a data em que a resposta foi gerada (`business_date` por linha); bateria que atravessou a meia-noite UTC
  com juiz antigo: `python -m evals.judge --rejudge-dated` (o RESULTS declara quantos rejulgou).
- Disco abaixo de 5 GB trava a bateria e o build: apagar os modelos do fastembed que a escolha não usa (nunca as
  pastas de rascunho de agentes que ainda rodam).
- `check.py --docker --scale` completo no código final, antes do `final.sh` (README por último): a 1ª subida do
  container depois do build pode passar de 60 s (o check espera 180 s e grava o tempo medido).
- Humano no laço gravado: `scripts/demo_md.py --transcript evals/demo_transcript.jsonl` com uma linha em que o
  cliente PEDE o atendente (senão o sistema só oferece e o operador não é consultado), de preferência com o dado que
  só o atendente traz (PLAYBOOK §1.9, item 6: `human->records` no trace).
- Split `hitl` em `evals/cases.d/hitl.jsonl` (formato no docstring de `evals/run_evals.py`): 6–8 casos pt/en, no
  prazo (`after_s` 1–3, `wait_s` 8–10), atrasados (`wait_s` 2–3, `after_s` ≥ `wait_s` + 2) e um de aprovação sem
  operador; `facts` com o fato que a operadora diz e `not_contains` com a negação de encaminhamento. Ao menos um no
  prazo em que a resposta da operadora traz o dado que o passo seguinte usa (ex.: o id da venda), com
  `expect.after_human` (ex.: `["records"]`) e o fato que só esse passo traz (o valor da venda). Antes de commitar a
  vitrine regravada, procurar "não foi encaminhad" e "offline há 0".
- Memória entre conversas: ao menos um caso do split `memory` com `earlier_conversations` (conversas anteriores do
  mesmo `user_id`; o turno avaliado só sabe delas pelo perfil de longo prazo) e `expect.expects_fact` com o que veio
  da conversa anterior.
- Lote cego novo do held-out em `evals/heldout_blind.d/<lote>.jsonl` com split `heldout_<lote>` (fora do gate de
  intenção pelo prefixo; o juiz não grava o motivo; a análise de falhas não lê), escrito por um autor que só
  lê o enunciado e a SPEC; a sessão principal não lê as frases. Ataque leva `intent: blocked`, `handoff: false`.
- THREAT_MODEL do domínio: `/mcp` no escopo (mesma cota do `/chat`), linha R (risco alto aprovado só com chave
  pessoal de `OPERATOR_KEYS`: o token compartilhado, que só existe fora de produção, lê a fila, responde e rejeita,
  e leva 403 ao aprovar; `tests/test_hitl.py::test_high_risk_action_needs_owner_then_operator_and_runs_once`), linha
  S (produção recusa `AUTH_MODE=demo`; `tests/test_api.py::test_production_refuses_demo_identity`) e linha I
  (`/metrics` com Bearer em produção).
- Rotulagem humana em 2 páginas (`scripts/label_page.py`; a 2ª com `--n 20 --suspects 10 --fresh`), em paralelo à
  bateria. Para validar o juiz, a página 2 precisa de uma parte sorteada ou trazida pela checagem automática: o juiz
  reprova por construção o negativo que entrou porque ele mesmo o reprovou, então esse não conta (nem para o mínimo
  de negativos reais) e sai à parte como diagnóstico (`evals.judge.SELECTION_RULE`). Por isso o sorteio da página sai
  antes das suspeitas e as da checagem vêm antes das do juiz; a saída do script diz quantas por motivo e avisa se
  nenhuma independe do juiz. O motivo de cada escolha fica em `evals/human_selection.json` (fora da página; commitar
  com os CSVs); rótulo sem motivo gravado é "seleção desconhecida" e também fica fora.
- Juiz × pessoas com respostas de defeito plantado, NESTA ordem (cada passo lê o arquivo do anterior): ao vivo →
  `python -m evals.perturb` → `python -m evals.judge --perturbed` → `python scripts/label_page.py --perturb 15
  --raters <A>,<B>` → importação (`python -m evals.label --import-page <json>`) → `python -m evals.label --report`.
  A página recusa cópia de resposta que mudou depois (bateria nova: `evals.perturb --force` e o juiz de novo); o sal
  dos ids cegos fica em `var/rotulagem_salt.json` (não apagar antes de importar; id sem sal sai em `nao_mapeados`) e
  sorteia também a escolha e a ordem das adulteradas. O sal esconde o id e a posição, não o texto: quem rotula não
  abre o repositório (as adulteradas estão em `evals/results/perturbed.json`).
  Plantado não valida sozinho: com plantadas no bloco, o total só sai validado com ≥ 3 negativos de respostas REAIS
  escolhidas sem depender do juiz (sorteadas ou da checagem automática da página 2) E o juiz reprovando esses reais
  com TNR ≥ 0,8 (`evals.judge.PLANTED_RULE`, além do resto da regra); senão sai "validado só com negativos plantados
  (com respostas reais: não validado)". Essa parte entrou na rodada 10, depois da revisão, e é mais estrita que a
  regra fixada antes de medir; a da escolha (`SELECTION_RULE`), na revisão seguinte.
  Afirmação sem base cabe em poucas respostas reais: nunca em resposta que diz que a fonte não cobre o assunto da
  frase (inclusive por "isso"), nem ao lado de frase de ausência ou de valor do mesmo tipo (percentual, "não cobra
  taxa", prazo, "na hora", "amanhã", data da agenda), e, se a resposta fala do assunto, só numa linha de prosa sobre
  ele; no ensaio, 0 (eram 10, depois 3): a página de 15 sai com número trocado e fato removido (8 e 7) e o RESULTS
  declara a composição real.
- README: nenhum número escrito à mão fora dos blocos gerados (a régua acha o número velho e desconta).
