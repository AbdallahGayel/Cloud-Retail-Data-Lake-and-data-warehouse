# SQL Server Ingestion Scripts (`sql/`)

Source database: `Cloud_Retail_Data_Lakehouse_v2` (SQL Server on-premises, loaded via T-SQL `BULK INSERT` from the Olist E-Commerce and Marketing Funnel CSV datasets).

## Scripts

- [`sql/ingestion/01_create_and_load_marketing_funnel.sql`](ingestion/01_create_and_load_marketing_funnel.sql): Creates `dbo.marketing_qualified_leads` (`8,000` rows) and `dbo.closed_deals` (`842` rows) and loads both CSVs using `BULK INSERT`.

## Operational Notes

- **LF line endings (`ROWTERMINATOR = '0x0a'`):** The Olist CSV files use Unix LF (`\n`) rather than Windows CRLF (`\r\n`). Specifying `ROWTERMINATOR = '0x0a'` with `FORMAT = 'CSV'`, `FIELDQUOTE = '"'`, and `CODEPAGE = '65001'` prevents multi-row read failures and preserves quoted values (such as `"cat, wolf"`).
- **Staging table for `closed_deals`:** `#stg_closed_deals` loads string columns first so `'True'` / `'False'` convert cleanly to `BIT` and float-formatted counts like `'2000.0'` cast safely via `DECIMAL(10, 1)` to `INT`.
- **Intentional FK boundary:** `dbo.closed_deals.seller_id` does **not** enforce a foreign key to `dbo.sellers` because `462` of the `842` closed-deal sellers had not yet fulfilled orders in `dbo.sellers` (`380` active, `462` onboarding).
- **Path adjustment:** Before running on another machine, update the `FROM '...'` CSV file paths inside the script to match your local dataset directory.
