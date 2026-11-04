# Frente R12-J: README modelo compacto e com os textos novos do motor

- **O quê:** §3 do README ("Cobertura da avaliação, por tema") com uma linha curta por tema: uma frase de mecanismo,
  1–2 provas com `::nome` e o limite em uma linha; o resto (provas extras, detalhes de configuração, limites
  inteiros) fica na docs/COBERTURA.md. A §3 caiu de 9.893 para 5.027 caracteres e a linha mais longa de 1.636 para
  453; o README de 40.069 para 36.391 bytes. Ordem e nomes dos temas mantidos; o "(mais provas em ...)" de cada linha
  saiu (o parágrafo de abertura já aponta a COBERTURA).
- **Por quê:** réguas da rodada 11 (reguas_r11.md, Régua 1 TOP8 #8: "README de 400 linhas/51 KB com células enormes
  no §3"; Régua 2 TOP8 #8: "linhas de 1–2 mil caracteres (README.md:277, 281, 284, 394)").
- **Prova:** `tests/test_evidence.py` (todo caminho em crase da §3 existe, ≥ 12 citações) e
  `tests/test_e53_readme.py` verdes; os 13 testes citados no README passam.
- **O quê:** textos das frentes no README, já curtos: A (§2.1 passo 7: texto final sem código interno; §2.3 item 4:
  aviso da decisão no idioma da conversa, sem nome de tool), B (§2.3 item 2: a resposta do operador volta ao
  supervisor LLM como passo `human` e pode chamar outro especialista, `human-><agente>`; §3 Orchestration com "todo
  achado das tools" e a prova nova; §3 Human Oversight; §2.5 F7; §1 Operador), E (§0.1 Knowledge Agent com
  `currency_rate`/`weather_forecast` e `src/app/live_data.py`), F (§2.1 passo 3 e §3 Memory: perfil de longo prazo
  do livro de fatos), H (§3 Observability e §5: cache de prompt), I (§2.3 item 4 e §3 Tools: risco alto só com chave
  pessoal) e Evaluation (`expect.after_human`).
- **Por quê:** as réguas pediam ver no README o que mudou (achado filtrado por regex, resposta do operador fora do
  laço, memória de longo prazo como string, aviso com nome da tool).
- **Prova:** as provas citadas existem e passam (lista no retorno da frente).
- **O quê:** jargão interno fora: o marcador "Na construção" do §5 sugeria "frentes em paralelo, orquestradas por uma
  sessão maestra" (o ensaio copiou "7 frentes em subagentes (K, R, T, Q, D ...)") e agora pede o que cada sessão fez,
  sem apelido, em 2 marcadores de até 60 caracteres (o detector do `check.py` só pega `{{...}}` até 60); "no relógio
  da V5" → "de uma entrega anterior"; "nas 3 rodadas" → "nas 3 repetições" (§4).
- **Por quê:** Régua 2 TOP8 #8 ("jargão interno ('frente K, R, T, Q, D', 'rodada 11'; README.md:314)").
- **Prova:** busca no README por frente/rodada/régua/J2/PLAYBOOK fora dos blocos gerados: nada.
- **O quê:** correções de texto: nó órfão "F" no diagrama (sobra do atalho de 1 passo, que desenhava uma caixa solta
  ligada à conferência) e "com a passos" no §0.
- **Prova:** tabelas com o mesmo número de células por linha; `tests/test_r11_compose_in_docs.py` verde.
