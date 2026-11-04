"""commit_titles_clean só do scaffold em diante: o repo do kit (sem scaffold) passa; na tentativa, título com {{ }}
depois do scaffold reprova e título com {{ }} de ANTES do scaffold (histórico do repositório) não conta."""
import subprocess

from scripts import check


def _git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=root, check=True,
                   capture_output=True)


def _commit(root, msg):
    _git(root, "commit", "--allow-empty", "-q", "-m", msg)


def test_kit_repo_without_scaffold_passes_even_with_markers_in_history(tmp_path):
    _git(tmp_path, "init", "-q")
    _commit(tmp_path, "fix(dominio): README sem marcador {{ }}")
    name, ok, _, detail = check.commit_titles_clean(tmp_path)
    assert ok and "repo do kit" in detail


def test_attempt_repo_rejects_markers_after_the_scaffold(tmp_path):
    _git(tmp_path, "init", "-q")
    _commit(tmp_path, "chore: repositório (antes do relógio) {{ok}}")  # antes do scaffold: não conta
    _commit(tmp_path, "chore: scaffold from kit")
    _commit(tmp_path, "feat: ok")
    assert check.commit_titles_clean(tmp_path)[1] is True
    _commit(tmp_path, "maestra: {{N}} frentes")
    _, ok, _, detail = check.commit_titles_clean(tmp_path)
    assert not ok and "{{N}} frentes" in detail and "amend" in detail


def test_scaffold_as_first_commit_checks_everything(tmp_path):
    _git(tmp_path, "init", "-q")
    _commit(tmp_path, "chore: scaffold {{x}}")
    _, ok, _, detail = check.commit_titles_clean(tmp_path)
    assert not ok and "scaffold {{x}}" in detail
