"""Erros de documentação que reprovam a entrega: o check reprova sozinho, sem depender de lembrar.

Do relógio de 60 min (as três avaliações tiraram ponto): `{{MINUTOS}}`/`{{VERSAO}}` na PROCEDENCIA; §7 citando
`docs/JUDGE_DIFF.md`, `retrieval_compare.json` e `ablation_replan*.json` que não existiam; linha "Vídeo" no topo sem
vídeo; "neste ensaio (decisão do dono)" no README; ENTREGA com 45 min e README com 65; "o último commit é só o README"
depois de um commit de código; números de outra entrega (0,868 / 0,921 / 0,789) no §4; e o push do final.sh caindo
sem nova tentativa. Fixtures com as frases reais.
"""
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from scripts import check, delivery_message, fill_readme, timesheet

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t"}


def _git(root: Path, *args: str, date: str | None = None) -> None:
    env = {**ENV, **({"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date} if date else {})}
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, env=env)


def _commit(root: Path, subject: str, files: dict[str, str], date: str) -> None:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", subject, date=date)


def _repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _commit(tmp_path, "chore: repositório", {"x": "0"}, "2026-11-04T10:47:00+00:00")
    _commit(tmp_path, "chore: scaffold from entregar-desafio-cronometrado kit v5.4.0", {"src/a.py": "a = 1\n"},
            "2026-11-04T11:07:00+00:00")
    _commit(tmp_path, "fix: motor", {"src/a.py": "a = 2\n"}, "2026-11-04T11:52:00+00:00")
    return tmp_path


# --- 1. marcador do modelo em qualquer doc da entrega ---------------------------------------------------------

def test_placeholders_in_any_delivery_doc_fail_but_not_actions_expressions(tmp_path):
    (tmp_path / "docs" / "kit").mkdir(parents=True)
    (tmp_path / "README.md").write_text("# P\n<!-- sem-prova:begin\n| q | {{causas}} | x |\nsem-prova:end -->\n",
                                        encoding="utf-8")
    (tmp_path / "docs" / "PROCEDENCIA.md").write_text("o que os {{MINUTOS}} minutos medem (kit {{VERSAO}})",
                                                      encoding="utf-8")
    (tmp_path / "docs" / "RUNBOOK.md").write_text("`token: ${{ secrets.GITHUB_TOKEN }}`", encoding="utf-8")
    (tmp_path / "docs" / "kit" / "PROMPTS.md").write_text("preencha {{VERSAO}}", encoding="utf-8")
    name, ok, _, detail = check.readme_has_no_placeholders(tmp_path)
    assert not ok and "docs" in name
    assert "docs/PROCEDENCIA.md: {{MINUTOS}}" in detail and "docs/PROCEDENCIA.md: {{VERSAO}}" in detail
    assert "RUNBOOK" not in detail and "kit/PROMPTS" not in detail and "README" not in detail  # comentário: invisível


# --- 2. caminho citado que não existe (inclusive com curinga); §7 tira a linha sem prova ------------------------

SECTION7 = """## 7. Perguntas da entrevista, respondidas

| Pergunta | Resposta curta | Onde está a prova |
|---|---|---|
| Quais respostas oficiais o juiz reprova? | official-04 sem a Get Conta | `docs/JUDGE_DIFF.md` |
| O rerank tem ganho medido? | não remedido no relógio | `evals/results/retrieval_compare.json` |
| Onde a memória perde informação? | rota × memória | §0 e `docs/RESULTS.md` |
| Como medir o ganho do replanejamento? | o braço sem não rodou | `evals/results/ablation_replan*.json` |

## 8. Procedência
"""


def test_section7_drops_rows_whose_proof_is_missing_and_brings_them_back(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "RESULTS.md").write_text("r", encoding="utf-8")
    once = fill_readme.prune_proofs(SECTION7, tmp_path)
    table = once.split("<!-- sem-prova:begin")[0]
    assert "docs/RESULTS.md" in table and "JUDGE_DIFF" not in table and "retrieval_compare" not in table
    assert "ablation_replan" not in table and "## 8. Procedência" in once
    assert fill_readme.prune_proofs(once, tmp_path) == once  # idempotente
    assert not check.visible(once).count("JUDGE_DIFF")  # o leitor não vê a linha guardada
    # a prova apareceu (rodada 2 rodou): a linha volta para a tabela, com a resposta escrita
    (tmp_path / "docs" / "JUDGE_DIFF.md").write_text("d", encoding="utf-8")
    (tmp_path / "evals" / "results").mkdir(parents=True)
    (tmp_path / "evals" / "results" / "ablation_replan_real.json").write_text("{}", encoding="utf-8")
    back = fill_readme.prune_proofs(once, tmp_path)
    table = back.split("<!-- sem-prova:begin")[0]
    assert "official-04 sem a Get Conta | `docs/JUDGE_DIFF.md`" in table and "ablation_replan*" in table
    assert "retrieval_compare" not in table


def test_check_rejects_the_unpruned_section7_and_cited_missing_files(tmp_path):
    _repo(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("# P\n\n" + SECTION7, encoding="utf-8")
    problems = fill_readme._check_repo_facts(readme.read_text(encoding="utf-8"), tmp_path, tmp_path)
    assert any("§7 cita prova que não existe" in p for p in problems)
    _git(tmp_path, "add", "-A")
    _, ok, _, detail = check.docs_links_exist(tmp_path)
    assert not ok
    assert "docs/JUDGE_DIFF.md" in detail and "evals/results/ablation_replan*.json" in detail  # curinga também


# --- 3. linha do vídeo e frase do último commit, geradas e conferidas ----------------------------------------

def test_video_row_only_with_a_video_in_the_repo(tmp_path):
    assert "Vídeo" not in fill_readme.links_block(tmp_path)
    (tmp_path / "docs" / "video").mkdir(parents=True)
    (tmp_path / "docs" / "video" / "walkthrough.mp4").write_bytes(b"\0")
    assert "| Vídeo | [walkthrough](docs/video/walkthrough.mp4)" in fill_readme.links_block(tmp_path)
    (tmp_path / "docs" / "video" / "URL.txt").write_text("https://github.com/o/r/releases/tag/video\n",
                                                         encoding="utf-8")
    assert "(https://github.com/o/r/releases/tag/video)" in fill_readme.links_block(tmp_path)


def test_hand_written_video_row_without_video_fails(tmp_path):
    _repo(tmp_path)
    old_top = ("| | |\n|---|---|\n| Vídeo | [walkthrough na página de Releases](../../releases/tag/video) (MP4 + "
               "legendas) |\n")
    problems = fill_readme._check_repo_facts("# P\n" + old_top, tmp_path, tmp_path)
    assert any("README aponta para um vídeo, mas não há docs/video/walkthrough.mp4" in p for p in problems)
    (tmp_path / "docs" / "video").mkdir(parents=True)
    (tmp_path / "docs" / "video" / "URL.txt").write_text("https://github.com/o/r/releases/tag/video", encoding="utf-8")
    assert fill_readme._check_repo_facts("# P\n" + old_top, tmp_path, tmp_path) == []


def test_last_commit_claim_must_match_head(tmp_path):
    _repo(tmp_path)
    final = "# P\n<!-- links:begin -->\n" + fill_readme.links_block(tmp_path, True) + "\n<!-- links:end -->\n"
    assert fill_readme.LAST_IS_README in final
    problems = fill_readme._check_repo_facts(final, tmp_path, tmp_path)
    assert any("mas o último commit mexeu em src/a.py" in p for p in problems)  # HEAD = fix de código
    _commit(tmp_path, "readme: números", {"README.md": final}, "2026-11-04T11:53:00+00:00")
    assert fill_readme._check_repo_facts(final, tmp_path, tmp_path) == []  # agora é verdade
    plain = final.replace(f" ({fill_readme.LAST_IS_README})", "")
    _commit(tmp_path, "fix: depois", {"src/a.py": "a = 3\n"}, "2026-11-04T11:55:00+00:00")
    assert fill_readme._check_repo_facts(plain, tmp_path, tmp_path) == []  # sem a frase, nada a dizer


@pytest.mark.skipif(check.domain_started(), reason="na entrega o make final escreve a frase de propósito (fill_readme "
                    "--final) e o --check confere; este teste é só do modelo do kit (ensaio 13: CI vermelha)")
def test_kit_readme_template_has_generated_top_without_video_or_claim():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    top = fill_readme._block(readme, "links")
    assert top and "| Vídeo |" not in top and fill_readme.LAST_IS_README not in top
    final_sh = (ROOT / "scripts" / "final.sh").read_text(encoding="utf-8")
    assert "fill_readme.py --final" in final_sh


# --- 4. palavras de processo ----------------------------------------------------------------------------------

def test_process_words_fail_in_delivery_docs_but_not_in_urls_or_kit_history(tmp_path):
    (tmp_path / "docs" / "kit").mkdir(parents=True)
    (tmp_path / "README.md").write_text(
        "a rotulagem humana NÃO rodou neste ensaio (decisão do dono: nenhum rotulador)\n"
        "Repositório: https://github.com/o/getnet-ensaio-60min-r12\n", encoding="utf-8")
    (tmp_path / "docs" / "ENTREGA.md").write_text("a maestra revisou; a r" + chr(233) + "gua leu", encoding="utf-8")
    (tmp_path / "docs" / "kit" / "ENSAIO.md").write_text("ensaio", encoding="utf-8")
    _, ok, _, detail = check.no_process_words(tmp_path)
    assert not ok
    assert "README.md:1: 'ensaio'" in detail and "'decisão do dono'" in detail and "'maestra'" in detail
    assert "README.md:2" not in detail and "kit/ENSAIO" not in detail
    (tmp_path / "README.md").write_text("sem validação humana nesta entrega\n", encoding="utf-8")
    (tmp_path / "docs" / "ENTREGA.md").write_text("ok", encoding="utf-8")
    assert check.no_process_words(tmp_path)[1]


def test_kit_templates_carry_no_process_words_nor_numbers_of_another_delivery():
    # a entrega herda o README, a PROCEDENCIA e os ADRs do kit: o que reprova lá não pode vir do modelo
    _, ok, _, detail = check.no_process_words(ROOT)
    assert ok, detail
    _, ok, _, detail = check.no_kit_numbers(ROOT)
    assert ok, detail


# --- 5. minutos do relógio de uma fonte só; PROCEDENCIA preenchida ---------------------------------------------

def test_minutes_come_from_one_source_and_procedencia_is_filled(tmp_path, monkeypatch):
    _repo(tmp_path)
    _git(tmp_path, "tag", "clock-start", "HEAD~1")
    monkeypatch.setattr(timesheet, "ROOT", tmp_path)
    assert timesheet.main([]) == 0  # TIMESHEET: scaffold 11:07 → último commit 11:52
    assert timesheet.clock_minutes(tmp_path) == 45 == delivery_message.minutes(tmp_path)
    line = fill_readme.timeline(tmp_path).splitlines()[-1]
    assert line == "Relógio: **45 min**, 3 commits."  # "do primeiro ao último commit" dava 65 (o commit do repo)
    proc = "o que os {{MINUTOS}} minutos medem (kit {{VERSAO}}); na versão {{VERSAO}}"
    filled = fill_readme.fill_inline(proc, tmp_path)
    assert check.visible(filled) == "o que os 45 minutos medem (kit v5.4.0); na versão v5.4.0"
    assert fill_readme.fill_inline(filled, tmp_path) == filled
    (tmp_path / "docs" / "PROCEDENCIA.md").write_text(filled.replace(">45<", ">44<"), encoding="utf-8")
    (tmp_path / "docs" / "ENTREGA.md").write_text("Relógio: 65 min do commit de scaffold", encoding="utf-8")
    readme = "# P\n<!-- timeline:begin -->\n| x |\n\nRelógio: **45 min**, 3 commits.\n<!-- timeline:end -->\n"
    problems = fill_readme._check_repo_facts(readme, tmp_path, tmp_path)
    assert "docs/ENTREGA.md diz 65 min de relógio, o docs/TIMESHEET.md diz 45: rode scripts/final.sh" in problems
    assert any("docs/PROCEDENCIA.md: minutos '44' × '45'" in p for p in problems)


def test_kit_procedencia_template_has_generated_minutes_and_version():
    text = (ROOT / "docs" / "PROCEDENCIA.md").read_text(encoding="utf-8")
    assert "{{" not in text and "<!-- minutos:begin -->" in text and "<!-- versao:begin -->" in text


# --- 7. números de outra entrega no README ---------------------------------------------------------------------

def test_kit_numbers_fail_outside_generated_blocks(tmp_path):
    row = ("| Busca dense + cross | escolher no relógio | no caminho do agente: Recall@3 0,868 · Recall@5 0,921 · "
           "MRR 0,789; oficiais 96,7% → 90% |")
    (tmp_path / "README.md").write_text(f"# P\n{row}\n<!-- retrieval:begin -->\nRecall@3 0,868\n"
                                        "<!-- retrieval:end -->\n", encoding="utf-8")
    _, ok, _, detail = check.no_kit_numbers(tmp_path)
    assert not ok and detail.count("README.md:2") == 4
    (tmp_path / "README.md").write_text("<!-- retrieval:begin -->\nRecall@3 0,868\n<!-- retrieval:end -->\n",
                                        encoding="utf-8")
    assert check.no_kit_numbers(tmp_path)[1]  # gerado da evidência desta entrega: vale


# --- o final.sh roda tudo antes do commit e o push tenta de novo -----------------------------------------------

def test_final_sh_checks_delivery_docs_before_committing():
    final = (ROOT / "scripts" / "final.sh").read_text(encoding="utf-8")
    assert final.index("scripts/check.py --docs") < final.index("git commit")


@pytest.mark.skipif(check.domain_started(), reason="com o domínio do desafio o --docs confere a entrega de verdade "
                    "(o make final roda e reprova); este teste é só do kit, que não tem entrega")
def test_check_docs_mode_is_quiet_in_the_kit():
    r = subprocess.run([shutil.which("python") or "python", "scripts/check.py", "--docs"], cwd=ROOT,
                       capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    assert r.returncode == 0 and "não conferidos" in r.stdout


@pytest.mark.skipif(BASH is None, reason="sem bash")
def test_push_retries_after_a_transient_failure(tmp_path):
    fake = tmp_path / "bin" / "git"
    fake.parent.mkdir()
    count = tmp_path / "count"
    fake.write_text(f"#!/usr/bin/env bash\nn=$(cat {count} 2>/dev/null || echo 0); echo $((n + 1)) > {count}\n"
                    f'[[ "$1" == push && $n -lt ${{FAILS:-1}} ]] && '
                    '{ echo "fatal error in commit_refs" >&2; exit 1; }\n'
                    "exit 0\n", encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    final = (ROOT / "scripts" / "final.sh").read_text(encoding="utf-8")
    func = re.search(r"^push_retry\(\) \{.*?^\}", final, re.S | re.M).group(0)
    env = {**os.environ, "PATH": f"{fake.parent}:{os.environ['PATH']}", "PUSH_WAITS": "0 0 0 0"}
    r = subprocess.run([BASH, "-c", f"set -euo pipefail\n{func}\npush_retry"], env=env, capture_output=True,
                       text=True)
    assert r.returncode == 0 and "nova tentativa" in r.stderr and count.read_text().strip() == "2"
    count.unlink()
    r = subprocess.run([BASH, "-c", f"set -euo pipefail\n{func}\npush_retry"], env={**env, "FAILS": "9"},
                       capture_output=True, text=True)
    assert r.returncode == 1 and "push recusado 5 vezes" in r.stderr and count.read_text().strip() == "5"
