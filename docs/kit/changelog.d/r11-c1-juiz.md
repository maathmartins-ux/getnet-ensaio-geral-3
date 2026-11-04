# Frente R11-C1: juiz honesto (rejulgamento simétrico e validação contra pessoas que não envelhece)

Base: avaliação cega da rodada 10 (3 réguas), perdas conferidas em `r10_problemas.md` §1 (itens 2 e 4(b)–(d)), §2 e
§19 (o `reason` do held-out). Nenhuma chamada de LLM e nenhuma bateria ao vivo. Testes novos em
`tests/test_r11_judge_honest.py`.

## 1. Rejulgamento só pela data, nunca pelo veredito (§2)
- **O quê:** `evals.judge.rejudge_plan` rejulga só a resposta com data relativa ou explícita (`date_kind`), aprovada
  ou reprovada, que não foi julgada com o dia em que foi gerada. Cada veredito grava agora `judge_date`, e o que já
  foi julgado com o dia certo não volta (seria só um novo sorteio; também deixa o `--rejudge-dated` idempotente). A
  resposta sem data fica com o veredito da 1ª passada, aprovado ou reprovado. Recusa ou teto no meio do rejulgamento
  mantêm o veredito da 1ª passada (`rejudge_refused`), e o denominador não muda.
- **Por quê:** a regra antiga (`verdict_fails or not helpful or dated`) dava nova chance só a quem tinha reprovado.
  As 3 réguas leram a manchete do juiz como vinda de um rejulgamento seletivo.
- **Prova:** `test_v55_judge_date.py::test_rejudge_plan_takes_dated_answers_only_passed_or_failed`,
  `test_r11_judge_honest.py::test_rejudge_by_date_only_keeps_every_undated_verdict_and_saves_the_first_pass` e
  `::test_rejudge_never_drops_a_verdict_the_judge_refuses_or_the_budget_cuts`.

## 2. A 1ª passada fica guardada e a evidência não se contradiz (§2)
- **O quê:** o veredito rejulgado guarda `first_pass` e `rejudge_reason`. O judge.json ganha o bloco `rejudge`, tirado
  sempre dos vereditos (`summarize`): a regra, quantos por motivo, como estavam na 1ª passada, quantos viraram, e
  fundamentadas e úteis antes → depois por split e no total. O resumo `judge` de cada live_*.json é reescrito
  (`sync_live_summaries`, também no juiz inteiro de novo) e o antigo fica em `judge_first_pass`, com a data que o juiz
  usou. O bloco do juiz no RESULTS (`fill_readme.judge_block`) mostra a regra e a tabela 1ª passada → rejulgado por
  split. `python -m evals.judge --restore-first-pass <judge.json da 1ª passada>` refaz, sem LLM, um rejulgamento feito
  pela regra antiga: os sem data voltam ao veredito da 1ª passada e os com data guardam `first_pass`. Recusa o arquivo
  que não é a 1ª passada desta bateria.
- **Por quê:** o live_official.json commitado dizia 19/30 fundamentadas ao lado do 30/30 publicado, sem antes → depois.
- **Prova:** `test_r11_judge_honest.py::test_restore_first_pass_redoes_an_old_asymmetric_rejudge_without_llm`,
  `::test_results_judge_block_shows_first_pass_to_rejudged_by_split_with_the_rule` e
  `::test_live_summary_is_the_one_run_evals_writes`. Dry run sobre uma cópia da evidência do ensaio, com a 1ª passada
  tirada do histórico do git: os rejulgados passam a ser só os datados, os reprovados sem data voltam, o oficial
  continua 30/30 e todos os resumos ficam coerentes.

## 3. Juiz × pessoas sobre o MESMO texto, com conjunto congelado (§1, itens 2 e 4(b)–(d))
- **O quê:** a página de rotulagem congela `evals/validation/<amostra>.json` antes de alguém rotular
  (`evals.label.freeze_page`). O arquivo guarda o texto e a entrada do juiz de cada item, as checagens, o veredito do
  juiz sobre esse texto (sem o `reason`), o juiz que o deu (modelo e `prompt_sha`), a bateria (git_sha) e o motivo da
  escolha. Ele guarda só ids de caso, nunca o id cego. O `--report` casa cada rótulo pelo id e pelo texto
  (`FROZEN_RULE`). Com o conjunto congelado, a validação continua valendo depois de bateria nova. Sem ele (página
  antiga), vale só o rótulo da resposta de hoje. O rótulo de outro texto sai de toda conta (humano × automático,
  held-out, entre humanos e juiz × humano) e é listado em `rotulos_de_outra_bateria`. O relatório declara a bateria
  (`bateria`) e avisa o veredito de outro juiz ou a falta de veredito (`aviso_juiz`).
  `python -m evals.judge --validation` rejulga com o juiz de hoje só os textos congelados que ainda não têm veredito
  dele, reaproveitando canários e calibração. A importação grava no CSV o texto que a pessoa viu. A `sample` da página
  passa a incluir os textos, para a mesma amostra numa bateria nova não sobrescrever o congelado de antes. As páginas
  já publicadas continuam importáveis (sal e human_selection.json como antes).
- **Por quê:** 35 dos 37 rótulos eram de outra bateria. O juiz × humano publicado não se reproduzia, e o relatório
  casava o rótulo real só pelo id.
- **Prova:** `test_r11_judge_honest.py::test_label_of_an_old_text_stays_out_of_every_count_and_is_listed`,
  `::test_frozen_page_keeps_the_validation_after_a_new_battery`,
  `::test_changed_judge_warns_and_validation_rejudges_only_the_frozen_texts` e
  `::test_two_texts_of_the_same_case_are_two_items_never_one`. Ajustado: `test_k1_perturb.py::
  test_label_of_an_answer_that_changed_since_is_left_out`, onde o congelado vale e, sem ele, o rótulo fica fora como
  antes.

## 4. Held-out sem `reason` (§19)
- **O quê:** nos splits heldout*, e na adulterada de uma resposta deles (`original_split`), o veredito grava só
  booleanos, nota e `failure_type`. O veredito reaproveitado de antes da regra perde o motivo no próximo julgamento.
  `python -m evals.judge --drop-blind-reasons` limpa, sem LLM, o que já está commitado.
- **Por quê:** o motivo do juiz descreve o erro, e ler o erro do conjunto cego fez o held-out virar conjunto de
  desenvolvimento em 4 classes de erro.
- **Prova:** `test_r11_judge_honest.py::test_heldout_verdicts_never_keep_the_reason`.

## 5. Uma checagem de coerência no `scripts/check.py`
- **O quê:** a etapa "evidência do juiz coerente" (`python -m evals.judge --check`, `coherence_problems`) confere,
  sem LLM, quatro coisas. O resumo de cada live_*.json bate com o judge.json, e o arquivo com veredito rejulgado
  guarda `judge_first_pass`. Todo veredito é de uma linha que existe e do texto de hoje (`answer_sha`). Nenhum
  veredito do held-out tem `reason`. O human_review.json é o que o `--report` dá hoje.
- **Prova:** `test_r11_judge_honest.py::test_check_flags_a_contradicting_summary_and_verdicts_of_another_text`.

## 6. Menor
- `judge_into`: a recusa do juiz numa rodada anterior do mesmo split não faz mais o juiz pular a resposta nova com o
  mesmo id (`::test_new_battery_of_a_split_is_judged_where_the_old_one_was_refused`).
- O texto do prompt do juiz foi para `PROMPT` (identidade `PROMPT_SHA`) sem mudar um caractere
  (`::test_the_judge_prompt_text_did_not_change`). Replay e cassetes continuam valendo.
