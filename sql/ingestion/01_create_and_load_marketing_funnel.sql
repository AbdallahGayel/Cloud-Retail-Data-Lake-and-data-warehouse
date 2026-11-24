/* ============================================================================
   Phase 1 — Create & Load Marketing Funnel Tables in SQL Server
   Database : Cloud_Retail_Data_Lakehouse_v2
   Sources  :
     1) D:\Retail-Lakehouse-Platform\datasets\Olist_Marketing_funnel\olist_marketing_qualified_leads_dataset.csv (8,000 rows)
     2) D:\Retail-Lakehouse-Platform\datasets\Olist_Marketing_funnel\olist_closed_deals_dataset.csv (842 rows)
   ============================================================================ */

USE Cloud_Retail_Data_Lakehouse_v2;
GO

-- ----------------------------------------------------------------------------
-- 1) Create dbo.marketing_qualified_leads (8,000 rows)
-- ----------------------------------------------------------------------------
IF OBJECT_ID('dbo.closed_deals', 'U') IS NOT NULL
    DROP TABLE dbo.closed_deals;
GO

IF OBJECT_ID('dbo.marketing_qualified_leads', 'U') IS NOT NULL
    DROP TABLE dbo.marketing_qualified_leads;
GO

CREATE TABLE dbo.marketing_qualified_leads (
    mql_id              CHAR(32)     NOT NULL,
    first_contact_date  DATE         NOT NULL,
    landing_page_id     CHAR(32)     NOT NULL,
    origin              VARCHAR(30)  NULL,
    CONSTRAINT PK_marketing_qualified_leads PRIMARY KEY (mql_id)
);
GO

-- ----------------------------------------------------------------------------
-- 2) Create dbo.closed_deals (842 rows)
--    NOTE: Do NOT add a FK on seller_id -> dbo.sellers because 462 of 842
--    closed-deal sellers have not placed/fulfilled orders yet in dbo.sellers.
-- ----------------------------------------------------------------------------
CREATE TABLE dbo.closed_deals (
    mql_id                         CHAR(32)       NOT NULL,
    seller_id                      CHAR(32)       NOT NULL,
    sdr_id                         CHAR(32)       NOT NULL,
    sr_id                          CHAR(32)       NOT NULL,
    won_date                       DATETIME2(0)   NOT NULL,
    business_segment               VARCHAR(50)    NULL,
    lead_type                      VARCHAR(30)    NULL,
    lead_behaviour_profile         VARCHAR(30)    NULL,
    has_company                    BIT            NULL,
    has_gtin                       BIT            NULL,
    average_stock                  VARCHAR(20)    NULL,  -- Range buckets: '1-5', '5-20', '20-50', '50-200', '200+', 'unknown'
    business_type                  VARCHAR(30)    NULL,
    declared_product_catalog_size  INT            NULL,
    declared_monthly_revenue       DECIMAL(14, 2) NOT NULL,
    CONSTRAINT PK_closed_deals PRIMARY KEY (mql_id),
    CONSTRAINT UQ_closed_deals_seller UNIQUE (seller_id),
    CONSTRAINT FK_closed_deals_mql FOREIGN KEY (mql_id)
        REFERENCES dbo.marketing_qualified_leads (mql_id)
);
GO

-- ----------------------------------------------------------------------------
-- 3) Bulk Load dbo.marketing_qualified_leads
-- ----------------------------------------------------------------------------
BULK INSERT dbo.marketing_qualified_leads
FROM 'D:\Retail-Lakehouse-Platform\datasets\Olist_Marketing_funnel\olist_marketing_qualified_leads_dataset.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDQUOTE = '"',
    ROWTERMINATOR = '0x0a',
    CODEPAGE = '65001',
    TABLOCK
);
GO

-- ----------------------------------------------------------------------------
-- 4) Bulk Load dbo.closed_deals via Staging Table
--    (Handles quoted commas like "cat, wolf", 'True'/'False' -> BIT, '2000.0' -> INT)
-- ----------------------------------------------------------------------------
IF OBJECT_ID('tempdb..#stg_closed_deals') IS NOT NULL
    DROP TABLE #stg_closed_deals;

CREATE TABLE #stg_closed_deals (
    mql_id                         VARCHAR(32)  NULL,
    seller_id                      VARCHAR(32)  NULL,
    sdr_id                         VARCHAR(32)  NULL,
    sr_id                          VARCHAR(32)  NULL,
    won_date                       VARCHAR(30)  NULL,
    business_segment               VARCHAR(50)  NULL,
    lead_type                      VARCHAR(30)  NULL,
    lead_behaviour_profile         VARCHAR(30)  NULL,
    has_company                    VARCHAR(10)  NULL,
    has_gtin                       VARCHAR(10)  NULL,
    average_stock                  VARCHAR(20)  NULL,
    business_type                  VARCHAR(30)  NULL,
    declared_product_catalog_size  VARCHAR(20)  NULL,
    declared_monthly_revenue       VARCHAR(30)  NULL
);

BULK INSERT #stg_closed_deals
FROM 'D:\Retail-Lakehouse-Platform\datasets\Olist_Marketing_funnel\olist_closed_deals_dataset.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDQUOTE = '"',
    ROWTERMINATOR = '0x0a',
    CODEPAGE = '65001',
    TABLOCK
);

INSERT INTO dbo.closed_deals (
    mql_id,
    seller_id,
    sdr_id,
    sr_id,
    won_date,
    business_segment,
    lead_type,
    lead_behaviour_profile,
    has_company,
    has_gtin,
    average_stock,
    business_type,
    declared_product_catalog_size,
    declared_monthly_revenue
)
SELECT
    LTRIM(RTRIM(mql_id)),
    LTRIM(RTRIM(seller_id)),
    LTRIM(RTRIM(sdr_id)),
    LTRIM(RTRIM(sr_id)),
    CAST(won_date AS DATETIME2(0)),
    NULLIF(LTRIM(RTRIM(business_segment)), ''),
    NULLIF(LTRIM(RTRIM(lead_type)), ''),
    NULLIF(LTRIM(RTRIM(lead_behaviour_profile)), ''),
    CASE
        WHEN LOWER(LTRIM(RTRIM(has_company))) = 'true'  THEN CAST(1 AS BIT)
        WHEN LOWER(LTRIM(RTRIM(has_company))) = 'false' THEN CAST(0 AS BIT)
        ELSE NULL
    END,
    CASE
        WHEN LOWER(LTRIM(RTRIM(has_gtin))) = 'true'  THEN CAST(1 AS BIT)
        WHEN LOWER(LTRIM(RTRIM(has_gtin))) = 'false' THEN CAST(0 AS BIT)
        ELSE NULL
    END,
    NULLIF(LTRIM(RTRIM(average_stock)), ''),
    NULLIF(LTRIM(RTRIM(business_type)), ''),
    CAST(CAST(NULLIF(LTRIM(RTRIM(declared_product_catalog_size)), '') AS DECIMAL(10, 1)) AS INT),
    CAST(declared_monthly_revenue AS DECIMAL(14, 2))
FROM #stg_closed_deals;

DROP TABLE #stg_closed_deals;
GO

-- ----------------------------------------------------------------------------
-- 5) Verification Queries (Run immediately after load)
-- ----------------------------------------------------------------------------
SELECT 'dbo.marketing_qualified_leads' AS table_name, COUNT(*) AS row_count FROM dbo.marketing_qualified_leads
UNION ALL
SELECT 'dbo.closed_deals', COUNT(*) FROM dbo.closed_deals;

-- Cross-table checks: expected 0 orphans vs MQL, 380 active sellers in dbo.sellers, 1 won_date < first_contact_date
SELECT
    (SELECT COUNT(*) FROM dbo.closed_deals d LEFT JOIN dbo.marketing_qualified_leads m ON d.mql_id = m.mql_id WHERE m.mql_id IS NULL) AS orphan_mqls,
    (SELECT COUNT(*) FROM dbo.closed_deals d INNER JOIN dbo.sellers s ON d.seller_id = s.seller_id) AS active_sellers_in_store,
    (SELECT COUNT(*) FROM dbo.closed_deals d INNER JOIN dbo.marketing_qualified_leads m ON d.mql_id = m.mql_id WHERE CAST(d.won_date AS DATE) < m.first_contact_date) AS won_before_first_contact;
GO
