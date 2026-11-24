# Retail Lakehouse Platform — Hybrid Architecture Baseline

**Version:** 1.0  
**Status:** User-approved target direction; implementation and compatibility gates remain subject to discovery and proof-of-concept validation.  
**Baseline date:** 18 November 2026

## 1. Architecture thesis

The platform has **one canonical cross-platform open lakehouse on ADLS Gen2 using Apache Iceberg v2 and Parquet**, **Microsoft Fabric as a managed analytics and collaboration lane**, and **ClickHouse Cloud as the selected warehouse and primary SQL query engine**. Power BI is the selected BI tool. The design avoids copying the entire Bronze/Silver/Gold lakehouse into OneLake or ClickHouse.

> **Canonical ownership rule:** ADLS Gen2 owns the physical source-of-truth data files and Iceberg table metadata for cross-platform Bronze, Silver, and Gold. OneLake exposes compatible Iceberg data through a tested Shortcut/metadata-virtualization access path; it is not a second canonical owner. ClickHouse Cloud reads selected Gold Iceberg data directly when compatibility is proven and stores only deliberately selected, benchmark-justified serving copies.

This is a target POC architecture, not a claim of production readiness, HA, SLA, or universal connector compatibility.

## 2. Business and source scope

The platform integrates a retail operational domain, review documents, historical Olist datasets, and synthetic digital-channel events.

### Operational relational source

The target operational relational design consolidates entities formerly spread across SQL Server and PostgreSQL into **one SQL Server database** with separate business schemas:

- `sales` — orders, order items, payments, and related transaction entities.
- `crm` — customer and customer-profile entities.
- `catalog` — products, sellers/stores, categories, inventory/reference entities as confirmed by discovery.
- `marketing` — marketing leads, acquisition, and closed-deal entities where present.

This is a target mapping, not permission to migrate data now. Discover actual schemas, PK/FK relationships, source ownership, duplicate keys, null semantics, and version support first. Preserve the original databases and source identifiers until a migration plan is approved and reconciliation passes. The final database name and exact table allocation remain discovery outputs unless separately approved.

### MongoDB review documents

The intended review CSV/XLSX input will be transformed into nested MongoDB BSON documents. Treat this as semi-structured document data with possible unstructured free-text fields. Preserve source file, source row/key, ingestion metadata, and the actual nested shape. Profile key uniqueness first; do not assume a review ID is unique. Do not convert or load during Discovery.

### File-based historical inputs

Olist historical CSV inputs are batch sources. Geolocation and product-category translation files remain file-based reference inputs unless a later decision changes that. Preserve original files; profile their exact current versions before loading. Do not infer row counts or uniqueness from older profiling snapshots.

### Python Retail Simulator

The Python simulator produces synthetic business events using versioned contracts and stable event IDs. Do not create or publish events during Discovery. Event types and schemas must be finalized before a producer/consumer implementation phase.

## 3. Logical platform lanes

### 3.1 Canonical open lakehouse lane

- **Physical storage:** ADLS Gen2.
- **File format:** Parquet.
- **Table format:** Apache Iceberg v2.
- **Catalog:** Apache Polaris is the proposed open REST catalog; connector, authentication, and commit compatibility must be proven before adoption.
- **Layers:** Bronze, Silver, Gold.
- **Batch compute:** PySpark is the intended batch ingestion and canonical Silver/Gold transformation engine.
- **Canonical writers:** assign exactly one writer to each target Iceberg table. Do not let multiple engines commit to the same table concurrently in the MVP.

Bronze preserves source-aligned records and ingestion context. Silver standardizes, deduplicates, applies deletes/updates, validates, and conforms entities. Gold contains documented business facts, dimensions, and approved aggregates. Exact table inventory and fact grains are finalized after source discovery.

### 3.2 Microsoft Fabric managed analytics lane

Fabric is a core complementary lane for managed analytics, team collaboration, and Fabric-native workloads. The selected capabilities are:

- Fabric Lakehouse / OneLake.
- Fabric Spark / PySpark notebooks.
- Fabric Data Factory pipelines for Fabric-managed notebook and data workflows.
- Fabric Eventstream for an explicitly assigned real-time ingestion path.
- SQL Analytics Endpoint for supported, read-optimized SQL access to Fabric Lakehouse tables.
- Power BI for BI consumption.

**OneLake interoperability:** a OneLake Shortcut plus Iceberg metadata virtualization is the intended access path to compatible ADLS Iceberg tables. It is a read/access path in this architecture. Do not write to canonical Iceberg tables through the Shortcut. Validate representative schemas, Iceberg v2 behavior, partitions, deletes, metadata refresh, identity, tenant settings, and region before claiming compatibility. If the required table shape is unsupported, document a bounded fallback instead of duplicating every table.

**Fabric-native Delta:** Eventstream or Fabric Spark may create Fabric-native Delta outputs for an explicitly owned Fabric workflow. These are not automatically part of canonical Gold and must have purpose, ownership, lineage, refresh/retention, reconciliation, and rebuild rules. Never mix Fabric sample/test records into business Gold facts.

**Test evidence boundary:** historical evidence records a small successful Fabric Lakehouse, PySpark notebook, Data Factory notebook pipeline, Eventstream sample, SQL Analytics Endpoint, and Python-to-Event-Hubs-protocol-to-Eventstream event path. This proves only the tested small scenarios. It does not prove Mirroring, Kafka protocol on the Fabric custom endpoint, large-scale performance, or Iceberg Shortcut compatibility.

### 3.3 Streaming and CDC boundaries

- Fabric Eventstream through the **Event Hubs protocol** is the tested Fabric-native event route. Kafka protocol connectivity through the Fabric custom endpoint remains unverified.
- Fabric Mirroring is a candidate for SQL Server CDC, not a proven project implementation. Tenant/admin prerequisites, source versions, supported table features, latency, and recovery must be checked.
- Kafka remains a candidate/open-source event backbone for independent fan-out and replay when a concrete use case requires it. Do not assume Kafka protocol works against the Fabric custom endpoint.
- Flink is deferred. Do not deploy it by default. The open-source stream processor/CDC engine and the method of committing stream output to Iceberg remain explicit design gates to be resolved by evidence and approval.
- For MongoDB review documents, the initial file-to-BSON load and any future incremental capture are separate decisions; do not assume MongoDB CDC is included in the first implementation slice.

### 3.4 Warehouse, query, and BI lane

- **Deployment target:** ClickHouse Cloud. Do not default to self-hosted ClickHouse Open Source or a local ClickHouse Docker service.
- **Primary query/warehouse engine:** ClickHouse Cloud. Fabric Warehouse and Trino are excluded from the MVP.
- **Default read pattern:** ClickHouse Cloud directly queries selected Gold Iceberg tables in ADLS if its current Cloud feature set, Azure access method, credentials, network path, and table format support the required pattern.
- **Conditional serving pattern:** materialize selected tables/aggregates into ClickHouse Cloud MergeTree only when a repeatable benchmark demonstrates business/performance value that justifies storage, refresh, and operational cost.
- **dbt:** dbt Core with `dbt-clickhouse` is optional for later ClickHouse-native marts/tests/documentation. PySpark owns canonical Iceberg Bronze/Silver/Gold transforms. dbt must not be a second writer to canonical Iceberg tables. Add dbt only after an approved need and phase.
- **BI:** Power BI is the selected BI tool. Validate ClickHouse Cloud connectivity/authentication, Fabric sharing requirements, licensing, and the intended semantic model. Do not imply that choosing Power BI selects Fabric Warehouse.

ClickHouse Cloud organization/service details remain unselected: cloud provider/region, service tier/size, trial/subscription, authentication, network configuration, budget, and direct Iceberg access method. Discovery must document them; POCs must validate them. No service creation or activation without explicit approval.

## 4. Orchestration and governance

- Fabric Data Factory owns Fabric-managed scheduled/notebook workflows.
- Airflow is deferred for open-source finite workflows until there is an approved workflow ownership gap that Fabric Data Factory does not address.
- Flink runtime ownership remains deferred with Flink itself.
- DataHub is deferred until metadata/lineage requirements justify its operating overhead. It is not an access-control enforcement layer.
- Avoid duplicate DAGs/orchestrators for the same workflow. Every workflow must have one declared owner.

## 5. Current technology disposition

| Component | Disposition | Boundary |
|---|---|---|
| ADLS Gen2 | Selected canonical storage | Physical source of truth for cross-platform Iceberg layers |
| Apache Iceberg v2 + Parquet | Selected target format | Compatibility and commit behavior must be tested |
| Apache Polaris | Proposed catalog | Adoption depends on connector/auth compatibility |
| Microsoft Fabric / OneLake | Selected managed lane | Not a duplicate canonical lakehouse |
| Fabric Lakehouse / Spark | Selected | Use for approved Fabric workloads |
| Fabric Data Factory | Selected | Fabric-managed orchestration |
| Fabric Eventstream | Selected for Fabric-native stream path | Event Hubs protocol tested; Kafka protocol not proven |
| Fabric Mirroring | Candidate | Not yet verified for project source/tenant |
| ClickHouse Cloud | Selected warehouse/query target | Cloud service details and Iceberg access are gates |
| Power BI | Selected BI | Connection path/licensing validation remains |
| dbt Core / dbt-clickhouse | Optional later | ClickHouse marts only, not canonical Iceberg writer |
| Kafka | Candidate open event backbone | Use only with approved stream/replay requirement |
| Flink | Deferred | Do not deploy by default |
| Airflow | Deferred | Add only for a justified open workflow gap |
| DataHub | Deferred | Add only when governance need justifies it |
| Fabric Warehouse | Excluded from MVP | ClickHouse is the selected warehouse/query engine |
| Trino | Excluded from MVP | Avoid second general-purpose SQL query engine |
| Self-hosted ClickHouse OSS | Not the target deployment | ClickHouse Cloud is selected |

## 6. Compatibility gates before production-like implementation

1. **ADLS ↔ OneLake:** validate Shortcut/metadata virtualization using a representative Iceberg v2 table and the real target schema; test partitions, deletes, refresh, tenant settings, identity, and region.
2. **ADLS/Iceberg ↔ ClickHouse Cloud:** validate current ClickHouse Cloud direct Iceberg-read support, Azure access/auth, network restrictions, table/catalog mode, and query limitations. Do not infer this from Blob ingestion or ClickPipes support.
3. **SQL Server CDC:** validate Fabric Mirroring prerequisites and source table support. If unsuitable, compare approved alternatives; do not install Flink/Debezium without a separate decision.
4. **Application event route:** preserve the proven Event Hubs protocol route as Fabric-native path. Validate Kafka separately for an open-source path; choose and test a stream processor before writing to canonical Iceberg.
5. **Power BI:** validate connector, credential flow, semantic model, refresh, and licensing against the selected serving path.
6. **ClickHouse Cloud cost and region:** establish the service/compute/storage/egress assumptions before provisioning.
7. **Fabric trial continuity:** verify live capacity and exact expiry; export reproducible code/configuration before trial end.

## 7. Cost and portability principles

- No Azure, Fabric, or ClickHouse Cloud resource may be created, upgraded, resumed, resized, or left running at cost without explicit user approval.
- Record owner, purpose, region, SKU/tier, size, storage, expected runtime, egress, retention, monitoring, shutdown/deallocation, and deletion/recovery path for each cloud resource.
- Keep source code, PySpark notebooks, SQL, event contracts, pipeline definitions/configuration, tests, and runbooks in Git in reproducible form. Do not commit secrets, transient outputs, or real customer data.
- Treat Fabric as a managed lane with trial/tenant constraints; the open lakehouse path must remain understandable and portable.

## 8. First recommended vertical slice (subject to Discovery)

Start with a bounded relational batch slice after source discovery: selected SQL Server order/order-item entities and selected catalog/product data → canonical Iceberg Bronze → Silver → Gold → ClickHouse Cloud query → Power BI consumption. Exact source objects, ingestion mechanism, and acceptance thresholds must be approved after schema profiling. Do not start this slice during Discovery.
