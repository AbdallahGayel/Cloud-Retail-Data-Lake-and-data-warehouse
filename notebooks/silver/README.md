# Silver Layer PySpark Notebooks (`notebooks/silver/`)

This directory contains the 11 Bronze-to-Silver PySpark transformation notebooks executed inside Microsoft Fabric Spark (`Retail_Analytics_Lakehouse`), reading raw Bronze data via OneLake Shortcuts to ADLS Gen2 (`retail-lakehouse/bronze/`) and writing curated, ACID-compliant Delta Lake tables (`silver.*`).

> **Governance note:** `NB_Silver_Sellers.ipynb` is the canonical Seller transformation. An experimental geolocation-joined variant is intentionally excluded to avoid duplicate Seller pipelines.

## Inventory & Verification Matrix

| # | Notebook | Source System | Target Table | Input Rows | Output / Curated Rows | Key Quality & Transformation Rules | Status |
|---|---|---|---|---:|---:|---|---|
| 1 | `NB_Silver_Dim_Geolocation.ipynb` | SQL Server (`dbo.dim_geolocation`) | `silver.geolocation_zip_reference` + `_quarantine_dim_geolocation` | 1,000,163 | 19,015 (+29 quarantined) | Brazil bounding-box filter, ZIP normalization, deterministic coordinate centroid aggregation | Verified (Fabric) |
| 2 | `NB_Silver_Sellers.ipynb` | SQL Server (`dbo.sellers`) | `silver.sellers` | 3,095 | 3,095 | Clean city/state normalization, ZIP prefix validation, geolocation enrichment lookup | Verified (Fabric) |
| 3 | `NB_Silver_Customers.ipynb` | SQL Server (`dbo.customers`) | `silver.customers` | 99,441 | 99,441 | Preserves order-level `customer_id` PK & `customer_unique_id` (96,096 distinct buyers) | Verified (Fabric Dry Run) |
| 4 | `NB_Silver_Orders.ipynb` | SQL Server (`dbo.orders`) | `silver.orders` | 99,441 | 99,441 | Preserves native `TIMESTAMP` (fixes string downgrades & `lpad(5)` bug), adds `silver.customers` FK check & chronology/SLA flags (`23` `delivered < carrier`, `7,827` late) | Ready |
| 5 | `NB_Silver_Order_Items.ipynb` | SQL Server (`dbo.order_items`) | `silver.order_items` | 112,650 | 112,650 | Explicit `DECIMAL(12,2)`, computes `line_total_amount`, flags `is_free_shipping` (`383`) & `shipping_limit_outlier_flag` (`4` 2020 rows) | Verified (Fabric Dry Run) |
| 6 | `NB_Silver_Products.ipynb` | SQL Server (`dbo.products`) | `silver.products` | 32,951 | 32,951 | Preserves `NULL` categories (`610` rows) + `is_missing_category`, nulls `4` zero-weight + `2` null-dim outliers (`is_zero_or_null_dimensions`), `DECIMAL(12,2)` | Verified (Fabric SQL Endpoint) |
| 7 | `NB_Silver_Product_Category_Translation.ipynb` | SQL Server (`dbo.product_category_name_translation`) | `silver.product_category_name_translation` | 71 | 71 | Trims keys, documents Olist `home_confort` spelling & `2` unmapped categories relative to `silver.products` (`73` vs `71`) | Ready |
| 8 | `NB_Silver_Marketing_Qualified_Leads.ipynb` | SQL Server (`dbo.marketing_qualified_leads`) | `silver.marketing_qualified_leads` | 8,000 | 8,000 | Typed `first_contact_date`, normalizes `origin` (`1,159` unknown/null preserved explicitly) | Verified (Fabric) |
| 9 | `NB_Silver_Closed_Deals.ipynb` | SQL Server (`dbo.closed_deals`) | `silver.closed_deals` | 842 | 842 | Preserves active/inactive seller flags (`380` in `sellers` / `462` onboarding), flags `1` `won_date < first_contact_date` | Verified (Fabric Dry Run) |
| 10 | `NB_Silver_Order_Reviews_MongoDB.ipynb` | MongoDB (`retail_reviews.order_reviews`) | `silver.order_reviews` | 99,224 | 99,224 | Flattens nested BSON (`comment.*`, `timestamps.*`, `source_lineage.*`), enforces `(review_id, order_id)` composite PK, flags `+664` Gold join fan-out & SLA correlation | Ready |
| 11 | `NB_Silver_Order_Payments.ipynb` | SQL Server (`dbo.order_payments`) | `silver.order_payments` | 103,886 | — | Initial skeleton created; full profiling and quality rules pending | Draft (11/11 Pending) |
