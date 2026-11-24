# Architecture Decision Precedence

**Status:** Active governance policy  
**Applies from:** 18 November 2026

## Source-of-truth order

1. **Latest explicit user-approved decision** in the active project conversation or subsequently recorded as an accepted ADR.
2. **Accepted ADRs** in `docs/decisions/`. If an ADR conflicts with a later explicit user decision, the later user decision wins and the ADR must be marked superseded when documentation work is approved.
3. **Current architecture baseline** in `docs/architecture/ARCHITECTURE_BASELINE.md`.
4. **Current standards and operational records** in `docs/standards/` and `docs/operations/` for their specific subjects.
5. **Preserved references** in `docs/reference/`, including the 12 November 2026 Hybrid Blueprint v2.0 and 16 November 2026 first-agent prompt. These are evidence/input documents; they do not silently override newer accepted decisions.
6. **Root README and legacy diagrams** from 7 November 2026. Preserve as historical baseline until a dedicated documentation reconciliation is approved.

## Conflict handling
- Never blend contradictory designs into an invented compromise.
- Record the conflicting statements, document names/dates, impact, and available evidence.
- Recommend an ADR or ask the user for a decision before implementing the disputed element.
- Mark claims separately as selected, implemented, tested, unverified, candidate, optional, deferred, or excluded.
- A selected target technology is not proof that its integration is compatible or operational.
- Implementation of an accepted decision proceeds only within an explicitly approved phase.

## Diagram authority
The original PNG diagrams in `docs/` are historical. They must not be deleted or silently edited. `docs/architecture/diagrams/HYBRID_TARGET_ARCHITECTURE.mmd` is the current editable logical diagram source. If a rendered PNG/SVG is later generated, it must be derived from this source and reviewed against the architecture baseline before replacing any presentation asset.
