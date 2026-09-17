# ⚡ Estratégia de Armazenamento NoCOW para Bancos de Dados (BTRFS)

Análise técnica, justificativa de engenharia e guia operacional para a instância nativa de banco de dados relacional e espacial **PostgreSQL 18 + PostGIS 3.6** no subvolume BTRFS dedicado com **NoCOW (No Copy-on-Write)** em `/srv/memory/db`.

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

## 🏛️ 2. Boas Práticas de DBA: Separação em Subvolume Dedicado no `fstab`

Em ambientes de produção e missões de engenharia aeroespacial, a separação do armazenamento de bancos de dados em **subvolumes dedicados** é um padrão estabelecido de confiabilidade:

1. **Isolamento de Contenção de I/O:** Evita que processos concorrentes do sistema operacional disputem o barramento de I/O com a ingestão contínua de telemetria dos satélites.
2. **Imunidade contra Esgotamento de Disco (ENOSPC):** O crescimento de dados de telemetria não afeta a partição raiz (`/`) do sistema operacional.
3. **Isolamento de Snapshots do SO:** Snapshots automáticos da raiz do sistema operacional (via Snapper ou Timeshift) não congelam os arquivos de banco de dados ativos, evitando consistência corrompida e explosão de espaço consumido.
4. **Resiliência Própria:** O PostgreSQL já implementa seus próprios checksums de páginas de dados e registro atômico no WAL (Write-Ahead Logging). A desativação de checksums do BTRFS decorrente do NoCOW é completamente segura.

---

## 🛠️ 3. Implementação Concreta no RPS-BR Ground

O banco de dados do projeto está alocado no subvolume dedicado mapeado no `/etc/fstab`:

```text
UUID=0f3dd4e2-9f43-4aef-900c-24058fc8d61f  /srv/memory/db  btrfs  rw,noatime,nodatacow,ssd,space_cache=v2,discard=async,subvol=/@db  0 0
```

### 📁 Estrutura de Diretórios
```text
/srv/memory/db/
├── matrix/                     # Outros serviços existentes (conduit, bridges)
└── rps_ground/                 # [Subdiretório de Domínio do RPS-BR Ground]
    └── postgresql/             # [Motor Primário: Relacional & Espacial]
        ├── data/               # Cluster de dados PostgreSQL (PG_DATA)
        │   ├── base/
        │   ├── global/
        │   ├── pg_wal/         # Write-Ahead Logs
        │   └── postgresql.conf # Configurações otimizadas (sockets /tmp e /run/user/1000)
        └── logs/               # Isolamento de logs de execução do motor
            └── postgres.log
```

> [!TIP]
> **Padrão de Persistência Poliglota:** A convenção `/srv/memory/db/<projeto>/<motor>/data/` confina todo o footprint do sistema em uma raiz unívoca. Caso motores complementares sejam adicionados (ex: Redis para caching em memória de barreiras temporais IEEE 1516 ou DuckDB para processamento analítico de arquivos RINEX), cada tecnologia habitará seu próprio espaço hermético (`/srv/memory/db/rps_ground/redis/data/`, etc.).

### 🛰️ Parâmetros de Conexão
* **Host:** `127.0.0.1` (TCP) ou `/tmp`, `/run/user/1000` (Unix Domain Socket)
* **Porta:** `5432`
* **Banco de Dados:** `rps_ground`
* **Usuário:** `rjgamito` (Superuser local)
* **Extensões Espaciais Ativas:** `postgis` (v3.6.4), `postgis_topology` (v3.6.4)
* **SRID Padrão:** `4326` (WGS84 / SIRGAS2000)

---

## 📜 4. Comandos de Inicialização e Operação (Instruções Repassadas)

### A. Criação e Inicialização do Cluster
Comandos executados para provisionar a base com NoCOW herdado:

```bash
# 1. Criação do diretório dedicado no subvolume NoCOW
mkdir -p /srv/memory/db/rps_ground/postgresql/{data,logs}

# 2. Inicialização do cluster nativo com locale C.UTF-8 e autenticação local confiável
initdb -D /srv/memory/db/rps_ground/postgresql/data --locale=C.UTF-8 -E UTF8 --auth-local=trust --auth-host=trust

# 3. Ajuste de portas e sockets no postgresql.conf
cat << 'EOF' >> /srv/memory/db/rps_ground/postgresql/data/postgresql.conf
listen_addresses = '127.0.0.1,localhost'
port = 5432
unix_socket_directories = '/tmp, /run/user/1000'
shared_buffers = 256MB
work_mem = 16MB
maintenance_work_mem = 64MB
EOF

# 4. Inicialização inicial
pg_ctl -D /srv/memory/db/rps_ground/postgresql/data -l /srv/memory/db/rps_ground/postgresql/logs/postgres.log start

# 5. Criação do banco de dados e extensões espaciais
createdb -h 127.0.0.1 -p 5432 -U rjgamito rps_ground
psql -h 127.0.0.1 -p 5432 -U rjgamito -d rps_ground -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;"
```

### B. Gerenciamento via Systemd do Usuário (`systemd --user`)
Para evitar a necessidade de `sudo` e manter o serviço integrado à sessão do usuário, foi criada a unit `~/.config/systemd/user/rps-ground-postgres.service`:

```ini
[Unit]
Description=PostgreSQL PostGIS Service for RPS-BR Ground Segment (NoCOW /srv/memory/db)
Documentation=https://github.com/Rj-mwe/brazilian-rps-ground
After=network.target

[Service]
Type=forking
ExecStart=/usr/bin/pg_ctl -D /srv/memory/db/rps_ground/postgresql/data -l /srv/memory/db/rps_ground/postgresql/logs/postgres.log start
ExecStop=/usr/bin/pg_ctl -D /srv/memory/db/rps_ground/postgresql/data -m fast stop
ExecReload=/usr/bin/pg_ctl -D /srv/memory/db/rps_ground/postgresql/data reload
PIDFile=/srv/memory/db/rps_ground/postgresql/data/postmaster.pid
TimeoutSec=120
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Comandos de controle do serviço:
```bash
# Iniciar o serviço
systemctl --user start rps-ground-postgres.service

# Verificar status
systemctl --user status rps-ground-postgres.service

# Parar o serviço
systemctl --user stop rps-ground-postgres.service

# Reiniciar
systemctl --user restart rps-ground-postgres.service

# Acesso interativo via psql
psql -d rps_ground
```

---

## 📊 5. Resultados de Benchmarking no Subvolume NoCOW

Testes executados com o benchmark `assurance/evals/benchmarks/eval_postgis_ingestion_bench.py`:

* **Serialização Geométrica WKT em Memória:** ~38.421 registros/segundo
* **Inserção em Lote no PostGIS Vivo (NVMe NoCOW):** **~5.549 registros espaciais/segundo**
* **Conformidade dos Testes de Integração:** 100% dos testes espaciais aprovados (`ST_Contains`, `ST_DWithin` com casting geodésico e `ST_MakeEnvelope`).
