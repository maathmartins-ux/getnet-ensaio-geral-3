# Frente R13-B: erros de documentação que reprovam a entrega sozinhos

- **O quê:** `scripts/check.py` (na entrega, com `src/app/domain/challenge/`) reprova: `{{...}}` em README e em todo
  docs/**/*.md (antes só README e SPEC); caminho citado que não existe, agora também com curinga
  (`ablation_replan*.json`); palavra de processo ("ensaio", "decisão do dono", "maestra", "régua") fora de URL e da
  linha do tempo; os números fixos que o modelo do README trazia de entregas anteriores (0,868 / 0,921 / 0,789,
  "96,7%"...) fora dos blocos gerados. `check.py --docs` roda só isso; o `scripts/final.sh` o roda antes do último
  commit (nada é commitado nem enviado com doc reprovado) e o push tem 4 novas tentativas (2/4/8/16 s).
- **O quê:** `scripts/fill_readme.py` gera o topo do README (bloco `links`: a linha "Vídeo" só aparece com
  `docs/video/walkthrough.mp4` ou `docs/video/URL.txt`; a frase "o último commit é só o README" só sai com `--final`,
  do final.sh, e o `--check` a reprova se o HEAD mexeu em outro arquivo); tira da tabela da §7 a linha cuja prova não
  existe (fica num comentário e volta quando a prova existir); preenche minutos e versão da PROCEDENCIA (`{{MINUTOS}}`
  e `{{VERSAO}}` viram valor gerado). Minutos do relógio de uma fonte só (`timesheet.clock_minutes`: o TIMESHEET, ou o
  mesmo cálculo no git): README, docs/ENTREGA.md e PROCEDENCIA saem iguais, e o `--check` reprova divergência.
- **O quê:** modelo do README sem os números de outra entrega no §4; PROCEDENCIA e ADRs 0004/0008 sem "ensaio".
- **O quê (guardas):** a guarda "sem id de caso" pega as famílias genéricas (`official-`, `dependent-`, `real-`,
  `memory-`, `hitl-`, `replan-`, `heldout-H1-`, `q-guard-`...) sem depender dos casos do domínio ativo; teste reprova
  `import numpy`/`torch`/`fastembed`... em tests/ fora de `pytest.importorskip` ou `try/except ImportError`; teste
  reprova exemplo de intenção (data/intent_examples*.jsonl e .d/) quase igual (Jaccard ≥ 0,6) a mensagem de caso de
  avaliação (casos + .d/, held-out, perguntas reais) no domínio do desafio.
- **Por quê:** no relógio de 60 min a PROCEDENCIA saiu com {{MINUTOS}}/{{VERSAO}}, a §7 citava 3 provas inexistentes, o
  topo tinha vídeo sem vídeo, o README dizia "neste ensaio (decisão do dono)", ENTREGA 45 min × README 65 min, o §4
  trazia números de outra entrega, um comentário com `dependent-07`/`real-31` e um `import numpy` quebraram a CI, e
  "Me passa uma receita de bolo de cenoura" era exemplo de intenção e caso do guardrail ao mesmo tempo. Aplicadas à
  entrega do relógio, as checagens novas reprovam cada um desses (o detector de contaminação acha essa frase, 1,0).
- **Prova:** `tests/test_r13_delivery_docs.py`, `tests/test_code_cites_no_eval_case.py`,
  `tests/test_tests_skip_optional_extras.py`, `tests/test_intent_examples_contamination.py`,
  `tests/test_r11_generated_docs.py` (ordem do final.sh).
