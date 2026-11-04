"""Um rotulador só (ensaio 13): a página sai sem nome fictício e o script avisa que a concordância não é medida."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_single_rater_is_allowed_with_a_warning(tmp_path):
    r = subprocess.run([sys.executable, "scripts/label_page.py", "--raters", "Matheus", "--n", "2",
                        "--out", str(tmp_path / "p.html")], cwd=ROOT, capture_output=True, text=True,
                       env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"})
    assert "pede 2+ pessoas" not in r.stderr
    assert "1 rotulador" in r.stderr
    if r.returncode == 0:  # com respostas ao vivo no kit a página sai; sem elas o script diz por quê
        assert json.loads(r.stdout.strip().splitlines()[-1])["raters"] == ["Matheus"]
