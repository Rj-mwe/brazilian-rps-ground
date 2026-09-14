# ADR 0002: Persistência Espacial Nativa com PostgreSQL e PostGIS (US124)

* **Status:** Aceito
* **Data:** 2026-09-14
* **Decisores:** Roger J. G. Gamito (TS#2 / ITA)

## 📌 Contexto
Para cumprir o épico **US124** de Big Data espacial, o sistema precisa persistir trajetórias em alta frequência, polígonos de cobertura de estações e geometrias de malhas viárias, executando consultas espaciais de contenção (`ST_Contains`) e vizinhança (`ST_DWithin`).

## 🎯 Decisão
Adotar **PostgreSQL 18 com extensão PostGIS 3.6** utilizando o padrão de coordenadas geodésicas **SRID 4326 (WGS84 / SIRGAS2000)** e índices espaciais **GIST**:
1. Implementação como um **Smart Adapter Fractal de Nível 3** em `rps_ground/adapters/postgis_sink/`.
2. Mapeamento bidirecional seguro entre VOs puros e tipos WKT/WKB via GeoAlchemy2.
3. Suporte a inserção em lote (*bulk insert*) para alta vazão de telemetria.

## ⚖️ Consequências
* **Positivas:** Padrão ouro na indústria geoespacial, conformidade com padrões OGC, interoperabilidade com ferramentas GIS (QGIS, Leaflet, CesiumJS).
* **Desafios:** Requer motor de banco ativo com PostGIS instalado. Mitigado através de testes de integração com skip condicional quando o banco estiver inativo.
