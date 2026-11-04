#!/usr/bin/env bash
# Script de configuração do ambiente da nuvem (PLAYBOOK §0, A10). Cole TUDO em: menu do ambiente → Edit → Setup script.
# GERADO por scripts/setup_env.py a partir de requirements-dev.lock + requirements-hybrid.lock (não edite à mão; o teste
# tests/test_setup_env.py confere que bate com os locks). Não lê nada do repositório: no repositório da tentativa os
# locks só existem no ramo kit-fonte. Instala com uv (segundos; o pip levou ~10 min) no python do sistema.
set -euo pipefail
UV="$(command -v uv || true)"; [ -n "$UV" ] || UV=/root/.local/bin/uv
if [ ! -x "$UV" ]; then python3 -m pip install -q uv && UV="$(command -v uv)"; fi
cat > /tmp/kit-requirements.txt <<'KIT_LOCK'
annotated-doc==0.0.5
annotated-types==0.8.0
anthropic==2.3.0
anyio==4.15.1
attrs==26.1.0
certifi==2026.10.23
cffi==2.1.1 ; platform_python_implementation != 'PyPy'
charset-normalizer==3.5.2
click==8.5.0
colorama==0.4.6 ; sys_platform == 'win32'
cryptography==50.0.2
docstring-parser==0.18.0
execnet==2.1.2
fastapi==0.162.0
fastembed==0.9.1
filelock==4.2.5
flatbuffers==25.12.19
fsspec==2026.9.0
h11==0.16.0
hf-xet==1.8.0 ; platform_machine == 'AMD64' or platform_machine == 'aarch64' or platform_machine == 'amd64' or platform_machine == 'arm64' or platform_machine == 'x86_64'
httpcore==1.0.9
httpcore2==2.16.0 ; sys_platform != 'emscripten'
httptools==0.9.0
httpx==0.28.1
httpx2==2.16.0
httpx2-jsfetch==1.0 ; sys_platform == 'emscripten'
huggingface-hub==1.33.0
idna==3.20
iniconfig==2.3.1
jiter==0.18.0
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
loguru==0.7.3
mcp==2.3.0
mcp-types==2.3.0
mmh3==5.3.1
numpy==2.5.4
onnxruntime==1.31.1
opentelemetry-api==1.45.2
opentelemetry-sdk==1.45.2
opentelemetry-semantic-conventions==0.66b2
packaging==26.3
pillow==13.0.0
pluggy==1.7.0
protobuf==7.36.2
psycopg==3.3.6
psycopg-binary==3.3.6 ; implementation_name != 'pypy'
py-rust-stemmers==0.1.8
pycparser==3.12 ; implementation_name != 'PyPy' and platform_python_implementation != 'PyPy'
pydantic==2.14.2
pydantic-core==2.50.2
pygments==2.21.0
pyjwt==2.15.1
pytest==9.2.0
pytest-xdist==3.8.0
python-dotenv==1.2.4
python-multipart==0.0.32
pywin32==312 ; sys_platform == 'win32'
pyyaml==6.0.3
referencing==0.37.0
requests==2.34.2
rpds-py==2026.9.1
ruff==0.17.3
sniffio==1.3.1
sse-starlette==3.6.0
starlette==1.10.0
tokenizers==0.23.3
tqdm==4.70.1
truststore==0.10.5 ; sys_platform != 'emscripten'
typing-extensions==4.16.0
typing-inspection==0.4.4
urllib3==2.8.0
uvicorn==0.54.0
uvloop==0.23.0 ; platform_python_implementation != 'PyPy' and sys_platform != 'cygwin' and sys_platform != 'win32'
watchfiles==1.3.0
websockets==17.4
win32-setctime==1.2.1 ; sys_platform == 'win32'
KIT_LOCK
"$UV" pip install --system -q -r /tmp/kit-requirements.txt
python3 -c "import fastembed, onnxruntime, numpy, tokenizers, fastapi, anthropic, pytest, xdist; print('dependencias do kit OK')"
# modelos do buscador padrão (~2,8 GB) no cache do fastembed; falha de rede aqui não derruba o ambiente: o relógio
# baixa no 1º eval (scripts/fetch_models.py)
python3 - <<'KIT_MODELS' || echo "AVISO: modelos do buscador não baixados; o 1º eval baixa"
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
TextEmbedding("intfloat/multilingual-e5-large")
TextCrossEncoder("BAAI/bge-reranker-v2-m3-int8")
print("modelos do buscador OK")
KIT_MODELS
