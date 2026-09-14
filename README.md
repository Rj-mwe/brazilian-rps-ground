# 🛰️ Brazilian RPS Ground Segment (`brazilian-rps-ground`)

Sistema de Operações e Processamento em Solo para o **Sistema de Posicionamento Regional Brasileiro (SPR-BR / SBAS-BR)**.

Projeto complementar e simétrico ao [`brazilian-rps-sim`](../brazilian-rps-sim), projetado sob o padrão arquitetural do **Hexágono Dourado** (*Clean Fractal Hexagonal Architecture*).

---

## 🎯 1. Visão Geral & Escopo

Enquanto o `brazilian-rps-sim` é o **emulador ciber-físico do segmento espacial** (astrodinâmica, perturbações orbitais, propagação eletromagnética e geração de sinais de satélites), o **`brazilian-rps-ground`** constitui o **Segmento Terrestre e de Usuário**:

1. **Ingestão e Descodificação de Sinais:** Recepção de telemetria e pseudodistâncias transmitidas pelos satélites em órbita (via API REST, WebSockets ou enlaces de rádio simulados).
2. **Estações de Monitoramento e Integridade (RIMS):** Processamento geodésico das estações de referência em território nacional (Alcântara, Natal, Brasília, Cachoeira Paulista, etc.).
3. **Geração de Correções SBAS:** Cálculo de correções de relógio, efemérides e grades de atraso ionosférico regional (IGPs).
4. **Big Data Geoespacial (US124):** Persistência de trajetórias, zonas de cobertura regional e cruzamento com malhas viárias e frotas terrestres via **PostgreSQL + PostGIS**.
5. **Console de Operações de Missão:** Visão cartográfica terrestre, skyplots de azimute/elevação e monitoramento da constelação a partir do ponto de vista do solo.

---

## 🏛️ 2. Arquitetura do Hexágono Dourado (Segmento de Solo)

```text
rps_ground/
├── core/
│   ├── domain/               # [Puro] Geodésia (SIRGAS2000/WGS84), RIMS, Mínimos Quadrados, SBAS
│   └── application/          # Casos de uso de solo, orquestração e Sub-Core de Governança
│       └── governance/       # Integridade de dados de navegação, limites de alarme (DO-229D)
├── adapters/                 # [Edge Adapters]
│   ├── downlink_client/      # Cliente receptor de telemetria do SPR-BR Sim
│   ├── postgis_sink/         # Adaptador de persistência espacial (US124: trajetórias e vias)
│   ├── web_console/          # Dashboard do operador de estação de solo
│   └── ntrip_server/         # Difusor de correções diferenciais padrão RTCM/NTRIP
└── infrastructure/           # [Substrates]
    ├── config/               # Resolução de configuração em cascata
    └── persistence/          # Drivers de conexão PostgreSQL/PostGIS e pools
```

---

## 🛡️ 3. Tríade de Garantia (Assurance Triad)

Seguindo o rigor do ecossistema do Hexágono Dourado:
* **`assurance/tests/`:** Testes unitários e de integração de portas e lógica de solo.
* **`assurance/evals/`:** Avaliações contínuas de latência de ingestão e precisão geodésica.
* **`assurance/audits/`:** Auditorias constitucionais de fronteira arquitetural e integridade de tipos.

---

## 🚀 4. Como Executar

```bash
# Instalação com uv
uv sync

# Execução dos testes
pytest
```
