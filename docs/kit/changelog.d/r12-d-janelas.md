# Frente R12-D: busca densa com janelas (a parte certa de um trecho misturado)

Base: avaliação cega da rodada 11 (8,92; meta ≥ 9,0), `r12/reguas_r11.md`: régua 1 TOP8 #2, régua 2 TOP8 #2 e
régua 3 TOP8 #1/#4 (official-01 diz nas 3 rodadas que as fontes não descrevem a Get Clássica; official-05 diz que
não trazem os passos do teste de comunicação). Medidas offline sobre uma cópia do ensaio (`grade_snap11a`: `data/`,
`evals/retrieval.d/`, cassetes), sem LLM e sem bateria ao vivo. Ideias (sem código copiado): MaxP de Dai & Callan
(SIGIR 2019, nota do documento = a da melhor passagem em janelas sobrepostas), recuperação small-to-big / parent
document (busca pela parte, entrega o trecho) e o viés de posição dos embeddings ("Dwell in the Beginning", 2024: o
vetor pesa o começo do texto).

## 1. Índice denso com janelas; a janela só conta quando se destaca

- **O quê:** `rag.window_spans` corta cada trecho longo em janelas de linhas inteiras (alvo 240 caracteres, passo
  de 120, nenhuma menor que o alvo: a última fica ancorada no fim). `HybridRetriever(windows=...)` embute as janelas
  com o mesmo cabeçalho do trecho (cache em disco por texto, como os trechos) e a nota densa do trecho passa a ser a
  da melhor janela quando ela casa melhor que o trecho inteiro e o ganho, descontado o ganho típico do trecho
  (`_window_bias`: os outros trechos do corpus como sondas, sem consulta), fica acima de zero e no percentil 95 dos
  ganhos da consulta. O `Hit` leva a janela (`window`); ids, textos e citações continuam os do trecho, e o redator
  recebe o trecho inteiro. Nome do buscador: `dense+windows`.
- **Por quê:** o trecho prod-taxas-02 junta a tabela de taxas do Get Tap (os ~600 primeiros caracteres) e o cartão
  de recursos da Get Clássica (aproximação, Pix/QR, comprovante, bobina, Wi-Fi e chip 3G). O vetor do trecho inteiro
  puxa para a tabela: ele ficava em 12º–18º no pool para "Get Clássica", "Get Clássica recursos características" e
  "What can the Get Clássica do?", fora dos 10 que o cross-encoder lê. Mesmo com a busca corretiva da R11-E, o
  redator do official-01 nunca o recebia. O mesmo com o sup-duvidas-07 (passos do teste de comunicação, misturados
  com o Chip Algar): 26º–27º para "teste de comunicação passos".
- **Medidas (gold do ensaio, 48 com fonte e 22 sem, dense+cross:base):** antes 0,917 / 0,938 / 0,858 (Recall@3 /
  Recall@5 / MRR), portão em −4,986 com 100% dos com fonte respondidos e 90,9% dos sem fonte recusados. O que não
  serviu e por quê: máximo puro com a sobra do fim virando janela sozinha deu 0,844 / 0,896 / 0,771 (janela de 23
  caracteres "Respondeu à sua dúvida?" e uma pergunta de FAQ sem a resposta ganhavam cosseno); sem janela curta,
  0,875 / 0,917 / 0,844; janela de 300, ou só em trecho > 480, ou o cross reordenando, a mesma perda; z-score pior
  (7 perguntas); percentil sem o desconto do trecho, 1 pergunta perdida (Santander/Pix). Com o desconto, o gold fica
  igual ao de antes nos percentis 90 a 99, e os alvos sobem em 90 e 95: prod-taxas-02 em 1º–2º nas 4 consultas em
  português (6º nas 2 em inglês, dentro do pool) e sup-duvidas-07 em 1º–2º nas 3 do teste de comunicação.
- **Prova:** `tests/test_r12_windows.py::test_a_matching_window_lifts_the_mixed_chunk_to_the_top`,
  `::test_windows_are_whole_lines_never_shorter_than_the_size_and_the_last_reaches_the_end`,
  `::test_short_or_single_line_chunks_get_no_window`, `::test_a_chunk_whose_windows_always_gain_is_not_lifted`,
  `::test_only_the_top_slice_of_window_gains_counts`, `::test_numpy_and_python_window_scores_rank_the_same`,
  `::test_window_vectors_are_cached_on_disk_by_text`.

## 2. Ids e citações iguais; o cross-encoder do portão lê a janela

- **O quê:** `rag.cross_text`: com janela e trecho maior que o corte (600 caracteres), o cross-encoder lê a partir do
  começo da janela (recua por linhas inteiras se o resto não enche o corte); sem janela, ou trecho que cabe, o mesmo
  texto de antes. A nota do portão mede a parte que casou. O redator, as fontes e as citações continuam com o trecho.
- **Por quê:** o portão lia os primeiros 600 caracteres do prod-taxas-02, a tabela do Get Tap, não o cartão.
- **Prova:** `tests/test_r12_windows.py::test_the_gate_cross_encoder_reads_from_the_matching_window`,
  `::test_cross_text_falls_back_to_the_old_cut_and_fills_the_budget_at_the_end`,
  `::test_ids_texts_and_citations_stay_those_of_the_whole_chunk`, `::test_windows_off_is_the_search_of_before`.

## 3. Ligado por padrão no kit; a escolha gravada sem a chave fica como foi medida

- **O quê:** `config.KIT_RETRIEVER["windows"] = True`; `config.rag_windows()` (RAG_WINDOWS=on|off vence; senão o
  `windows` da escolha; escolha gravada sem a chave = sem janelas). `config.choice_gate()` só aplica o limiar gravado
  à mesma busca (com ou sem janelas). `--choose-retriever --fast` mede o cross sobre o denso com janelas (as mesmas 2
  configurações com cross, nas duas ordens) e o denso sem e com janelas sem cross (segundos cada: a diferença entre as
  duas é o efeito das janelas no domínio, e a com janelas é o "sem o cross" da frase gerada do README); `--windows`
  mede cada denso com e sem. A configuração medida leva `windows` explícito (o `--verify` refaz a busca gravada,
  qualquer que seja o ambiente); a chave do cache da medida offline (`run_evals._retrieval_cache_key`) inclui o estado
  das janelas.
- **Por quê:** a regra da frente: ligar por padrão só se o gold não piorar (não piorou: as mesmas métricas e o mesmo
  portão), sem mudar a escolha gravada do ensaio nem o portão.
- **Prova:** `tests/test_r12_windows.py::test_a_recorded_choice_without_the_key_keeps_the_search_it_measured`,
  `::test_a_choice_with_windows_carries_its_gate_only_with_windows`, `::test_without_a_choice_the_kit_default_decides`,
  `::test_app_retriever_follows_the_switch_without_a_stale_cache`, `::test_eval_config_names_and_builds_windows_explicitly`,
  `::test_fast_choice_measures_the_kit_package_and_windows_flag_measures_both`,
  `::test_readme_sentence_of_a_windowed_choice_keeps_the_without_cross_comparison`.
- **Depois do merge:** o bloco gerado `retriever` do README passa a dizer `dense+windows+cross:base` (o nome sai do
  `KIT_RETRIEVER`): `python scripts/fill_readme.py` antes do `check.py`, senão o `--check` acusa o bloco.

## Medida final (dense+windows+cross:base, percentil 95, a mesma máquina)

- Gold: 0,917 / 0,938 / 0,858, igual ao de antes; portão recalibrado −4,986 (o mesmo), 100% / 90,9%, e o mesmo no
  limiar gravado. Latência por busca p50 1.050 ms / p95 1.403 ms (gravado sem janelas: 1.092 / 1.312; máquina
  compartilhada, dentro do ruído).
- Caminho do agente nas consultas gravadas do official-01 (`["Get Clássica","Get Smart"]` + as palavras do cliente):
  o prod-taxas-02 e o prod-ofertas-maquininha-02 (os dois cartões da Get Clássica) entram no top-5 do redator.
- O que muda no que o redator recebe (cassetes do ensaio, buscas do plano e corretivas refeitas offline, portão
  aberto): o conjunto do top-5 muda em 207 de 460 buscas gravadas, em todos os 14 splits; o replay desses turnos
  perde a chave e os splits precisam ser regravados. Fatos esperados (`expect.facts`) nos trechos do redator, nos
  turnos gravados dos casos que os têm: 5 ganhos (o 3G/bobina do official-01 nas 3 rodadas, o "Get Conta" do
  official-04 em 2) e 0 perdidos.

## Custo

- Corpus do ensaio: 300 vetores a mais (janelas de 133 dos 193 trechos), +6,4 MB no cache em disco e ~18 MB de RSS
  com o índice montado (37 MB contra 19 MB). Busca densa: +0,3 ms (0,7 → 1,0 ms na mediana); o cross-encoder lê os
  mesmos 5 pares de 600 caracteres.
- Montagem a frio: vetorizar as janelas custou 127 s de CPU na máquina compartilhada (os trechos, 143 s): +~90% do
  tempo de vetorização do corpus, uma vez por corpus (cache por texto; a imagem Docker já sai com os vetores). O pico
  de RAM é o mesmo da vetorização dos trechos (~2,1 GB com o e5-large), não se soma.
