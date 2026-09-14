# ADR 0003: Estratégia de Armazenamento NoCOW para Motores de Banco de Dados

* **Status:** Aceito
* **Data:** 2026-09-14
* **Decisores:** Roger J. G. Gamito (TS#2 / ITA)

## 📌 Contexto
Em sistemas de arquivos modernos com Copy-on-Write (BTRFS), bancos de dados relacionais que realizam frequentes gravações aleatórias em blocos de 8 KB sofrem com fragmentação extrema, latência imprevisível de I/O e amplificação de escrita (*write amplification*).

## 🎯 Decisão
1. Adotar formalmente o atributo **NoCOW (No Copy-on-Write)** para diretórios de bancos de dados no BTRFS:
   * Aplicação do atributo `+C` (`chattr +C`) em `/var/lib/postgres` enquanto o diretório estiver vazio antes de rodar `initdb`.
   * Para desenvolvimento sem privilégios de root, utilizar o subvolume dedicado `/srv/memory/db` já montado nativamente com a opção `nodatacow` no `/etc/fstab`.
2. Não alterar o `/etc/fstab` do sistema raiz desnecessariamente, preservando a estabilidade da máquina.

## ⚖️ Consequências
* **Positivas:** Previne fragmentação severa de I/O, maximiza IOPS em SSD NVMe e protege os arquivos de banco de dados contra corrupção em snapshots do sistema operacional.
* **Desafios:** Arquivos NoCOW no BTRFS não possuem checksums de dados do filesystem; essa responsabilidade é delegada ao próprio PostgreSQL (WAL e integridade de páginas).
