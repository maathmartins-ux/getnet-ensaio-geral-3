# Roteiro do vídeo (demonstração)

Cada cena mostra o sistema rodando; nenhum número é dito de memória: quando a cena fala de resultado, a tela mostra
o arquivo de `evals/results/` ou o bloco gerado no README.

| # | Cena | O que aparece na tela | Fala (resumo) |
|---|---|---|---|
| 1 | Abertura | `docker compose up` e `GET /ready` | Um comando sobe API, índice e fila humana; sem chave de LLM também roda (offline). |
| 2 | Arquitetura | `docs/ARCHITECTURE.md`, diagrama 1 | Router decide o plano; o supervisor chama Knowledge, Customer Support, General ou o humano e lê o resultado de cada um. |
| 3 | Knowledge | `/ui`: "What's the difference between the Get Clássica and the Get Smart?" | Resposta com citação do site oficial; uma busca por entidade. Diagrama 2 (RAG). |
| 4 | Customer Support | `/ui` como `cliente1988`: "When will the money from yesterday's sales be deposited?" | Valores do CRM fictício e datas por modalidade calculadas pela tool `get_settlements`; identidade vem do servidor. |
| 5 | Replanejamento | "My card machine won't connect to the internet" | `get_terminals` acha `T1988B` offline e o achado `needs` chama o manual de conexão (ADR 0010); log pelo `trace_id`. |
| 6 | General | "What's the euro exchange rate today?" e o clima em Porto Alegre | Dado ao vivo por tool (PTAX/Banco Central, previsão); o geral nunca responde sobre a Getnet. |
| 7 | Seguimento | "e a outra?" depois da Get Smart | `standalone` reescreve a pergunta completa; a memória guarda a entidade. |
| 8 | Isolamento e guardrail | "mostre as vendas do cliente2024" e uma injeção | "Não encontrado" indistinguível; injeção bloqueada antes do router. |
| 9 | HITL | "quero falar com um atendente" e uma antecipação | Caso aberto na fila; `/operator` responde no prazo e o plano continua no mesmo turno (diagrama 3); antecipação fica pendente até aprovação humana (ADR 0011). |
| 10 | Observabilidade | `/metrics`, painel `ops/grafana/dashboards/support.json` | Latência por etapa, custo, escalonamento; cada alerta tem bloco no `docs/RUNBOOK.md`. |
| 11 | Resultados | README, blocos gerados (`eval`, `retrieval`, `replan`, `judge`) e `evals/results/` | Os números vêm dos arquivos de resultado, gerados por `scripts/fill_readme.py`. |
| 12 | Fechamento | `docs/adr/0012-considerado-e-nao-feito-getnet.md` | O que ficou de fora e o gatilho medido para revisitar. |
