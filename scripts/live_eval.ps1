# Eval ao vivo por split + juiz + FAILURE_MODES + README, no PowerShell do Windows (5.1 ou 7).
#
# Uso (de qualquer pasta; roda bem em segundo plano desde T+30):
#   powershell -ExecutionPolicy Bypass -File <projeto>\scripts\live_eval.ps1 -MaxUsd 3
#   powershell -ExecutionPolicy Bypass -File <projeto>\scripts\live_eval.ps1 -Splits official,replan -Workers 4
#   Start-Job { powershell -ExecutionPolicy Bypass -File <projeto>\scripts\live_eval.ps1 -MaxUsd 3 }
#
# - Lê o .env do projeto SEM imprimir valores (a chave nunca aparece no console nem no log).
# - O teto -MaxUsd vale só para as conversas, dividido entre os splits (num processo só). O juiz roda SEM teto (ordem
#   do dono, 04/11: com teto ele parou no meio da rodada). Ao estourar a cota, o split para limpo e grava o parcial em
#   evals/results/live_<split>.json.
# - Recusa rodar (código 4, nada gasto) com o domínio de exemplo ativo ou o gate offline vermelho/velho
#   (evals/results/latest.json ausente, passed=false ou de outro código): run_evals --check-live-ready diz o motivo.
#   Para seguir assim mesmo, declarado no relatório: LIVE_EVAL_ALLOW_STALE_GATE=1 / LIVE_EVAL_ALLOW_EXAMPLE_DOMAIN=1.
# - -Repeat 3 por padrão (pass^3): o gasto é ~3x o de uma rodada; -Repeat 1 para um smoke barato.
# - Sem chave: o run_evals sai com código 2 e mensagem clara; o script para sem traceback.
# - Salvo em UTF-8 COM BOM: sem ele o PowerShell 5.1 lê como ANSI e os acentos saem quebrados.
param(
    [string[]]$Splits = @(),
    [double]$MaxUsd = 24.0,  # teto das conversas (medido ~11 em 11 splits, official/memory repeat 3); juiz sem teto
    [int]$Workers = 8,  # até LIVE_MAX_CONCURRENT=12 no processo; memory (o mais longo) precisa de mais de 4
    [int]$Repeat = 3,  # cada caso roda N vezes: pass^k e instáveis (1 rodada esconde o caso que acerta às vezes; custo x N)
    [switch]$NoJudge,
    [switch]$SemReadme,  # só ao vivo + juiz: o README é da sessão principal (pc_live.ps1 usa isto)
    [switch]$DryRun   # mostra splits e teto e sai, sem gastar
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
# Mesma ordem do live_eval.sh: LIVE_EVAL_PY explícito (inexistente = erro) → .venv → python/python3 do PATH
if ($env:LIVE_EVAL_PY) {
  $py = $env:LIVE_EVAL_PY
  if (-not (Test-Path $py)) { Write-Host "LIVE_EVAL_PY=$py não existe (references/brief-de-fork.md, seção Ambiente)."; exit 1 }
} else {
  $py = Join-Path $root ".venv\Scripts\python.exe"
  if (-not (Test-Path $py)) {
    $cmd = Get-Command python, python3 -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $cmd) { Write-Host "Sem intérprete: nem .venv em $root\.venv, nem LIVE_EVAL_PY, nem python no PATH."; exit 1 }
    $py = $cmd.Source
  }
}

if (Test-Path ".env") {
    Get-Content ".env" | Where-Object { $_ -match '^\s*[A-Za-z_][A-Za-z0-9_]*\s*=' } | ForEach-Object {
        $name, $value = $_ -split '=', 2
        Set-Item -Path "env:$($name.Trim())" -Value $value.Trim()
    }
}
$env:PYTHONIOENCODING = "utf-8"

# Via `powershell -File`, "-Splits a,b" chega como UM texto "a,b": separa por vírgula.
$Splits = @($Splits | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($Splits.Count -eq 0) {
    # Todos os splits presentes nos casos, na ordem em que aparecem.
    $Splits = & $py -c "import json,pathlib; s=[]; [s.append(c['split']) for p in ['evals/cases.jsonl', *sorted(map(str, pathlib.Path('evals').glob('cases.d/*.jsonl'))), 'evals/heldout_blind.jsonl', *sorted(map(str, pathlib.Path('evals').glob('heldout_blind.d/*.jsonl'))), 'evals/real_questions.jsonl', *sorted(map(str, pathlib.Path('evals').glob('real_questions.d/*.jsonl')))] if pathlib.Path(p).exists() for c in map(json.loads, filter(str.strip, open(p, encoding='utf-8'))) if c['split'] not in s]; print(' '.join(s))"
    $Splits = $Splits -split ' '
}

if ($DryRun) {
    $teto = $MaxUsd.ToString([Globalization.CultureInfo]::InvariantCulture)
    Write-Host "DRYRUN splits=$($Splits -join '|') teto=$teto workers=$Workers repeat=$Repeat juiz=$(-not $NoJudge) processos=1"
    exit 0
}

# Antes de gastar: domínio do desafio ativo e gate offline verde do código atual (o motivo sai no console).
& $py -m evals.run_evals --check-live-ready
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ao vivo RECUSADO (nada foi gasto): corrija o motivo acima ou declare a exceção pela variável indicada."
    exit 4
}

# Os splits rodam ao mesmo tempo num processo SÓ (run_evals --splits), cada um com a sua cota (o teto inteiro, que é
# das conversas, proporcional aos casos). Com o buscador denso cada processo carrega e5-large + cross-encoder (GBs de
# RAM) e, em fila, cada split recarregava os modelos; num processo, eles carregam uma vez para todos.
$inv = [Globalization.CultureInfo]::InvariantCulture
$splitsUsd = [math]::Round($MaxUsd, 4).ToString($inv)
Write-Host "== splits $($Splits -join ',') num processo (teto dos splits US$ $splitsUsd, dividido igualmente)"
# repeat 3 só em official e memory (pass^3); juiz por split no mesmo processo (corte no fim não perde o juiz), sem
# --judge-max-usd: o juiz julga tudo.
$extra = @()
if ($Repeat -gt 1) { $extra += @("--repeat-by", "official=$Repeat,memory=$Repeat"); $Repeat = 1 }
if (-not $NoJudge) { $extra += @("--judge") }
& $py -m evals.run_evals --live --splits ($Splits -join ',') --max-usd $splitsUsd --workers $Workers --repeat $Repeat @extra
$code = $LASTEXITCODE
if ($code -eq 2) { Write-Host "Sem credencial: na nuvem, APP_ANTHROPIC_API_KEY nas variáveis do ambiente; no PC, ANTHROPIC_API_KEY no .env."; exit 2 }
$remaining = $MaxUsd
foreach ($split in $Splits) {
    $out = "evals/results/live_$split.json"
    if (Test-Path $out) {
        $rec = Get-Content $out -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Host "   ${split}: $($rec.status)"
        $remaining = $remaining - [double]$rec.spent_usd
    } else { Write-Host "   ${split}: ausente" }
}
if ($code -ne 0) { Write-Host "   saída $code (split abortado, degradado ou quebrado): a rodada ruim NÃO substituiu o resultado anterior" }

# o juiz já rodou por split no mesmo processo (--judge)
if ($SemReadme) { exit 0 }
$env:LLM_PROVIDER = "offline"
& $py -m evals.run_evals | Out-Null   # relatório offline (bloco principal do README e gate)
# análise de erros da bateria que acabou de rodar (gerada, nunca à mão: o fill_readme --check compara);
# commite docs/FAILURE_MODES.md junto com evals/results/
& $py -m evals.failure_modes
if ($LASTEXITCODE -ne 0) { Write-Host "   docs/FAILURE_MODES.md não gerado (motivo acima)" }
& $py scripts/fill_readme.py
