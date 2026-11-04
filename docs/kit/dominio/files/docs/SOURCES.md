# Fontes do corpus

Site oficial Getnet Brasil, ingerido em 2026-11-04 com `python -m app.ingest` e `scripts/ingest_render.py` (host `site.getnet.com.br`; 23 páginas, 272 trechos em `data/knowledge/`: a conta se refaz com `cat data/knowledge/*/*.jsonl | wc -l`). Cada trecho guarda `fetched_at` (data da coleta) e `sha256` do texto. Títulos conferidos: nenhum slug redireciona para outro produto (o `/antecipacao/` do site cai na Reserva Financeira e por isso NÃO foi usado; antecipação vem de `/duvidas/antecipacao-de-vendas/` e da FAQ geral `/duvidas/`).

| id (prefixo) | URL |
|---|---|
| prod-get-smart | https://site.getnet.com.br/maquininha/get-smart/ |
| prod-get-classica | https://site.getnet.com.br/maquininha/get-classica/ |
| prod-pix | https://site.getnet.com.br/pix/ |
| prod-crediario | https://site.getnet.com.br/crediario/ |
| prod-link-de-pagamento | https://site.getnet.com.br/link-de-pagamento/ |
| prod-conta-digital | https://site.getnet.com.br/conta-digital/ |
| prod-todas-maquininhas | https://site.getnet.com.br/todas-as-maquininhas/ |
| prod-taxas | https://site.getnet.com.br/taxas/ |
| prod-get-tap | https://site.getnet.com.br/get-tap/ |
| sup-duvidas | https://site.getnet.com.br/duvidas/ |
| sup-antecipacao-de-vendas | https://site.getnet.com.br/duvidas/antecipacao-de-vendas/ |
| sup-crediario | https://site.getnet.com.br/duvidas/crediario/ |
| sup-get-conta | https://site.getnet.com.br/duvidas/get-conta/ |
| sup-get-smart | https://site.getnet.com.br/duvidas/get-smart/ |
| sup-link-de-pagamento | https://site.getnet.com.br/duvidas/link-de-pagamento/ |
| sup-operacional | https://site.getnet.com.br/duvidas/operacional/ |
| sup-pix | https://site.getnet.com.br/duvidas/pix/ |
| sup-pix-mais-respostas | https://site.getnet.com.br/duvidas/pix-mais-respostas/ |
| sup-taxas | https://site.getnet.com.br/duvidas/taxas/ |
| sup-parcelado | https://site.getnet.com.br/duvidas/parcelado/ |
| sup-erro-adq-1-19 | https://site.getnet.com.br/get-ajuda-erros-maquininha/erro-adq-1-19/ |
| sup-erro-adq-1-84 | https://site.getnet.com.br/get-ajuda-erros-maquininha/erro-adq-1-84/ |
| sup-erro-adq-1-87 | https://site.getnet.com.br/get-ajuda-erros-maquininha/erro-adq-1-87/ |

Central get-ajuda: o índice é montado por JavaScript; entraram os 3 artigos de erro ADQ listados acima (renderizados
por `scripts/ingest_render.py`). Os outros artigos da central e o PDF de manual ficaram fora: erros e códigos da
maquininha vêm desses 3 artigos, de `sup-operacional` e de `sup-get-smart`; o significado dos códigos de recusa vem da
tool `get_transactions` (tabela do domínio).

Cuidados conhecidos do corpus:
- páginas de produto trazem texto de campanha com ano ("para vender mais em 2025") ao lado das taxas: a data que vale
  é o `fetched_at` do trecho, e a resposta cita a página, sem tratar o ano da campanha como vigência;
- a página da Get Clássica tem um trecho de modelo da página (ficha técnica com marcador de campo entre chaves
  duplas, sem dado): trechos assim saem do índice na carga (`src/app/rag.py`, `load_docs`, métrica
  `template_chunks_dropped_total`); as taxas, o prazo de recebimento e "para quem é" da Get Clássica estão no 1º
  trecho da página, e o redator do faq busca de novo por item antes de dizer que falta.
