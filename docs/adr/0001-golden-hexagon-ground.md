# ADR 0001: Adoção do Hexágono Dourado no Segmento de Solo

* **Status:** Aceito
* **Data:** 2026-09-14
* **Decisores:** Roger J. G. Gamito (TS#2 / ITA)

## 📌 Contexto
O segmento terrestre do SPR-BR/SBAS-BR exige alta integridade, desacoplamento de frameworks e conformidade com normas aeroespaciais (DO-178C e DO-229D). O modelo hexagonal clássico (Cockburn 2005) é insuficiente por não estruturar internamente o core e não possuir regulação temporal.

## 🎯 Decisão
Adotar a **Clean Fractal Hexagonal Architecture (Hexágono Dourado)**:
1. Estruturação rígida em **12 Elementos Canônicos** (4 em Application e 8 em Domain).
2. O **Sub-Core de Governança** é o único sub-core de aplicação, responsável por barreiras temporais (IEEE 1516) e censura de integridade.
3. Substituição do diretório `ports/` por `interfaces/` dentro de `core/application/`.

## ⚖️ Consequências
* **Positivas:** Isolamento hermético do domínio puro, testabilidade de 100% dos modelos matemáticos sem banco ou rede, simetria com o simulador espacial `brazilian-rps-sim`.
* **Desafios:** Exige disciplina para manter Value Objects imutáveis e zero importações de infraestrutura. Mitigado via Linters AST automáticos em `assurance/audits/`.
