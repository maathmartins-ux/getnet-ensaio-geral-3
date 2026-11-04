# official-06 ("How does receivables advance (antecipação) work with Getnet?"): causa da rodada sem o fato D+1/taxa

Medida offline (domínio do r14 em `6645d77`, buscador padrão, US$ 0), Maestra B, 04/11.

O fato que falta é o 2º regex do caso: prazo/condição/custo (`D+1`, `D-3`, `dias úteis`, `taxas adicionais`…). A
checagem lê a RESPOSTA, então o que decide é o redator receber um trecho com ele:
`sup-antecipacao-de-vendas-10` e `-11` (janelas D+1/D-3) e `sup-duvidas-15` ("sem taxas adicionais"). O
`sup-duvidas-100` casa a regex por acaso ("aluguel" de máquina) e vem em todas as rodadas.

Fontes por rodada (o fato na resposta = `facts`):

| bateria | rodada | facts | trechos do fato que vieram |
|---|---:|---|---|
| r14 rodada 1 | 0 | ok | duvidas-15, antecipação-10 |
| r14 rodada 1 | 1 | **falta** | nenhum (a 2ª busca trouxe taxas da loja virtual: taxas-18, link-08) |
| r14 rodada 1 | 2 | ok | duvidas-15, antecipação-10 |
| medida do faq.md | 0 | **falta** | nenhum (só 5 fontes: uma busca só) |
| medida do faq.md | 1, 2 | ok | duvidas-15, antecipação-10/11 |
| parcial no motor (ao vivo) | 0, 1, 2 | ok | duvidas-15 e/ou antecipação-09/10/11 |

Posição de cada trecho do fato na busca (top-15; None = fora):

| consulta | antecipação-10 | antecipação-11 | duvidas-15 |
|---|---:|---:|---:|
| How does receivables advance (antecipação) work with Getnet? | — | — | 5 |
| Como funciona a antecipação de recebíveis na Getnet? | — | — | 4 |
| antecipação de recebíveis como funciona | — | — | — |
| antecipação de vendas prazo taxa | 2 | 4 | — |
| como antecipar minhas vendas | — | — | 4 |

Causa: as janelas D+1/D-3 só entram quando o router escreve uma 2ª busca sobre prazo/taxa, e o `sup-duvidas-15` fica
em 4º–5º na pergunta crua (na beira dos 5 que o redator lê). Quando o router não escreve essa 2ª busca (2 de 9
rodadas medidas), a resposta descreve o mecanismo sem prazo nem custo. É variação do plano de busca, não do redator
nem do corpus (o fato está no índice).

Decisão: nenhuma mudança agora. Na rodada ao vivo do parcial no motor o caso saiu 3/3, e a correção possível (o
router pedir sempre uma busca de "prazo e condições" em "como funciona X") é regra de prompt do domínio, que muda o
pedido de todo caso "como funciona" e precisaria de outra rodada ao vivo para medir. Fica declarada como variação
conhecida (1 caso, ~2 de 9 rodadas).
