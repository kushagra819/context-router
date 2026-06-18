"""
Evaluation metrics and scorers for all datasets.
Handles answer extraction, comparison, and cost calculation.
"""

import re
import string
from collections import Counter
from src.utils.config import MODEL_CONFIG


# ──────────────────────────────────────────
# GSM8K SCORER
# ──────────────────────────────────────────

def extract_gsm8k_answer(text: str) -> str | None:
    """
    Extract the final numerical answer from model output.
    
    GSM8K ground truth format: "#### 42"
    Model output format: "Final Answer: 42" or just the last number
    
    Returns the extracted number as a string, or None if not found.
    """
    if not text:
        return None

    # Try 1: Look for "Final Answer: X" pattern
    match = re.search(r"[Ff]inal\s*[Aa]nswer\s*[:\-]\s*\$?\s*([\-\d,\.]+)", text)
    if match:
        return _clean_number(match.group(1))

    # Try 2: Look for "#### X" pattern (GSM8K format)
    match = re.search(r"####\s*([\-\d,\.]+)", text)
    if match:
        return _clean_number(match.group(1))

    # Try 3: Look for "answer is X" pattern
    match = re.search(r"answer\s+is\s*[:\-]?\s*\$?\s*([\-\d,\.]+)", text, re.IGNORECASE)
    if match:
        return _clean_number(match.group(1))

    # Try 4: Look for "= X" at end of text (last equation result)
    match = re.search(r"=\s*\$?\s*([\-\d,\.]+)\s*$", text, re.MULTILINE)
    if match:
        return _clean_number(match.group(1))

    # Try 5: Last number in text
    numbers = re.findall(r"[\-\d,\.]+", text)
    if numbers:
        return _clean_number(numbers[-1])

    return None


def extract_gsm8k_ground_truth(answer_text: str) -> str | None:
    """Extract ground truth from GSM8K dataset's answer field (format: '...#### 42')."""
    match = re.search(r"####\s*([\-\d,\.]+)", answer_text)
    if match:
        return _clean_number(match.group(1))
    return None


def _clean_number(num_str: str) -> str:
    """Remove commas and trailing dots from number string."""
    cleaned = num_str.replace(",", "").strip(".")
    # Handle cases like "42.0" → "42" and "42.50" → "42.5"
    try:
        num = float(cleaned)
        if num == int(num):
            return str(int(num))
        return str(num)
    except ValueError:
        return cleaned


def gsm8k_check_correct(predicted: str | None, ground_truth: str | None) -> bool:
    """Check if predicted answer matches ground truth."""
    if predicted is None or ground_truth is None:
        return False
    try:
        return abs(float(predicted) - float(ground_truth)) < 1e-6
    except ValueError:
        return predicted.strip() == ground_truth.strip()


def extract_hotpotqa_answer(text: str) -> str:
    """
    Extract the final text answer from model output for HotpotQA.
    Look for "Final Answer: [text]" or similar, otherwise fallback to cleaning up the last line or returning the whole text.
    """
    if not text:
        return ""
        
    # Try 1: Look for "Final Answer: X" pattern
    match = re.search(r"[Ff]inal\s*[Aa]nswer\s*[:\-]\s*(.*)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
        
    # Try 2: Look for "answer is X" pattern
    match = re.search(r"answer\s+is\s*[:\-]?\s*(.*)$", text, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()

    # Fallback to the last non-empty line
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        last_line = lines[-1]
        # Remove trailing dot if any
        return last_line.strip(".")
        
    return text.strip()


def normalize_answer(s: str) -> str:
    """Lower text and remove punctuation, articles and extra whitespace."""
    if not s:
        return ""
        
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def hotpotqa_check_correct(predicted: str | None, ground_truth: str | None) -> bool:
    """Check if predicted answer matches ground truth using HotpotQA Exact Match (EM)."""
    if predicted is None or ground_truth is None:
        return False
    return normalize_answer(predicted) == normalize_answer(ground_truth)


def hotpotqa_compute_f1(predicted: str | None, ground_truth: str | None) -> float:
    """Compute token-level F1 score between predicted and ground truth answers."""
    if not predicted or not ground_truth:
        return 0.0
    
    pred_tokens = normalize_answer(predicted).split()
    gold_tokens = normalize_answer(ground_truth).split()
    
    if len(pred_tokens) == 0 or len(gold_tokens) == 0:
        return 1.0 if pred_tokens == gold_tokens else 0.0
        
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_same = sum(common.values())
    
    if num_same == 0:
        return 0.0
        
    precision = 1.0 * num_same / len(pred_tokens)
    recall = 1.0 * num_same / len(gold_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1



# ──────────────────────────────────────────
# COST CALCULATOR
# ──────────────────────────────────────────

def calculate_cost(input_tokens: int, output_tokens: int, tier: int) -> float:
    """Calculate cost in USD using published pricing for the given tier."""
    config = MODEL_CONFIG[tier]
    input_cost = (input_tokens / 1_000_000) * config["cost_per_1m_input"]
    output_cost = (output_tokens / 1_000_000) * config["cost_per_1m_output"]
    return round(input_cost + output_cost, 8)


# ──────────────────────────────────────────
# SUMMARY STATISTICS
# ──────────────────────────────────────────

def compute_experiment_stats(results: list[dict]) -> dict:
    """Compute aggregate stats from a list of problem results."""
    total = len(results)
    correct = sum(1 for r in results if r.get("correct", False))
    total_cost = sum(r.get("total_cost", 0) for r in results)
    total_tokens = sum(r.get("total_input_tokens", 0) + r.get("total_output_tokens", 0) for r in results)
    total_latency = sum(r.get("total_latency", 0) for r in results)
    
    # Calculate average F1 score if present in results
    f1_scores = [r.get("f1", 0.0) for r in results if "f1" in r]
    avg_f1 = round(sum(f1_scores) / len(f1_scores) * 100, 2) if f1_scores else None

    stats = {
        "total_problems": total,
        "correct": correct,
        "accuracy": round(correct / total * 100, 2) if total > 0 else 0,
        "total_cost_usd": round(total_cost, 6),
        "avg_cost_per_problem": round(total_cost / total, 6) if total > 0 else 0,
        "total_tokens": total_tokens,
        "avg_tokens_per_problem": round(total_tokens / total, 1) if total > 0 else 0,
        "total_latency_s": round(total_latency, 2),
        "avg_latency_per_problem": round(total_latency / total, 2) if total > 0 else 0,
    }
    
    if avg_f1 is not None:
        stats["avg_f1"] = avg_f1
        
    return stats

