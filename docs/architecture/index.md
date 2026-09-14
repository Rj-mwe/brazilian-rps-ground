# 🏛️ Visão Geral da Arquitetura & O Hexágono Dourado

Especificação arquitetural do **Segmento de Solo do RPS-BR (`brazilian-rps-ground`)**, fundamentada no paradigma do **Hexágono Dourado** (*Clean Fractal Hexagonal Architecture*).

---

## 🎯 1. Princípios da Clean Fractal Hexagonal Architecture

O sistema de solo foi concebido sob quatro postulados invioláveis:

1. **Pureza Absoluta do Domínio:** O núcleo de domínio (`core/domain/`) desconhece bancos de dados, frameworks de rede ou bibliotecas externas. Contém apenas tipos primitivos, funções matemáticas puras e Value Objects imutáveis.
2. **Dependência Concêntrica Unidirecional:** O fluxo de acoplamento aponta sempre para o centro ($\text{Domínio} \leftarrow \text{Aplicação} \leftarrow \text{Adaptadores/Infraestrutura}$).
3. **Os 12 Elementos Canônicos:** Estrutura formal rígida composta por 4 elementos na Camada de Aplicação e 8 elementos táticos DDD na Camada de Domínio.
4. **Governança Unificada:** O **Sub-Core de Governança** é o único sub-core de aplicação, assegurando conformidade com contratos, barreiras temporais (IEEE 1516) e isolamento de integridade.

---

## 🧭 2. Topologia Concêntrica do Solo

```mermaid
graph TD
    subgraph Infra ["Camada de Infraestrutura (Substratos de Plataforma)"]
        RT["Substrato de Ambiente (RuntimeSubstrate)<br/>(NativeDriver, VirtualEnvDriver, ContainerDriver)"]
        DB["Substrato de Persistência (DatabaseSubstrate)<br/>(Pool QueuePool, Engine, SessionScope, HealthCheck)"]
        CFG["Substrato de Configuração (ConfigurationSubstrate)<br/>(Cascata 4 níveis: Defaults -> YAML -> ENV -> Overrides)"]
    end

    subgraph Adapters ["Camada de Adaptadores de Borda (Edge Adapters)"]
        PostGIS["postgis_sink (Smart Adapter Fractal Nível 3)<br/>(Schema GeoAlchemy2, Mappers WKT, Repositório)"]
        DL["downlink_client (Cliente do RPS-BR Sim)<br/>(Ingestão REST / WebSocket)"]
    end

    subgraph App ["Camada de Aplicação (core/application/)"]
        Gov["Sub-Core de Governança<br/>(GroundTemporalBarrier, GroundDataIntegrityCensor)"]
        Services["Application Services (Casos de Uso)<br/>(IngestStationCoverage, RecordTrajectory, LogSignals)"]
        DTOs["DTOs & Mappers<br/>(Contratos de Borda e Tradução)"]
        Interfaces["Interfaces (Portas Abstratas)<br/>(ISpatialStorageInterface, etc.)"]
    end

    subgraph Dom ["Camada de Domínio Puro (core/domain/)"]
        Geo["Sub-Core Geodesy<br/>(GeodeticCoordinatesVO, DistanceCalculator)"]
        Stations["Sub-Core Stations<br/>(GroundStationEntity, NetworkAggregate, RedundancyPolicy)"]
        Track["Sub-Core Tracking<br/>(VehicleTrackPointVO, RoadSegmentEntity, RoadMatching)"]
        Telem["Sub-Core Telemetry<br/>(ConstellationSignalLogVO, SignalIntegritySpec)"]
    end

    Infra --> PostGIS
    PostGIS --> Interfaces
    DL --> Services
    Services --> Interfaces
    Services --> Gov
    Services --> Dom
```
