# Testing and Validation Standard

**Status:** Active project standard. Exact thresholds are phase-specific and must be agreed before implementation.

## 1. General rules
- Define tests and acceptance thresholds before a phase is implemented.
- Separate static checks, unit tests, integration tests, data-quality checks, reconciliation, recovery tests, and performance tests.
- A successful command exit is not sufficient evidence of business correctness.
- Record test ID, environment, timestamp, code/config version, input range or fingerprint, expected result, actual result, and pass/fail.
- Do not use production or sensitive data for test fixtures unless explicitly approved and appropriately protected.

## 2. Source discovery checks
- Capture server/engine version, database/schema/table/collection names, column names/types, PK/FK/unique constraints, and source ownership.
- Profile row counts and null/duplicate distributions only through safe, read-only methods.
- Identify mutable vs append-only behavior, delete semantics, time columns, and CDC prerequisites.
- For CSV/XLSX, record file fingerprint/size, sheets, headers, row counts, data types, nulls, likely keys, and encoding/date issues without exposing personal row contents.

## 3. Batch ingestion checks
- Source-to-target row counts and rejected/quarantined counts reconcile.
- Important totals (amount, quantity, order count, etc.) reconcile under documented filters and null rules.
- Re-running the same batch is idempotent; no duplicate target records are introduced.
- Watermark/fingerprint, source window, and run metadata are persisted.
- Schema drift and late updates/deletes are detected and handled explicitly.

## 4. CDC checks (when a CDC engine is approved)
- Initial snapshot completes and transitions to log/change streaming without gaps.
- Insert, update, delete, key changes (if supported), restart, checkpoint/resume, duplicate delivery, and ordering behavior are tested.
- Source sequence/LSN/offset, operation type, and source commit timestamp are retained where available.
- Reconcile source current state to target state after each scenario.
- CDC mechanism must be approved and version compatibility documented before execution.

## 5. Streaming/event checks (when a route and processor are approved)
- Validate event contract, schema version, required fields, event ID uniqueness, and event time.
- Test duplicate delivery, late/out-of-order events, consumer restart/replay, checkpoint/recovery, and dead-letter/quarantine behavior where supported.
- Reconcile produced, accepted, rejected, and persisted event counts by event ID/run ID.
- Event Hubs protocol evidence and Kafka protocol evidence must be tracked separately.

## 6. Silver and Gold checks
- Type, nullability, accepted-value, uniqueness, referential-integrity, and deduplication tests.
- Explicit grain tests for every fact table; keep order, order-item, payment, review, and inventory grains distinct.
- Dimension surrogate-key resolution and Unknown-member policy.
- SCD1 overwrite behavior and SCD2 validity-window/non-overlap/current-row rules.
- Fact-to-dimension joins resolve using the correct business-effective time.
- Reconcile important business KPIs to documented source definitions.

## 7. Fabric checks
- Notebook output/schema is correct and repeatable.
- Data Factory activity dependencies, parameters, retries, and output status are validated.
- Eventstream route is tested with the exact selected protocol and destination.
- SQL Analytics Endpoint results are checked against the underlying supported Lakehouse data.
- OneLake Shortcut/metadata virtualization is tested separately using the actual target Iceberg format/schema/features.
- Never mix capability-test/sample records into business facts.

## 8. ClickHouse Cloud and BI checks
- Verify current Cloud feature support and connectivity before running the integration.
- Compare result correctness and row/business-total reconciliation against the canonical source.
- Record freshness/refresh lag and failure/retry behavior for any materialized serving table.
- For performance comparisons, use the same query, equivalent data range, repeat runs, p50/p95 latency, scanned/read bytes, resource use, concurrency, refresh duration, storage, and estimated cost where measurable.
- Only retain MergeTree copies when measured benefit justifies operating cost.
- Validate Power BI connector/authentication, semantic definitions, refresh behavior, and licensing.

## 9. dbt checks (only if later approved)
- `dbt build`/tests and model documentation apply to ClickHouse-native models only unless a new ADR assigns a different boundary.
- Do not use dbt to write canonical Iceberg tables in this baseline.

## 10. Phase evidence
Each phase report must list tests planned, tests run, exact outcomes, skipped tests and reasons, unresolved defects, data reconciliation evidence, and remaining risks. A test not run is `NOT RUN`, never `PASS`.
