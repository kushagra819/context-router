# ADR-001: Baseline Truth Source

## Status: ACCEPTED

## Decision
CSV files in `results/baselines/` are the single source of truth for all experimental results. Stats JSON files are derived summaries and may be stale or incorrect.

## Alternatives Considered
1. **Use stats JSON files** — Rejected: JSON files for resumed runs only contain last-session metrics, not full-run aggregates. Multiple JSONs showed F1 < EM (mathematically impossible).
2. **Use in-memory results** — Rejected: Not persistent. Lost when script terminates.
3. **Use a database** — Rejected: Overengineered for this project scale.

## Reason Chosen
CSVs contain every individual agent call with full metadata. Any aggregate metric can be recomputed from CSVs. CSVs are append-only during experiments, making them naturally resilient to resume/restart scenarios.

## Impact
- All metric reporting must be backed by CSV recomputation
- Stats JSONs are convenience files, not authoritative
- Created `scripts/recompute_and_update_metrics.py` for recomputation
- Created `scripts/verify_baseline_integrity.py` for validation
