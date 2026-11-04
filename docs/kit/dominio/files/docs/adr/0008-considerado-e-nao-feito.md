# ADR 0008 — Considerado e não feito (com o número que decidiu)

Status: registrado no kit v5.4 (03/11/2026).

**Contexto.** Cada item abaixo foi medido ou pesado e ficou de fora. Registrar o que NÃO entrou evita refazer a
medida no relógio e responde "por que não X?" com número.

| Considerado | Medido | Por que não |
|---|---|---|
| Busca híbrida BM25 + denso como padrão | caminho do agente, Recall@3 / Recall@5 / MRR: híbrido 10/600 0,895 / 0,895 / 0,794 contra dense+cross 0,868 / 0,921 / 0,789; sem filtro de idioma, o BM25 sobre a pergunta em inglês tirou o trecho de um cenário oficial do top-5 nas 3 repetições (oficiais 96,7% → 90%) | perde no Recall@5, o que o redator lê; o dense+cross é o validado ao vivo. Fica disponível (`RETRIEVER=hybrid`, BM25 só no idioma do corpus, `rag.lexical_fits`) |
| Rerank sobre 20 candidatos (pool 20) | 0,842 / 0,921 / 0,776, p95 6,1 s (× 2,8 s) | o dobro da latência sem ganho no top-5 |
| Trecho de 1000 caracteres no rerank | 0,842 / 0,868 / 0,759 | piora as três medidas |
| Híbrido com pool 20 e 1000 caracteres | 0,842 / 0,868 / 0,816, p95 7,0 s | MRR um pouco maior, Recall@5 menor e latência 2,5× |
| Juiz de outra família de modelo | — (não medido) | a troca existe (`JUDGE_PROVIDER=openai_compat`), mas exige outra chave e outra calibração no relógio. O que garante a medida é a validação contra pessoas com a regra fixada antes de medir (≥ 10 por classe, TPR e TNR ≥ 0,8, negativos reais escolhidos sem depender do juiz): o resultado de cada entrega sai no bloco humano de `docs/RESULTS.md` (gerado) e, enquanto ele não passa, a nota do juiz vale só como regressão |
| Janelas pelo máximo puro, z-score, janela maior, janela só em trecho longo, cross reordenando ou percentil sem o desconto do trecho | no gold de uma entrega anterior: o máximo puro perdia 1 a 3 perguntas (a sobra curta do fim do trecho ganhava cosseno), o z-score 7, as outras variantes a mesma perda, o percentil sem desconto 1 | a regra que ficou é o percentil 95 com o ganho típico do trecho descontado (ADR 0004, emenda) |
| Escolher o buscador no relógio (`--choose-retriever`) | V5: com 8 subagentes na mesma CPU, p95 do rerank 2,9–3,5 s × 1,1–1,25 s com a máquina parada; foi o caminho crítico | latência só se mede com a máquina parada: a escolha é do kit, antes do relógio (ADR 0004) |

**Decisão.** Padrão mantido: denso (e5-large) + cross-encoder (bge-reranker-v2-m3), top-10, 600 caracteres, com a
ordem do denso e a nota do cross-encoder só no portão sem fonte (`rerank_order: base`, desde o kit v5.5.1); juiz
do kit com a regra de validação.

**Consequências.** Nenhuma variante ganha no top-5 sem custar latência. O juiz da mesma família fica declarado como
limite (README §3); a validação contra pessoas é o que o valida, e o estado dela é o do bloco humano (gerado), nunca um
número copiado de outra entrega.

**Números.** Variantes medidas no caminho do agente, gold da entrega anterior (38 perguntas), commit `29222e0`:
pool 20 0,842/0,921/0,776 (6,1 s); 1000 caracteres 0,842/0,868/0,759; híbrido 10/600 0,895/0,895/0,794;
híbrido 20/1000 0,842/0,868/0,816 (7,0 s). Prova do método:
`tests/test_v54_retrieval_method.py::test_published_retrieval_is_the_agent_path_with_the_base_beside_it`,
`tests/test_v54_retrieval_method.py::test_bm25_only_fuses_when_the_query_is_in_the_corpus_language`.
