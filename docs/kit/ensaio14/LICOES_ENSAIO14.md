# Lições do ensaio 14 (para o kit)

1. T0 em < 1 min (sessão criada 15:47:40, scaffold 15:48:30 UTC): commit antes do pip + domínio montado funcionaram.
   Reforçar: manter o passo 1 exatamente assim.
2. ERREI: a lista `tools` do get_session não mostra o send_message, mas a sessão do relógio TEM (deferido) e a linha
   chegou. Não mandar "não use send_message". Para acompanhar, NÃO ler list_events sem filtro (subagentes inundam o
   contexto: ~40 KB por chamada); usar git log + get_session (task_summary, flag_settings) + as linhas que ela manda.
3. get_session da sessão nova não mostra flag_settings (modo rápido) até o dono ligar: lembrar o dono na largada.
4. Script de configuração do ambiente que passei estava INCOMPLETO (só fastembed/onnxruntime/numpy/tokenizers): faltou
   o lock inteiro (fastapi, pytest, ruff…). O pré-voo reprovou e o relógio teve de instalar. Próximo: linha completa e
   testada, com uv. Raiz: dei a linha sem testar numa máquina limpa.
5. Docker indisponível no container da nuvem (sem /var/run/docker.sock): docker/scale é corte previsível; o kit deve
   tratar como corte declarado de saída (não gastar tempo tentando).
6. Dependabot abriu 5 ramos no repo da tentativa logo no T+1 (actions/cache, checkout, setup-python, gitleaks): PRs
   disparam CI e enchem a fila no T+40. Kit: desligar dependabot na tentativa (open-pull-requests-limit: 0) ou não
   levar .github/dependabot.yml no scaffold.
7. Fumaça: 6/10 oficiais completos. 01/05/06 "partial" por MISSING de item vizinho que o cliente não pediu (o
   faq.md já proíbe; o modelo não obedece) → para o kit: decidir parcial no MOTOR, não no prompt (ex.: MISSING só
   conta se cobrir um item que o planner/router listou como parte da pergunta; item extra vira só frase, status ok).
   04: a fonte certa (sup-pix-09, requisitos do Pix) fica em 7º–10º lugar; o trecho abre com "O botão Pix não está
   disponível…" e os requisitos vêm no meio → kit: cabeçalho contextual por trecho (pergunta/seção + resumo) antes
   do embedding (ideia: "contextual retrieval"), medido no gold de busca.
8. A maestra puxou a fumaça para si (ordem do dono) enquanto o relógio instalava pacotes; o relógio terminou antes e
   a página saiu da fumaça dele (melhor: evidência do mesmo commit). Lição: a maestra deve ter um clone já com venv
   quente ANTES da largada, para a fumaça dela ficar pronta em ~2 min (a minha ainda montava o índice frio).
9. Rotulador marcou 10 respostas em ~100 s (10 s cada, tudo "passa"): a página deve pedir um tempo mínimo por item
   ou mostrar "leia a resposta inteira" antes de liberar o botão; o relatório deve registrar o tempo por item.
10. A CI rodava em push de ramo fix/ (ci.yml só ignorava maestra/): corrigido no kit (9937914).
11. As 2 pessoas aprovaram 10/10 (AC1 1,0, kappa indefinido: sem variância). Sem resposta adulterada na página, a
    concordância não prova atenção. Kit: página padrão com `--perturb 3` (defeitos plantados, cegos) para medir se a
    pessoa pega o erro; o README diz quantas adulteradas cada pessoa achou.
12. A Bianca não tinha acesso à página (privada) e mandou pelo "Copiar minhas respostas" via dono: o caminho de texto
    (`evals.label --import-text`) funcionou. Kit/PLAYBOOK: o dono compartilha a página (Share, permissão de
    interagir) ANTES da largada, ou a maestra já manda o texto de fallback junto do link.
13. A sessão do relógio mandou uma linha com hora "de cabeça" adiantada e corrigiu sozinha depois.
14. Rodada 1 (fdcb685, 13/13 splits): oficiais completas 0,57, pass^k 0,50, parciais 0,30, juiz 1,00/1,00, memória
    0,83, HITL 1,00, R@3 0,89, sem humano 0,85, US$ ~4,3. Teste da correção do faq.md (MISSING só para item nomeado),
    fora do relógio, official repeat 1 (73979b7): 7/10 completas (fumaça 6/10), parciais 1 (fumaça 3); 01 e 05
    viraram completas; 06 perdeu o fato D+1/taxa (variação de busca); 08 parcial (códigos 51/05 sem doc). Antes de ir
    ao kit de produção: official e memory repeat 3 + bateria integral, comparar com a rodada 1 (judge_diff).
