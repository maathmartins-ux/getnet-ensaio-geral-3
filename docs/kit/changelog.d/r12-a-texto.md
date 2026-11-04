# Frente R12-A: a resposta final sem artefato de texto, sem nome interno e sem conclusão que o dado não traz

Base: `r12/reguas_r11.md` (relatórios das 3 réguas da rodada 11). Conferido nas respostas ao vivo e nas gravações do
ensaio (snapshot `grade_snap11a`): a causa de cada artefato foi achada no texto que o LLM escreveu antes da limpeza.
Nada rodou ao vivo; as medidas estão nos comentários do código, com a origem.

## 1. A limpeza do código do cartão não deixa fragmento
- **O quê:** `pipeline._scrub_internal` tira a oração inteira da citação `[policy:x]`: as palavras que só existiam por
  causa dela (preposição, artigo, locução: "segundo a", "de acordo com o", "from", "as stated in"), os parênteses,
  as vírgulas e o rótulo ("Fonte:") que a delimitavam, e a frase que só apontava a citação ("Veja [ref]."); a
  maiúscula muda só quando a frase passa a começar ali; a frase que responde ("Sim, conforme [ref].") fica. Nome de
  agente vira palavras com o artigo e a contração certos ("do faq_agent" → "da base de conhecimento"). Resposta que
  era só a citação não volta vazia. Texto sem código interno não muda.
- **Causa:** a versão anterior conhecia uma lista fixa de aberturas coladas na citação ("segundo [ref]") e engolia o
  `)` de fechamento: "Segundo a [ref], a antecipação" → "Segundo a, a antecipação" (o artigo não estava na regra);
  "confirmar (conforme [ref])." → "confirmar (." (o `\)?` comia o fecho e deixava a abertura); "From [ref]," →
  "From," (fora da lista); "(conforme [ref])\n\nNão…" → "(Não…" (o `\s*` engolia o parágrafo); "Fonte: [ref]" →
  "Fonte:".
- **Por quê:** régua 1, TOP8 #4 e régua 3, TOP8 #3 ("Segundo a, a antecipação…" em hitl-07 e "confirmar (." em
  memory-16, como prova da cirurgia por regex na resposta final).
- **Prova:** `tests/test_r12_texto.py::test_citation_scrub_never_leaves_a_fragment` (frases literais de hitl-07,
  memory-16 e dependent-04, e as variantes), `::test_answer_that_was_only_the_citation_never_comes_back_empty`,
  `::test_agent_names_keep_article_and_contraction`, `::test_text_without_internal_code_is_left_alone`; os testes
  antigos da limpeza (`tests/test_claims.py`, `tests/test_v55_officials_have_facts.py`) seguem verdes.

## 2. O aviso da decisão do operador sai no idioma da conversa e com a ação em palavras
- **O quê:** `actions.decide_action` escreve o aviso por `_decision_notice`: idioma das falas do cliente (o mesmo
  critério da retomada, `resume.py`), a ação pelo rótulo do domínio (`LABELS` da tool) e pelo número da proposta que
  o cliente viu; nunca o nome da tool. A nota do caso na fila do operador não mudou.
- **Por quê:** régua 3, TOP8 #8 ("o aviso de aprovação ao cliente sai só em português e expõe o nome interno da tool",
  `actions.py:164`).
- **Prova:** `tests/test_r12_texto.py::test_operator_decision_notice_speaks_the_customer_language_without_the_tool_name`,
  `::test_approved_notice_in_portuguese_has_no_internal_name`; `tests/test_hitl.py` segue verde.

## 3. Valor interno de enum nunca chega cru ao cliente
- **O quê:** o cartão de capacidades mostra o rótulo legível de cada opção (o valor cru fica no schema da tool, para a
  chamada) e o padrão no idioma do cartão ("default" no inglês, antes "padrão"). O rótulo vem de `LABELS` do domínio
  ({valor: "palavras" ou {"pt", "en"}}, também para o nome do parâmetro); sem ele, o valor sai sem "_". Na resposta,
  `capabilities.readable_values` (chamado pelo `_scrub_internal`) troca o valor com "_" que o modelo copiou pelo
  rótulo, tira a crase e não repete a tradução que o modelo já pôs entre parênteses. O contrato do records diz para
  descrever em palavras.
- **Por quê:** régua 2, TOP8 #5 e régua 3, TOP8 #8 ("reason 'sem_sinal' or 'sem_conexao'" em official-05). Nas
  respostas ao vivo do ensaio o valor cru aparecia em vários splits, não só no official-05 (medida no comentário de
  `readable_values`).
- **Prova:** `tests/test_r12_texto.py::test_capability_card_shows_the_label_of_each_option`,
  `::test_enum_value_in_the_answer_becomes_the_readable_label`; `tests/test_v53_capabilities_card.py` atualizado.

## 4. Contrato do motor: o dado sem conclusão inventada; o sim/não primeiro
- **O quê:** contrato do records: "diga o que o dado traz: não conclua causa, proporção ("a maioria") nem relação
  entre registros ("só um aponta para…") que ele não mostre; se não dá para concluir, diga isso" e a regra do valor
  em palavras. Contrato do supervisor: "ao juntar os resultados, não acrescente conclusão que eles não trazem… a 1ª
  frase responde com o próprio dado". Contrato do faq: a regra de sim/não que já existia foi reforçada (começa por
  sim, não ou "depende de X" e traz, na mesma frase, o que o trecho da regra diz, com a citação; depois as opções; a
  lista de opções não substitui a resposta). Os prompts do kit (`faq.md`, `records.md`, `supervisor.md`) trazem as
  mesmas frases, como já traziam o resto do contrato.
- **Causa (nas gravações):** as duas inferências reprovadas pelo juiz e o "Your options are" do official-04 foram
  escritos pelo supervisor ao reescrever o especialista (o records tinha escrito certo no official-03); a regra
  "a 1ª frase já responde" levava o supervisor a sintetizar uma conclusão. No official-04, o especialista deu o
  sim/não na 1ª frase, sem citação, e a checagem de frases cortou a frase como sem base.
- **Por quê:** régua 1, TOP8 #2; régua 2, TOP8 #5; régua 3, TOP8 #1 (official-08 "Only one of them points to a
  terminal problem", official-03 "Most of that has already been deposited", official-04 sem o sim/não).
- **Prova:** `tests/test_r12_texto.py::test_engine_contract_rules_reach_domain_and_kit_prompts` (domínio + contrato e
  prompt do kit), `::test_kit_prompt_carries_every_line_of_the_engine_contract` (faq e records: o prompt do kit traz
  cada linha do contrato); `tests/test_v53_prompt_contract.py` e `tests/test_router_contamination.py` seguem verdes.
  Muda o pedido ao LLM do faq, do records e do supervisor: o efeito só aparece numa bateria regravada.
