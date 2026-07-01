# ADR-002: Dataset Strategy

## Status: ACCEPTED

## Decision
Use three datasets — GSM8K, HotpotQA, and MuSiQue — to evaluate routing across a complexity gradient (single-hop → 2-hop → 2-4 hop).

## Alternatives Considered
1. **Single dataset only** — Rejected: Can't show generalization.
2. **Add MMLU/HumanEval** — Rejected: Different evaluation paradigm (multiple choice / code). Constants exist in config but no agents were built.
3. **Use only multi-hop datasets** — Rejected: GSM8K provides a "ceiling" case where routing has less room to help, which strengthens the story.

## Reason Chosen
The three datasets create a natural difficulty spectrum. GSM8K shows that even simple routing works at ceiling performance. HotpotQA and MuSiQue show where routing adds real value — on harder, multi-hop tasks where agent capability differences matter most.

## Impact
- 12 baseline experiments (4 tiers × 3 datasets)
- 200 problems each = 2,400 evaluations total
- Router must be evaluated on all 3 to demonstrate generalization
