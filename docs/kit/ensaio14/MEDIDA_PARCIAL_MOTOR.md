# Medida do parcial no motor (b/parcial-motor, Maestra B, 04/11) — re-pontuação SEM LLM

Regra (src/app/coverage.py, ligada no `faq_agent`): uma linha `MISSING` só deixa a resposta parcial se cobre um item
que o cliente pediu (termo em comum com a pergunta, a versão autônoma e a parte do agente, com glossário e grupos de
conceito custo/taxa, precisa/obrigatório, prazo/quando; o assunto de "como funciona X" e de "diferença entre A e B" não
conta como atributo pedido). Item vizinho: a resposta fica `ok`, o item vai para `facts.missing_dropped` e a frase de
ausência dele sai do texto mostrado ao cliente. Na dúvida (sem termo para comparar), continua parcial.

Como foi medido: `docs/kit/ensaio14/rescore_parcial.py` sobre as respostas GRAVADAS (o mesmo texto que o juiz julgou;
nenhuma chamada de LLM, US$ 0). Itens do que falta = as frases de ausência da resposta; perguntas = a mensagem e os
turnos anteriores do caso (mais conservador que o motor). Resolvida = a regra de sempre (regex de fato + `grounded`
do juiz). Rodada 1 do ensaio 14 (`fdcb685`) e a medida do faq.md (`2fc4ff1`).

Resumo:

| bateria | completas | parciais | pass^k |
|---|---:|---:|---:|
| r14 rodada 1, official | 17/30 → **26/30** (0,57 → 0,87) | 9 → **0** | 0,50 → **0,80** |
| medida do faq.md, official | 19/30 → **25/30** (0,63 → 0,83) | 6 → **0** | 0,60 → **0,70** |

O que fica de fora das completas, nos dois: official-04 (o que falta é a própria pergunta, "preciso de conta
bancária": continua parcial, e a regex de fato não acha o critério; é a busca do Pix), a rodada de official-06 em
que falta o fato D+1/taxa (variação de busca) e, na medida do faq, a official-01 run 1 que o juiz reprovou. Memória: o split não conta completas; 6 das 20
respostas parciais viram completas, todas de item não pedido (conferência abaixo).

Conferência à mão (feita pela Maestra B; para a Maestra A conferir): nenhuma frase descartada é de item pedido. Duas
frases que o `states_absence` pega sem ser falta ("A proposal you don't confirm expires after 15 minutes", "Other
customers have a different table that I can't see") ficam vizinhas e não mudam nada (o motor só tira do texto frase
com termo em comum com o MISSING descartado). Caso mais discutível: memory-02 run 1 ("And the other one, the Get
Clássica?" depois de "What is the Get Smart?"; falta "a full description of its features or hardware"): o cliente
pediu o que é a máquina, e a resposta disse; a descrição completa do hardware não foi pedida.

### r14 official (live_official.json, juiz: judge.json, fdcb685)

| split | completas | parciais | pass^k | completas + parciais |
|---|---:|---:|---:|---:|
| official | 17/30 → **26/30** | 9 → **0** | 0.5 → **0.8** | 26 → 26 |

| caso | completas antes → depois | parciais antes → depois |
|---|---:|---:|
| official-01 | 0/3 → 3/3 | 3 → 0 |
| official-05 | 0/3 → 3/3 | 3 → 0 |
| official-06 | 0/3 → 2/3 | 2 → 0 |
| official-08 | 2/3 → 3/3 | 1 → 0 |

Cada frase de ausência das respostas parciais, com a decisão:

| caso | rodada | decisão | frase de ausência (o que falta) | termos em comum com a pergunta |
|---|---:|---|---|---|
| official-01 | 0 | **vira completa** | (vizinho) I couldn't find the Get Smart's debit and credit rates per brand, so I can't compare its rates with the Clássica's. | — |
| official-04 | 0 | parcial | (pedido) The sources don't say outright that you need a bank account to receive Pix sales, but they do show where the money goes. | accou, bank, need, pix, recei, sale |
| official-04 | 0 | parcial | (pedido) The sources don't say whether you can receive Pix sales in an account at another bank instead of a Get Conta. | accou, bank, pix, recei, sale |
| official-05 | 0 | **vira completa** | (vizinho) The sources don't say what to do if there's still no signal after the test. | — |
| official-06 | 0 | **vira completa** | (vizinho) I didn't find the fee for a standard manual advance. | — |
| official-08 | 0 | **vira completa** | (vizinho) The data doesn't show a terminal fault on T1988A. | — |
| official-01 | 1 | **vira completa** | (vizinho) **What I couldn't find:** The sources don't give technical specs or separate rates for each machine. | — |
| official-04 | 1 | parcial | (pedido) The sources I found don't say a bank account is mandatory. | accou, bank, manda |
| official-04 | 1 | parcial | (pedido) The sources don't say whether you can receive Pix sales in an account at another bank instead of a Get Conta. | accou, bank, pix, recei, sale |
| official-05 | 1 | **vira completa** | (vizinho) The sources don't say what to do if there is still no signal after these steps. | — |
| official-06 | 1 | **vira completa** | (vizinho) A proposal you don't confirm expires after 15 minutes. | — |
| official-06 | 1 | **vira completa** | (vizinho) I didn't find the fee rate for the advance or a step-by-step request process. | — |
| official-01 | 2 | **vira completa** | (vizinho) I don't have the Get Smart's own rates or receipt timing, or current 2026 rates for either machine. | — |
| official-04 | 2 | parcial | (vizinho) It probably does, but the sources don't say so outright. | — |
| official-04 | 2 | parcial | (pedido) The sources don't say whether a bank account is mandatory, or whether you can receive in another bank's account instead of the Get Conta. | accou, bank, manda, recei |
| official-05 | 2 | **vira completa** | (vizinho) The sources don't say what to do if these steps fail. | — |
| official-06 | 2 | **vira completa** | (vizinho) Other customers have a different table that I can't see [7]. | — |
| official-06 | 2 | **vira completa** | (vizinho) I couldn't find the advance fee or rate for physical-terminal sales. | — |

### faq official (faq_official.json, juiz: faq_judge.json, 2fc4ff1)

| split | completas | parciais | pass^k | completas + parciais |
|---|---:|---:|---:|---:|
| official | 19/30 → **25/30** | 6 → **0** | 0.6 → **0.7** | 25 → 25 |

| caso | completas antes → depois | parciais antes → depois |
|---|---:|---:|
| official-01 | 0/3 → 2/3 | 2 → 0 |
| official-05 | 1/3 → 3/3 | 2 → 0 |
| official-06 | 0/3 → 2/3 | 2 → 0 |

Cada frase de ausência das respostas parciais, com a decisão:

| caso | rodada | decisão | frase de ausência (o que falta) | termos em comum com a pergunta |
|---|---:|---|---|---|
| official-01 | 0 | **vira completa** | (vizinho) The sources don't give the Get Smart's rate table or rental amounts, so I can't compare fees directly. | — |
| official-04 | 0 | parcial | (pedido) The sources don't say whether a bank account is mandatory. | accou, bank, manda |
| official-04 | 0 | parcial | (pedido) They also don't say whether you can receive Pix sales in an account at another bank. | accou, bank, pix, recei, sale |
| official-05 | 0 | **vira completa** | (vizinho) The sources don't say what to do if the test still fails. | — |
| official-04 | 1 | parcial | (pedido) The sources don't say a bank account is mandatory. | accou, bank, manda |
| official-04 | 1 | parcial | (pedido) The sources don't say whether you can receive Pix sales in an account at another bank instead of Get Conta. | accou, bank, pix, recei, sale |
| official-05 | 1 | **vira completa** | (vizinho) The sources don't cover Wi-Fi setup or what to do if the test still fails. | — |
| official-06 | 1 | **vira completa** | (vizinho) The sources I found don't give the advance fee. | — |
| official-01 | 2 | **vira completa** | (vizinho) The sources don't give a Get Smart card rate table, so I can't compare its rates with the Get Clássica's. | — |
| official-04 | 2 | parcial | (pedido) Depends: the sources don't say that a bank account is required to receive Pix sales. | accou, bank, pix, recei, requi, sale |
| official-04 | 2 | parcial | (pedido) The sources don't say whether you can receive Pix sales in an account at another bank instead of Get Conta. | accou, bank, pix, recei, sale |
| official-06 | 2 | **vira completa** | (vizinho) The sources I found don't give the advance fee percentage. | — |

### r14 memory (r14_memory.json, juiz: judge.json, fdcb685)

| split | completas | parciais | pass^k | completas + parciais |
|---|---:|---:|---:|---:|

| caso | completas antes → depois | parciais antes → depois |
|---|---:|---:|

Cada frase de ausência das respostas parciais, com a decisão:

| caso | rodada | decisão | frase de ausência (o que falta) | termos em comum com a pergunta |
|---|---:|---|---|---|
| memory-02 | 0 | parcial | (pedido) The sources don't have a detailed technical description of the Get Clássica, such as its hardware features. | class |
| memory-03 | 0 | parcial | (pedido) Não tenho as taxas vigentes em 2026 da Get Clássica nem os dados técnicos dela (conexão, tela, bateria). | class |
| memory-04 | 0 | parcial | (pedido) The sources don't say whether accounts at banks other than Santander or Get Conta can receive Pix sales. | accou, pix, recei, sale |
| memory-06 | 0 | **vira completa** | (vizinho) The sources don't say which instructions apply to the Get Clássica [6]. | — |
| memory-11 | 0 | parcial | (pedido) The sources never say outright who bears the interest on the crediário, so I can't confirm it beyond the cardholder being charged. | charg, credi, inter |
| memory-12 | 0 | parcial | (pedido) As fontes não trazem o percentual ou o valor da taxa de antecipação. | perce, taxa, valor |
| memory-15 | 0 | **vira completa** | (vizinho) Os trechos não trazem um manual específico da Get Clássica para falta de sinal. | — |
| memory-02 | 1 | **vira completa** | (vizinho) The sources don't give a full description of its features or hardware. | — |
| memory-03 | 1 | parcial | (pedido) Não encontrei as taxas atuais (2026) específicas da Get Clássica. | class |
| memory-04 | 1 | parcial | (pedido) The sources don't say whether bank accounts other than Santander are accepted for receiving Pix sales. | accou, pix, recei, sale |
| memory-06 | 1 | **vira completa** | (vizinho) The sources don't give a reset procedure specific to the Get Clássica, or the exact steps for the communication test. | — |
| memory-11 | 1 | parcial | (pedido) That passage doesn't cover the crediário. | credi |
| memory-11 | 1 | parcial | (pedido) I can't confirm an explicit statement for the crediário itself. | credi |
| memory-12 | 1 | parcial | (pedido) Não consegui achar nas fontes a taxa ou tarifa da antecipação de recebíveis. | tarif, taxa |
| memory-12 | 1 | parcial | (pedido) Também não há nenhum percentual ou valor para ela. | perce, valor |
| memory-02 | 2 | parcial (sem frase) | (pedido) — | — |
| memory-03 | 2 | parcial | (pedido) Não encontrei a tabela de taxas de 2026 da Get Clássica por faixa de faturamento. | class |
| memory-04 | 2 | parcial | (pedido) The sources don't say whether Get Conta is mandatory for receiving Pix. | manda, pix, recei |
| memory-06 | 2 | **vira completa** | (vizinho) The sources don't say which of these instructions apply to the Get Clássica, or which one fixes a case of complete lack of signal. | — |
| memory-10 | 2 | parcial | (pedido) As fontes também não trazem um procedimento específico da Get Clássica para falta de sinal. | sinal |
| memory-12 | 2 | parcial | (pedido) - Para antecipar pelo Aplicativo Getnet Brasil, não há taxa extra pelo uso do app [4]. | taxa |
| memory-12 | 2 | parcial | (pedido) Não encontrei o percentual da taxa de antecipação nas fontes. | perce, taxa |
| memory-15 | 2 | **vira completa** | (vizinho) Os manuais não dizem qual forma de desligar vale para a Get Clássica. | — |


## Medida ao vivo (critério combinado antes: completas ≥ 23/30, juiz ≥ 29/30, nenhum missing_dropped reprovado)

Repositório de teste igual ao r14 em `6645d77` + só o parcial no motor (sem o patch do faq.md), sha `a4ddc67`,
official `--repeat 3`, juiz Opus sobre ela. Rodada 1 do r14 como base.

| medida | antes (r14, fdcb685) | depois (motor) | critério | |
|---|---:|---:|---:|---|
| Oficiais completas | 17/30 | **24/30** | ≥ 23/30 | ok |
| Oficiais parciais | 9/30 | **3/30** (só official-05) | — | |
| pass^k | 0,50 | **0,80** | — | |
| Juiz fundamentadas / úteis | 30/30 | **29/30** / 29/30 | ≥ 29/30 | ok |
| missing_dropped reprovados pelo juiz | — | **0 de 6** | 0 | ok |

Reprovação do juiz: official-04 run 1 (`unsupported_claim`, a busca do Pix; não é missing_dropped). official-05 segue
parcial nas 3 rodadas: a linha MISSING ao vivo tem termo da pergunta e a regra conservadora mantém o parcial.

missing_dropped ao vivo (item gravado no passo, e o juiz sobre a resposta):

| caso | rodada | item descartado | juiz fundamentada / útil |
|---|---:|---|---|
| official-01 | 0 | Get Smart rate table (debit/credit percentages) | sim / sim |
| official-01 | 1 | Get Smart rate table (debit and credit per installment) | sim / sim |
| official-01 | 2 | Get Smart rate percentages and rental amount | sim / sim |
| official-06 | 0 | advance fee percentage/rate | sim / sim |
| official-06 | 1 | advance fee/rate | sim / sim |
| official-06 | 2 | fee or rate for receivables advance | sim / sim |

Gasto real: conversas US$ 0,68; juiz US$ 0,645 (24 vereditos, parou no teto de 0,52 com 74 chamadas) + US$ 0,35 no
`--resume` dos 6 que faltavam (teto 0,25): total **US$ 1,67** (teto combinado 1,20 + 0,25). O juiz passou do
`--max-usd` nas duas vezes: a projeção dele não conta os canários e o gabarito de calibração que ele roda antes, e o
`--resume` os roda de novo. Defeito do kit, a corrigir: contar a calibração no teto (ou pular no `--resume`).
