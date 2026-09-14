# 🛡️ Tríade de Garantia (Assurance Triad)

A garantia contínua de confiabilidade e qualidade de software no **`brazilian-rps-ground`** apoia-se em três pilares metodológicos:

---

## 🏛️ Os Três Pilares da Garantia

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRÍADE DE GARANTIA (ASSURANCE TRIAD)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. TESTS (Testes Automatizados - assurance/tests/)                         │
│     • Unitários: Verificação de invariantes, VOs, cálculos geodésicos       │
│     • Integração: Persistência real PostGIS e consultas espaciais ST_*      │
│                                                                             │
│  2. EVALS (Avaliações Contínuas de Performance - assurance/evals/)          │
│     • Benchmarks de taxa de ingestão (records/segundo)                      │
│     • Medição de latência de serialização e contenção de banco              │
│                                                                             │
│  3. AUDITS (Auditorias Constitucionais por AST - assurance/audits/)         │
│     • Domain Isolation: AST Linter que proíbe importação cruzada            │
│     • Value Object Immutability: Inspeção de @dataclass(frozen=True)        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Como Executar a Tríade Completa

```bash
# 1. Executar os Testes Unitários e de Integração
uv run pytest -v

# 2. Executar as Auditorias Arquiteturais (AST Linters)
uv run python assurance/audits/architecture/audit_domain_isolation.py
uv run python assurance/audits/architecture/audit_immutability.py

# 3. Executar o Benchmark de Ingestão de Big Data
uv run python assurance/evals/benchmarks/eval_postgis_ingestion_bench.py
```
