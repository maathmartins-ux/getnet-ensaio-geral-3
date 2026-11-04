"""Cache de vetores aplicado pelo `mount` (rodada 15): extrai só com o VERSAO do mesmo lock e do mesmo script de
modelos, declara na PROCEDENCIA, avisa e segue sem ele quando a versão é outra ou o tar é inseguro."""
import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "docs" / "kit" / "tools" / "dominio.py"
pytestmark = pytest.mark.skipif(not TOOL.exists(), reason="sem docs/kit/ (entrega)")


def _tool():
    spec = importlib.util.spec_from_file_location("dominio_cache", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tar(path: Path, members: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:gz") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))


@pytest.fixture
def setup(tmp_path, monkeypatch):
    d = _tool()
    store, root = tmp_path / "store", tmp_path / "tentativa"
    (store / "files" / "data").mkdir(parents=True)
    (store / "files" / "data" / "x.jsonl").write_text("{}\n", encoding="utf-8")
    (store / "MANIFEST.json").write_text(json.dumps({"source": "https://github.com/o/r", "commit": "abcdef1234",
                                                     "saved_at": "2026-11-04", "files": ["data/x.jsonl"]}))
    (root / "docs").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "docs" / "PROCEDENCIA.md").write_text("# Procedência\n\n## 1. O kit e a sua história\n", encoding="utf-8")
    (root / "requirements-hybrid.lock").write_text("fastembed==1.0\n", encoding="utf-8")
    (root / "scripts" / "fetch_models.py").write_text("MODELS = []\n", encoding="utf-8")
    monkeypatch.setattr(d, "STORE", store)
    monkeypatch.delenv("EMBED_CACHE_DIR", raising=False)
    (store / "cache").mkdir()
    return d, store, root


def _version(d, root, **over):
    return json.dumps({**d.cache_version(root), "kit": "0123456789abcdef", **over})


def test_right_version_extracts_and_declares(setup, capsys):
    d, store, root = setup
    _tar(store / "cache" / "embeddings.tar.gz", {"e5-x-passages.jsonl": b'{"k":"a","v":[0.1]}\n', "q-e5.jsonl": b""})
    (store / "cache" / "VERSAO").write_text(_version(d, root), encoding="utf-8")
    d.mount(root)
    assert (root / "var" / "embeddings" / "e5-x-passages.jsonl").read_text() == '{"k":"a","v":[0.1]}\n'
    assert "cache de vetores: 2 arquivos (kit 0123456)" in capsys.readouterr().out
    assert d.CACHE_SENTENCE in (root / "docs" / "PROCEDENCIA.md").read_text(encoding="utf-8")


def test_other_version_warns_and_does_not_extract(setup, capsys):
    d, store, root = setup
    _tar(store / "cache" / "embeddings.tar.gz", {"e5-x-passages.jsonl": b"{}\n"})
    (store / "cache" / "VERSAO").write_text(_version(d, root, hybrid_lock_sha256="outro"), encoding="utf-8")
    d.mount(root)
    assert not (root / "var" / "embeddings").exists()
    assert "AVISO: cache de vetores de outra versão (lock/modelos)" in capsys.readouterr().out
    assert d.CACHE_SENTENCE not in (root / "docs" / "PROCEDENCIA.md").read_text(encoding="utf-8")


def test_without_artifact_nothing_changes(setup, capsys):
    d, store, root = setup
    d.mount(root)
    assert not (root / "var").exists() and capsys.readouterr().out == ""
    proc = (root / "docs" / "PROCEDENCIA.md").read_text(encoding="utf-8")
    assert "Domínio montado antes do relógio" in proc and d.CACHE_SENTENCE not in proc


@pytest.mark.parametrize("bad", ["../x", "/abs/x", "a/../../x"])
def test_unsafe_tar_is_refused_and_mount_goes_on(setup, capsys, bad):
    d, store, root = setup
    _tar(store / "cache" / "embeddings.tar.gz", {"ok.jsonl": b"{}\n", bad: b"x"})
    (store / "cache" / "VERSAO").write_text(_version(d, root), encoding="utf-8")
    d.mount(root)  # não derruba o T+0
    out = capsys.readouterr().out
    assert "membro inseguro" in out and "segue sem cache" in out
    assert not (root / "var" / "embeddings" / "ok.jsonl").exists()  # nada extraído: valida tudo antes
    assert not (root.parent / "x").exists()
    assert (root / "data" / "x.jsonl").exists()  # o domínio montou


def test_symlink_member_is_refused(setup, capsys):
    d, store, root = setup
    with tarfile.open(store / "cache" / "embeddings.tar.gz", "w:gz") as tar:
        link = tarfile.TarInfo("link")
        link.type, link.linkname = tarfile.SYMTYPE, "/etc/passwd"
        tar.addfile(link)
    (store / "cache" / "VERSAO").write_text(_version(d, root), encoding="utf-8")
    d.mount(root)
    assert "membro inseguro" in capsys.readouterr().out and not (root / "var" / "embeddings" / "link").exists()


def test_corrupt_archive_warns(setup, capsys):
    d, store, root = setup
    (store / "cache" / "embeddings.tar.gz").write_bytes(b"isto nao e um tar")
    (store / "cache" / "VERSAO").write_text(_version(d, root), encoding="utf-8")
    d.mount(root)
    assert "segue sem cache" in capsys.readouterr().out
