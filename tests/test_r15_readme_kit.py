"""README ⇔ evidência: no repo do kit (sem `chore: scaffold`) passa, declarado; na tentativa roda o
`fill_readme --check` como antes e o vermelho dele continua vermelho."""
import subprocess

from scripts import check


def _git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=root, check=True,
                   capture_output=True)


def test_kit_repo_skips_fill_readme(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "commit", "--allow-empty", "-q", "-m", "fix(kit): qualquer")
    monkeypatch.setattr(check, "step", lambda *a, **k: (_ for _ in ()).throw(AssertionError("não devia rodar")))
    name, ok, _, detail = check.readme_matches_evidence(tmp_path)
    assert name == "README ⇔ evidência commitada" and ok and "repo do kit" in detail


def test_attempt_repo_runs_fill_readme_and_keeps_its_failure(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "commit", "--allow-empty", "-q", "-m", "chore: scaffold from kit")
    calls = []

    def fake_step(name, cmd, env=None):
        calls.append(cmd)
        return name, False, 0.1, "README ≠ evidência: bloco scorecard diferente"

    monkeypatch.setattr(check, "step", fake_step)
    name, ok, _, detail = check.readme_matches_evidence(tmp_path)
    assert not ok and "README ≠ evidência" in detail
    assert calls == [[check.PY, "scripts/fill_readme.py", "--check"]]
