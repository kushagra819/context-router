"""
Signal Extraction Utilities
============================
Functions to extract routing signals from questions and agent responses.
"""

import re
import string
from collections import Counter


def extract_question_features(question: str) -> dict:
    """
    Extract routing-relevant features from a question.
    
    Returns:
        dict with keys: word_count, entity_count, estimated_hops,
                       has_comparison, has_temporal, complexity_score
    """
    words = question.split()
    word_count = len(words)
    
    # Count potential named entities (capitalized words not at start of sentence)
    entity_count = sum(
        1 for i, w in enumerate(words)
        if w[0].isupper() and i > 0 and not words[i-1].endswith((".", "?", "!"))
    ) if len(words) > 1 else 0
    
    # Estimate reasoning hops from question structure
    hop_indicators = [
        "who", "what", "where", "when", "which", "how",
        "and", "also", "both", "same", "different",
    ]
    hop_count = sum(1 for w in words if w.lower().strip(string.punctuation) in hop_indicators)
    estimated_hops = min(max(1, hop_count // 2), 4)
    
    # Check for comparison questions
    comparison_words = ["same", "different", "more", "less", "both", "compare", "versus", "vs"]
    has_comparison = any(w.lower().strip(string.punctuation) in comparison_words for w in words)
    
    # Check for temporal reasoning
    temporal_words = ["before", "after", "during", "when", "year", "date", "born", "died"]
    has_temporal = any(w.lower().strip(string.punctuation) in temporal_words for w in words)
    
    # Composite complexity score (0-1)
    complexity_score = min(1.0, (
        (word_count / 50) * 0.3 +
        (entity_count / 5) * 0.3 +
        (estimated_hops / 4) * 0.2 +
        (0.1 if has_comparison else 0.0) +
        (0.1 if has_temporal else 0.0)
    ))
    
    return {
        "word_count": word_count,
        "entity_count": entity_count,
        "estimated_hops": estimated_hops,
        "has_comparison": has_comparison,
        "has_temporal": has_temporal,
        "complexity_score": complexity_score,
    }


def extract_confidence(response_text: str) -> float:
    """
    Extract a confidence score [0, 1] from an agent's response text.
    Uses linguistic cues to estimate how confident the agent is.
    
    Returns:
        float in [0, 1] — higher means more confident.
    """
    if not response_text:
        return 0.5
    
    text = response_text.lower()
    
    # High confidence signals
    high_signals = [
        "i am confident", "clearly", "definitely", "without doubt",
        "the answer is", "final answer:", "correct answer",
        "fully supported", "accurately", "confirms",
        "correctly identifies", "is correct",
    ]
    
    # Low confidence signals
    low_signals = [
        "i'm not sure", "uncertain", "might be", "possibly",
        "it's unclear", "cannot determine", "insufficient",
        "not enough information", "ambiguous", "could be",
        "hard to tell", "unable to", "no information",
        "does not provide", "not mentioned",
    ]
    
    high_count = sum(1 for s in high_signals if s in text)
    low_count = sum(1 for s in low_signals if s in text)
    
    if high_count > 0 and low_count == 0:
        return 0.9
    elif low_count > 0 and high_count == 0:
        return 0.3
    elif high_count > low_count:
        return 0.7
    elif low_count > high_count:
        return 0.4
    else:
        return 0.6  # neutral


def confidence_from_logprob(mean_logprob: float | None) -> float | None:
    """Calibrated confidence in [0,1] from a response's mean per-token logprob.

    confidence = exp(mean_logprob) = the GEOMETRIC-MEAN token probability of the
    generated answer -- a real, model-derived uncertainty estimate (unlike the
    lexical `extract_confidence` keyword heuristic, which validates at AUC~0.56).
    Returns None when no logprob is available (caller falls back to lexical).
    """
    if mean_logprob is None:
        return None
    import math
    return max(0.0, min(1.0, math.exp(mean_logprob)))


ROLE_ORDER = ("analyzer", "solver", "verifier")

# Canonical, ORDERED feature names for the learned router. Keeping this list in
# one place guarantees training and inference build identical feature vectors.
FEATURE_NAMES = (
    "word_count",
    "entity_count",
    "estimated_hops",
    "has_comparison",
    "has_temporal",
    "complexity_score",
    "context_complexity",
    "role_analyzer",
    "role_solver",
    "role_verifier",
)


def router_feature_vector(question: str, agent_role: str, context=None) -> list[float]:
    """Build the ordered numeric feature vector consumed by the learned router.

    The order matches FEATURE_NAMES exactly. Used by both
    src/router/training_data.py (training) and LearnedRouter (inference).
    """
    f = extract_question_features(question)
    ctx_complexity = extract_context_complexity(context)
    role = (agent_role or "").lower()
    return [
        float(f["word_count"]),
        float(f["entity_count"]),
        float(f["estimated_hops"]),
        1.0 if f["has_comparison"] else 0.0,
        1.0 if f["has_temporal"] else 0.0,
        float(f["complexity_score"]),
        float(ctx_complexity),
        1.0 if role == "analyzer" else 0.0,
        1.0 if role == "solver" else 0.0,
        1.0 if role == "verifier" else 0.0,
    ]


def extract_context_complexity(context: dict | None) -> float:
    """
    Estimate context complexity from the supporting documents.
    
    Returns:
        float in [0, 1] — higher means more complex context.
    """
    if not context:
        return 0.0
    
    # Count total context tokens
    total_text = ""
    if isinstance(context, dict):
        for v in context.values():
            if isinstance(v, str):
                total_text += v
            elif isinstance(v, list):
                total_text += " ".join(str(item) for item in v)
    elif isinstance(context, str):
        total_text = context
    
    word_count = len(total_text.split())
    
    # Normalize: 0-500 words = low, 500-2000 = medium, 2000+ = high
    return min(1.0, word_count / 2000)
