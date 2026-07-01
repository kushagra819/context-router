# Session Handoff

> **Session Date:** 2026-06-22
> **Session Type:** Full build-out — router system, pipelines, evaluation, figures, docs (Office/Claude)
> **Outcome:** Repo is **execution-ready**: only API-heavy runs remain. See
> [00_PROJECT_STATE.md](00_PROJECT_STATE.md) and [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md).

---

## What was done this session

### Verified ground truth (offline, on real CSVs)
- Wrote `scripts/validate_baselines.py` (portable, ASCII, no deps) and ran it.
- **GSM8K 4/4 LOCKED.** HotpotQA/MuSiQue: EM reliable everywhere; F1 pending clean re-runs
  (active GSM8K/T1 CSVs and all backups are truncated at 500 chars; only HotpotQA T2/T3 active
  are full-length but partial). Full write-up: [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md).
- Corrected the stale "12/12 complete" claim in `implementation_plan.md` / `project_audit.md`.

### Built the full system (all offline-tested with `tests/test_offline.py`, 9/9 pass)
- **Models:** `registry.py` (cached, real|mock) + `mock_model.py` (offline pipeline testing);
  `models/__init__.py` made lazy; alt providers isolated to `models/alt_providers/`.
- **Pipeline:** `dataset_adapters.py` (3 datasets, one interface) + `routed_pipeline.py`
  (shared by baselines & routers) + `experiment.py` (resume, mock, full self-describing schema).
- **Routers:** `router/__init__.py` factory + 15 routers (oracle/random/fixed_t1-4/fixed_mixed/
  complexity/cascade/adaptive/learned + 4 ablations); `learned_router.py` + `training_data.py`.
- **Evaluation:** `routing_metrics.py` (all metrics + bootstrap), `csv_io.py`, `aggregate.py`,
  `simulate.py` (offline router estimates from baselines).
- **Figures:** `visualization/figures.py` + `make_figures.py` (7 figures; 1–5 generated).
- **CLIs:** `run_experiment.py`, `simulate_routing.py`, `aggregate_results.py`, `train_router.py`,
  `make_figures.py`; rewrote `test_models.py`.
- **Logger** extended with ground_truth/predicted/f1/confidence/routing_reason.

### Docs operating system completed & reconciled
- New: 13–17, ROUTER_FINAL_SPEC, BASELINE_VALIDATION_REPORT + un-numbered aliases.
- Updated: 00, 05 (banner), 08 (verified numbers), 01 (added MasRouter), docs/README index.
- Stale docs banner-corrected (audit, implementation_plan).

### Cleanup
- Deleted: `gpt5_model.py`, `check_csvs.py`, `debug_results.py`, `test_gpt5.py`,
  `copy_context_docs.py`, `recompute_metrics.py`, `verify_baseline_integrity.py`, and the 3
  old per-dataset baseline runners (superseded by `run_experiment.py`).
- Renamed `recompute_and_update_metrics.py` → `recompute_metrics_from_dataset.py` (ASCII, schema-aware).
- `requirements.txt` trimmed (removed unused langchain/langgraph/sentence-transformers/rouge/seaborn).
- Created `.env.example`; updated `.gitignore` to version the truth-source results.

---

## What remains (HOME machine — commands only)

Follow [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md):
1. Re-run 8 multi-hop baselines (HotpotQA T1–T4, MuSiQue T1–T4) — clean EM+F1, N=200. (GSM8K LOCKED.)
2. `train_router.py`; run routed experiments (6 routers × 3 datasets) + ablations.
3. `aggregate_results.py` → `make_figures.py`; verify metrics; lock the ledger.

---

## Important notes for next session
- **Use the system Python or rebuild the venv on the new machine** — the committed `venv/` is
  non-portable (its interpreter shim points at the old `C:\Users\Kumud\` path). `pip install -r requirements.txt`.
- **Offline-verify anytime:** `python tests/test_offline.py` (no API/keys/network needed).
- **Trust** `scripts/validate_baselines.py` + the CSVs over any prose.
- **RISK R1:** never run Tier 3 and Tier 4 simultaneously (shared GitHub token pool).
