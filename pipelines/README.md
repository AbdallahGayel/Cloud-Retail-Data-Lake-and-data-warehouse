# Fabric Data Pipelines (`pipelines/`)

## `PL_SQLServer_To_ADLS_Bronze_Metadata_Load.template.json`

Sanitized metadata-driven Microsoft Fabric Data Pipeline definition for ingesting all 11 sources (10 SQL Server tables + 1 MongoDB collection) into ADLS Gen2 (`retail-lakehouse/bronze/`).

### Pipeline Flow
1. **`Lookup_Bronze_Table_List`**: Evaluates the inline metadata table for 10 SQL Server tables across CRM, Sales, Catalog, Reference, and Marketing domains.
2. **`FE_Load_Bronze_Tables`**: Sequentially invokes `Copy_Current_Table_To_Bronze`, landing each SQL Server table as Snappy-compressed Parquet (`enableVertiParquet: true`) under `bronze/<domain>/<table>/`.
3. **`Copy_MongoDB_Reviews_To_Bronze`**: Runs after the SQL Server loop succeeds, extracting `99,224` nested BSON documents from MongoDB (`retail_reviews.order_reviews`) via the On-Premises Data Gateway + TLS and writing JSON (`setOfObjects`) to `bronze/reviews/order_reviews/`.

### Connection Placeholders (Replace After Import)
Replace these placeholder values with your Fabric Connection GUIDs before running:

| Placeholder | Connection Type | Purpose |
|---|---|---|
| `<FABRIC_SQLSERVER_CONNECTION_ID>` | SQL Server (via On-Premises Data Gateway) | Reads `Cloud_Retail_Data_Lakehouse_v2` (`dbo.*`) |
| `<FABRIC_MONGODB_CONNECTION_ID>` | MongoDB (via On-Premises Data Gateway + TLS + `SCRAM-SHA-256`) | Reads `retail_reviews.order_reviews` |
| `<FABRIC_ADLS_CONNECTION_ID>` | Azure Data Lake Storage Gen2 (Storage Account / RBAC) | Writes Bronze Parquet and JSON to `retail-lakehouse` |

### Required Gateway & Connection Settings
- Both on-premises sources (`SQL Server` and `MongoDB`) require an active **On-Premises Data Gateway** registered in Microsoft Fabric.
- On the **destination ADLS Gen2 connection** in Fabric (*Manage connections and gateways* -> Connection Settings), you **must** enable:
  > **"Allow this connection to be utilized with either on-premises data gateways or VNet data gateways"**
  Otherwise Fabric pipeline validation rejects copying from an on-premises gateway source to a cloud ADLS Gen2 sink.
- For MongoDB `8.3` with the Fabric Gateway connector:
  - Enable TLS (`preferTLS` or `requireTLS`) and trust the server certificate in Windows `Cert:\LocalMachine\Root` (see `scripts/setup_mongodb_tls.ps1`).
  - Use alphanumeric `SCRAM-SHA-256` credentials for the read-only gateway user to avoid URI encoding issues in older connector drivers.
