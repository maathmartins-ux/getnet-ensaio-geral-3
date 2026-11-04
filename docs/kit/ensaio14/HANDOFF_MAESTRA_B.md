# Passagem para a Maestra B (ensaio 14 → rodada 15 em produção)

Escrito pela Maestra A (sessão `session_011qmqFpm1AijAdQEQ7HP3Te`) em 04/11/2026, 13:36 (Brasília), logo depois do
último commit do ensaio 14. Leia antes: `CLAUDE.md`, `docs/kit/MELHORIA_CONTINUA.md` (ordens do dono, palavra por
palavra), `docs/kit/PLAYBOOK.md` §0, §2.2 e §2.4, `docs/kit/V5_PROMPT_M_MONTADO.md`, `docs/kit/RODADAS.md` (as notas por
rodada) e `docs/kit/ensaio14/LICOES_ENSAIO14.md` (o que deu errado hoje, com a causa).

## 1. Quem é quem

- **Dono:** Matheus. Fala português simples, não é da área. Não peça nem mostre chave de API. Pronome: use "a pessoa"
  ou o nome; não presuma gênero.
- **Maestra A** (`session_011qmqFpm1AijAdQEQ7HP3Te`): operação. Fala com o dono; acompanha a sessão do relógio minuto
  a minuto; integra ramos; vigia a CI; roda as réguas cegas; dona dos ramos `r12/int` e `kit-v5.4.0` deste repo (só
  ela faz merge e push neles).
- **Maestra B** (você): qualidade. Tarefas fechadas, com prova, entregues em ramos `b/<tarefa>` deste repo
  (`kit-preflight`). Nunca dê push em `r12/int` nem `kit-v5.4.0`. Avise a Maestra A com a tool `send_message`
  (`session_id = session_011qmqFpm1AijAdQEQ7HP3Te`), numa linha: `PRONTO b/<tarefa> <sha>: <o que muda> · <prova>`.
- **Sessão do relógio (M)** do ensaio 14: `session_011qmqFpPtvDtL7rfbKSQEoK`, repo
  `maathmartins-ux/getnet-ensaio-60min-r14`. Não mande nada para ela: o ensaio terminou.

## 2. Meta e regras (resumo; o texto completo está nos arquivos acima)

- Meta: ≥ 9,0 na nossa régua (média de 2+ réguas cegas). Calibração: 8,73 no simulador ≈ 9,5 real; 8,65 ≈ 9,35.
- **Não há mais ensaio:** a próxima é a rodada 15, já em produção, cronometrada em 60 min (último commit até T+59).
  Pela regra do dono, a produção só roda se o ensaio 14 der ≥ 9,0 nas réguas (a Maestra A roda e avisa). "Não há mais
  margem para erros": tudo que entra no kit entra com teste e medido.
- Domínio pode ir montado (`docs/kit/tools/dominio.py`, `docs/kit/dominio/`), com 3 condições: PROCEDENCIA declara a
  origem; todos os números medidos no relógio; held-out e perguntas reais escritos de novo, às cegas, no relógio.
- Melhoria contínua: medir → corrigir a causa → medir; nada de gastar API sem hipótese; rodar só o split afetado;
  registrar antes → depois.
- Commits: `git -c user.name=Claude -c user.email=noreply@anthropic.com commit`, mensagem em português terminando com
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` e `Claude-Session: <link da SUA sessão>`. Nenhum id de
  modelo em commit, PR ou código. Não copie código nem texto dos repos de referência (só a ideia, com a origem).
- No máximo 2 processos pesados ao mesmo tempo. Espera sempre em 2º plano (Bash `run_in_background` ou Monitor),
  nunca em 1º plano: hoje a sessão do relógio travou 4 min num `until` em 1º plano e não lia mensagens.

## 3. Onde o ensaio 14 parou

- Repo da entrega: https://github.com/maathmartins-ux/getnet-ensaio-60min-r14 (público, descartável).
- T0 = `a2320ad` (scaffold) 15:48:30 UTC; último commit `6645d77` 16:31 UTC (T+42), README sozinho. CI do final:
  run 41868143038 (rodando às 13:36).
- Kit usado: `kit-fonte` = `f5c4949` (kit v5.6.1, domínio montado do ensaio 13).
- Rodada 1 integral ao vivo no `fdcb685` (13/13 splits, ~US$ 4,3):

  | medida | valor |
  |---|---:|
  | Oficiais resolvidas por completo (manchete honesta) | 0,57 |
  | Oficiais pass^k | 0,50 |
  | Oficiais parciais (fora da manchete) | 0,30 |
  | Juiz: fundamentadas / úteis | 1,00 / 1,00 |
  | Memória pass@1 | 0,83 |
  | HITL | 1,00 |
  | Recall@3 / MRR | 0,89 / 0,90 |
  | Turnos sem humano | 0,85 |

- Conferência humana: 2 rotuladores (Matheus, Bianca), 10 respostas da fumaça (`evals/validation/51221c7885f8.json`),
  as duas aprovam 10/10 (AC1 1,0, kappa indefinido por falta de variância); checagem automática 9/10 (diverge
  `official-04`). Sem respostas adulteradas na página, então a concordância não prova atenção.
- Cortes declarados: rodada 2 (sem tempo; a correção do prompt muda o pedido de quase todos os splits, rodar só os
  oficiais deixaria evidência de 2 SHAs) e vídeo (`make video` falhou: caminho relativo recusado pelo capture_demo).
  Docker/scale NÃO é corte: o job `check` da CI roda `check.py --docker --scale` (o container da nuvem não tem docker).
- Falhas conhecidas, com mecanismo:
  - `official-01/05/06` saem "partial": o redator marca `MISSING` para item vizinho que o cliente não pediu (tabela da
    Get Smart; "e se não conectar"; taxa e passo a passo da antecipação), apesar de o `faq.md` já proibir.
  - `official-04` (Pix sem conta bancária): o trecho certo `sup-pix-09` ("critérios de elegibilidade: domicílio
    bancário Santander e uma chave Pix ativa") abre com outra pergunta ("O botão Pix não está disponível…") e fica em
    7º–10º lugar na busca (o redator lê 5). Medido com `docs/kit/ensaio14/pixrank.py`: 7º com a frase crua, 9º com a
    frase em pt, 5º com "requisitos para habilitar o Pix", 1º só com "critérios de elegibilidade… domicílio bancário
    … chave Pix". O glossário não age no caminho ao vivo (as consultas do router não passam pelo `expand_query`).

## 4. Medidas feitas fora do relógio (base para decidir o que entra no kit)

- **Correção do `faq.md`** ("antes de escrever MISSING, confira se o que falta está NOMEADO na pergunta"; teste em
  `tests/test_domain_prompts_r14.py`), ramo `maestra/faq-parcial` = `73979b7` do repo r14 (só local da Maestra A; o
  diff está em `docs/kit/ensaio14/faq_parcial.patch`). Ao vivo, official repeat 1: **7/10 completas** (fumaça sem ela:
  6/10), parciais 1 (antes 3); 01 e 05 viraram completas; 06 perdeu o fato D+1/taxa (variação de busca); 08 parcial
  (códigos 51/05 sem documento). n=1: não basta para produção.

## 5. Divisão do trabalho até a rodada 15

**Maestra A (operação):** CI do ensaio 14; 3 réguas cegas sobre `6645d77` e a estimativa; RODADAS/CHANGELOG; aviso ao
dono; PLAYBOOK e prompts do relógio (inclui o papel da Maestra B); merge dos seus ramos `b/*` com a suíte verde; o
"ensaio geral fechado" final (repo descartável montado como na largada: pré-voo, suíte, fumaça) antes da produção.

**Maestra B (qualidade), em ordem de prioridade — cada uma com teste, medida e o número antes → depois:**

1. **`b/faq-parcial`:** aplique `docs/kit/ensaio14/faq_parcial.patch` no domínio montado (`docs/kit/dominio/files/
   src/app/domain/challenge_prompts/faq.md` e o teste) e meça num repo de teste montado (§6): official e memory
   `--repeat 3` ao vivo + o juiz; compare com a rodada 1 do ensaio 14 (`evals/results/*.json` do r14 no `fdcb685`) com
   `python -m evals.judge_diff`. Entra só se as completas subirem sem queda em fundamentadas/úteis nem na memória.
   Gasto previsto: ~US$ 3. Se não melhorar, registre e não entre.
2. **`b/rotulagem`:** `scripts/label_page.py` com `--perturb 3` por padrão no PLAYBOOK e no prompt do relógio (respostas
   adulteradas, cegas); tempo por item gravado na ficha e no `evals.label --report`; o texto de "Copiar minhas
   respostas" e o `--import-text` já funcionam (a Bianca entrou por ele). Teste para cada mudança.
3. **`b/setup-env`:** a linha do Setup script do ambiente da nuvem, COMPLETA e testada numa máquina limpa (a de hoje
   tinha só fastembed/onnxruntime/numpy/tokenizers e faltou o lock inteiro). Precisa funcionar sem o repo da tentativa
   ter os locks no `main` (eles só existem no ramo `kit-fonte`). Prefira `uv pip install --system` (o pip levou ~10
   min). Entregue a linha exata no `PLAYBOOK.md` A10 e um teste que a confere contra os locks.
4. **`b/busca-pix`** (só se 1–3 estiverem prontos): cabeçalho contextual por trecho (título da página + pergunta da
   seção) antes do embedding, medido no gold de busca (`python -m evals.run_evals --compare-retrievers`) e no
   `pixrank.py`. Entra só se Recall@3/MRR não caírem e o `sup-pix-09` subir para o top-5. É a mudança mais arriscada:
   na dúvida, não entra e fica declarada.
5. **`b/make-eval-sujo`:** `make eval` (e o `--calibrate-gate --apply`) recusam na hora com árvore suja nos arquivos
   que o gate lê, com mensagem que diz "commit antes" (hoje o ao vivo recusou depois, ~5 min perdidos).

## 6. Como montar um repo de teste igual ao da largada (sem tocar no r14)

```bash
git -C /home/user/kit-preflight archive HEAD | tar -x -C /home/user/sim15
cd /home/user/sim15 && git init -q && git add -A && git -c user.name=Claude -c user.email=noreply@anthropic.com commit -qm "chore: scaffold (sim)"
python3 docs/kit/tools/dominio.py mount && git add -A && git -c user.name=Claude -c user.email=noreply@anthropic.com commit -qm dominio
uv pip install --system -q -r requirements-dev.lock -r requirements-hybrid.lock && uv pip install --system -q --no-deps -e .
python scripts/preflight.py --mounted
```

Suíte: `python -m pytest -q -p no:cacheprovider -n 4`. Ao vivo: `LLM_PROVIDER=anthropic` e a chave já vem no ambiente
(confira só com `[ -n "$APP_ANTHROPIC_API_KEY" ]`). O 1º eval monta o índice denso (~2 min de CPU).

## 7. O que já entrou no kit hoje (ramo `r12/int` = `kit-v5.4.0`)

`47cdb34` prompt sem pronome presumido · `691d26b` uv no lugar do pip · `88e8582` docker provado pela CI ·
`9937914` CI não roda em `fix/**` · `3faca0e` commit da calibração antes do `make eval` · `8acea52` README e SOURCES
do domínio montado coerentes com a PROCEDENCIA.
