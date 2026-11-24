# Naming Conventions

**Status:** Baseline conventions; actual source names must be discovered and preserved in lineage mappings.

## General
- Prefer lowercase `snake_case` for new database schemas, analytical tables, columns, Python modules, and file names unless a platform has a stronger native convention.
- Use clear business names; avoid unexplained abbreviations and reserved words.
- Do not rename existing source columns/tables during Discovery. Map source names to curated names explicitly.
- Keep names stable; schema changes require compatibility and migration review.

## SQL Server operational target
Approved business schema names:
- `sales`
- `crm`
- `catalog`
- `marketing`

The final database name and exact object allocation are not yet fixed by this standard. Discover source objects and relationships first. Preserve source PKs/identifiers and document any renamed target columns.

## Lakehouse
- Layer names: `bronze`, `silver`, `gold`.
- Use one catalog/database namespace per layer or another convention only after a documented decision.
- Source-aligned Bronze names should identify source system/object/pattern where needed, e.g. `bronze.sqlserver_orders_cdc` or `bronze.olist_orders_batch`.
- Silver names should represent conformed business entities, e.g. `silver.orders`, `silver.products`.
- Gold facts use `fact_` prefix; dimensions use `dim_` prefix, e.g. `gold.fact_order_item`, `gold.dim_customer`.
- Document each fact grain in the model specification and table metadata.

## ClickHouse Cloud
- Separate serving objects by database/schema purpose where supported and agreed.
- Use `mart_` or clearly named business marts only for ClickHouse-native serving models. Avoid implying every Gold table is copied.
- Use MergeTree only for approved materializations; table names must reflect business purpose and refresh grain.

## Fabric items
- Keep concise, consistent type prefixes where practical: `lh_` for Lakehouse, `nb_` for Notebook, `pl_` for Pipeline, `es_` for Eventstream, and `ws_` for Workspace documentation references.
- Preserve existing tested artifact names. Do not recreate or rename Fabric items during Discovery.

## Git branches
- `main` — stable baseline.
- `feature/<short-kebab-name>` — feature or implementation work.
- `fix/<short-kebab-name>` — defect fixes.
- `docs/<short-kebab-name>` — documentation-only work.
- Never switch/delete/rename the user's active branch without approval.

## Tests and events
- Test files should state the subject and scenario, e.g. `test_order_item_deduplication.py`.
- Event contracts require stable `event_id`, `event_type`, `event_schema_version`, `event_time`, producer, and business key where applicable.
