"""Quick debug script to analyze baseline results and find extraction issues."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datasets import load_dataset
from src.evaluation.metrics import extract_gsm8k_answer, extract_gsm8k_ground_truth, gsm8k_check_correct

# Load results
csv_path = "results/baselines/gsm8k_baseline_tier2.csv"
df = pd.read_csv(csv_path)

# Filter to only the 200-problem run (problem_id 0-199, skip first 5-problem run duplicates)
# Get only verifier rows (final answer comes from verifier)
verifier = df[df.agent_role == "verifier"]
# Take last 200 entries (the 200-problem run)
if len(verifier) > 200:
    verifier = verifier.tail(200).reset_index(drop=True)

print(f"Total verifier entries: {len(verifier)}")
print(f"Marked correct: {verifier.correct.sum()}")
print(f"Marked wrong: {(~verifier.correct).sum()}")
print()

# Load original dataset to get ground truth
dataset = load_dataset("openai/gsm8k", "main", split="test")

# Debug: check extraction on wrong answers
wrong = verifier[verifier.correct == False]
print(f"=== Debugging {min(10, len(wrong))} WRONG answers ===\n")

for idx, row in wrong.head(10).iterrows():
    pid = int(row["problem_id"])
    response = row["response_text"]
    
    # Get ground truth
    gt_text = dataset[pid]["answer"]
    gt = extract_gsm8k_ground_truth(gt_text)
    
    # Get predicted
    predicted = extract_gsm8k_answer(response)
    
    # Also try extracting from full response (not truncated)
    print(f"Problem {pid}:")
    print(f"  Ground truth: {gt}")
    print(f"  Extracted:    {predicted}")
    print(f"  Response:     {response[:200]}...")
    print(f"  Match: {gsm8k_check_correct(predicted, gt)}")
    print()

# Also check: are some "wrong" answers actually correct but extraction failed?
print("=== Re-checking all with fresh extraction ===")
re_correct = 0
extraction_fail = 0
for idx, row in verifier.iterrows():
    pid = int(row["problem_id"])
    response = row["response_text"]
    gt_text = dataset[pid]["answer"]
    gt = extract_gsm8k_ground_truth(gt_text)
    predicted = extract_gsm8k_answer(response)
    
    if gsm8k_check_correct(predicted, gt):
        re_correct += 1
    elif predicted is None:
        extraction_fail += 1

print(f"Re-checked accuracy: {re_correct}/{len(verifier)} = {re_correct/len(verifier)*100:.1f}%")
print(f"Extraction failures (None): {extraction_fail}")
