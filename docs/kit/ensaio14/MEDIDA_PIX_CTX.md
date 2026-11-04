# Cabeçalho por trecho gerado por modelo pequeno (official-04) — hipótese escrita antes de gastar

Teto aprovado pelo dono, via Maestra A (04/11): geração < US$ 0,10; teto total da fila nova: US$ 5,00.

Hipótese: com `context` = "<título> › <frase do modelo sobre o que o trecho responde>" e `RAG_CONTEXT=on`, o
`sup-pix-09` (critérios do Pix: conta Santander e chave Pix) sobe do 7º lugar para o top-5 na pergunta oficial ("Do I
need a bank account to receive my sales via Pix?"), porque a frase nomeia o assunto que hoje está só no meio do texto.

Entra só se, no gold de busca (`--choose-retriever --fast`, sem `--apply`) com o buscador padrão:
- Recall@3 e MRR não caem em relação ao mesmo gold sem o cabeçalho; e
- o `sup-pix-09` fica entre os 5 primeiros na pergunta oficial (`pixrank.py`).

Se entrar no top-5: official-04 ao vivo `--repeat 3` com juiz (~US$ 0,30) para ver se a resposta muda. Se não: fica
declarado e não entra.

## Resultado

Medido em 04/11 (offline, domínio do r14 em `6645d77`): cabeçalhos gerados em 256 de 272 trechos (2 páginas de
produto ficaram sem: a lista voltou com contagem errada), US$ 0,054 (`docs/kit/ensaio14/ctx_headers.py`, modelo pequeno,
um grupo de até 10 trechos por chamada). O `sup-pix-09` ganhou "Critérios de elegibilidade para habilitar o botão Pix:
meio de captura compatível, domicílio Santander com chave Pix ativa e representante legal PF".

Posição do `sup-pix-09` (pixrank.py), sem → com cabeçalho: pergunta oficial em inglês 7 → **4**; em português 9 → 7;
"requisitos para habilitar o Pix" 5 → 4.

Gold de busca (`--choose-retriever --fast`, sem `--apply`), sem → com cabeçalho:

| configuração | Recall@5 | Recall@3 | MRR |
|---|---:|---:|---:|
| dense+windows+cross:base (o padrão do kit) | 0,924 → 0,989 | 0,884 → 0,917 | **0,909 → 0,873** |
| dense+windows+cross (o cross reordena) | 0,949 → 1,000 | 0,909 → 0,982 | 0,924 → 0,960 |
| dense+windows | 0,924 → 0,989 | 0,884 → 0,917 | 0,909 → 0,873 |
| bm25 | 0,877 → 0,851 | 0,822 → 0,819 | 0,801 → 0,826 |

**Decisão: não entra.** O `sup-pix-09` foi ao top-5, mas o MRR do buscador padrão caiu (0,909 → 0,873), e a regra
combinada antes de medir era "Recall@3 e MRR não caem". Fica declarado como próximo passo: o cabeçalho junto com o
cross-encoder reordenando subiu tudo (MRR 0,924 → 0,960, Recall@3 0,909 → 0,982), mas trocar a ordem do buscador
padrão é outra decisão, a medir com a bateria ao vivo. Sem rodada ao vivo do official-04 (a condição era entrar).
