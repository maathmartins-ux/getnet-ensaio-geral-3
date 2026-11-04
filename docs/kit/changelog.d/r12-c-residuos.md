# Frente R12-C: segurança residual e texto velho no código e nos docs do motor

Base: kit-v5.4.0 (18b897b). As perdas vêm dos relatórios das 3 réguas da rodada 11 (r12/reguas_r11.md), conferidas
no kit antes de corrigir. Nenhuma chamada a LLM, nenhuma bateria ao vivo, nenhuma gravação ou resultado alterado: o
que muda no código de produção é só o portão da subida; o resto é comentário, doc, script de smoke e teste.

## 1. APP_ENV=production recusa subir com AUTH_MODE=demo

- **O quê:** `api.production_gaps()` soma `AUTH_MODE=demo` quando o modo efetivo (`config.auth_mode()`, sem caixa) é
  demo. Mesma mensagem e mesma saída do portão de antes: `RuntimeError("segredos padrão em produção: [...]")` no
  lifespan, e o uvicorn não sobe. No dev nada muda: o demo segue opt-in, visível no `/health` (`auth_mode`) e marcado
  `identity_verified=false`. Docstrings de `api.py` e o comentário de `config.auth_mode` dizem a regra.
- **Por quê:** Régua 1 TOP8 #5, Régua 2 TOP8 #4 e Régua 3 TOP8 #7. O portão de produção não conferia o modo de
  identidade: com `AUTH_MODE=demo`, o `user_id` do corpo (/chat) ou da query (/conversations, /actions/{id}/confirm)
  valia como identidade, e quem trocasse o `user_id` lia a conversa e confirmava a ação de outro cliente.
- **Prova:** `tests/test_api.py::test_production_refuses_demo_identity`: com todo o resto forte, o dev sobe em demo
  (resposta com `identity_verified=false`); com `APP_ENV=production` o lifespan levanta a mensagem com
  `['AUTH_MODE=demo']`, também com `AUTH_MODE=DEMO`; com `required` o portão passa.

## 2. Compose de réplicas sem segredo fixo

- **O quê:** `docker-compose.scale.yml` lê o `AUTH_SECRET` só de `${SCALE_AUTH_SECRET:?...}`: sem padrão, sem a
  variável o compose recusa subir (com a mensagem que aponta o script). `scripts/scale_smoke.py` usa o
  `SCALE_AUTH_SECRET` do ambiente ou gera um aleatório por execução (`secrets.token_urlsafe(48)`), passa o mesmo valor
  às réplicas e ao token do teste, e com `--keep` diz como derrubar. A exceção do `.gitleaks.toml` para o segredo
  antigo saiu (ficaria morta, com o literal no repositório). Achado no teste: com `AUTH_KEYS` no ambiente de quem
  roda, o token do smoke saía assinado por outra chave e as réplicas o recusariam; o `token()` agora tira
  `AUTH_KEYS`/`AUTH_ACTIVE_KID` (as réplicas só recebem o `AUTH_SECRET`).
- **Por quê:** Régua 3 (ressalva do gate Critical Security e TOP8 #7): o compose de escala trazia um `AUTH_SECRET`
  padrão "só para o smoke"; quem subisse o arquivo fora do smoke ficava com um JWT forjável por quem lesse o
  repositório.
- **Prova:** `tests/test_no_literal_secrets.py::test_no_compose_file_ships_a_literal_secret` (varre todo
  `docker-compose*.yml`: variável de segredo vem do ambiente ou do marcador `change-me` que o portão recusa; o
  compose antigo é acusado), `::test_literal_secret_is_caught` e
  `::test_scale_smoke_generates_the_secret_that_the_compose_and_the_token_use` (duas execuções, dois segredos; o
  compose recebe o mesmo valor; o token valida com ele e não com outro; vale o do ambiente quando há). Conferido com o
  Docker Compose (só interpolação, sem build): sem a variável, `config` falha com a mensagem; com o ambiente do script,
  o `AUTH_SECRET` das réplicas é o segredo gerado.

## 3. Comentários sem id de caso e sem custo velho

- **O quê:** os comentários que davam um caso do eval como motivo de regra viraram regra genérica com a medida, sem
  o id: `pipeline.py` (resposta primeiro), `supervisor.py` (achados juntos, tabela que não escala turno já
  respondido, negação do encaminhamento), `grounding.py` (hora ISO e número em identificador), `ingest.py` (tabela de
  preços, agora com exemplo neutro), `live_data.py` (segunda fonte de clima) e, em `evals/`, `run_evals.py`,
  `error_analysis.py`, `trace_stats.py` e `judge.py`. Saíram também as menções à avaliação como motivo ("a régua da
  rodada 10 leu..."). O comentário do orçamento perto de `MAX_STEPS` não traz mais "~6–10 chamadas e US$ 0,01":
  aponta para os blocos gerados (custo por turno resolvido no §0 do README; latência e custo por split no RESULTS).
- **Por quê:** Régua 3 TOP8 #5 (comentários citam official-04 e official-08 como motivo de regras, então o número
  oficial é em parte de desenvolvimento) e a ressalva de "heurísticas ajustadas a casos"; Régua 2 TOP8 #7 e #8 (o
  código dizia "US$ 0,01 por turno" contra o custo medido).
- **Prova:** `tests/test_code_cites_no_eval_case.py::test_source_cites_no_eval_case_by_id`: nenhum arquivo de `src/`
  cita `official-NN` nem um id dos conjuntos do eval (`evals/<nome>.jsonl` e `.d/`, então no ensaio vale para os casos
  do domínio sem lista fixa); acusa o `pipeline.py` e o `supervisor.py` de antes. `::test_case_citation_is_caught`
  prova o detector (palavra inteira; `memory-070` não é `memory-07`).

## 4. ADR 0005 sem número que envelhece

- **O quê:** o parágrafo "Números" (resolvidas, fundamentadas, latência) virou apontador para os blocos gerados: §0 do
  README (oficiais resolvidas, juiz, custo) e bloco `trace` do RESULTS (latência por split e quem decide cada passo).
  A decisão e a prova por teste ficam. O "cerca de 4 s" do contexto virou "alguns segundos". O adendo deixa o jargão
  interno: "(kit v5.5.2)" no título e o motivo datado pela bateria do kit v5.5.1, sem citar as réguas.
- **Por quê:** Régua 1 TOP8 #8, Régua 2 TOP8 #8 e Régua 3 TOP8 #5: o ADR dizia "resolvidas 1,00, fundamentadas 0,97"
  contra os números atuais do README; e a menção às réguas no adendo é lida como otimizar para a nota.
- **Prova:** `tests/test_evidence.py::test_every_test_cited_in_compose_docs_and_readme_exists` (os testes que o ADR e
  o compose citam existem).
