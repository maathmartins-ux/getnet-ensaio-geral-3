# Frente R11-D2: JWT por biblioteca auditada (PyJWT)

Base: seção 14 do resultado da régua da rodada 10 ("JWT implementado à mão, sem biblioteca auditada", réguas 1 e 2).
Nenhuma chamada de API ou LLM; os prompts não mudam, então as gravações do replay continuam válidas.

## 1. Emissão e leitura do JWT pelo PyJWT
- **O quê:** `auth.issue_token` usa `jwt.encode` com a chave ativa do conjunto (`kid` no cabeçalho). `auth.decode_token`
  usa `jwt.get_unverified_header` só para escolher a chave pelo `kid` e `jwt.decode` com `algorithms=[alg da chave]`,
  `audience`, `issuer`, `leeway=LEEWAY_S` e `require` de exp/iat/sub/jti. Saíram `keys.sign` e `keys.verify`
  (assinatura e conferência à mão); `Key.signing_key`/`Key.verifying_key` entregam o material ao PyJWT, e a JWK do
  `/.well-known/jwks.json` sai do `to_jwk` do PyJWT (com `use: sig`, sem `key_ops`, RFC 7517 §4.3). Continuam: o
  conjunto de chaves com `kid`, a rotação, HS256/EdDSA/RS256, a revogação por `jti` e a recusa da confusão de
  algoritmo (o `alg` aceito é o da chave, nunca o do token).
- **Por quê:** §14 — "O JWT é implementado à mão (encode/decode próprios), não por biblioteca auditada" (réguas 1 e 2,
  `src/app/auth.py`, emissão e leitura). O PyJWT já estava na imagem (via `mcp`).
- **Prova:** `tests/test_key_rotation.py` inteiro (rotação nos três algoritmos, confusão de algoritmo, `kid`
  desconhecido, JWKS validado pelo `PyJWK`) e `tests/test_key_rotation.py::test_hs256_tokens_interoperate_with_pyjwt_both_ways`
  (o padrão sem AUTH_KEYS: o PyJWT puro abre o nosso token, e o token dele vale aqui, com e sem `kid`).

## 2. Token malformado é 401, nunca 500
- **O quê:** toda a leitura do token fica dentro do `try`. Token assinado com a chave certa e malformado vira `None`
  (401): exp/iat/nbf fora de número JSON, payload que não é objeto, sub/jti ausentes, vazios ou com tipo errado,
  `iss`/`aud` com tipo errado, `crit` desconhecido, `b64` falso, `kid` que não é texto, `alg` ausente ou em lista.
  NumericDate tem de ser número JSON (RFC 7519 §2): o PyJWT aceita texto ("123" vira int), e a denylist grava `exp`
  numa coluna REAL.
- **Por quê:** §14, item 4 — a conferência de exp/iat/iss/aud ficava fora do `try`, e payload em lista ou `exp` em
  texto davam AttributeError/TypeError (500 no `/chat`, no `/auth/revoke` e no portão do `/mcp`). Rodados contra o
  código antigo, esses casos dão 500, e passavam `exp` infinito, `nbf` em texto, `crit` desconhecido, token sem `jti`
  (que não pode ser revogado) e `sub` numérico, que virava o id do usuário. Os demais casos (sub vazio, `aud` em
  número, `kid` numérico...) já eram recusados e ficam como guarda de regressão.
- **Prova:** `tests/test_identity.py::test_signed_but_malformed_token_gets_401_not_500` (cada caso no `verify_token`, no
  `/chat` e no `/auth/revoke`, com controle) e `tests/test_mcp.py::test_signed_but_malformed_token_gets_401_not_500`
  (uvicorn de verdade, portão do `/mcp`).

## 3. `aud` em lista, `nbf` e `jti` obrigatório
- **O quê:** `aud` em lista vale quando contém a nossa API (RFC 7519 §4.1.3); `nbf` no futuro (além da folga) é 401;
  token sem `jti` ou com `jti` vazio é recusado.
- **Por quê:** §14, item 4 — `aud` em lista era recusado, `nbf` e `crit` eram ignorados, e um token sem `jti` levava a
  revogação para a chave vazia.
- **Prova:** `tests/test_identity.py::test_audience_list_is_accepted_when_it_names_this_api`,
  `tests/test_identity.py::test_not_before_and_expiry_respect_the_clock_leeway` e os casos `sem-jti`/`jti-vazio` do
  teste do item 2.

## 4. Um relógio só na emissão e na leitura
- **O quê:** `auth._now()` lê o mesmo relógio com que o PyJWT valida (`datetime.now` em UTC). O
  `test_expired_token_is_rejected` mantém o nome (é citado no README, na COBERTURA e no SECURITY_ASI) e agora desloca
  o relógio só na emissão, com `monkeypatch.context()` para não desfazer o ambiente do conftest.
- **Por quê:** com `time.time()` na emissão e o relógio do PyJWT na leitura, quem adianta `time.time()` para vencer outra
  coisa dessincronizava o JWT: `tests/test_hitl.py::test_pending_action_expires` recebia 401 (iat no futuro) em vez do
  410 da ação vencida.
- **Prova:** `tests/test_identity.py::test_token_clock_is_the_validator_clock`,
  `tests/test_identity.py::test_expired_token_is_rejected` e `tests/test_hitl.py::test_pending_action_expires`.

## 5. Chave que o PyJWT recusa é erro de configuração na carga
- **O quê:** a chave só entra no conjunto se o `prepare_key` do PyJWT a aceita para o `alg` dela (recusa segredo HS256
  vazio, em PEM ou em JWK, o formato da confusão de algoritmo). Arquivo de chave ausente ou sem permissão e PEM
  ilegível ou cifrado viram `KeyConfigError`.
- **Por quê:** com o PyJWT, um segredo nesses formatos passaria na carga e daria InvalidKeyError no primeiro login
  (500). O arquivo de chave ausente já dava OSError fora do tratamento (500 no `/health` e em toda requisição com token).
  Agora o `/health` mostra `jwt.ok=false` com o motivo, e o token vira 401 (falha fechado).
- **Prova:** `tests/test_key_rotation.py::test_key_material_the_library_refuses_is_a_config_error_not_a_500`.

## 6. Dependências diretas e segredo de teste
- **O quê:** `pyproject.toml` declara `pyjwt[crypto]` e `cryptography` como dependências diretas, com piso na versão do
  lock. O `tests/conftest.py` usa um AUTH_SECRET de teste com pelo menos 32 bytes.
- **Por quê:** §14, item 3 — o PyJWT vinha só via `mcp` e a `cryptography` só via `pyjwt`, embora `app/keys.py` importe
  as duas. O segredo de teste curto fazia o PyJWT avisar (`InsecureKeyLengthWarning`, RFC 7518 §3.2) a cada token da
  suíte; nenhum teste dependia dele ser fraco (o aviso de segredo curto no `/health` e a recusa em produção seguem
  provados pelo OPERATOR_TOKEN curto e pelo `AUTH_KEYS[curta]`).
- **Lock:** não regerado. `uv pip compile --offline` não resolve sem rede (o `mcp` não está no cache). As versões do lock
  já cumprem os pisos e a imagem e o CI instalam do lock com `--no-deps`; ao regerar com rede (comando no topo do
  `requirements.lock`), só o comentário `# via` de `pyjwt` e `cryptography` muda.
- **Prova:** os testes focados rodam sem nenhum aviso.
