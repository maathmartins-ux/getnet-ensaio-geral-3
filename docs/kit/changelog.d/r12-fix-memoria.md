# Frente R12-FIX-MEMORIA: achados da revisão adversarial na memória de longo prazo e na página de rotulagem

Base: `r12/fix/memoria.md` (3 achados confirmados pela revisão adversarial sobre `r12/int`, área memoria). Nada rodou
ao vivo; a prova são os testes abaixo. As variantes Postgres rodam no job `postgres` do CI (`TEST_DATABASE_URL`).

## 1. Postgres: a retenção não esconde um apagamento nem desfaz a poda que contou
- **O quê:** o perfil do usuário é lido com a trava da linha (`SELECT ... FOR UPDATE`, gancho `FOR_UPDATE` do
  dialeto; no SQLite fica vazio, porque o BEGIN IMMEDIATE já trava o arquivo) antes de mudar: em
  `update_user_profile` (turno) e em `_prune_profile` (apagamento a pedido e retenção). Na poda, só o perfil que vai
  mudar é relido travado, então a purga não segura o turno de quem não tem nada a podar. A purga percorre os perfis
  em ordem de `user_id` (duas purgas juntas travam na mesma ordem).
- **Por quê:** achado 1 (`store.py`, `_prune_profile` com `lock=False`). No READ COMMITTED, o apagamento que lia o
  texto de antes do commit da purga tinha o UPDATE condicional reavaliado contra o texto novo: 0 linhas, a rota
  respondia 200 com `user_memory_items: 0` na auditoria e os itens da conversa apagada seguiam no perfil até o TTL; o
  turno no mesmo intervalo regravava o que a purga tinha tirado (reproduzido pelo cético em Postgres real).
- **Prova:** `tests/test_memory_ledger.py::test_delete_during_retention_purge_still_takes_the_conversation_out`,
  `::test_turn_during_retention_purge_does_not_write_back_what_it_cut` (purga presa na auditoria; no Postgres o teste
  confere em `pg_blocking_pids` que a segunda transação esperou a purga),
  `::test_postgres_reads_the_profile_row_locked_before_changing_it` (sem servidor: o SQL que o PgStore manda).

## 2. Cada item do perfil guarda o conjunto das conversas que o citaram
- **O quê:** item do perfil ganha `convs` ({conversa: data da última citação nela}, até `PROFILE_ORIGINS`, as mais
  recentes). O mesmo fato citado em outra conversa soma a origem em vez de trocá-la; apagar uma conversa tira só a
  origem dela e o item sai quando não sobra nenhuma; retenção e expiração cortam a citação velha e o item segue pela
  recente; `render(exclude=X)` mostra o item que outra conversa também citou, com a data dessa citação. `conv` e `ts`
  continuam no JSON (a origem mais recente e sua data): o perfil gravado antes (só `conv`) é lido como uma origem, e
  uma versão anterior do kit lê o perfil novo sem erro. Assunto segue um por conversa.
- **Por quê:** achado 2 (`memory.py`, `Profile.add`): "o mais recente vence por tipo + valor" deixava uma origem só;
  "1002" citado em A e em B ficava com B, e apagar B tirava do perfil o que A, que continua existindo, também citou.
- **Prova:** `tests/test_memory_ledger.py::test_a_fact_two_conversations_cited_stays_when_one_of_them_is_deleted`,
  `::test_profile_origins_merge_read_the_old_format_and_keep_the_old_fields`,
  `::test_topic_is_still_one_per_conversation_with_origins`; os testes de perfil anteriores seguem verdes.

## 3. Página de rotulagem: o perfil de conversas anteriores é uma anotação, não fonte
- **O quê:** `scripts/label_page.evidence_blocks` junta o bloco `[memória de conversas anteriores]` (várias linhas
  `- ` numa moldura `<untrusted_memory>`) num só bloco de memória, sem a moldura e o cabeçalho ("De conversas
  anteriores do cliente: registro citado pelo cliente: 1002; produto ..."); perfil cortado no teto não engole o que
  vem depois (só `- [` ou `- {` abre item novo dentro dele). As linhas do livro "Valores citados pelo cliente" e
  "Datas citadas pelo cliente", que faltavam na lista, também viram anotação.
- **Por quê:** achado 3 (`label_page.py`, `MEMORY_PREFIXES`): cada linha do perfil virava cartão "Fonte" (com "tem
  número da resposta"), e o rotulador cego lia memória de outra conversa como fonte; o valor que o cliente disse
  saía do mesmo jeito.
- **Prova:** `tests/test_evidence_scripts.py::test_label_page_shows_the_earlier_conversations_profile_as_one_memory_note`,
  `::test_label_page_keeps_a_cut_profile_and_every_ledger_line_out_of_the_sources`.
