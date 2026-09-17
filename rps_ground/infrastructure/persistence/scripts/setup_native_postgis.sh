#!/usr/bin/env bash
# ==============================================================================
# Projeto: Brazilian RPS Ground Segment (SPR-BR / SBAS-BR)
# Script: setup_native_postgis.sh
# Descrição: Provisionamento do cluster nativo PostgreSQL 18 com PostGIS 3.6.
#            Suporta ambientes BTRFS (aplicação de NoCOW antes do initdb).
# ==============================================================================

set -euo pipefail

PG_DATA_DIR="${RPS_GROUND_DB_DATA_DIR:-/srv/memory/db/rps_ground/postgresql/data}"
PG_PORT="${RPS_GROUND_DB_PORT:-5432}"
PG_DB="${RPS_GROUND_DB_NAME:-rps_ground}"
PG_USER="${RPS_GROUND_DB_USER:-$USER}"

echo "🛰️ [RPS-BR Ground] Configuração do Cluster PostgreSQL Nativo"
echo "   Diretório de Dados: $PG_DATA_DIR"
echo "   Porta: $PG_PORT"
echo "   Banco: $PG_DB"
echo "   Usuário: $PG_USER"

# 1. Preparação do Diretório com NoCOW (para BTRFS) se aplicável
if [ ! -d "$PG_DATA_DIR" ]; then
    echo "📁 Criando diretório de dados..."
    mkdir -p "$PG_DATA_DIR"
    
    # Se o filesystem for BTRFS, desabilitar Copy-on-Write (NoCOW)
    if command -v chattr >/dev/null 2>&1; then
        echo "⚡ Aplicando flag NoCOW (chattr +C)..."
        chattr +C "$PG_DATA_DIR" 2>/dev/null || true
    fi
fi

# 2. Inicialização do Cluster (initdb) se não inicializado
if [ ! -f "$PG_DATA_DIR/PG_VERSION" ]; then
    echo "⚙️ Inicializando banco de dados com initdb..."
    initdb -D "$PG_DATA_DIR" --no-locale -E UTF8 --auth-local=trust --auth-host=trust
else
    echo "✅ Cluster já inicializado em $PG_DATA_DIR."
fi

# 3. Iniciar Servidor se inativo
if ! pg_isready -p "$PG_PORT" -h 127.0.0.1 >/dev/null 2>&1; then
    echo "🚀 Iniciando servidor PostgreSQL na porta $PG_PORT..."
    pg_ctl -D "$PG_DATA_DIR" -o "-p $PG_PORT -k /tmp" -l "$PG_DATA_DIR/postgres.log" start
    sleep 1
fi

# 4. Criar Banco de Dados se não existir
if ! psql -p "$PG_PORT" -h 127.0.0.1 -U "$PG_USER" -lqt | cut -d \| -f 1 | grep -qw "$PG_DB"; then
    echo "📦 Criando banco de dados '$PG_DB'..."
    createdb -p "$PG_PORT" -h 127.0.0.1 -U "$PG_USER" "$PG_DB"
fi

# 5. Habilitar Extensão PostGIS
echo "🗺️ Habilitando extensões PostGIS no banco '$PG_DB'..."
psql -p "$PG_PORT" -h 127.0.0.1 -U "$PG_USER" -d "$PG_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -p "$PG_PORT" -h 127.0.0.1 -U "$PG_USER" -d "$PG_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"

echo "✅ [RPS-BR Ground] PostgreSQL + PostGIS nativo configurado com sucesso!"
psql -p "$PG_PORT" -h 127.0.0.1 -U "$PG_USER" -d "$PG_DB" -c "SELECT PostGIS_Full_Version();"
