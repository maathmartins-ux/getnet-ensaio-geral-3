"""Pré-voo da nuvem: docker pull da base (429), push de teste e modelos no cache, com subprocess falso."""
from types import SimpleNamespace

from scripts import cloud_probe as cp

DIGEST = "python:3.12-slim@sha256:" + "a" * 64


def fake_run(table):
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        for key, res in table.items():
            if key in " ".join(cmd):
                return res
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    run.calls = calls
    return run


def dockerfile(tmp_path):
    p = tmp_path / "Dockerfile"
    p.write_text(f"FROM {DIGEST} AS build\nRUN true\n", encoding="utf-8")
    return p


def test_base_image_le_o_digest(tmp_path):
    assert cp.base_image(dockerfile(tmp_path)) == DIGEST
    assert cp.base_image(tmp_path / "nao-existe") is None


def test_sem_docker_diz_que_o_check_roda_so_no_ci(monkeypatch, tmp_path):
    monkeypatch.setattr(cp.shutil, "which", lambda _: None)
    _, ok, detail = cp.docker_pull_row(dockerfile(tmp_path))
    assert ok and "só no CI" in detail


def test_pull_429_falta_com_a_instrucao(monkeypatch, tmp_path):
    monkeypatch.setattr(cp.shutil, "which", lambda _: "/usr/bin/docker")
    err = SimpleNamespace(returncode=1, stdout="", stderr="toomanyrequests: You have reached your pull rate limit")
    monkeypatch.setattr(cp.subprocess, "run", fake_run({"pull": err}))
    _, ok, detail = cp.docker_pull_row(dockerfile(tmp_path))
    assert not ok and "429" in detail and "espelho" in detail and DIGEST in detail


def test_pull_ok_usa_o_digest(monkeypatch, tmp_path):
    monkeypatch.setattr(cp.shutil, "which", lambda _: "/usr/bin/docker")
    run = fake_run({})
    monkeypatch.setattr(cp.subprocess, "run", run)
    _, ok, _ = cp.docker_pull_row(dockerfile(tmp_path))
    assert ok and ["docker", "pull", "-q", DIGEST] in run.calls


def test_push_de_teste_nao_deixa_ramo_no_remoto(monkeypatch):
    # ensaio 13: o proxy recusou apagar o ramo descartável e ele ficou no repositório da entrega
    run = fake_run({})
    monkeypatch.setattr(cp.subprocess, "run", run)
    _, ok, detail = cp.push_row()
    assert ok and "nenhum ramo criado" in detail
    assert all("--dry-run" in c for c in run.calls if "push" in c) and not any("--delete" in c for c in run.calls)


def test_push_recusado_falta(monkeypatch):
    bad = SimpleNamespace(returncode=1, stdout="", stderr="fatal error in commit_refs")
    monkeypatch.setattr(cp.subprocess, "run", fake_run({"HEAD:refs": bad}))
    _, ok, detail = cp.push_row()
    assert not ok and "recusou escrita" in detail


def test_modelos_fora_do_cache_faltam(monkeypatch, tmp_path):
    monkeypatch.setenv("RETRIEVER", "dense")
    monkeypatch.setenv("RERANK", "cross")
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path / "vazio"))
    _, ok, detail = cp.models_row(tmp_path)
    assert not ok and "fetch_models" in detail


def test_modelos_no_cache_passam(monkeypatch, tmp_path):
    monkeypatch.setenv("RETRIEVER", "dense")
    monkeypatch.setenv("RERANK", "cross")
    cache = tmp_path / "cache"
    for d in ("models--intfloat--multilingual-e5-large", "models--BAAI--bge-reranker-v2-m3-int8"):
        (cache / d).mkdir(parents=True)
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(cache))
    _, ok, _ = cp.models_row(tmp_path)
    assert ok


def test_missing_heavy_dependency_is_a_pending_item_before_the_clock():
    # ensaio 13: o pip de ~530 pacotes passou de 10 min no T0; o pré-voo reprova antes do relógio
    name, ok, detail = cp.deps_row(("json", "pacote_que_nao_existe_xyz"))
    assert not ok and "pacote_que_nao_existe_xyz" in detail and "script de configuração" in detail
    assert cp.deps_row(("json",))[1]
