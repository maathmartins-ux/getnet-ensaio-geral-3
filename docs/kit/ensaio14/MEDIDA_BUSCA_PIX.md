# Busca do Pix (official-04): medida offline antes de mudar (b/busca-pix, Maestra B, 04/11)

O trecho certo `sup-pix-09` ("critérios de elegibilidade para habilitação do Pix: meio de captura compatível,
domicílio bancário Santander, chave Pix ativa") abre com outra pergunta ("O botão Pix não está disponível nos portais
indicados, o que devo fazer?"), e o contexto do ingest é o mesmo para todos os trechos da página ("Arquivos Pix - Getnet
› Pix"). O redator lê 5 trechos.

Posição do `sup-pix-09` (domínio do r14 em `6645d77`, buscador padrão `dense+windows+cross:base`,
`docs/kit/ensaio14/pixrank.py`, offline, US$ 0):

| consulta | padrão | + glossário (`expand_query`) | `RAG_CONTEXT=on` | `RAG_CONTEXT=on` + glossário |
|---|---:|---:|---:|---:|
| Do I need a bank account to receive my sales via Pix? | 7 | 10 | 8 | 8 |
| preciso de conta bancária para receber vendas via Pix | 9 | 8 | 9 | 8 |
| requisitos para habilitar o Pix na Getnet | 5 | 6 | 7 | 9 |
| critérios de elegibilidade … domicílio bancário chave Pix | 1 | 1 | 1 | 1 |

Conclusões:
- O glossário no caminho ao vivo (as buscas do router não passam pelo `expand_query`) não resolve: piora a pergunta
  oficial (7 → 10).
- O cabeçalho contextual que já existe (`RAG_CONTEXT=on`, "título › seção") também não: o rótulo de seção é o mesmo
  em todos os trechos da página (a mesma razão pela qual ele foi medido pior antes: Recall@3 0,82 → 0,75).
- O que falta no índice é o ASSUNTO da resposta ("requisitos do Pix: conta Santander e chave Pix"), não o título.
  Sem modelo, isso só sairia escrevendo à mão no trecho, que é ajustar o corpus ao caso: não feito.

Próximo passo possível (não feito, precisa de gasto aprovado): cabeçalho por trecho gerado por modelo pequeno na
ingestão (uma frase "do que este trecho trata", com a página inteira como contexto: a ideia do "contextual
retrieval"), gravado no `context` do trecho e indexado com `RAG_CONTEXT=on`. Corpus: 272 trechos, 121 mil
caracteres, 23 páginas: < US$ 0,10 por geração. Entra só se Recall@3/MRR do gold não caírem e o `sup-pix-09` subir ao
top-5 na pergunta oficial. Enquanto isso, fica declarado: official-04 é perda de busca conhecida.
