# ADR-002 — ClickHouse Cloud as the Selected Warehouse and Query Engine

- **Status:** Accepted
- **Decision date:** 18 November 2026
- **Owners:** Project owner / platform team

## Context
The earlier design selected ClickHouse as the only query engine but did not explicitly settle the deployment mode. The user has now selected ClickHouse Cloud rather than self-hosted ClickHouse Open Source.

## Decision
ClickHouse Cloud is the target deployment for the platform's selected warehouse and primary SQL query engine. Self-hosted ClickHouse Open Source is not the target implementation and must not be added as a local Docker service by default.

Direct reads from selected Gold Iceberg tables in ADLS are the preferred first consumption mode only after validating current ClickHouse Cloud product support, Azure authentication/network access, catalog/path mode, and table feature compatibility.

MergeTree materialization is selective and conditional on repeatable benchmark evidence showing that performance, concurrency, or workload isolation justifies the added storage, refresh, reconciliation, and operating cost.

## Consequences
- ClickHouse Cloud region, tier/size, compute behavior, authentication, network access, subscription/trial, cost limits, and operational controls must be discovered and approved before service creation.
- Do not confuse Azure Blob ingestion/ClickPipes with direct querying of Iceberg tables; test them as different integration patterns.
- Do not claim direct Iceberg reads until a real representative table query succeeds and is reconciled.
- Fabric Warehouse and Trino remain excluded from the MVP; no second general-purpose SQL engine is introduced.

## Open gates
The deployment target is selected; Cloud service configuration and ADLS/Iceberg compatibility remain unverified until a controlled POC is approved and performed.
