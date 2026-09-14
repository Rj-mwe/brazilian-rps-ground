# ⚡ Estratégia de Armazenamento NoCOW para Bancos de Dados (BTRFS)

Análise técnica e justificativa de engenharia para o isolamento de motores de banco de dados relacionais em sistemas de arquivos BTRFS com o atributo **NoCOW (No Copy-on-Write)**.

---

## 🎯 1. O Desafio: Copy-on-Write vs. Bancos de Dados Relacionais

O sistema de arquivos BTRFS utiliza por padrão o paradigma **Copy-on-Write (CoW)**: ao modificar um bloco de arquivo existente, o BTRFS nunca sobrescreve o bloco no local original (*in-place*); ele aloca um bloco livre em outro ponto do disco, grava a nova versão e atualiza os ponteiros da árvore B-Tree.

Embora o CoW seja excelente para segurança de dados do sistema operacional e criação instantânea de snapshots, ele apresenta **severos problemas para bancos de dados como o PostgreSQL**:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                 O DILEMA DE I/O: CoW vs. BANCOS DE DADOS                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PostgreSQL:                                                                │
│  • Opera com blocos fixos de 8 KB com atualizações in-place.               │
│  • Possui mecanismo próprio de resiliência e journaling (WAL).             │
│  • Executa milhares de escritas e atualizações aleatórias concorrentes.     │
│                                                                             │
│  BTRFS com CoW Ativo (Padrão):                                              │
│  • Cada update de 8 KB gera uma nova alocação física em outro setor.        │
│  • Causa fragmentação catastrófica do arquivo de dados em poucos dias.      │
│  • Degrada drasticamente o throughput de leitura e escrita (IOPS).          │
│  • Amplifica o desgaste de células de SSD NVMe (Write Amplification).       │
│                                                                             │
│  Solução Arquitetural (NoCOW):                                              │
│  • Desativação do CoW para o diretório de banco (+C / nodatacow).           │
│  • Permite que o PostgreSQL execute escritas in-place determinísticas.      │
│  • Preserva o desempenho de IOPS em SSD NVMe com latência mínima.           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ 2. Boas Práticas de DBA: Separação em Subvolumes ou Discos Distintos

Em ambientes de produção ou de missão crítica aeroespacial, a separação do armazenamento de bancos de dados em **subvolumes, partições ou discos dedicados** é um padrão estabelecido de confiabilidade:

1. **Isolamento de Contenção de I/O:** Evita que processos intensivos do sistema operacional (atualizações de pacotes, compilações pesadas ou gravações de logs) concorram pelo mesmo barramento de I/O do banco de telemetria.
2. **Imunidade contra Esgotamento de Disco (ENOSPC):** Um banco de dados que preenche seu disco não pode derrubar a partição raiz (`/`) do sistema operacional.
3. **Isolamento de Snapshots do SO:** Ferramentas como Snapper ou Timeshift que criam snapshots automáticos da raiz do sistema operacional não devem congelar recursivamente arquivos de banco de dados ativos, evitando inconsistências transacionais e explosão de consumo de espaço em disco.
4. **Política Específica de Checksums:** O PostgreSQL já implementa seus próprios checksums de integridade de páginas de dados e registro de transações no WAL. A desativação de checksums do BTRFS decorrente do NoCOW é completamente segura para bancos de dados.

---

## 🛠️ 3. Como o NoCOW foi Estruturado no RPS-BR Ground

No sistema operacional do host (Arch Linux), identificamos duas opções:

1. **Subvolume Dedicado no `fstab` (`/srv/memory/db`):**
   * Já configurado com `nodatacow`, `noatime`, `space_cache=v2` e `discard=async`.
   * Ideal para clusters gerenciados sem necessidade de privilégios de root.
2. **Diretório Padrão do Sistema (`/var/lib/postgres`):**
   * Configurado com atributo `+C` (`sudo chattr +C /var/lib/postgres`) antes da inicialização do cluster `initdb`.
   * Mantém compatibilidade com o serviço padrão do systemd (`postgresql.service`).
