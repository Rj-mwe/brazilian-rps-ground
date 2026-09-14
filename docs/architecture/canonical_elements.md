# 🏛️ Os 12 Elementos Canônicos do Hexágono Dourado

Tanto o **Core** quanto os **Adaptadores Fractais Nível 3** decompõem-se estritamente em **12 Elementos Canônicos**:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                 OS 12 ELEMENTOS CANÔNICOS DO HEXÁGONO DOURADO               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CAMADA DE APLICAÇÃO (4 Elementos Canônicos):                               │
│  ├── 1. Application Services: Orquestração de casos de uso de missão        │
│  ├── 2. Data Transfer Objects (DTOs): Contratos imutáveis de transferência  │
│  ├── 3. Mappers: Tradutores puros bidirecionais (DTO <-> Domínio)           │
│  └── 4. Interfaces: Contratos abstratos (driving e driven)                  │
│                                                                             │
│  CAMADA DE DOMÍNIO (8 Elementos Táticos DDD - 100% Puros):                  │
│  ├── 5. Aggregates: Raiz de consistência e invariantes transacionais        │
│  ├── 6. Entities: Objetos com identidade unívoca e ciclo de vida            │
│  ├── 7. Value Objects (VOs): Imutabilidade (@dataclass(frozen=True))        │
│  ├── 8. Domain Services: Cálculos matemáticos e geodésicos sem estado       │
│  ├── 9. Specifications: Predicados booleanos isolados para regras           │
│  ├── 10. Policies: Estratégias de decisão e contingência dinâmica          │
│  ├── 11. Domain Events: Notificações de eventos e anomalias locais          │
│  └── 12. Factories: Construtores seguros de agregados e redes complexas     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Mapeamento Concreto no RPS-BR Ground

| Elemento | Papel no Sistema | Exemplos Implementados no Projeto |
| :--- | :--- | :--- |
| **1. Application Services** | Coordena o fluxo de execução dos casos de uso de solo. | `IngestStationCoverageUseCase`, `RecordVehicleTrajectoryUseCase`, `LogConstellationSignalUseCase` |
| **2. DTOs** | Estruturas tipadas imutáveis para transferência de dados. | `GroundStationDTO`, `VehicleTrackDTO`, `RoadSegmentDTO`, `SignalReceptionDTO` |
| **3. Mappers** | Conversores estritos entre borda e domínio. | `GroundSpatialMapper` |
| **4. Interfaces** | Contratos de portas desacoplados (substitui pasta `ports/`). | `IGroundStationStorageInterface`, `ITrajectoryStorageInterface`, `ISpatialStorageInterface` |
| **5. Aggregates** | Raiz transacional de consistência. | `GroundStationNetworkAggregate`, `VehicleTrackingSessionAggregate` |
| **6. Entities** | Entidades com identidade que perdura no tempo. | `GroundStationEntity`, `RoadSegmentEntity`, `VehicleEntity` |
| **7. Value Objects** | Valores imutáveis com validação em `__post_init__`. | `GeodeticCoordinatesVO`, `BoundingBoxVO`, `VehicleTrackPointVO`, `CoveragePolygonVO`, `ConstellationSignalLogVO`, `SignalQualityVO` |
| **8. Domain Services** | Lógica de cálculo geodésico sem acoplamento a ORM. | `GeodeticDistanceCalculator`, `RoadMatchingService` |
| **9. Specifications** | Predicados reutilizáveis para validações de negócio. | `ElevationMaskSatisfiedSpecification`, `WithinStationCoverageSpecification`, `SignalIntegrityValidSpecification`, `SpeedLimitSpecification` |
| **10. Policies** | Regras de tolerância e contingência operacional. | `RimsCoverageRedundancyPolicy` (mínimo $N$ estações para integridade), `TrajectoryDecimationPolicy` |
| **11. Domain Events** | Disparo de notificações de eventos críticos. | `StationCoverageDegradedEvent`, `VehicleEnteredRegionalZoneEvent`, `LossOfSignalDetectedEvent` |
| **12. Factories** | Construtores seguros de topologias complexas. | `GroundStationFactory` (as 5 estações e anéis de pegada), `RoadNetworkFactory` (BR-116 Dutra e SP-099 Tamoios) |
