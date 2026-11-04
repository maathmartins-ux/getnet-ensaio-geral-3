# Medida da correção do faq.md (b/faq-parcial, Maestra B, 04/11)

## Hipótese (escrita antes de gastar)

A regra "antes de escrever MISSING, confira se o que falta está NOMEADO na pergunta" faz o redator parar de marcar
parcial por item vizinho (official-01, 05, 06 na rodada 1 do ensaio 14). Esperado, official e memory `--repeat 3`
ao vivo + juiz, contra a rodada 1 do ensaio 14 (`fdcb685`):

| medida | antes (r14, fdcb685) | esperado depois | entra se |
|---|---:|---:|---|
| Oficiais completas (resolved by_split) | 17/30 = 0,57 | ≥ 20/30 = 0,67 | sobe |
| Oficiais parciais | 9/30 = 0,30 | ≤ 5/30 | cai |
| Juiz oficiais fundamentadas / úteis | 30/30 / 30/30 | 30/30 / 30/30 | não cai |
| Memória pass@1 | 0,83 | ≥ 0,83 | não cai |
| Juiz memória fundamentadas / úteis | 47/48 / 47/48 | ≥ 47/48 | não cai |

Não deve mudar: official-04 (busca: `sup-pix-09` fora do top-5; é a tarefa 4) e official-08 (códigos 51/05 sem
documento). Gasto previsto ~US$ 3,5 (rodada 1: official US$ 0,65 + memory US$ 2,58) + juiz; teto da tarefa US$ 5.

## Resultado

Medido em 04/11 (~17:00 UTC) num repositório de teste igual ao r14 no `6645d77` + só o patch (`2fc4ff1`), official e
memory `--repeat 3` ao vivo + juiz (Opus), contra a rodada 1 do ensaio 14 (`fdcb685`). Caso a caso do juiz:
[JUDGE_DIFF_FAQ_PARCIAL.md](JUDGE_DIFF_FAQ_PARCIAL.md).

| medida | antes (r14, fdcb685) | depois (patch) | esperado | resultado |
|---|---:|---:|---:|---|
| Oficiais completas | 17/30 = 0,57 | **19/30 = 0,63** | ≥ 20/30 | subiu, abaixo do esperado |
| Oficiais pass^k (resolvidas) | 0,50 | 0,60 | — | subiu |
| Oficiais parciais | 9/30 | **6/30** | ≤ 5/30 | caiu, quase o esperado |
| Juiz oficiais fundamentadas / úteis | 30/30 / 30/30 | **28/30 / 28/30** | 30/30 | **caiu 2** |
| Memória pass@1 | 0,833 | 0,854 | ≥ 0,833 | ok |
| Juiz memória fundamentadas / úteis | 47/48 / 47/48 | **46/48 / 47/48** | ≥ 47/48 | **caiu 1** |

Por caso (completas, parciais em 3 rodadas): official-05 0/3 → 1/3 (parcial 3 → 2), official-08 2/3 → 3/3, official-01
0/3 → 0/3 (parcial 3 → 2), official-06 igual (0/3, 2 parciais: o fato D+1/taxa varia com a busca), official-04 igual
(0/3: busca, tarefa b/busca-pix).

As 3 reprovações novas do juiz, com o motivo: official-04 run 0 (escreveu que as fontes não dizem se a conta bancária é
obrigatória; é a busca do Pix, `sup-pix-09` fora do top-5, não o MISSING de item vizinho), official-01 run 1 (traduziu
errado um item da lista "Conta e cartão grátis / Recebimento em 2 dias"; sem relação com MISSING) e memory-16 run 0
(`unsupported_claim`). Com n = 3 rodadas, 1 a 2 vereditos estão no ruído, mas a regra combinada antes de medir era
"entra só se as completas subirem sem queda em fundamentadas/úteis nem na memória".

**Decisão pela regra: não entra no kit como está.** Fica declarado. A causa que sobra nos parciais (01, 05, 06) não é
mais o MISSING de item vizinho sozinho: é variação de busca e de redação. A lição 7 do ensaio 14 já apontava a raiz:
decidir o parcial no MOTOR (MISSING só conta se cobre item que o planner listou), não no prompt.

Gasto da tarefa: US$ 6,09 (teto aprovado US$ 5,2, estourado em US$ 0,89): 0,21 de um gate offline rodado por engano com
o provedor ao vivo; 1,34 de uma rodada parada por usar o domínio errado (o do kit atual, não o do r14); 3,03 das
conversas desta medida; 1,51 do juiz (77 vereditos novos). O estouro foi o juiz: estimei ~US$ 0,4 e custou 1,51.
