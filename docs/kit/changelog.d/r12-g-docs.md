# Frente R12-G: docs sem jargão interno

- **O quê:** ADR 0002 (contexto das réplicas), ADR 0004 (status, alternativas e emenda), ADR 0008 e
  docs/SECURITY_ASI.md sem "frente X", "rodada N" nem "régua"; versões do kit no lugar das rodadas.
- **Por quê:** uma régua da rodada 11 leu "docs que tratam de otimizar para a régua (ex.: docs/adr/0002:5)" e outra
  citou o jargão interno ("frente K, R, T, Q, D", "rodada 11") como defeito de Judgment.
- **Prova:** `tests/test_security_asi.py` verde (o mapa continua citando só arquivos e testes que existem).
- **O quê:** o bloco ao vivo do `docs/RESULTS.md` abre com UMA tabela (uma linha por split: a checagem que define o
  split com IC95 e n, execuções sem falha, casos que falharam com quantas vezes, p50 · p95, gasto); as outras taxas de
  cada split ficam num bloco recolhido. No offline, a tabela métrica × split também vai para um bloco recolhido e à
  vista ficam resolvidas, gate, red team e busca (o que reprova o CI).
- **Por quê:** as 3 réguas da rodada 11 citaram "tabelas de IC95 repetidas por split no lugar de explicação"
  (RESULTS.md:11-37 e 75-221), a régua pune esse padrão em Judgment e Evaluation.
- **Prova:** `tests/test_r12_results_table.py` (uma tabela, oficiais primeiro, falhas contadas e cortadas, status fora
  de `complete` à vista, linha vazia antes do HTML); os testes de docs gerados continuam verdes.
- **O quê:** `expect.after_human` no avaliador (`evals/run_evals.py`): agentes que rodam no mesmo turno DEPOIS da
  resposta do humano (rota depois da escalada respondida) → `after_human_acc` ("plano seguiu depois do humano").
- **Por quê:** uma régua da rodada 11 procurou nos `live_*.json` um passo de agente depois do humano e não achou; o
  split hitl só tinha pedido direto de humano. A checagem deixa o domínio escrever casos em que a resposta do
  atendente alimenta o passo seguinte (ex.: o atendente dá o id da venda e o agente consulta).
- **Prova:** `tests/test_r12_after_human.py`.
