# Frente R12-fix-texto: a limpeza da resposta final nunca apaga conteúdo

Base: os achados confirmados da revisão adversarial da limpeza de `pipeline._scrub_internal` (frente R12-A), cada
um reproduzido por um cético. Regra seguida: na dúvida, o texto fica e sai só o código interno. Rodada sobre os
textos com citação gravados nas baterias das rodadas 10 e 11, a versão nova só muda os textos com defeito, nenhum
código vaza e nenhum marcador de lista fica sozinho (a medida está no comentário do bloco, em `pipeline.py`).

## 1. A palavra antes da citação só sai quando a introduz (gravidade alta)
- **O quê:** a abertura que sai com a citação é a locução de adjunto ("conforme", "segundo a", "de acordo com o",
  "per", "according to") ou o apontador ("veja", "see"), com listas por idioma. No português também saem a
  preposição e o artigo definido logo antes da citação (lá a preposição não fica solta no fim da frase). No inglês a
  preposição só sai abrindo a oração ("From [ref], I can") ou depois de verbo que aponta ("is listed in [ref]"),
  porque no fim da frase ela costuma ser partícula ("logged in", "turned on"). Pronome e numeral ("cada uma",
  "propor um") e o "do"/"no" do inglês ("I can do", "The answer is no") ficam.
- **Por quê:** a lista única, pt e en juntos e sem olhar o idioma, apagava a última palavra da frase quando ela
  estava na lista: "qual foi o código de cada uma [policy:capabilities]." virava "...de cada." (gravado nas respostas
  finais de dependent-07 e real-31, rodada 10); "No [ref]. A human agent decides" perdia o "No".
- **Prova:** `tests/test_r12_texto_revisao.py::test_lead_strip_never_eats_a_word_of_the_sentence` (frases gravadas
  de dependent-07 e real-31 e as variantes em inglês; a abertura de verdade continua saindo).

## 2. A frase curta que responde fica; a que só apontava a citação sai (gravidade média)
- **O quê:** a regra que contava as palavras restantes depois de tirar a abertura saiu. A frase (ou só a oração final dela, depois
  do último separador, de "porque"/"because" ou de outra abertura) sai inteira quando apontava a citação e nada
  mais: vazia ("Veja [ref]."), rótulo de fonte ("Fonte: [ref]") ou citação como objeto de verbo que aponta ("Essa
  política de ações está em [ref]."; "..., porque as ações disponíveis são só as de [ref]."). Nunca sai a oração com
  número e nunca a resposta: "15 minutos conforme [ref]." fica "15 minutos."; "Requer confirmação conforme [ref]."
  fica "Requer confirmação.".
- **Por quê:** a contagem apagava o prazo e a regra ("A proposta vale pouco tempo. 15 minutos conforme [ref]."
  perdia o prazo; a resposta que era só isso virava "Não encontrei base") e deixava fragmento quando a frase que
  apontava era mais longa: "Essa política de ações está." (resposta final de real-11) e "...são só."
  (texto do agente em real-39), gravados na rodada 10.
- **Prova:** `tests/test_r12_texto_revisao.py::test_short_answer_sentence_is_not_dropped`,
  `::test_pointer_sentence_is_not_left_without_its_object` (frases gravadas de real-11 e real-39),
  `::test_answer_with_content_never_becomes_no_answer`.

## 3. O separador que não abria a citação fica (gravidade baixa)
- **O quê:** o par de separadores em volta da citação só sai quando delimitava um aposto (vírgula e vírgula, ou
  travessão e travessão) e o que vem antes não é só "Sim/Não/Yes/No/Depende"; senão fica o da esquerda e sai só o da
  direita: "Não, segundo o [ref], a decisão" → "Não, a decisão"; "a proposta; conforme [ref], ela expira" → "a
  proposta; ela expira".
- **Por quê:** o ramo "entre separadores" tirava os dois sempre e colava as orações ("Não a decisão é de um
  atendente humano."; "No the assistant can't decide disputes."), justo na forma "Sim/Não, ..." que o contrato do
  faq pede.
- **Prova:** `tests/test_r12_texto_revisao.py::test_separator_that_is_not_part_of_the_insertion_stays` (o aposto de
  verdade continua saindo com o par de vírgulas).

## 4. Lista, rótulo, citação em bloco e negrito (gravidade baixa)
- **O quê:** o item de lista que era só a citação sai com o marcador ("- [ref]", "1. [ref]"); só rótulo de fonte
  (Fonte/Fontes/Source/Ref/Referência/Ver/Detalhes) conta como rótulo que aponta, e o cabeçalho ("Próximos passos:
  [ref]") fica sem a citação; "> " de citação em bloco conta como começo de linha; a marcação que ficaria vazia em
  volta da citação ("**Conforme [ref]**", "**[ref]**") sai junto.
- **Por quê:** sobrava "-" ou "1." sozinho; "Próximos passos: [ref]\n1. ..." perdia o cabeçalho (regressão frente
  ao kit-v5.4.0); "**Conforme [ref]**, a proposta" virava "** **, a proposta"; "> Conforme [ref], nada" virava ">,
  nada".
- **Prova:** `tests/test_r12_texto_revisao.py::test_list_header_survives_and_no_bare_marker_is_left`.

## 5. Sem citação, nada muda: a limpeza de parênteses é só no ponto do corte (gravidade baixa)
- **O quê:** a "rede de segurança" global (tirar "()", "(" antes de pontuação, ", ." e espaço antes de pontuação em
  toda resposta) saiu; o mesmo acabamento é feito por `_join`, só onde a citação foi cortada.
- **Por quê:** rodava em toda resposta final, com ou sem citação, e mudava conteúdo: "chame `pos.init()`" virava
  "chame `pos.init`"; "f() = 0" virava "f = 0".
- **Prova:** `tests/test_r12_texto_revisao.py::test_text_without_citation_keeps_empty_parentheses`,
  `::test_parentheses_elsewhere_survive_the_cut_of_a_citation`; `tests/test_r12_texto.py` (frases literais de
  hitl-07 e memory-16), `tests/test_claims.py`, `tests/test_hitl.py` e `tests/test_v55_officials_have_facts.py`
  seguem verdes.
