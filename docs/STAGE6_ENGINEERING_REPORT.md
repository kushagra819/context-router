# Stage 6 — Final Engineering Report (Audit → Fixes → Compute-Only Remainder)

> **Status:** Canonical. This is the authoritative record of the engineering pass that
> took the repo from "well-documented system spec with ~10 reviewer-blocking issues" to
> "final engineering version; only computation remains." It supersedes the optimistic
> status banners in older docs. Trust **code + the regenerated CSVs/JSON** over any prose.
>
> Companion machine-readable artifacts produced this pass:
> `results/recompute_provenance.json`, `results/baseline_validation.json`,
> `results/master_results.*`, `results/cost_sensitivity.json`,
> `results/confidence_validation.json`.

---

## 0. TL;DR

The reviewer pre-mortem ([reviewer_attack_report.md](reviewer_attack_report.md)) listed ~10
blockers. Most were **fixable by engineering without spending API quota**, and they now are.
The headline data problem (the "Tier-4 EM anomaly") was diagnosed as **mostly a
measurement/extraction artifact** and corrected offline. The provider reliability problem was
fixed by migrating Tier 3 off the sunset Llama-3.1-405B. What remains is genuinely
compute-only: **3 multi-hop baseline cells, the routed/ablation runs, learned-router training,
and figure generation** — all with exact commands in §8.

---

## 1. Repository audit summary

A 17-agent audit (code, data, defects, docs, providers, literature) plus first-hand review
confirmed:

* **Architecture is sound and worth keeping:** one shared `RoutedPipeline` (a baseline is
  just `FixedTierRouter(t)`), `BaseMultiKeyModel` key-rotation infra, stdlib-only offline
  analysis, `MockModel` offline path. KEEP.
* **The #1 code smell** was 5× duplication of the OpenAI-compatible `generate()` loop across
  `github/gpt41/openrouter/sambanova` wrappers → **REFACTORed** into one
  `OpenAICompatibleModel` base.
* **Data was in *better* shape than the docs/reviewer report claimed** (which described 48/118
  partial cells). Ground truth after recompute: **8/12 baseline cells LOCKED**; only 3 need
  live re-runs (see §4).
* **Docs are bloated** (~57 files, much redundant/superseded). Consolidation plan in §7.

Per-file KEEP/REFACTOR/REMOVE verdicts: see the audit JSON in the task transcript; the
actionable subset is implemented in this pass.

## 2. Research audit summary (claims vs evidence)

| Claim | Verdict after this pass |
|------|--------------------------|
| C1 per-agent routing is novel | **Narrowed & made honest.** MasRouter (ACL'25), DAAO ('25) and esp. *Explainable Model Routing for Agentic Workflows* (CHI'26) already do per-agent role+confidence+stage+budget routing. Defensible residue: **fixed typed A→S→V topology + upstream-confidence as a cross-agent handoff + training-free/interpretable + rigorous honest eval.** Added the missing `query_level` baseline to make the per-agent-vs-per-query test real. See [RELATED_WORK.md](RELATED_WORK.md). |
| C2 oracle headroom | Holds (GSM8K oracle 98.5% EM @ \$0.049 vs T4 97% @ \$1.18, offline). Cost robust across price vectors (§ Fix D). |
| C3 retention@cost | **Reference fixed:** quality retention is now vs the **best-performing tier** (not T4, which is *not* the multi-hop ceiling). Pending live routed runs. |
| C4 Workflow Context Gain (headline) | Now has an **operational matched-cost protocol** + the **registered one-sided** test. Pending live runs. |
| C5 ablation | Router variants + harness ready; pending live runs. |
| C6 learned router | **Rebuilt rigorously** (grouped CV, OOD, role-importance evidence). Honestly reframed as a **data-driven difficulty classifier** (role importance ≈ 0 is *proven*, not hidden). |
| C7 generalization | OOD leave-one-dataset-out harness added; honest in/out-of-distribution gap will be reported. |
| C8 honesty | **Strengthened:** confidence signal validated (weak: AUC≈0.56), cost sensitivity analyzed, F1-aware labels, T4 anomaly explained. |

## 3. The Tier-4 anomaly — diagnosed and corrected (offline)

**Root cause:** GPT-4.1's verifier answers are verbose/Markdown (`**Final Answer:** yes`), and
the legacy extractor captured the bare `**` marker or full sentences → EM/F1 mis-scored *only*
Tier 4. Fixed with a Markdown-robust, last-marker extractor (`metrics.extract_hotpotqa_answer`,
applied identically to every tier) + an offline recompute from the immutable `response_text`
(`scripts/recompute_metrics.py`).

**Effect (symmetric — terse tiers unchanged, only T4 moves):**

| cell | EM before→after | F1 before→after |
|------|:---------------:|:---------------:|
| hotpotqa T4 | 37.5 → **41.5** | 57.6 → **62.9** |
| musique T4  | 27.9 → **31.0** | 45.4 → **49.7** |
| hotpotqa/musique T1–T3 | unchanged | unchanged |

Residual: T4 is still below T1 on multi-hop even after the fix → a **genuine, reportable**
finding (a verbose frontier model in a verifier role is under-credited by span-EM/F1), not just
an artifact. **Quality retention is therefore referenced to the best tier, and oracle labels
use F1-aware correctness** so verbose-but-correct T4 answers are credited (`training_data.py`).
The remaining live re-runs additionally tighten the verifier prompt to emit a clean
`FINAL ANSWER:` line.

## 4. Data state (regenerated; CSV = source of truth)

`python scripts/validate_baselines.py` →

* **LOCKED (8):** gsm8k T1–T4, hotpotqa T1, hotpotqa T4, musique T1, musique T4.
* **Needs work (4):**
  * hotpotqa **T2** — 200 untruncated rows, F1 only pending → **offline** backfill
    `python scripts/recompute_metrics.py --use-hf` (API-free; ~no-op EM).
  * hotpotqa **T3** — active 169/200; backup truncated → **live re-run** (Tier 3 = new model).
  * musique **T2** — active 184/200 → **live re-run** (or accept N=184).
  * musique **T3** — backup-only, truncated → **live re-run**.

Note: all Tier-3 cells (incl. the previously-complete gsm8k T3) must be re-run on the new
Tier-3 model (Llama-4-Maverick) for consistency — see §5.

## 5. Provider migration (Phase 2)

Llama-3.1-405B (old Tier 3) has been **sunset** across free providers. Recent comparable papers
use Llama-4 / 70B-class open models + a closed frontier (DAAO: Llama-3.1-70B/Qwen-2-72B; CHI'26:
**Llama-4-Maverick** + GPT-5/Claude/Gemini). New matrix:

| Tier | Model | Provider(s) | $/1M in/out (representative, hypothetical) |
|:----:|-------|-------------|:------------------------------------------:|
| 1 | Gemma-3-4B | Ollama (local) | 0.03 / 0.06 |
| 2 | Llama-3.3-70B | Groq | 0.59 / 0.79 |
| 3 | **Llama-4-Maverick** | **Groq (primary) + OpenRouter (failover)** | 0.60 / 0.90 |
| 4 | GPT-4.1 | **OpenAI direct (preferred) + GitHub (fallback)** | 2.00 / 8.00 |

* New `FailoverModel` advances to a fallback provider on permanent exhaustion (logs the backend
  mix; a single results table should use ONE backend — fallback is documented robustness, not
  silent substitution).
* **Tier 3 and Tier 4 no longer share the GitHub PAT pool** → resolves confound **R1**; latency
  is no longer contaminated by shared-quota queueing.
* Adding any OpenAI-compatible provider is now a ~15-line config (`OpenAICompatibleModel`).

## 6. Metrics & statistics (Phase 6 / Fix C)

`src/evaluation/routing_metrics.py` now has, with formulas: one-sided **paired bootstrap**
(the *registered* WCG test), **exact McNemar**, **Holm-Bonferroni** + **Benjamini-Hochberg**,
**paired-difference bootstrap CI** (effect size + CI), an unpaired **minimum-detectable-effect**
helper (≈14 pts at N=200, p=.5 → power caveat), and an **operational matched-cost WCG**
(`workflow_context_gain_matched`) that selects the comparator by cost budget *without peeking at
quality* (fixes the forking-path). `under_provision_rate` corrected to the symmetric
`chosen < oracle` definition. Quality reference fixed in `aggregate.py` (vs best tier + vs T4 for
transparency).

## 7. Repository quality (Phase 7)

* New self-describing artifacts (this report, `RELATED_WORK.md`) + regenerated result files.
* Consolidation: many planning/legacy docs are superseded; this report + `00_PROJECT_STATE.md`
  + `ROUTER_FINAL_SPEC.md` + `16_EXPERIMENT_MANIFEST.md` + `17_RESEARCH_CLAIMS.md` are the
  canonical set. (Legacy docs retained but banner-deferred; safe to delete in a cleanup commit.)
* Code: 5× duplication removed; `alt_providers` import made lazy (no longer crashes without
  `google` SDK).

---

## 8. Remaining compute-only tasks + EXACT home-machine commands

Prereqs: `pip install -r requirements.txt`; `pip install datasets`; `ollama pull gemma3:4b`;
`cp .env.example .env` and fill Groq + OpenRouter + (OpenAI or GitHub) keys; `python test_models.py`.

```bash
# (0) Offline F1 backfill for hotpotqa T2 (API-free) + confirm state
python scripts/recompute_metrics.py --use-hf
python scripts/validate_baselines.py

# (1) Re-run the 3 (or 4) Tier-3 baselines on Llama-4-Maverick + the 2 incomplete multi-hop cells
python run_experiment.py --mode baseline --dataset gsm8k    --tier 3   # Tier-3 model changed -> re-run
python run_experiment.py --mode baseline --dataset hotpotqa --tier 3
python run_experiment.py --mode baseline --dataset musique  --tier 2
python run_experiment.py --mode baseline --dataset musique  --tier 3
python scripts/recompute_metrics.py            # canonical extractor on the new CSVs
python scripts/validate_baselines.py           # expect 12/12 LOCKED

# (2) Train + rigorously evaluate the learned router (F1-aware labels; grouped CV/OOD)
python train_router.py --datasets gsm8k hotpotqa musique --metric f1 --max-depth 5

# (3) Routed runs (per-agent) + the per-query control + ablations, x3 datasets
for D in gsm8k hotpotqa musique; do
  for R in query_level complexity cascade adaptive learned random fixed_mixed \
           adaptive_no_complexity adaptive_no_role adaptive_no_confidence adaptive_no_budget; do
    python run_experiment.py --mode routed --dataset $D --router $R
  done
done

# (4) Aggregate, sensitivity, confidence validation, figures
python aggregate_results.py
python measure_cost_sensitivity.py --metric f1
python make_figures.py
```

(Do **not** run Tier 3 and Tier 4 concurrently only matters historically; they are now
decoupled. Keep one backend per results table.)

## 9. Remaining publication risks (honest)

1. **Novelty is narrow** — per-agent routing is no longer new (CHI'26/MasRouter/DAAO). Lead with
   the *fixed-typed-pipeline + upstream-confidence-handoff + rigorous honest study*, not "we
   invented per-agent routing." Include the `query_level` head-to-head.
2. **Confidence signal — weak lexical signal now has a calibrated replacement.** The lexical
   `extract_confidence` validated at AUC≈0.56 (`results/confidence_validation.json`). The pipeline
   now requests token **logprobs** and uses `confidence_from_logprob = exp(mean_logprob)` (a real
   model-derived uncertainty), falling back to lexical only when a provider returns no logprobs;
   the run logs `confidence_source` + `mean_logprob`, and `confidence_validation.py` auto-computes
   the logprob-confidence AUC/ECE once live runs exist. Still: don't *headline* the cascade until
   the calibrated AUC is in hand; the gains (if any) come mostly from role/stage routing.
3. **N=200 is underpowered** (MDE≈14 EM pts unpaired). Use paired tests, report CIs + Holm
   correction, consider N=500 for the headline; one-sided WCG must be justified.
4. **Costs are hypothetical** — mitigated by the sensitivity analysis (savings robust 62–96%);
   frame as ratios, never deployment savings.
5. **Offline simulation ≠ live** — `simulate.py`'s independence assumption assumes away
   cross-agent effects; cascade/adaptive are NOT simulable. Only **live** routed runs back C3–C5.
6. **One pipeline shape** — A→S→V only; no second topology (would need new live runs).
