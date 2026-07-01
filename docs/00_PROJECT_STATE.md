# Project State

> **Last Updated:** 2026-06-25 (Stage 6 engineering pass)
> **Current Stage:** Stage 6 — Final Engineering Version. The reviewer-blocking issues are fixed
> offline; Tier 3 migrated off the sunset Llama-3.1-405B to Llama-4-Maverick. **Only computation
> remains.** Read **[STAGE6_ENGINEERING_REPORT.md](STAGE6_ENGINEERING_REPORT.md) first** — it is
> the authoritative record of what changed, the corrected data state (8/12 cells LOCKED), the
> remaining compute-only tasks, and the exact home-machine commands.
> **Authoritative sub-docs:** [STAGE6_ENGINEERING_REPORT.md](STAGE6_ENGINEERING_REPORT.md),
> [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md) (baselines — note: regenerated;
> trust `results/baseline_validation.json`), [ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md),
> [RELATED_WORK.md](RELATED_WORK.md) (honest novelty), [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md).

---

## Stage status

| Stage | Name | Status |
|:-----:|------|:------:|
| 1 | Cleanup & truth-source locking | ✅ Done |
| 2 | Router design & innovation selection | ✅ Done ([ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md)) |
| 3 | Router implementation | ✅ Done (15 routers, pipeline, runners, tests) |
| 4 | Evaluation & ablation framework | ✅ Done (code); ⏳ runs pending |
| 5 | Visualization & presentation | ✅ Figures code done; schematics + GSM8K data figures generated |
| 6 | Final polish & publication readiness | ✅ Repo self-describing; ⏳ final numbers pending runs |

---

## What is DONE (this machine, verified)

- **Baselines validated** offline (`scripts/validate_baselines.py`): GSM8K 4/4 LOCKED;
  HotpotQA/MuSiQue EM reliable, F1 pending clean re-runs. See validation report.
- **Router system** (`src/router/`): 15 routers + `get_router()` factory
  (oracle/random/fixed_t1-4/fixed_mixed/complexity/cascade/adaptive/learned + 4 ablations).
- **Unified pipeline** (`src/pipeline/`): one `RoutedPipeline` drives baselines *and* routed
  runs over all 3 datasets via dataset adapters; `MockModel` makes it fully offline-testable.
- **Experiment driver** (`run_experiment.py`): baseline + routed, resume, mock, full
  self-describing CSV schema (incl. ground_truth/predicted/f1/confidence/routing_reason).
- **Evaluation** (`src/evaluation/`): task + routing + efficiency + research metrics, CSV
  aggregation, offline simulation; `aggregate_results.py`, `simulate_routing.py`.
- **Learned router** (`train_router.py`): train→save→load→predict path verified offline.
- **Figures** (`make_figures.py`): 7 figures; schematics + GSM8K Pareto/utilization generated.
- **Tests** (`tests/test_offline.py`): 9 offline smoke tests pass (no API/network/deps-beyond-stdlib).
- **Docs operating system**: 00–17 + ROUTER_FINAL_SPEC + BASELINE_VALIDATION_REPORT + ADRs +
  pointer aliases. Stale docs (audit, implementation_plan) banner-corrected.

## What REMAINS (home machine — commands only)

See [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md) for copy-paste commands.
1. Re-run 8 multi-hop baselines (HotpotQA T1–T4, MuSiQue T1–T4) for clean EM+F1, N=200.
2. `train_router.py` (learned router).
3. Run routed experiments (random/fixed_mixed/complexity/cascade/adaptive/learned) ×3 datasets.
4. Run ablations (`adaptive_no_*`).
5. `aggregate_results.py` + `make_figures.py` → final tables & figures.
6. Verify metrics, update [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md), mark cells LOCKED.

GSM8K baselines are LOCKED — do **not** re-run.

---

## Resume instructions (next session / future Claude)

1. Read this file, then [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md) and
   [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md).
2. `python scripts/validate_baselines.py` and `python tests/test_offline.py` to confirm state.
3. If new CSVs exist in `results/`, run `aggregate_results.py` + `make_figures.py`.
4. Trust CSVs + `validate_baselines.py` over any prose. The repo is self-describing — no chat
   history is required.
