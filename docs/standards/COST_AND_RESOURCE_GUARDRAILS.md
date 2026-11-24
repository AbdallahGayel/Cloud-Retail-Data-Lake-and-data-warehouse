# Cost and Resource Guardrails

## Approval boundary
No agent may create, enable, resume, resize, deploy, or leave running a paid Azure/Fabric/ClickHouse Cloud resource without explicit user approval for the named resource and scope. Discovery must not change resource state.

## Before any cloud action
Prepare a short plan containing:
- Provider, subscription/project, region, service, SKU/tier, and size.
- Business/technical purpose and expected workload.
- Expected runtime and whether it can auto-pause/auto-suspend (verify actual capability; do not assume).
- Storage, compute, egress, backup, retention, and monitoring implications.
- Cost basis and estimate assumptions; mark unknown prices/usage clearly.
- Budget cap/alerts where available, and stop/deallocate/shutdown procedure.
- Data handling, access, and rollback/deletion consequences.

Wait for approval before executing.

## Fabric trial continuity
- Record the exact expiry shown in the Fabric portal, the time checked, capacity/workspace state, and trial restrictions.
- Historical note: a project reference recorded 66 days remaining after an invite on 11 November 2026. This is not a verified current expiry date. Re-check the portal; do not present historical countdown arithmetic as authoritative.
- At the beginning of Fabric-related work, check the latest recorded verification date. If stale or missing, ask the user to confirm the live portal state or mark it `NEEDS USER VERIFICATION`.
- Propose an export/continuity checklist ahead of confirmed expiry. Keep reusable notebooks, SQL, pipeline definitions/configuration, event contracts, and runbooks in Git where exportable.
- Never commit credentials, SAS keys, personal data, transient caches, or trial-only secrets. Git is not a backup for OneLake/ADLS data.

## ClickHouse Cloud
- Cloud is the selected target; do not create or activate a service automatically.
- Verify current region/tier/compute model, storage, network, authentication, pause/idle behavior, and billing details in current provider documentation/console.
- Record query workload, service uptime, storage, data scanned/egress if billed, refresh jobs, and trial credits/limits where available.
- Keep direct Iceberg-read POC separate from Blob/COPY/ClickPipes ingestion tests; their cost and architecture are not interchangeable.

## Resource register
Maintain an approved resource register in `docs/operations/` when cloud resources are first authorized. Include owner, purpose, state, region, configuration, cost controls, data classification, backup, shutdown, and expiry/review date.
