"""O caminho de saída da captura do vídeo é absoluto antes do chdir (ensaio 14: o relativo derrubou o `make video`)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("capture_demo", ROOT / "scripts" / "video" / "capture_demo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # só define funções: o corpo do script roda em main()
    return mod


def test_relative_output_resolves_against_the_caller_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = _module().out_path(["capture_demo.py", "docs/video/demo.json"])
    assert out.is_absolute() and out == tmp_path / "docs" / "video" / "demo.json"


def test_default_output_is_the_committed_demo_json():
    out = _module().out_path(["capture_demo.py"])
    assert out == ROOT / "docs" / "video" / "demo.json" and out.is_relative_to(ROOT)


def test_make_video_passes_a_path_the_script_accepts():
    sh = (ROOT / "scripts" / "video" / "make_video.sh").read_text(encoding="utf-8")
    assert 'cd "$ROOT"' in sh and "capture_demo.py docs/video/demo.json" in sh  # relativo à raiz, resolvido no script
