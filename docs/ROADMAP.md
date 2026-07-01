# Project Roadmap

> **Last Updated:** 2026-06-22

---

## Timeline

```
Week 1 (Current)
├── ✅ Baselines complete (GSM8K locked, HotpotQA/MuSiQue re-running)
├── ✅ Logger bug fixed
├── 🔄 Docs operating system (Stage 1)
└── 🔄 5 baseline re-runs (parallel, HOME)

Week 2
├── Router design finalization (Stage 2)
├── Oracle/Random/Fixed Mixed routers (from CSVs, no API calls)
├── Complexity + Cascade routers (code)
└── Lock all baseline results

Week 3
├── Router experiments on live models (HOME)
├── Evaluation + ablation analysis
├── Pareto frontier plots
└── Signal ablation study

Week 4
├── Visualization + figures
├── Presentation slides
├── Final repo polish
└── Publication discussion prep
```

## Milestones

| Milestone | Target | Depends On |
|-----------|--------|-----------|
| M1: All baselines locked | Week 1 end | Re-runs complete |
| M2: Docs system complete | Week 1 end | Current session |
| M3: Router code ready | Week 2 mid | M2 |
| M4: Oracle/Random/Fixed results | Week 2 end | M1, M3 |
| M5: Live router experiments | Week 3 mid | M3, API access |
| M6: Final results + figures | Week 3 end | M4, M5 |
| M7: Presentation ready | Week 4 mid | M6 |
| M8: Repo publication-ready | Week 4 end | All above |

## Risk-Adjusted Schedule

If re-runs take longer: Push M1 to Week 2, compress Weeks 2-3.
If router doesn't show improvement: Pivot to cost-quality Pareto analysis as primary contribution.
If Opus credits run out: Resume with docs as context bridge.
