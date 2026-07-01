# Baseline Protocol

## 1. Pipeline Architecture

Every baseline experiment uses a **3-agent sequential pipeline**:

```
Question → Analyzer → Solver → Verifier → Final Answer
```

| Agent | Role | Output |
|-------|------|--------|
| **Analyzer** | Decomposes the question into sub-questions, identifies relevant facts | Structured analysis with reasoning hops |
| **Solver** | Resolves each sub-question step by step, produces answer | Step-by-step reasoning + proposed answer |
| **Verifier** | Checks the solver's reasoning against context, confirms/corrects | Verification + `Final Answer: <answer>` |

All three agents use the **same model tier** in baseline experiments (no routing).

## 2. Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Problems per tier | 200 |
| Temperature | 0.1 |
| Max output tokens | 2,048 |
| Tiers | 1 (Gemma 4B), 2 (Llama 70B), 3 (Llama 405B), 4 (GPT-4.1) |
| Datasets | GSM8K, HotpotQA, MuSiQue |
| Total experiments | 12 (4 tiers × 3 datasets) |

## 3. Logging

Each agent call is logged to a CSV with these columns:
```
timestamp, experiment_id, problem_id, dataset, agent_role, tier,
model_name, router_type, input_tokens, output_tokens, latency_s,
cost_usd, correct, escalated_from, response_text
```

- `router_type = "none"` for all baselines
- `correct` is computed at runtime (before logging)
- `response_text` stores the full agent response (newlines replaced with spaces)

## 4. Resume Capability

All baseline runners support `--resume` mode:
1. Scans existing CSV for completed problem IDs (verifier rows without `[ERROR]`)
2. Removes error rows from CSV
3. Skips completed problems, runs only missing ones
4. Appends new results to same CSV

### Known Bug (Resume Path)
The resume stats computation uses a `validation_problems` global variable that references the dataset loaded at `__main__` scope. When called inside the function, `validation_problems` is undefined → F1 computation crashes or produces wrong values. **This bug only affects the stats JSON, not the CSV data itself.**

## 5. Evaluation

### GSM8K
- Extract answer from verifier output using regex (`Final Answer: <number>` or `#### <number>`)
- Compare with ground truth via float equality (tolerance 1e-6)
- Metric: **Accuracy** (% correct)

### HotpotQA & MuSiQue
- Extract answer from verifier output using regex (`Final Answer: <text>`)
- Normalize both predicted and ground truth (lowercase, remove punctuation/articles)
- **Exact Match (EM):** Normalized string equality
- **Token F1:** Token-level precision/recall between normalized predicted and gold

## 6. File Naming Convention

```
results/baselines/{dataset}_baseline_tier{n}.csv       # Raw experiment data
results/baselines/{dataset}_baseline_tier{n}_stats.json # Computed statistics
```

## 7. Execution Commands

```bash
# GSM8K
python run_baseline.py --tier {1,2,3,4} --num-problems 200

# HotpotQA
python run_hotpotqa_baseline.py --tier {1,2,3,4} --num-problems 200

# MuSiQue
python run_musique_baseline.py --tier {1,2,3,4} --num-problems 200

# Resume a failed run
python run_hotpotqa_baseline.py --tier 3 --num-problems 200 --resume
```
