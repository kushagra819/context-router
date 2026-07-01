# Risk Register

> Updated Stage 6 (2026-06-25). See [STAGE6_ENGINEERING_REPORT.md](STAGE6_ENGINEERING_REPORT.md).

| # | Risk | Severity | Likelihood | Mitigation | Status |
|---|------|:--------:|:----------:|-----------|:------:|
| R1 | **Tiers 3 & 4 shared GitHub token pool** — confounded quota/latency | 🟡 Medium | — | **RESOLVED:** Tier 3 → Llama-4-Maverick on Groq+OpenRouter; Tier 4 → OpenAI-direct/GitHub. Separate key pools. | ✅ Resolved |
| R2 | **HotpotQA T4 EM suspiciously low (37.5%)** | 🔴 High | — | **RESOLVED (mostly artifact):** Markdown-robust extractor + offline recompute → EM 41.5 / F1 62.9 (was 37.5/57.6). Residual gap is genuine (verbose verifier) and reported honestly; oracle labels now F1-aware. | ✅ Resolved |
| R3 | **MuSiQue T4 EM (25.6%) also low** | 🔴 High | — | Same fix as R2 → EM 31.0 / F1 49.7 (no longer the worst tier). | ✅ Resolved |
| R4 | **Sample size N=200 is small** for publication | 🟡 Medium | Low | Paired tests (McNemar/bootstrap) + Holm correction + paired-diff CIs implemented; MDE≈14pt documented. Consider N=500 for headline. | Accepted (mitigated) |
| R5 | **No automated tests** — silent metric breakage | 🟡 Medium | Medium | `tests/test_offline.py` (9 tests) + new metric/extractor/router tests added Stage 6. | ✅ Mitigated |
| R11 | **Confidence signal weak** (lexical; AUC≈0.56) | 🟡 Medium | — | **Mitigated:** pipeline now uses CALIBRATED logprob confidence (`exp(mean_logprob)`), lexical fallback; logs `confidence_source`/`mean_logprob`; auto-validated by `confidence_validation.py` on live runs. Still don't headline the cascade until calibrated AUC is in hand. | Mitigated (validate on runs) |
| R12 | **Tier-3 model changed (405B sunset → Llama-4-Maverick)** | 🟡 Medium | — | All Tier-3 cells re-run on the new model for consistency; single (provider,model) per results table; failover documented as robustness not substitution. | Managed |
| R13 | **Novelty narrowed** (per-agent routing pre-empted by MasRouter/DAAO/CHI'26) | 🔴 High | — | Reframe honestly: fixed typed pipeline + upstream-confidence handoff + rigorous study; add `query_level` head-to-head. See [RELATED_WORK.md](RELATED_WORK.md). | Accepted (disclosed) |
| R6 | **Router may not show improvement** on simple datasets (GSM8K) | 🟡 Medium | High | GSM8K has near-ceiling performance. Focus routing story on HotpotQA/MuSiQue. | Accepted |
| R7 | **Opus credit exhaustion** — session may terminate mid-work | 🟡 Medium | High | Save `SESSION_CONTEXT.md` and `10_SESSION_HANDOFF.md` before every major operation. | Managed |
| R8 | **max_tokens=2048 may truncate complex reasoning** | 🟢 Low | Low | Monitor for `[ERROR]` rows in CSVs. Current baselines show no truncation at output level. | Monitored |
| R9 | **`validation_problems` bug in resume path** — F1 stats wrong on resume | 🟢 Low | N/A | Fixed by re-running fresh (no `--resume`). Bug only affects stats JSON, not CSV. | Resolved |
| R10 | **Reviewer may challenge hypothetical costs** — all models are free | 🟢 Low | Medium | Clearly state costs are hypothetical based on published pricing. Focus on relative cost ratios. | Accepted |
