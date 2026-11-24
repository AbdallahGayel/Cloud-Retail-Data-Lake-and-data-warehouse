# Retail Lakehouse — Reference Pack Index

This folder preserves the architecture reference baseline alongside the reconciled project documentation.

## Reference documents

1. `Retail_Lakehouse_Hybrid_Blueprint_v2.docx` — Hybrid architecture baseline, version 2.0, dated 12 November 2026.
2. `LEGACY_README_2026-11-07.md` — Preserved copy of the original 7 November 2026 open-source-only planning `README.md`, superseded by the hybrid architecture baseline and reconciled root `README.md`.

## How to interpret these documents

The Hybrid Blueprint v2.0 and `docs/architecture/ARCHITECTURE_BASELINE.md` define the core architectural boundaries:

- **ADLS Gen2** is the canonical physical object store for Bronze, Silver, and Gold open-table layers (Parquet / Apache Iceberg v2 target).
- **Microsoft Fabric / OneLake** is the managed analytics lane. OneLake shortcuts to ADLS Gen2 provide the verified read/access path from Fabric Spark without mirroring the full medallion lakehouse into OneLake.
- **ClickHouse Cloud** is the selected warehouse and primary SQL query engine. Direct Iceberg reads are the default; selective MergeTree materialization requires benchmark evidence.
- **Fabric Eventstream** through the Event Hubs protocol was tested historically; Kafka protocol compatibility on the Fabric custom endpoint remains unverified.
- **Fabric Warehouse** and **Trino** are excluded from the MVP.
- **SQL Server (`Cloud_Retail_Data_Lakehouse_v2`)** consolidates the relational tables (`customers`, `orders`, `order_items`, `order_payments`, `products`, `sellers`, `product_category_name_translation`, `dim_geolocation`, `marketing_qualified_leads`, `closed_deals`), while **MongoDB 8.3** stores `retail_reviews.order_reviews` as nested BSON documents with source lineage.
- **Flink, Airflow, and DataHub** remain deferred until a concrete operational need justifies their addition.
- **Fabric Mirroring** remains a candidate for SQL Server CDC rather than a verified production pattern.

## Conflict-resolution rule

Where documents disagree, follow `docs/architecture/DECISION_PRECEDENCE.md`. Never silently blend contradictory claims or upgrade a `compatibility gate`, `candidate`, `optional`, or `deferred` component without reproducible evidence.
