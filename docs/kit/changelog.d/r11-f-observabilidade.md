# Frente R11-F: observabilidade com histograma, custo de busca menor e quickstart que funciona

Base: `kit-v5.4.0` (81e60ff). Medidas de CPU feitas nesta máquina (4 vCPU compartilhadas com outras frentes), sobre o
corpus e o gold do ensaio da rodada 10 (snapshot só de leitura), com o cross-encoder do kit (bge-reranker-v2-m3-int8).

## 1. Latência como histograma: o p95 sai do Prometheus

- **O quê:** `Metrics.observe` conta a latência em baldes fixos (`LATENCY_BUCKETS_MS`, com um limite em cada valor que
  o kit compara: alerta da média do agente, escalada do runbook, SLO por turno, `NODE_TIMEOUT_S` do produto e do eval,
  timeout do balanceador) e `render()` emite `span_latency_ms_bucket{span,le}` cumulativo, com `le="+Inf"` igual ao
  `_count` e `# TYPE span_latency_ms histogram`; `_sum` e `_count` seguem com os mesmos nomes (o alerta e o painel da
  média não mudam). Memória fixa por etapa e scrape O(etapas × baldes). Span novo `turn`: o turno respondido inteiro
  (`pipeline.handle`; o bloqueio do guardrail fica fora, porque leva ms e uma rajada de ataques esconderia o turno
  lento). Dois painéis novos: p95 por etapa e p50/p95 do turno com as linhas do SLO. Alerta novo `LatenciaP95DoTurno`
  (p95 do turno acima de `SLO_P95_S` por 30 min) com a sua seção no runbook; a PromQL do p95 está no runbook, que
  mandava escalar por p95 sem o `/metrics` permitir calcular.
- **Por quê:** régua 2 (r10 §21): sem histograma, o p95 não saía do Prometheus; a lista de latência só crescia, e cada
  scrape a somava inteira segurando a trava do `observe()`.
- **Prova:** `tests/test_r11_latency_histogram.py` (baldes cumulativos, +Inf = `_count`, memória igual com 1 e com 10
  mil observações, `histogram_quantile` exato no limite do runbook, span `turn` com o tempo do turno e sem o bloqueio,
  alerta/painel/runbook com os limites do SLO e nos limites dos baldes);
  `tests/test_alerts.py::test_latency_series_include_the_histogram_buckets` e
  `tests/test_observability_stack.py::test_dashboard_has_the_p95_from_the_histogram_for_each_stage_and_for_the_turn`
  (os filtros de sufixo aceitam `_bucket`, e as séries conhecidas saem de um `render()` de verdade).

## 2. Cross-encoder: só os k trechos devolvidos, um par por chamada

- **O quê:** na ordem do base (a do kit), `CrossRerankRetriever.search` pontua só os k trechos que devolve, e não o
  pool inteiro (a saída é a mesma: `diversify` só lê a URL, e o portão só lê a nota dos devolvidos). E
  `FastEmbedCrossEncoder.score` passa um par por chamada ao modelo.
- **Por quê:** réguas 1, 2 e 3 (r10 §5, latência alta): o faq pontuava 10 pares para ler 5, em 2 ou 3 buscas por
  turno. A hipótese do verificador ("mesmas notas no que o portão lê") **não vale no modelo int8**: ele tem 98 nós
  `DynamicQuantizeLinear` (a escala da ativação sai do lote inteiro) e a nota de um par muda com os outros trechos do
  lote. Medido em 6 consultas do ensaio: até 0,51 entre o lote de 10 e o de 5, até 0,57 entre o lote de 10 e o par
  sozinho; a ordem dentro do lote não muda nada, e o par sozinho repete a nota. Par a par, a nota é só do par (a mesma
  no agente, k 5, no eval, k 10, e na calibração do portão; o `Memo` deixa de guardar a nota de quem chegou primeiro) e
  mais barata, sem preenchimento até o trecho mais longo do lote. Tempo do cross por consulta (8 consultas do ensaio,
  menor de 2 rodadas): pool de 10 em lote 1258 ms; 10 par a par 912 ms; 5 em lote 476 ms; **5 par a par 418 ms**.
- **Efeito no portão** (gold do ensaio, 59 perguntas com fonte e 22 sem, limiar −5,5017 da escolha): 1 com fonte passa
  a ser respondida; 2 sem fonte trocam de lado (uma entra e uma sai: a taxa de recusa fica igual). Com os 5 em lote
  seria 1 troca. O limiar foi calibrado com notas de lote de 10: recalibrar no ensaio.
- **Prova:** `tests/test_r11_cross_base_order.py` (um scorer que conta os textos recebe 5 do pool de 10 e devolve os
  mesmos ids e notas do caminho antigo; k igual ao pool e a ordem do cross seguem lendo o pool; scorer quebrado cai na
  ordem do base; um modelo falso sensível ao lote mostra a nota do par igual sozinho ou acompanhado).

## 3. Carga gravada e bloqueios fora do SLO

- **O quê:** o `live_<split>.json` grava `concurrency` (casos ao mesmo tempo no processo = mínimo entre o teto e
  workers × splits; o teto `LIVE_MAX_CONCURRENT`, lido no import como o semáforo; workers; splits no processo; CPUs).
  `evals/trace_stats.py` escreve a carga ao lado do SLO ("não registrada" para gravação anterior ao campo) e tira as
  linhas bloqueadas pelo guardrail do p50/p95, do SLO e da fatia, contadas à parte (`+N bloqueadas`).
- **Por quê:** r10 §5: o bloco gerado não dizia que a latência foi medida com 8 conversas dividindo a CPU, e 39
  bloqueios do guardrail baixavam o p50 do total de 17,6 s para 16,3 s (o número citado pelas réguas).
- **Prova:** `tests/test_trace_stats.py::test_guardrail_blocks_leave_the_percentiles_and_the_slo_and_are_counted_apart`,
  `::test_slo_line_declares_the_load_it_was_measured_under` e `::test_live_report_records_the_load_it_ran_under`.

## 4. Quickstart com o token de dentro do container e comandos do compose conferidos

- **O quê:** o quickstart gerado (`scripts/fill_readme.py`) manda `TOKEN=$(docker compose exec -T api python -m
  app.auth <usuário>)`. Teste novo: todo `docker compose [-f X]* exec|run|logs|restart|up ... <serviço>` do README e dos
  docs aponta para um serviço que existe nos arquivos de compose que o comando usa (os `-f`; sem eles, o
  docker-compose.yml). Fora: o histórico (CHANGELOG, changelog.d) e os estudos de repositórios de terceiros.
- **Por quê:** réguas 1 e 3 (r10 §11): o passo "Entrar" do README dizia `docker compose exec app` e o serviço é `api`
  (o comando falhava no passo 2 do teste de 3 minutos); o atalho do token rodava no host, que com `AUTH_SECRET` vazio
  tem outro segredo que o container (o token dava 401).
- **Prova:** `tests/test_r11_compose_in_docs.py` (fica vermelho até o README e o PLAYBOOK trocarem `exec app` por
  `exec api`: README.md:63 e docs/kit/PLAYBOOK.md:277) e `tests/test_e53_readme.py::test_quickstart_comes_from_the_first_official_case`.
