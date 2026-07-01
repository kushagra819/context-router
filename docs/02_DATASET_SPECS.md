# Dataset Specifications

## 1. Datasets Used

| Dataset | Type | Complexity | n (per tier) | Source | Split |
|---------|------|:----------:|:------------:|--------|-------|
| **GSM8K** | Math Reasoning | Single-hop | 200 / 1,319 | `openai/gsm8k` | `test` |
| **HotpotQA** | Multi-hop QA | 2-hop | 200 / 7,405 | `hotpotqa/hotpot_qa` (distractor) | `validation` |
| **MuSiQue** | Multi-step QA | 2-4 hop | 200 / 2,417 | `dcroyals/musique` | `validation` |

## 2. Why These Three

| Purpose | GSM8K | HotpotQA | MuSiQue |
|---------|:-----:|:--------:|:-------:|
| Tests mathematical reasoning | ✅ | | |
| Tests multi-hop reasoning | | ✅ | ✅ |
| Provides difficulty gradient | Easy | Medium | Hard |
| Standard NLP benchmark | ✅ | ✅ | ✅ |
| Has supporting context | No (closed-book) | Yes (distractor paragraphs) | Yes (supporting paragraphs) |

The three datasets create a **complexity spectrum**: single-hop → 2-hop → 2-4 hop. This lets us show that routing behavior should change with task difficulty.

## 3. Dataset Details

### 3.1 GSM8K
- **Task:** Grade school math word problems
- **Answer format:** `#### <number>` in ground truth; `Final Answer: <number>` from agents
- **Evaluation:** Exact numerical match (float comparison with 1e-6 tolerance)
- **Context provided:** None (closed-book)
- **Loading:** `datasets.load_dataset("openai/gsm8k", "main", split="test")`

### 3.2 HotpotQA
- **Task:** Multi-hop question answering requiring 2 supporting documents
- **Setting:** Distractor (10 paragraphs, 2 relevant + 8 distractors)
- **Answer format:** Free-text short answer
- **Evaluation:** Exact Match (normalized) + Token F1
- **Context provided:** Yes — 10 paragraphs via `format_hotpotqa_context()`
- **Loading:** `datasets.load_dataset("hotpotqa/hotpot_qa", "distractor", split="validation")`

### 3.3 MuSiQue
- **Task:** Multi-step compositional QA requiring 2-4 reasoning hops
- **Answer format:** Free-text short answer
- **Evaluation:** Exact Match (normalized) + Token F1 (same functions as HotpotQA)
- **Context provided:** Yes — supporting paragraphs via `format_musique_context()`
- **Loading:** `datasets.load_dataset("dcroyals/musique", split="validation")`

## 4. Sample Size Rationale

200 problems per tier × 4 tiers × 3 datasets = **2,400 total baseline evaluations**

- 200 is sufficient for initial baselines with reasonable confidence intervals
- For final publication, consider increasing to 500+ or reporting bootstrap CIs
- Each problem involves 3 agent calls → **7,200 total API calls for baselines**

## 5. Data Flow

```
Dataset → First 200 problems → Pipeline (Analyzer → Solver → Verifier) → CSV Log
                                    ↑                                       ↓
                              Model (tier)                          Evaluation metrics
```
