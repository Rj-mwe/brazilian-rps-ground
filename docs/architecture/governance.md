# ⚖️ Sub-Core de Governança & Regulação Temporal (IEEE 1516)

O **Sub-Core de Governança (`core/application/governance/`)** é o **único sub-core de aplicação** no Hexágono Dourado, operando como o xerife e o regulador de conformidade do sistema.

---

## ⏱️ 1. A Barreira Temporal (IEEE 1516 High Level Architecture)

Em simulações e operações aeroespaciais distribuídas, o tempo não é um detalhe de transporte. A classe `GroundTemporalBarrier` garante:
* **Monotonicidade Estrita:** É proibido que qualquer evento retrógrado (com timestamp no passado em relação ao relógio mestre) seja admitido.
* **Sincronismo de Solo:** Alinha as telemetrias assíncronas recebidas de múltiplas estações remotas (SJC, Alcântara, Natal, Brasília, CPQ) antes do cálculo diferencial.

---

## 🛡️ 2. O Censor de Integridade de Dados

O `GroundDataIntegrityCensor` intercepta dados externos antes da entrada na camada de aplicação:
* Valida conformidade com as `Specifications` de domínio.
* Se um sinal de satélite possuir pseudodistância fisicamente impossível ou $C/N_0$ degradado, ele é sumariamente isolado em **quarentena**.
* Impede que anomalias de sinal ou dados corrompidos contaminem o banco de dados PostGIS ou distorçam a matriz de navegação SBAS.
