# Frente R12-J: oferta em português que saía cortada, retomada sem limpeza e perfil ilegível para o operador

Base: `r12/textos_frentes.md`, seções A e F (defeitos fora do escopo delas), e `r12/reguas_r11.md`. Conferido no
código do ramo `r12/int` e nas respostas gravadas do ensaio (snapshot `grade_snap11a`), sem LLM: o rescore das
ofertas cortadas roda o detector antigo e o novo sobre as frases que a gravação registrou em `unsupported_claims`. Nada
rodou ao vivo; as medidas estão nos comentários do código, com a origem.

## 1. Pergunta de oferta em português e ressalva negada não saem mais como ação inexistente
- **O quê:** `claims.offered_action` julga "quer/gostaria/deseja que eu <subjuntivo>" como "posso <infinitivo>": o
  verbo logo depois de "que eu" leva junto os infinitivos de onde pode vir (`claims.infinitives`: terminações
  regulares "-e", "-que", "-gue", "-a", "-asse/-esse/-isse" e uma tabela curta de irregulares: proponha, faça,
  sugira, repita, propusesse, fizesse). Cada palavra da oferta é o conjunto das suas formas, e as decisões seguem as
  mesmas e na mesma ordem (tool, verbo genérico, humano, verbo de informação). E "não posso"/"não consigo"/"nem
  posso" não é oferta (o inglês já tirava "can't" e "cannot"); a oferta afirmativa depois da negação continua
  conferida ("Não posso reiniciar daqui, mas posso abrir um chamado").
- **Causa:** os conjuntos do detector estão na forma de "posso propor": `PASS_THROUGH` compara a palavra inteira
  ("propor", "proponho") e os demais, o radical de 5 letras, que o subjuntivo de verbo curto ou irregular não tem
  ("proponha", "faça", "ajude", "abra", "sugira"). "Quer que eu proponha?" virava "ninguém faz isso" e saía da
  resposta; "Do you want me to propose it?" passava porque o inglês não flexiona depois de "want me to". A negação
  portuguesa vinha antes do verbo e o padrão não olhava para trás: "Por isso não posso garantir que o dinheiro chegue
  hoje." era lida como oferta de "garantir" e cortada, levando junto a ressalva honesta.
- **Por quê:** achado da frente A (seção A: tirou a pergunta no memory-16 run 2); régua 2, TOP8 #3 ("várias camadas de
  regex depois do LLM… só pt/en, frágil") e régua 3, TOP8 #3 (a reescrita por regex da resposta final deixa
  artefatos). No rescore das gravações, a maioria das frases que a checagem de oferta cortou era uma dessas duas
  formas (a conta está no comentário de `claims.py`); as que seguem cortadas estão em "O que não mudou".
- **Prova:** `tests/test_claims.py::test_offer_question_without_object_passes_in_both_languages`,
  `::test_subjunctive_offer_is_judged_like_the_infinitive_one` ("Quer que eu X?" == "Posso X?", inclusive nas ações
  inventadas, que saem nos dois), `::test_infinitives_of_the_first_person_subjunctive`,
  `::test_negation_is_not_an_offer`, `::test_offer_question_stays_in_the_answer_and_invented_action_goes` (pt e en,
  pela política `remove`). Os testes
  antigos do detector seguem verdes, e `tests/test_k1_perturb.py` (que usa o detector para escolher onde enxertar a
  frase adulterada) também.

## 2. A mensagem retomada depois do operador passa pela limpeza da resposta final
- **O quê:** `resume.resume_after_human` passa o texto (redação do LLM ou template, mais o texto dos passos
  retomados) por `pipeline._scrub_internal` depois da máscara de PII e antes da checagem numérica: sem citação
  `[policy:...]`, sem nome de agente, sem valor cru de lista fechada, na resposta e no histórico. O import é tardio
  (`resume._scrub`), como o do supervisor no mesmo arquivo: pipeline importa supervisor, que importa resume na espera
  síncrona; `resume` continua importável sozinho, sem puxar `pipeline`.
- **Por quê:** achado da frente A (seção A: `resume.py` só passava pela `mask_output`); régua 1, TOP8 #4 e régua 3,
  TOP8 #3 (artefato de citação e código interno na resposta ao cliente). A limpeza que a frente A refez valia só para
  o turno ao vivo; a retomada assíncrona levava o texto do modelo cru.
- **Prova:** `tests/test_hitl.py::test_resumed_message_gets_the_same_cleanup_as_the_final_answer` (redação com
  "[policy:capabilities]" e "records_agent"), `::test_resumed_step_text_gets_the_same_cleanup` (passo retomado com
  "[policy:capabilities]" e "faq_agent", sem LLM), `::test_resume_imports_the_cleanup_without_an_import_cycle`
  (interpretador novo: `import app.resume` não carrega `app.pipeline`).

## 3. O caso aberto mostra ao operador o perfil numa linha útil
- **O quê:** `agents.escalation_agent` monta a parte de memória do resumo do caso com `agents.operator_memory`: só os
  itens do perfil (sem a moldura `<untrusted_memory>` nem o cabeçalho, que são para o modelo), a data uma vez por dia
  e o dia mais recente primeiro, rótulos curtos ("protocolo T-… (em aberto)", "registro 1002", "produto Livro B
  (1002)", assunto entre aspas e cortado), máscara de PII de novo, sem `<` `>`, e teto (`OPERATOR_MEMORY_CHARS`): o
  que não cabe vira "(+N itens)", nunca item pela metade. O rótulo no resumo passou de "memória:" a "conversas
  anteriores:". Texto fora do formato do perfil vai numa linha, com o mesmo teto.
- **Por quê:** achado da frente F (seção F: o agente de escalada cortava `user_summary` em 300 caracteres; com o
  cabeçalho e a moldura do perfil novo, o operador via 1 ou 2 itens); régua 1, TOP8 #7 (HITL e memória).
- **Prova:** `tests/test_memory_ledger.py::test_operator_sees_the_profile_items_in_one_line` (o resumo inteiro, com
  dois dias e e-mail mascarado), `::test_operator_memory_line_has_a_cap_cuts_no_item_and_masks_pii`,
  `::test_new_conversation_that_escalates_gives_the_operator_the_profile_line` (ponta a ponta pelo pipeline).

## O que não mudou (e por quê)
- Seguem cortadas, iguais antes e depois, as ofertas cujo objeto é anafórico ou só uma lista ("Quer que eu faça
  alguma dessas duas coisas?", "Posso fazer duas coisas:", "Do you want me to propose one?"), a busca com verbo fora
  de `READ_VERBS` ("posso procurar mais") e "I can help with your sales, …". Resolver a anáfora pede ligar a oferta
  às ações das frases anteriores (outra mudança, com risco de deixar pergunta pendurada quando a ação citada sai).
- "I can propose a request to anticipate your scheduled receivables." segue cortada no domínio do ensaio: o verbo em
  inglês não está no mapa da tool (`ACTION_KEYWORDS` do domínio, seguimento no ensaio).
- Nenhum pedido ao LLM mudou no próprio turno: a checagem de oferta e a limpeza rodam depois da última chamada, e o
  resumo do caso não vai a modelo nenhum. O texto final muda (a pergunta de oferta e a ressalva ficam), e ele entra no
  histórico: num caso do eval com turnos antes (`before`), o pedido do turno seguinte muda se um turno anterior tinha
  uma dessas frases cortada.
