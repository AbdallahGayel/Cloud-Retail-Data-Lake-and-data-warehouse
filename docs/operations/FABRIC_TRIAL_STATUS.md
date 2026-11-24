# Microsoft Fabric Workspace & Trial Continuity Register

**Status:** VERIFIED IN LIVE POC ENVIRONMENT  
**Last observed in Fabric UI / REST API:** 2026-11-24  
**Workspace / Lakehouse:** `dev_env` / `Retail_Analytics_Lakehouse`

## Observed Live Environment State

| Field | Value | Evidence |
|---|---|---|
| Verified at (date) | `2026-11-24` | Fabric Pipeline UI & SQL Analytics Endpoint runs |
| Active Workspace | `dev_env` | Verified via pipeline authoring & notebook execution |
| Primary Lakehouse | `Retail_Analytics_Lakehouse` | ADLS Gen2 OneLake Shortcut + Delta Silver tables |
| Data Pipeline | `PL_SQLServer_To_ADLS_Bronze_Metadata_Load` | Executed Bronze load for 10 SQL tables + MongoDB `order_reviews` |
| Trial Days Remaining (UI Banner) | `54 days left` (observed 2026-11-24 in Fabric UI) | Historical POC capacity SKU/region: `FTL4` / `UAE North` (2026-11-11) |
| Export Readiness | Synced to Git | Pipeline template (`pipelines/`), Silver notebooks (`notebooks/silver/`), SQL & TLS scripts promoted |

## Historical Evidence (11 November 2026 Baseline)

- Earlier POC workspace: `Retail-Lakehouse-POC` (`FTL4` / `UAE North`).
- Fabric Lakehouse, PySpark Notebook, Data Factory activity, Eventstream sample, and SQL Analytics Endpoint were demonstrated.
- Python producer -> Fabric Event Hubs protocol endpoint -> Eventstream tested with two 10-event batches (`20` test rows); Kafka + SAS protocol selection on the custom endpoint remained unverified.

## Continuity & Export Checklist

- [x] Export Fabric Silver PySpark notebooks to Git (`notebooks/silver/`).
- [x] Preserve SQL ingestion scripts (`sql/ingestion/01_create_and_load_marketing_funnel.sql`) and TLS setup script (`scripts/setup_mongodb_tls.ps1`).
- [x] Export sanitized Fabric Data Pipeline template (`pipelines/PL_SQLServer_To_ADLS_Bronze_Metadata_Load.template.json`) with connection placeholders.
- [x] Confirm ADLS Gen2 (`retail-lakehouse`) acts as canonical physical storage independent of Fabric trial lifecycle.
- [ ] Complete `NB_Silver_Order_Payments.ipynb` upgrade (11/11 Silver table) and run full end-to-end Silver reconciliation.
- [ ] Build Gold Star Schema layer and run ClickHouse Cloud direct Iceberg vs MergeTree benchmarks.
- [ ] Preserve Eventstream design and validate Kafka vs Event Hubs protocol paths if streaming resumes.
- [ ] Confirm ClickHouse Cloud and Power BI connectivity paths cleanly decouple from Fabric trial expiry.
