# Verificação (`scripts/check.py`, sem docker)

Commit `078cf2c`, 04/11/2026 18:46 UTC. Resultado: **VERMELHO**.

| etapa | resultado | s |
|---|---|---:|
| venv aponta para este repo | PASS | 0.0 |
| ruff | PASS | 0.0 |
| buscador = o configurado (sem fallback) | PASS | 15.8 |
| pytest | PASS | 58.3 |
| provas do README passam | PASS | 0.0 |
| eval gate | PASS | 52.7 |
| README ⇔ evidência commitada | FAIL | 0.3 |
| evidência do juiz coerente | PASS | 0.1 |
| resultado commitado = código atual | PASS | 0.1 |
| títulos de commit sem marcador {{ }} | PASS | 0.0 |
| sem dado de exemplo no produto | PASS | 0.1 |
| README e docs sem marcador do modelo | PASS | 0.0 |
| docs sem link para arquivo inexistente | FAIL | 0.0 |
| docs sem palavra de processo | PASS | 0.0 |
| README sem número de outra entrega | PASS | 0.0 |
| cenários oficiais com fato verificável | PASS | 0.0 |
| replay das gravações ao vivo | PASS | 24.1 |
