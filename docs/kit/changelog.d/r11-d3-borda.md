# Frente R11-D3: borda (rate limit no MCP, produção fechada por padrão, overlay que cabe no buscador)

Base: kit-v5.4.0 (81e60ff). As perdas vêm da avaliação cega da rodada 10 (seções 15, 24 e 17 de r10_problemas.md).
Nenhuma chamada a LLM e nenhuma bateria ao vivo. A medida do overlay usou a imagem local `app-check`, com os dados do
ensaio (22 arquivos em data/) e o buscador `dense+cross:base`, e o LLM offline. Rodou num container com as travas do
overlay (rootfs só leitura, usuário 10001, `cap_drop: ALL`, `no-new-privileges`), num host de 4 vCPU parado.

## 1. A cota do /chat também nas ferramentas do MCP

- **O quê:** `ask`, `search_knowledge` e `crm_tool` passam por `mcp_server._caller`: a identidade do token e
  `LIMITER.allow(user_id)`, a mesma chave do /chat com identidade verificada. Trocar de canal não dobra a cota. Em `ask`,
  a cota é conferida antes do pipeline, então o pedido recusado não chega ao LLM. O limite fica por ferramenta chamada,
  não no `require_bearer`: sem estado, `initialize` e `tools/list` passam por lá e gastariam a cota sem atender nada.
  A recusa é um `ToolError` com "muitas requisições; tente em 1 minuto". O SDK 2.x só mostra ao cliente a mensagem
  de `ToolError`. Qualquer outra exceção vira "Error executing tool" e traceback no log. Por isso o token inválido
  (defesa em profundidade) também passou a `ToolError`. Métrica: `rate_limited_total{channel="mcp",tool=...}`.
- **Por quê:** seção 15. Um laço de `ask` rodava o pipeline sem limite (só o teto de US$ 0,25 por turno), a busca
  rodava o cross-encoder sem limite e `crm_tool` criava ações pendentes sem limite.
- **Prova:** `tests/test_mcp.py::test_mcp_tools_share_the_chat_rate_limit`. Com `RATE_LIMIT_PER_MIN=2`, um /chat e um
  `ask` gastam a cota; depois as três ferramentas e o próprio /chat recusam, e outro cliente segue atendido. Esse teste
  falha com o `mcp_server.py` anterior.

## 2. Produção fechada por padrão: OPERATOR_KEYS e METRICS_TOKEN obrigatórios

- **O quê:** com `APP_ENV=production`, a subida (`api.refuse_insecure_production`, chamada no lifespan) soma a
  `production_gaps()` ao segredo fraco: falta de `OPERATOR_KEYS`, e `METRICS_TOKEN` ausente, curto (< 16) ou de
  exemplo. A mensagem é a mesma, "segredos padrão em produção: [...]". No dev nada muda: `insecure_defaults()` é o
  mesmo, e o /metrics sem token segue aberto. `config.metrics_token()` lê o token aparado, como o Prometheus apara o
  `credentials_file`.
- **Prometheus do perfil endurecido:** `ops/prometheus.hardened.yml` é o `ops/prometheus.yml` com
  `authorization: {type: Bearer, credentials_file: /run/secrets/metrics_token}`. O overlay monta esse arquivo no
  lugar do padrão. O segredo `metrics_token` do compose vem de `environment: METRICS_TOKEN`, o mesmo valor do `.env`
  que a API lê. Conferido com `docker compose`: o segredo aparece em `/run/secrets/metrics_token` com modo 0444,
  legível pelo usuário `nobody` do Prometheus. Sem a variável, o `up` do perfil falha alto. O `config -q` da CI
  continua passando.
- **Texto:** o `.env.example` e a docstring de `config._local_secret` diziam que o token de operador gerado "sai no
  log". Isso era falso, e o código e o teste negavam. Agora dizem onde ele fica (var/local_secrets.json, 0600) e o que
  a produção exige.
- **Por quê:** seção 24. O OPERATOR_TOKEN compartilhado valia como "admin" sem nenhuma chave pessoal. Com ele se
  aprovava escrita de risco alto, se purgava a retenção e se lia a auditoria, sem o nome de uma pessoa. O /metrics
  ficava sem token na porta da API, e o portão de produção só olhava segredo fraco.
- **Prova:** `tests/test_api.py::test_production_refuses_shared_operator_and_open_metrics`. Cobre a recusa no
  lifespan citando os dois, o token de exemplo recusado, o portão que passa com os dois, /metrics 401 sem o Bearer e
  o compartilhado sem valor ao lado da chave pessoal. Outra prova é
  `tests/test_supply_chain.py::test_hardened_prometheus_scrapes_with_the_metrics_token`: os dois arquivos do Prometheus
  não descolam, o overlay monta o hardened e o segredo sai do METRICS_TOKEN.
- **Conferido no container:** mesmas travas do overlay e `APP_ENV=production`, com o `src/` e o `data/` do kit montados
  sobre a imagem, sem build.
  - Sem os dois, o processo sai com código 3 e "segredos padrão em produção: ['OPERATOR_KEYS', 'METRICS_TOKEN']".
  - Com os dois, sobe com `operator_auth: personal` e `dense+cross:base` sem fallback.
  - /metrics responde 401 sem o Bearer e 200 com. Em /handoffs, o token compartilhado leva 403 e a chave pessoal, 200.
  - Os vetores do corpus que a imagem não trazia saíram em memória, com o aviso `embed_cache_unwritable` do rootfs
    só leitura.

## 3. Overlay endurecido que cabe no buscador escolhido

- **O quê:** `mem_limit: 1g → 8g` e `cpus: 1.0 → 2.0`. A citação de `tests/test_hardening.py`, que não existe, virou
  as provas reais. Saiu o aviso velho de que o fastembed gravava em /opt/models: o rootfs só leitura serve o denso +
  cross, com `/health` em `retriever: dense+cross:base` e `retriever_fallback` vazio.
- **Medida** (container com as travas do overlay):
  - RSS do processo: 2401 MB ociosa logo depois da subida.
  - FAQs simultâneas, pico de RSS: 1 → 2678 MB, 5 → 3369 MB, 10 → 4563 MB e 20 → 6111 MB, no teto de 6g, com o
    kernel devolvendo o cache das páginas e sem OOM. Uma 2ª rajada de 20 com 8g chegou a 6708 MB, sem tocar no limite.
  - Latência da mesma FAQ por CPU: 4 CPUs 1,3–2,2 s; 2 CPUs 2,9–4,7 s; 1 CPU 7,2–10,8 s.
  - Com 2 CPUs, 20 simultâneas levaram 50–54 s cada: a CPU satura antes da memória.
  - O Docker recusa `--cpus` acima das CPUs do host ("range of CPUs is from 0.01 to 4.00"). Por isso fica 2, e não 4.
- **Regra no teste** (`tests/test_supply_chain.py::test_hardened_overlay`): `mem_limit` ≥ RAM do buscador + 20 FAQs
  simultâneas × 180 MB.
  - A RAM do buscador é o maior entre a medida do escolhido em `data/retriever.json` (domínio) e o teto `ram_budget_mb`
    da escolha. `choose()` reprova o que passa do teto, então o domínio pode reescolher sem mexer no overlay.
  - No kit, sem escolha gravada, vale `RAM_BUDGET_MB`.
  - O teste também exige `cpus` ≥ 2.
- **Guarda:** `tests/test_evidence.py::test_every_test_cited_in_compose_docs_and_readme_exists`. Todo `tests/x.py`
  (e `::teste`) citado em `docker-compose*.yml`, `README.md`, `docs/*.md` e `docs/adr/*.md` existe.
  `docs/KIT_CHANGELOG.md` fica de fora, por ser histórico, como no `check.py`. A guarda falhava no overlay anterior.
- **Por quê:** seção 17. Com 1g, o cgroup matava o processo ao carregar o buscador escolhido, que ocupa 2,4 GB. Com
  `restart: unless-stopped`, o container entrava em laço de reinício. O comentário apontava para um teste que não
  existe.
- **Prova:** `tests/test_supply_chain.py::test_hardened_overlay`, que falha com o overlay anterior
  (`mem_limit 1g < 7696 MB`), e `tests/test_supply_chain.py::test_hardened_overlay_memory_rule_follows_the_recorded_choice`,
  que confere a regra com e sem escolha gravada e com o teto desligado.
