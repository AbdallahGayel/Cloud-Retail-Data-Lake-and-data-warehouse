# ADR-001 — Canonical Storage Ownership: ADLS Gen2 and OneLake

- **Status:** Accepted
- **Decision date:** 18 November 2026
- **Owners:** Project owner / platform team

## Context
The earlier diagram represented OneLake as unified physical Bronze/Silver/Gold storage, while the Hybrid Blueprint v2 described ADLS Gen2 as the physical Iceberg store. Ambiguous ownership could cause duplicate data copies or unsafe write paths.

## Decision
ADLS Gen2 is the canonical physical storage and source of truth for cross-platform Bronze, Silver, and Gold Apache Iceberg v2 tables stored as Parquet. OneLake is the managed Fabric analytics/collaboration lane and may expose compatible ADLS Iceberg tables through OneLake Shortcuts and metadata virtualization as a read/access path. Do not write to canonical Iceberg tables through a Shortcut.

Fabric-native Delta tables may exist for specifically assigned Fabric workloads (for example, a Fabric Eventstream path), but they are separate outputs and are not automatically canonical Gold.

## Consequences
- ADLS owns canonical physical files and Iceberg commits.
- Compatible OneLake external-table views may expose data without creating a second bulk copy of the Parquet data files; exact behavior must be tested for the actual target table.
- A representative Iceberg v2 Shortcut/metadata-virtualization POC is mandatory before relying on Fabric access.
- Every persisted noncanonical copy needs an explicit purpose, owner, refresh/retention rule, reconciliation rule, and rebuild path.
- The original PNGs remain preserved as historical references until a reviewed replacement is approved.

## Evidence and open gates
The design intent is approved; end-to-end compatibility for the project's actual Iceberg schema, partitions, deletes, identity, tenant settings, and region is not yet proven. Record POC evidence before implementation depends on it.
