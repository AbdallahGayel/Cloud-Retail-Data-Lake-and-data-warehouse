# ADR-003 — Microsoft Fabric Scope, Fabric Warehouse Exclusion, and Power BI

- **Status:** Accepted
- **Decision date:** 18 November 2026

## Context
The old PNG contains Fabric Warehouse and several optional/deferred tools. The user-approved direction uses Fabric as a managed lane while ClickHouse Cloud is the selected warehouse/query engine.

## Decision
Microsoft Fabric is a core managed analytics and collaboration lane, using Fabric Lakehouse/OneLake, Fabric Spark/PySpark, Fabric Data Factory, Fabric Eventstream, and the SQL Analytics Endpoint where appropriate. Power BI is the selected BI tool.

Fabric Warehouse is excluded from the MVP. The Fabric SQL Analytics Endpoint is a read-optimized SQL interface for supported Lakehouse data and is not a replacement for ClickHouse Cloud.

## Consequences
- Fabric-native pipelines/notebooks and configuration should be versioned in Git in reproducible form where exportable.
- Do not duplicate all canonical Iceberg Gold data into Fabric Delta or Warehouse.
- Validate Power BI connectivity to the selected analytical serving path and required licenses.
- Keep the old image unchanged; create current diagrams from `docs/architecture/diagrams/HYBRID_TARGET_ARCHITECTURE.mmd` and review before publication.

## Evidence limits
Small Fabric Lakehouse, notebook, pipeline, Eventstream, SQL endpoint, and Event Hubs protocol demonstrations were previously recorded. They do not prove production behavior, Mirroring, Kafka protocol support, or Iceberg Shortcut compatibility.
