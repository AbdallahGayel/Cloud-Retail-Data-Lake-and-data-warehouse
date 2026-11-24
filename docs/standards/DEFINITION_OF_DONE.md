# Definition of Done — Phase Gate

A phase is complete only when all applicable requirements below are satisfied and the user has reviewed the evidence. Criteria not applicable must be marked `N/A` with a reason; criteria not executed must be marked `NOT RUN` (not PASS).

## Required phase closure
1. **Scope:** approved deliverables are implemented; no unapproved scope was added.
2. **Correctness:** relevant unit/integration/data tests pass; expected and actual results are documented.
3. **Data quality:** applicable schema, null, duplicate, key, referential-integrity, and business-rule checks pass.
4. **Reconciliation:** source/target counts and material business totals reconcile, or a documented exception is accepted.
5. **Reliability:** rerun/idempotency, restart/recovery, and failure paths are tested when relevant.
6. **Security:** no secrets or sensitive customer data in Git, reports, logs, or notebook outputs; permissions are least-privilege.
7. **Cost:** resource owner, region, size/tier, expected runtime, monitoring, and stop/shutdown path are documented for any approved cloud service.
8. **Documentation:** architecture, ADRs, data contracts, runbooks, and known limitations are updated as required.
9. **Reproducibility:** commands, versions, configuration placeholders, and test evidence are sufficient for another contributor to repeat the work without secrets.
10. **Change review:** changed files, diff summary, test results, risks, and Git status are presented to the user.
11. **User review:** the user accepts the phase outcome before the agent advances.

## Phase-specific examples
- Discovery: read-only inventory, source maps, current-state evidence, conflicts, compatibility gates, and a proposed next-phase plan. No repository writes.
- Foundation: repository structure, configuration templates, documented resource plan, and local checks; no cloud provisioning without explicit approval.
- Batch/Bronze: idempotent loads, fingerprints/watermarks, quarantine, and count reconciliation.
- CDC: snapshot/change/delete/restart/resume and state reconciliation.
- Streaming: event contract, deduplication, replay, late-event behavior, and DLQ/quarantine where supported.
- Silver/Gold: conformed schemas, quality rules, documented fact grain, SCD behavior, and business metric reconciliation.
- Fabric: actual notebook/pipeline/Eventstream/Shortcut behavior demonstrated for the specific route and version.
- ClickHouse Cloud: real query correctness, cost/region configuration approval, and justified serving strategy.
- BI: approved Power BI connection, semantic definitions, and reconciled visuals.
