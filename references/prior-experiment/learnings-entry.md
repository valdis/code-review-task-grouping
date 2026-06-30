## 2026-04-15 — Single-Pass vs Multi-Pass Review Experiment

**PR:** QualOps `observability-instrumentation` (OpenTelemetry tracing, 17 files, +1647/-254)
**Model:** claude-opus-4-6 (temperature 0)
**Full artifacts:** `~/.claude/memory/experiments/single-vs-multi-pass-review/`

### Experiment Design
- **Condition A (single-pass):** 1 LLM call with full 18-section checklist + diff
- **Condition B (multi-pass):** 4 focused calls, each with a thematic checklist subset + same diff
  - Pass 1: Correctness & Safety (§1, §6, §10, §16.4, §16.7, §18.6)
  - Pass 2: Design & Architecture (§3, §4, §15, §16.1, §16.3, §16.5, §16.6, §17.1-§17.4)
  - Pass 3: Type Safety, Concurrency & Contracts (§11-§14, §16.2, §16.8, §17.6, §18.2-§18.4)
  - Pass 4: Testing & Observability (§2, §5, §8, §9, §17.5, §18.1, §18.5)

### Results

| Metric               | Single-Pass | Multi-Pass            |
| -------------------- | ----------- | --------------------- |
| Total issues         | 11          | 26 (deduplicated)     |
| True Positives       | 9           | 20                    |
| Precision            | 82%         | 77%                   |
| Recall               | 41%         | 91%                   |
| Token cost           | ~73K        | ~250K (3.4x)          |
| High-severity unique | 0           | 1 (§18.4.5 violation) |
| Real bugs            | 1           | 2                     |

### Key Learnings

1. **Multi-pass finds 2.4x more TPs at 3.4x cost.** The ROI is strongly positive for critical PRs.

2. **Attention budget hypothesis confirmed.** Focused passes go deeper. Pass 3 found the global TracerProvider ownership violation (§18.4.5) and a span leak bug — both invisible to single-pass. Pass 4 identified systemic test coverage gaps missed entirely by single-pass.

3. **Single-pass is a strict subset.** Every issue found by single-pass was also found by multi-pass. Single-pass catches the "obvious" issues.

4. **Pass grouping matters.** Pass 3 was most productive because related concerns (§18.4.5 resource ownership + §13 Brittle Patterns + §18.4 Concurrency) reinforced each other, directing attention to span lifecycle issues.

5. **Cross-cutting issues survive splitting.** Each pass received the full diff, so cross-file patterns (like attribute duplication in run-eval.js) were caught by 4 different passes.

6. **Deduplication is essential.** 31 raw → 26 unique. Without dedup, multi-pass output is noisy.

7. **§18.4.5 is high-value.** The most impactful finding in the entire experiment came from this criterion. It should always be included in reviews of infrastructure/observability code.

8. **Testing criteria need focused attention.** §2/§8 are systematically overlooked when mixed with 15+ other criteria. Giving them a dedicated pass reveals coverage gaps.

### Recommendations

- **Default:** Multi-pass for production/infrastructure PRs; single-pass for routine changes
- **Always include:** "Type Safety & Contracts" pass (most productive) and "Testing" pass (catches systemic gaps)
- **4 passes is about right** — each found unique issues; fewer would lose depth, more would hit diminishing returns
- **Future:** Run N=3+ per condition to measure variance; try 2-pass variant to find the cost/benefit sweet spot
