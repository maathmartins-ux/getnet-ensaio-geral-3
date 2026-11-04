"""Com o domínio montado, o exemplo da loja que o mount apaga não reprova o pré-voo como "kit não consumido"."""
import subprocess

from scripts import preflight


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "x", "GIT_AUTHOR_EMAIL": "x@x", "GIT_COMMITTER_NAME": "x",
                        "GIT_COMMITTER_EMAIL": "x@x", "PATH": "/usr/bin:/bin", "HOME": str(cwd)})


def test_mounted_domain_removal_is_not_unconsumed_kit(tmp_path, monkeypatch):
    repo = tmp_path / "r"
    (repo / "data").mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "kit-fonte")
    (repo / "a.py").write_text("x", encoding="utf-8")
    (repo / "data" / "records.json").write_text("{}", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "kit")
    _git(repo, "checkout", "-q", "-b", "main")
    (repo / "data" / "records.json").unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "chore: scaffold from kit")
    monkeypatch.setattr(preflight, "kit_ref", lambda r: "refs/heads/kit-fonte")
    monkeypatch.setattr(preflight, "default_branch", lambda r: "main")
    problems = [p for p in preflight.check_repo(repo) if "não foi consumido" in p]
    assert problems == []
    assert "data/records.json" in preflight.MOUNT_REMOVES
