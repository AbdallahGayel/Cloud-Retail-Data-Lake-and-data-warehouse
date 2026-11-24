# ADR-004 — Tool Boundaries and Transformation Ownership

- **Status:** Accepted baseline; deferred items require a new ADR/user approval before addition
- **Decision date:** 18 November 2026

## Decision

| Component | Current disposition | Boundary |
|---|---|---|
| PySpark | Selected | Batch ingestion and canonical Silver/Gold Iceberg transformation owner |
| Fabric Data Factory | Selected | Fabric-managed notebook/pipeline workflows |
| Fabric Eventstream | Selected | Fabric-native event route; tested with Event Hubs protocol |
| Kafka | Candidate open-source event backbone | Use when independent fan-out/replay is required; do not equate with Fabric custom endpoint protocol |
| Fabric Mirroring | Candidate | SQL Server CDC; verify tenant/source/table constraints before selecting |
| Flink | Deferred | No default deployment; stream/CDC engine remains a gate |
| Airflow | Deferred | Add only if an approved open-source finite-workflow gap exists beyond Fabric Data Factory |
| DataHub | Deferred | Add only when metadata/lineage needs justify operating it |
| dbt Core + dbt-clickhouse | Optional later | ClickHouse-native marts/tests/docs only, not canonical Iceberg writes |
| Fabric Warehouse | Excluded from MVP | ClickHouse Cloud is the selected warehouse/query engine |
| Trino | Excluded from MVP | Avoid introducing a second general-purpose query engine |
| Kubernetes/AKS | Out of scope for MVP | Require a separate concrete deployment need and approval |

## Transformation ownership
PySpark is the intended owner for canonical Iceberg transformations. dbt-clickhouse may later manage ClickHouse-native marts and tests. Never allow two tools to write the same canonical table without an explicit concurrency design, test evidence, and approved ADR.

## Consequences
The architecture remains intentionally lean. Discovery and bounded POCs should determine whether a deferred tool solves a specific requirement better than the selected Fabric-native or PySpark path. Tool count is not a project success metric.
