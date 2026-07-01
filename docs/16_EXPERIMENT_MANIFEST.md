# 16 — Experiment Manifest (exact commands)

> **Purpose:** the home machine should only need to *run commands*. This is the complete,
> copy-paste list, in order. Everything else (code, docs, figures-from-data) is done.
> All commands are run from the repo root with the venv active.

---

## 0. One-time setup (home machine)

```bash
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt
ollama pull gemma4:e4b           # Tier-1 local model id from MODEL_CONFIG (src/utils/config.py)
copy .env.example .env           # then paste your Groq + GitHub keys
python check_all_keys.py         # verify keys/rotation
python tests/test_offline.py     # sanity: full pipeline works offline (no API)
```

> **Windows console note:** all repo scripts are ASCII-only and safe. If you run a third-party
> tool that prints Unicode, set `set PYTHONUTF8=1`.

---

## A. Baselines (API-heavy — the only baselines still needed)

GSM8K is already **LOCKED** (do not re-run). Re-run the 8 multi-hop cells for clean,
untruncated, N=200 logs with valid F1 (see [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md)).

```bash
# HotpotQA  (T2/T3 resume the partial active CSVs; T1/T4 fresh)
python run_experiment.py --dataset hotpotqa --router fixed_t1 --num-problems 200
python run_experiment.py --dataset hotpotqa --router fixed_t2 --num-problems 200 --resume
python run_experiment.py --dataset hotpotqa --router fixed_t3 --num-problems 200 --resume
python run_experiment.py --dataset hotpotqa --router fixed_t4 --num-problems 200

# MuSiQue  (all fresh)
python run_experiment.py --dataset musique --router fixed_t1 --num-problems 200
python run_experiment.py --dataset musique --router fixed_t2 --num-problems 200
python run_experiment.py --dataset musique --router fixed_t3 --num-problems 200
python run_experiment.py --dataset musique --router fixed_t4 --num-problems 200

python scripts/validate_baselines.py        # confirm all 12 cells LOCKED
```

> **RISK R1:** Tier 3 and Tier 4 share the GitHub Models token pool — run them **one at a
> time**, never concurrently.

---

## B. Train the learned router (no API; needs `datasets` + scikit-learn)

```bash
python train_router.py --datasets gsm8k hotpotqa musique --model tree --max-depth 5
# -> results/routing/learned_router.pkl (+ _report.json)
```

---

## C. Routed experiments (API-heavy — the core results)

For **each** dataset run the proposed + reference routers. (Oracle/random/fixed_* are also
obtainable offline via §F; running them live validates the simulation.)

```bash
for D in gsm8k hotpotqa musique; do
  python run_experiment.py --dataset $D --router random       --num-problems 200
  python run_experiment.py --dataset $D --router fixed_mixed  --num-problems 200
  python run_experiment.py --dataset $D --router complexity   --num-problems 200
  python run_experiment.py --dataset $D --router cascade      --num-problems 200
  python run_experiment.py --dataset $D --router adaptive     --num-problems 200
  python run_experiment.py --dataset $D --router learned      --num-problems 200
done
```

Windows PowerShell equivalent:

```powershell
foreach ($D in "gsm8k","hotpotqa","musique") {
  foreach ($R in "random","fixed_mixed","complexity","cascade","adaptive","learned") {
    python run_experiment.py --dataset $D --router $R --num-problems 200
  }
}
```

Every run is **resumable**: re-add `--resume` if interrupted.

---

## D. Ablations (API-heavy — supports the WCG claim)

The proposed router's signals are toggled via constructor kwargs; run these variants and they
are logged under distinct ids. (Use the ablation presets documented in
[ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md) §6.)

```bash
# Example pattern; one ablation per removed signal, per dataset:
python run_experiment.py --dataset hotpotqa --router cascade --num-problems 200   # full
# no-confidence / no-role / no-complexity / no-budget variants -> see ROUTER_FINAL_SPEC.md §6
```

---

## E. Aggregate + figures (no API — fast)

```bash
python aggregate_results.py                  # -> results/master_results.{json,csv,md}
python make_figures.py                       # -> results/figures/*.png (+ .pdf)
```

---

## F. Offline preview (NO API — runnable on the office machine today)

Produces preliminary router estimates and figures from the baselines alone (exact for
single-tier & oracle; estimates for mixed/random; see `src/evaluation/simulate.py`):

```bash
python simulate_routing.py --dataset gsm8k                       # 4 complete tiers
python simulate_routing.py --with-questions --routers complexity learned   # needs datasets
python make_figures.py                                           # uses sim data if no live data
```

---

## G. Full pipeline in one go (after baselines exist)

```bash
python scripts/validate_baselines.py && \
python train_router.py --datasets gsm8k hotpotqa musique && \
# ... run §C routed experiments ... && \
python aggregate_results.py && \
python make_figures.py
```

---

## Output locations

| Path | Produced by | Contents |
|------|-------------|----------|
| `results/baselines/*.csv` | `run_experiment.py --router fixed_tN` | baseline logs (truth source) |
| `results/routing/*.csv` | `run_experiment.py --router <other>` | routed logs (truth source) |
| `results/routing/learned_router.pkl` | `train_router.py` | trained classifier |
| `results/baseline_validation.json` | `scripts/validate_baselines.py` | completeness/EM/F1 status |
| `results/master_results.{json,csv,md}` | `aggregate_results.py` | master metrics table |
| `results/routing_sim/*.json` | `simulate_routing.py` | offline estimates |
| `results/figures/*.png` | `make_figures.py` | all figures |
| `results/_mock/*` | `run_experiment.py --mock` | throwaway smoke-test output (gitignored) |
