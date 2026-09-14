# 💾 Modelo de Dados Espacial & Schema PostGIS (US124)

Especificação do modelo relacional e espacial implementado no PostgreSQL com extensão PostGIS (SRID 4326 - WGS84 / SIRGAS2000), concebido para armazenar grandes volumes de trajetórias, telemetrias de constelação e malhas viárias.

---

## 🗺️ 1. Diagram-as-Code: Diagrama Entidade-Relacionamento (ER)

```mermaid
erDiagram
    GROUND_STATIONS ||--o{ SATELLITE_SIGNAL_LOGS : "recebe_telemetria"
    
    GROUND_STATIONS {
        int id PK "Autoincrement"
        string code UK "Código canônico (SJC, ALC, NAT, BSB, CPQ)"
        string name "Nome descritivo da estação"
        string station_type "RIMS | MASTER_CONTROL | UPLINK | AEROSPACE_RESEARCH"
        float elevation_mask_deg "Máscara de corte de elevação (ex: 5.0°)"
        float coverage_radius_km "Raio de cobertura nominal (km)"
        boolean is_operational "Flag de status operacional"
        datetime created_at "Data/hora de registro"
        geometry location "POINTZ (lon, lat, alt) - GIST Index"
        geometry coverage_area "POLYGON (footprint regional) - GIST Index"
    }

    ROAD_SEGMENTS {
        int id PK "Autoincrement"
        string segment_id UK "Identificador unívoco do trecho"
        string name "Nome da via (ex: Rodovia Presidente Dutra)"
        string road_code "Código oficial (BR-116, SP-099)"
        string road_type "HIGHWAY_FEDERAL | HIGHWAY_STATE | ARTERIAL"
        float length_meters "Extensão total calculada em metros"
        geometry geom "LINESTRING (eixo geodésico da via) - GIST Index"
    }

    VEHICLE_TRACK_POINTS {
        bigint id PK "Autoincrement"
        string vehicle_id "Identificador do veículo / receptor"
        string session_id "Sessão de rastreamento de missão"
        datetime timestamp "Data/hora GPS (UTC) - Index"
        float speed_mps "Velocidade escalar instantânea (m/s)"
        float heading_deg "Azimute de rumo [0, 360]"
        float pdop "Diluição de precisão tridimensional"
        string fix_status "3D_FIX | DGPS_FIX | RTK_FIX | SBAS_FIX"
        geometry location "POINTZ (lon, lat, alt) - GIST Index"
    }

    SATELLITE_SIGNAL_LOGS {
        bigint id PK "Autoincrement"
        datetime timestamp "Data/hora da amostra (UTC) - Index"
        string station_code FK "Estação de recepção (ground_stations.code)"
        int satellite_id "Identificador do satélite (1 a 7)"
        string satellite_type "GEO | IGSO"
        float elevation_deg "Ângulo de elevação no horizonte [-90, +90]"
        float azimuth_deg "Azimute geodésico da visada [0, 360]"
        float pseudorange_m "Pseudodistância bruta observada (m)"
        float c_n0_dbhz "Densidade Portadora/Ruído (dB-Hz)"
        float doppler_hz "Desvio Doppler de frequência (Hz)"
        geometry los_geometry "LINESTRINGZ (Vetor LOS Estação-Satélite) - GIST Index"
    }
```

---

## 🏛️ 2. Índices Espaciais e Performance de Consulta

Todas as colunas geométricas utilizam **Índices Espaciais GIST (Generalized Search Tree)** baseados em R-Tree no PostGIS:

1. **`ground_stations.location` & `coverage_area`:**
   * Permite consultas de contenção espacial instantâneas:
     ```sql
     SELECT code, name FROM ground_stations
     WHERE is_operational = TRUE 
       AND ST_Contains(coverage_area, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326));
     ```
2. **`road_segments.geom`:**
   * Permite consultas de proximidade viária (Map Matching) com cálculo geodésico no esferóide em metros:
     ```sql
     SELECT road_code, name FROM road_segments
     WHERE ST_DWithin(
         geom::geography, 
         ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 
         :distance_meters
     );
     ```
3. **`vehicle_track_points.location`:**
   * Suporta filtragem por bounding box geográfico de alta velocidade:
     ```sql
     SELECT * FROM vehicle_track_points
     WHERE ST_Within(location, ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326));
     ```

---

## ⚡ 3. Atendimento aos Requisitos da US124

| Requisito US124 | Implementação no Schema | Validação |
| :--- | :--- | :--- |
| **Persistir Trajetórias** | Tabela `vehicle_track_points` com geometria `POINTZ`, timestamps indexados e métricas de qualidade (PDOP). | `ITrajectoryStorageInterface` |
| **Persistir Malhas Viárias** | Tabela `road_segments` com geometria `LINESTRING` e codificação oficial (BR-116 Dutra, SP-099 Tamoios). | `IRoadNetworkStorageInterface` |
| **Persistir Cobertura Regional** | Tabela `ground_stations` com polígonos `coverage_area` das 5 estações canônicas (SJC, ALC, NAT, BSB, CPQ). | `IGroundStationStorageInterface` |
| **Persistir Telemetria de Sinais** | Tabela `satellite_signal_logs` com integridade referencial com as estações e vetores de visada `LINESTRINGZ`. | `ISignalLogStorageInterface` |
