# Frente R11-C2: documentos que se geram sozinhos e guardas de avaliação

Base: avaliação cega da rodada 10 (3 réguas, 8,86). As perdas daqui estão em `r10_problemas.md` §10 (docs defasados:
FAILURE_MODES, TIMESHEET, §0 do README), §12 (fato de referência que só ecoa a pergunta), §19 item 2 (ferramentas que
leem o held-out) e §23 (RESULTS com tabela no lugar de explicação). Tudo offline: nenhuma chamada ao LLM, nenhum
cassete ou resultado regravado.

## 1. §0 do README com o KPI do negócio

- **O quê:** `scripts/scorecard.py` põe `resolved_fraction` e `cost_per_resolved` na manchete (`HEADLINE`), nesta
  ordem e por último, cada uma com a sua frase em `HOW`: a fração conta toda execução ao vivo que saiu sem pedir humano
  e sem erro (recusa do guardrail conta; o fato só se confere nas oficiais resolvidas); o custo divide o gasto ao vivo
  de todos os splits, inclusive turnos que foram ao humano, por essa mesma contagem. As duas seguem diagnósticas (sem
  meta): a mensagem de entrega não as lista como abaixo da referência.
- **Por quê:** §10, ponto 6. O README promete o "custo por turno resolvido (§0)" e o §0 não o trazia (as 3 réguas).
- **Prova:** `tests/test_r11_generated_docs.py::test_readme_headline_shows_resolved_fraction_and_cost_per_resolved_turn`,
  `::test_headline_declares_the_cost_as_not_measured_without_live_results`.

## 2. FAILURE_MODES gerado de verdade, sem o held-out

- **O quê:** `evals/failure_modes.py` ganha `generate(results)` (o texto do arquivo, ou None sem bateria ao vivo), pula
  todo split `heldout*` (declarado no texto, com as execuções deixadas de fora) e os arquivos laterais
  `live_<split>.degraded.json`/`.aborted_*.json`. `scripts/live_eval.sh`, `scripts/live_eval.ps1` (depois do
  `-SemReadme`) e `scripts/final.sh` rodam `python -m evals.failure_modes` antes do `fill_readme`. O
  `fill_readme.py --check` reprova o `docs/FAILURE_MODES.md` ausente com bateria commitada, diferente do que os
  resultados geram, ou sem bateria que o gere. `evals/error_analysis.py` exclui o held-out pelo mesmo prefixo
  (`failure_modes.is_blind`), não mais pela lista `{"heldout"}`, que deixava um lote cego novo (`heldout_h3`) dentro.
- **Por quê:** §10, ponto 1 (o arquivo dizia "42 falhas em 281 execuções", de outra bateria; nenhum passo rodava o
  gerador) e §19, item 2 (o FAILURE_MODES mostrava pergunta e resposta do held-out).
- **Prova:** `tests/test_r11_generated_docs.py::test_failure_modes_leaves_every_blind_split_and_side_file_out`,
  `::test_error_analysis_leaves_every_blind_split_out`,
  `::test_check_fails_when_failure_modes_is_stale_missing_or_without_results`,
  `::test_live_eval_ps1_generates_failure_modes_before_the_readme` e
  `tests/test_live_splits_one_process.py::test_live_eval_sh_starts_one_eval_process_for_all_splits` (ordem: bateria,
  FAILURE_MODES, README).

## 3. TIMESHEET gerado, com o fim do relógio declarado

- **O quê:** `scripts/timesheet.py --clock-end <sha>` fecha o relógio nesse commit (vence a tag `clock-end`, que o
  proxy da nuvem não deixa subir); cada commit sai "antes do relógio" (anterior ao scaffold), "dentro" ou
  "pós-relógio", o cabeçalho conta os três, a maior rajada é só a de dentro do relógio e `|` do título não abre coluna.
  `scripts/final.sh [--clock-end <sha>]` (ou `CLOCK_END=<sha> make final`) gera o TIMESHEET antes do último commit;
  `docs/TIMESHEET.md` e `docs/FAILURE_MODES.md` entram em `GENERATED` do final.sh e em `fill_readme.README_ONLY`, e o
  `--check` reprova o TIMESHEET com menos linhas de commit que o `git log --no-merges`, tolerando só o último commit
  quando ele leva só arquivos gerados (o do próprio final.sh).
- **Por quê:** §10, ponto 3. O TIMESHEET parou em "446 min, 0 depois" com 47 commits a mais no git (o final.sh não o
  chamava e, sem a tag, "0 depois" saía por construção); o commit anterior ao scaffold saía "dentro".
- **Prova:** `tests/test_r11_generated_docs.py::test_timesheet_clock_end_by_sha_declares_pre_scaffold_and_post_clock_commits`,
  `::test_check_counts_timesheet_rows_against_git_log_tolerating_the_last_generated_commit`,
  `::test_generated_docs_are_in_readme_only_and_in_final_sh` e
  `::test_final_sh_refuses_other_changes_and_commits_only_the_generated_docs_last` (a garantia do final.sh rodada de
  verdade num repositório temporário: recusa código sujo; commit final só com gerados; push; `--clock-end` repassado).

## 4. Fato de referência que só ecoa a pergunta é recusado na carga

- **O quê:** `evals/run_evals.load_cases` recusa o caso em que toda a lista `expect.facts`, ou toda a
  `expect.expects_fact`, já casa a própria mensagem (o mesmo casamento de cada checagem: regex sem caixa e
  `fact_present` da memória): "todo fato já está na pergunta (<campo>); eco não mede a resposta". A fixture do kit
  carrega igual.
- **Por quê:** §12, item 4 (2 réguas): o official-10 passava só repetindo "WhatsApp" e "Payment Link". Varridos os
  casos do ensaio com a guarda: 4 de 251 recusados (official-10, q-ov-10-pt, q-ov-10-en, q-mem-06), os mesmos que o
  verificador achou; com os fatos propostos na §12, os 4 carregam.
- **Prova:** `tests/test_e53_resolved.py::test_case_whose_every_fact_echoes_the_question_fails_at_load`,
  `::test_kit_fixture_cases_load_under_the_echo_guard`.

## 5. "Como ler" gerado no topo de cada bloco denso do RESULTS

- **O quê:** uma frase gerada, sem número digitado, abre cada bloco do `docs/RESULTS.md` (o que mede, de onde vem,
  como ler o IC): offline em `run_evals.how_to_read` (o que reprova sai do próprio relatório, o resto informa; o que
  depende do LLM se lê no ao vivo), ao vivo, trace, juiz (a origem do gabarito sai do `judge.json`), humano, busca e
  replan em `fill_readme.HOW_TO_READ`. Bloco "não rodado" fica sem a frase. O ao vivo aponta a causa de cada falha para
  o `docs/FAILURE_MODES.md`.
- **Por quê:** §23 (régua 2): tabelas densas no lugar de explicação; o FAILURE_MODES não tinha link no RESULTS.
- **Prova:** `tests/test_r11_generated_docs.py::test_every_dense_results_block_opens_with_how_to_read_and_placeholders_do_not`,
  `::test_how_to_read_texts_carry_no_hand_typed_number`; ajustado
  `tests/test_e53_resolved.py::test_report_has_resolved_per_split_and_case_and_markdown_leads_with_it` (a 1ª linha de
  dado continua a das resolvidas, depois do "como ler").
