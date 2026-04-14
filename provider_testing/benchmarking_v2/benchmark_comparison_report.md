# Master Model Benchmark Comparison Report — Dummy App 2

**Date:** 2026-04-13 22:53:07Z  
**PDF:** Dummy App (2) — Ananya Kapoor

| # | Model | Status | Call 1 (s) | Call 2 (s) | Signals | Themes | Q-Groups | Error |
|---|-------|--------|------------|------------|---------|--------|----------|-------|
| 1 | `google/gemini-2.5-flash-lite` | PASSED | 6.72 | 2.89 | 5 | 2 | 2 |  |
| 2 | `openai/gpt-4o-mini` | PASSED | 18.01 | 7.96 | 4 | 2 | 2 |  |
| 3 | `openai/gpt-5.4-nano` | PASSED | 9.92 | 4.42 | 5 | 2 | 2 |  |
| 4 | `anthropic/claude-3-haiku` | CRASH | 13.43 | 0.0 | 0 | 0 | 0 | Expecting ',' delimiter: line 17 column 69 (char 1285) |
| 5 | `google/gemini-3.1-flash-lite-preview` | PASSED | 7.52 | 4.75 | 4 | 2 | 2 |  |
| 6 | `openai/gpt-4.1-mini` | PASSED | 54.02 | 8.46 | 5 | 3 | 3 |  |
| 7 | `google/gemini-2.5-flash` | CRASH | 20.29 | 0.0 | 0 | 0 | 0 | Expecting value: line 1 column 1 (char 0) |
| 8 | `google/gemini-3-flash-preview` | CRASH | 25.66 | 0.0 | 0 | 0 | 0 | Expecting ',' delimiter: line 46 column 6 (char 3731) |
| 9 | `anthropic/claude-3.5-haiku` | GUARD_1_FAILED | 23.0 | 0.0 | 4 | 3 | 0 | fragment_entity_mismatch |
| 10 | `openai/gpt-5.4-mini` | PASSED | 11.84 | 6.23 | 6 | 2 | 2 |  |
| 11 | `anthropic/claude-haiku-4.5` | PASSED | 22.17 | 9.74 | 5 | 3 | 3 |  |
| 12 | `openai/gpt-5` | CALL_1_API_ERROR | 185.03 | 0.0 | 0 | 0 | 0 | AICredits budget has been exhausted for this key. |
| 13 | `google/gemini-2.5-pro` | CALL_1_API_ERROR | 1.02 | 0.0 | 0 | 0 | 0 | AICredits budget has been exhausted for this key. |
| 14 | `openai/gpt-4o` | CALL_1_API_ERROR | 0.62 | 0.0 | 0 | 0 | 0 | AICredits budget has been exhausted for this key. |