# Frente R11-E: busca do faq, resposta primeiro, gold e frase do buscador gerada

Base: avaliação cega da rodada 10 (8,86; meta ≥ 9,0), perdas conferidas em `r10_problemas.md` §5, §6, §7, §8 e §20.
Medidas desta frente feitas offline sobre a cópia só leitura do ensaio (`grade_snap10a`: respostas gravadas em
`evals/results/`, cassetes, gold de busca), sem LLM e sem bateria ao vivo.

## 1. Comparação mantém 1 busca corretiva (official-01, memory-01)

- **O quê:** `agents.faq_agent`: `left = max(1, FAQ_MAX_SEARCHES − buscas do plano)`. O plano que gasta o teto (as
  palavras do cliente + uma busca por item) ainda deixa 1 `search` ao redator; a mensagem de limite cita o teto que
  valeu no turno (plano + 1). Com plano abaixo do teto, nota e mensagem saem idênticas às de antes.
- **Por quê:** §6(1). O router escreveu `["Get Clássica","Get Smart"]`, o plano chegou a 3 (o teto), o redator ficou
  sem a tool e marcou "MISSING: recursos da Get Clássica" nas 3 rodadas, com o trecho dos recursos no corpus.
- **Prova:** `tests/test_k53_agentic_retrieval.py::test_comparison_that_spent_the_budget_keeps_one_corrective_search`
  (o teste que fixava o contrário foi invertido) e `::test_plan_under_the_budget_keeps_the_same_tool_budget_and_limit_text`.
- **Alcance:** vale para todo turno em que o router escreve 2+ consultas (com as palavras do cliente, o plano chega
  a 3), não só comparação de produto: nos cassetes do ensaio, ~43 turnos de 10 splits.

## 2. Buscas do plano em paralelo, na ordem do plano

- **O quê:** `agents.plan_rankings`: a 1ª busca na thread do agente e as outras ao mesmo tempo, com o contexto de
  quem chama (cassete, trace, memo desligado da medida de latência); o resultado volta na ordem do plano (a fusão por
  rodada depende dela). Teto do processo para as buscas a mais (`FAQ_SEARCH_PARALLEL`, padrão 2; 0 = em série): sem
  vaga, a busca roda em série, sem fila e sem pico de RAM a mais. BM25 puro fica em série (~1 ms por busca).
- **Por quê:** §5 ("rodar as 2 ou 3 buscas do plano em threads, mantendo a ordem"): cada busca do denso + cross leva
  ~0,95 s de p50 e o faq as fazia em série. O teto existe por causa da frente R2 (20 inferências ONNX simultâneas
  chegaram a 5,8 GB).
- **Prova:** `tests/test_k53_agentic_retrieval.py::test_plan_searches_run_at_the_same_time_and_come_back_in_plan_order`
  (barreira de 3: em série o teste quebra), `::test_parallel_searches_keep_the_callers_context_and_give_back_the_slots`,
  `::test_without_a_slot_or_with_bm25_the_plan_runs_in_series`. Dois testes que conferiam a ordem de CHEGADA à busca
  passaram a conferir a ordem do plano e a fusão (`test_v53_search_queries`, `test_v54_retrieval_method`).

## 3. Resposta primeiro (official-04)

- **O quê:** `pipeline.answer_first`, depois da última chamada ao LLM: tira a 1ª frase quando ela abre dizendo que as
  fontes não trazem algo (sem citação), a 2ª cita fonte do turno e responde (não é outra ausência nem "só achei..."),
  outra frase de ausência das fontes fecha a resposta e a 2ª não depende da 1ª ("They do say X [n]" vira "X [n]").
- **Por quê:** §6(2). A rodada 0 do official-04 abriu com "The sources don't say a bank account is mandatory." e o
  eval marcou não resolvido; a regra estava no prompt e nada a impunha.
- **Medido (respostas gravadas do ensaio):** muda 1 de 626 (a rodada 0 do official-04; `opens_with_abstention`
  passa de verdadeiro a falso); nos textos crus dos cassetes, 4 aberturas-ressalva, todas melhores sem a 1ª frase.
- **Não feito de propósito:** levar a 1ª frase para o fim quando ela é a única ausência. Valeria em 3 respostas
  gravadas (memory-15 ×2, real-29) e pioraria as 3: ali a ressalva era a resposta direta ("the sources don't say
  whether X connects over Wi-Fi") e a frase seguinte dependia dela.
- **Prova:** `tests/test_r11_answer_first.py` (texto gravado da rodada 0, resposta sem citação, recusa legítima,
  ressalva que é a resposta, "só achei", ressalva de um trecho só, resposta de registros, e o turno ponta a ponta).

## 4. Separação com × sem fonte no caminho do agente

- **O quê:** `retrieval_eval.separation`: pergunta que o portão recusou (lista vazia) entra com nota −inf em vez de
  sair da conta; o gap fica entre as não recusadas e `refused` conta as recusadas. A calibração do limiar da nota
  segue só com nota de verdade (a recusa não é nota do cross).
- **Por quê:** §7(1) e §7(4). O portão recusava 18 das 22 sem fonte e a AUC publicada saía de 57 × 4, "indicativa";
  as réguas 1 e 2 leram "AUC com 4". Pelos números gravados, a conta nova dá ~0,967 em 59 × 22.
- **Prova:** `tests/test_v54_retrieval_method.py::test_question_refused_by_the_agent_gate_counts_as_minus_infinity` e
  `::test_agent_path_rerank_note_is_minus_infinity_only_when_refused`.

## 5. Import do gold essencial

- **O quê:** `essential_gold.import_labels`: consenso vazio tira da linha o rótulo de um import anterior (a linha
  sem nenhum outro gold sai do gold e volta a rascunho, em vez de ler como "sem fonte"); na união, `essential_by`
  lista só quem marcou (e a pergunta vai a `no_agreement`); `report.json` lista em `gold` os arquivos escritos; o
  `--out` sem linha própria não fica como arquivo vazio.
- **Por quê:** §7(3a,b) e §7(5). real.jsonl:1-2 seguiam com a regra velha e contavam acerto no rank 1; q069/q078/q079
  diziam "2 rotuladores" com 1; `report.json` apontava para `retrieval.d/k.jsonl` de 0 bytes.
- **Medido:** re-import dos rótulos do ensaio numa cópia: as 2 linhas voltam a rascunho, as 3 ficam com
  `essential_by: ["labels_A"]`, o k.jsonl sai e `gold` lista official/page/real.
- **Prova:** `tests/test_essential_gold.py::test_import_clears_stale_labels_lists_only_who_marked_and_leaves_no_empty_file`
  e `::test_import_does_not_create_an_empty_out_nor_touch_explicit_negatives`.

## 6. Cabeçalho e chamada do site fora do gold

- **O quê:** `gold_questions.generic`: GENERIC também com "Como você prefere continuar", "Qual a sua máquina", "Já é
  (nosso) cliente", "Dúvidas sobre"; BANNER pega "Já tem/Já é" e "Dúvidas sobre" com maiúscula no meio do texto
  (título seguinte grudado), e deixa "Quem já tem conta...?".
- **Por quê:** §7(3). 9 das 39 perguntas `page` do ensaio eram cabeçalho, tela ou chamada do site.
- **Medido:** no gold do ensaio pega exatamente as 9 linhas, nenhuma das official/real; o gerador sobre o corpus do
  ensaio não emite mais nenhuma delas.
- **Prova:** `tests/test_v54_gold_origin.py::test_site_headers_and_banners_are_not_customer_questions`.

## 7. Frase do buscador gerada (bloco `retriever`)

- **O quê:** `scripts/fill_readme.py::retriever_block` (marcadores `<!-- retriever:begin -->`/`<!-- retriever:end -->`):
  o item "Retrieval" gerado de `data/retriever.json` (ou do `KIT_RETRIEVER`): modelos, ordem, papel do cross ("ordem
  do denso; nota do cross só no portão sem fonte" quando a ordem é `base`), limiar, cobertura do portão com e sem o
  cross, custo a mais por busca e o que reordenar fez, quando medidos. Entra em `BLOCKS`, então o `--check` reprova a
  frase escrita à mão que diverge da escolha.
- **Por quê:** §8 (as 3 réguas: o README dizia "denso + cross-encoder sobre o top-10" e "ninguém roda
  --choose-retriever no relógio"; a escolha gravada era `dense+cross:base`, saída do --choose-retriever).
- **Prova:** `tests/test_v55_rerank_order_choice.py::test_retriever_sentence_says_what_the_recorded_choice_does`,
  `::test_retriever_sentence_without_a_recorded_choice_is_the_kit_default_and_a_reordering_choice_says_so`,
  `::test_check_flags_a_hand_written_retriever_sentence`.

## 8. Prompt do domínio não copia pergunta de avaliação

- **O quê:** `tests/test_router_contamination.py`: `eval_questions` (official, official-var e todo `heldout*`, com os
  turnos anteriores) e `contaminated_prompts` (5 palavras seguidas, o mesmo `shingles` do held-out) sobre os prompts
  que o LLM lê no domínio ativo. Roda no kit (prompts do kit × casos do kit) e no domínio (`domain_data`).
- **Por quê:** §20(b). A regra do faq.md do domínio copiava a frase do official-04 ("do I need a bank account?").
- **Medido:** sobre o ensaio, acusa só o faq.md × official-04 ("do i need a bank", "i need a bank account"), nenhum
  outro prompt nem o contrato do motor; o texto genérico proposto no §20(a) passa.
- **Prova:** `::test_detector_catches_an_eval_question_copied_into_a_prompt`, `::test_kit_prompts_do_not_copy_eval_questions`,
  `::test_domain_prompts_do_not_copy_eval_questions`.
