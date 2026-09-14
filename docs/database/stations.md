# 📍 Estações Canônicas de Monitoramento e Zonas de Cobertura

Especificação das 5 estações terrestres de referência do **Sistema de Posicionamento Regional Brasileiro (SPR-BR / SBAS-BR)**.

---

## 🗺️ 1. Distribuição Geográfica Estratégica

As estações foram posicionadas para cobrir a extensão territorial continental do Brasil, os centros aeroespaciais estratégicos e os eixos de transporte mais densos do país:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                 REDE DE ESTAÇÕES CANÔNICAS DO SPR-BR / SBAS-BR              │
├─────┬────────────────────────────────┬──────────┬───────────┬───────┬───────┤
│ Cód │ Estação & Localidade           │ Latitude │ Longitude │ Alt.  │ Raio  │
├─────┼────────────────────────────────┼──────────┼───────────┼───────┼───────┤
│ SJC │ São José dos Campos (ITA/DCTA) │ -23.210° │ -45.880°  │ 660 m │ 1200k │
│ ALC │ Alcântara (CLA - Maranhão)     │  -2.316° │ -44.368°  │  35 m │ 1500k │
│ NAT │ Natal (CLBI - Rio Grande N.)   │  -5.795° │ -35.209°  │  42 m │ 1500k │
│ BSB │ Brasília (CCM - Distrito Fed.) │ -15.794° │ -47.882°  │ 1172m │ 1800k │
│ CPQ │ Cachoeira Paulista (INPE - SP) │ -22.686° │ -45.007°  │ 565 m │ 1200k │
└─────┴────────────────────────────────┴──────────┴───────────┴───────┴───────┘
```

---

## 🛰️ 2. Papel Operacional de Cada Estação

### 1. São José dos Campos / SP (`SJC`)
* **Local:** Campus do DCTA / ITA / INPE.
* **Classificação:** `AEROSPACE_RESEARCH` e RIMS de Alta Precisão.
* **Função:** Polo central de engenharia de solo, validação de novos receptores multifrequência, suporte aos testes de integração com o simulador de satélites (`brazilian-rps-sim`) e monitoramento da malha viária do Vale do Paraíba.

### 2. Alcântara / MA (`ALC`)
* **Local:** Centro de Lançamento de Alcântara (CLA).
* **Classificação:** `RIMS` (Ranging and Integrity Monitoring Station).
* **Função:** Estação equatorial de referência. Crítica para a caracterização do atraso ionosférico na região equatorial e monitoramento da subida de veículos lançadores.

### 3. Natal / RN (`NAT`)
* **Local:** Centro de Lançamento da Barreira do Inferno (CLBI).
* **Classificação:** `RIMS` (Ranging and Integrity Monitoring Station).
* **Função:** Ponto mais oriental do território brasileiro. Essencial para a geometria de visada e DOP dos satélites geoestacionários da costa leste (`RPS-GEO-3`).

### 4. Brasília / DF (`BSB`)
* **Local:** Centro de Controle de Missão Master (CCM).
* **Classificação:** `MASTER_CONTROL`.
* **Função:** Centro nevrálgico onde convergem todas as telemetrias RIMS, cálculo das correções diferenciais de relógio e efemérides (Fast/Slow corrections) e estimativa dos pontos de grade ionosférica (IGPs).

### 5. Cachoeira Paulista / SP (`CPQ`)
* **Local:** Instituto Nacional de Pesquisas Espaciais (INPE) / CPTEC.
* **Classificação:** `RIMS` (Ranging and Integrity Monitoring Station).
* **Função:** RIMS de alta estabilidade para a região Sudeste, conectada ao eixo rodoviário Presidente Dutra e em linha de visada contínua com a estação de SJC.
