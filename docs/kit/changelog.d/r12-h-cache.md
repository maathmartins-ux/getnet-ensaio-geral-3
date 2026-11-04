# Frente R12-H: cache de prompt nos pedidos ao LLM

- **O quê:** `src/app/llm.py` (`with_prompt_cache`): marca de cache no fim do system de todo pedido (tools + system
  de cada papel são fixos) e, no laço de tool use, a marca automática no fim da conversa (cada volta lê a anterior);
  pedido de uma volta só não leva a marca do fim (a escrita nunca seria lida). `LLM_PROMPT_CACHE=off` desliga. O custo
  (`observability.llm_cost`) conta a escrita (1,25× a entrada) e a leitura (US$ 0,20/MTok no Sonnet e no Opus 5.5,
  US$ 0,01 no Haiku); métricas `llm_tokens_total{kind=cache_read|cache_write}` e o resumo do request ganham os tokens
  de cache só quando houve cache. A chave do cassete sai do pedido antes das marcas: as gravações continuam valendo.
- **Por quê:** as réguas da rodada 11 citaram latência (p50 12,4 s, p95 24,8 s) e custo por turno resolvido; nenhum
  pedido usava cache, e o system + tools de cada papel se repete em todo turno.
- **Prova:** `tests/test_r12_prompt_cache.py`; sonda ao vivo (2 chamadas do supervisor do kit, mesmo papel, perguntas
  diferentes): 1ª escreveu 1692 tokens no cache (US$ 0,0048, 1,47 s); 2ª leu 1609 do cache (US$ 0,0012, 1,24 s).
