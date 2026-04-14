# Comparative Model Reliability Test Report

**Date:** 2026-04-13 20:49:37Z
**Target Applicant:** `0ec647d9-1b79-43b9-9c12-4bd1c92fc075`

| Provider | Model | Iteration | Status | Latency | Violation/Repair |
|---|---|---|---|---|---|
| google | `google/gemini-2.5-flash-lite` | 1 | PASSED | 6.55s |  |
| openai | `openai/gpt-4o-mini` | 1 | PASSED | 59.45s |  |
| openai | `openai/gpt-4o-mini` | 2 | PASSED | 18.21s |  |
| deepseek | `deepseek/deepseek-r1` | 1 | PASSED | 151.93s |  |
| deepseek | `deepseek/deepseek-r1` | 2 | GUARD_FAILED | 270.12s | structure_error |
| deepseek | `deepseek/deepseek-r1` | 3 | LLM_ERROR | 369.79s | AICredits upstream error (502). |