# Experiment Summary: Single-Pass vs Multi-Pass Code Review

## TL;DR

Multi-pass review found **2.4x more true positives** than single-pass (20 vs 9) at a cost of **3.4x more tokens**. The multi-pass approach discovered the two most impactful findings that single-pass missed entirely: a process-global resource ownership violation (§18.4.5) and a span leak bug in error handling. Single-pass had slightly higher precision (82% vs 77%) but dramatically lower recall (41% vs 91%).

## Key Findings

### 1. Multi-pass finds significantly more issues

- **Single-pass:** 11 issues, 9 TP (82% precision)
- **Multi-pass:** 26 issues, 20 TP (77% precision)
- **Recall:** A found 41% of all TPs; B found 91%

The multi-pass approach is not just finding more noise — it's finding more real issues. Precision dropped only 5 percentage points while recall more than doubled.

### 2. The attention budget hypothesis is confirmed

Each focused pass was able to go deeper on its assigned criteria. The most striking evidence:

- **Pass 3 (Type Safety & Contracts)** found the global TracerProvider ownership issue (B-15, high severity). This requires reasoning about §18.4.5 in the context of `NodeSDK.start()` registering a global singleton — a cross-reference between the OTel API design and the checklist criterion. When reviewing with the full 18-section checklist, the model spent its attention budget across all sections and missed this.

- **Pass 3** also found the span leak bug (B-20, medium) where `currentTurnSpan` is not ended in the catch block. This requires careful analysis of async control flow paths — again, the kind of deep focus that benefits from a narrower attention scope.

- **Pass 4 (Testing)** identified the systemic test coverage gap for instrumentation code (B-22, B-23). The single-pass review noted individual code issues but never stepped back to ask "is any of this new instrumentation code tested?"

### 3. Single-pass catches the "obvious" issues

Every issue found by single-pass was also found by multi-pass (or very close variants). The single-pass review is essentially a strict subset of multi-pass. The 2 issues unique to single-pass (A-9 hardcoded tag, A-10 concurrent context) were both rated "debatable" — they aren't missed by multi-pass so much as they're borderline non-issues.

### 4. Different passes have different productivity

| Pass                 | Unique TP Issues | Best Finding                      |
| -------------------- | ---------------- | --------------------------------- |
| Pass 1 (Correctness) | 2                | Magic string fallback             |
| Pass 2 (Design)      | 2                | Long method identification        |
| Pass 3 (Type Safety) | 4                | Global TracerProvider + span leak |
| Pass 4 (Testing)     | 3                | Systemic test coverage gap        |

Passes 3 and 4 were the most productive. Pass 3 found the deepest technical issues; Pass 4 identified the broadest coverage concern. Passes 1 and 2 had more overlap with what single-pass already catches.

### 5. Cross-cutting issues are NOT lost

A concern with multi-pass was that splitting context might prevent finding cross-file issues. This did not happen — each pass still received the full diff and could observe cross-file patterns. The duplication between `run-eval.js` and the observability module (B-2) was caught by 4 different passes.

### 6. Cost-effectiveness

Multi-pass costs ~3.4x more tokens. Is the marginal value worth it?

- **If you're reviewing for correctness:** Yes. The span leak bug (B-20) and global resource ownership issue (B-15) are the kind of findings that prevent production incidents.
- **If you're reviewing for style/design:** Diminishing returns. Most design issues were caught by both approaches.
- **Practical recommendation:** Use multi-pass for critical PRs (security-sensitive, infrastructure, observability) and single-pass for routine changes.

## What We Learned

### For the checklist itself
1. §18.4.5 (shared resource ownership) proved its worth — it's the single most impactful criterion applied in this experiment
2. Testing criteria (§2, §8) benefit enormously from focused attention — when mixed with 15+ other concerns, test coverage gaps are systematically overlooked
3. §13 (Brittle Patterns) combined with domain-specific knowledge about OTel span lifecycle produced the span leak finding

### For the review process
1. **Grouping matters.** Pass 3 (Type Safety & Contracts) was the most productive because §18.4.5 was paired with §13 (Brittle Patterns) and §18.4 (Concurrency), creating reinforcing attention on resource lifecycle issues
2. **4 passes is about right.** Each pass found unique issues. Fewer passes would lose the depth benefit; more would likely hit diminishing returns
3. **The deduplication step is essential.** 31 raw issues → 26 unique after dedup. Without dedup, the multi-pass output would be noisy

### For future experiments
1. Run each condition multiple times (N=3+) to measure variance — the nondeterminism study showed LLM reviews vary significantly between runs
2. Test with a harder PR (more subtle bugs, larger diff) to see if the recall gap widens further
3. Try a 2-pass variant (simpler grouping) to see if it captures most of the multi-pass benefit at lower cost
4. Consider whether pass ordering matters (does Pass 3 find more because it runs later?)

## Conclusion

Multi-pass review is the better approach for any PR where finding issues matters more than token cost. The 3.4x cost premium buys 2.4x more true positives, including the highest-severity findings. The attention budget hypothesis is strongly supported: when a model reviews with a focused subset of criteria, it goes deeper and finds issues that are invisible in a single broad pass.

**Recommended default:** Multi-pass for production/infrastructure PRs, single-pass for routine changes. Always include a "Type Safety & Contracts" pass (the most productive in this experiment) and a "Testing" pass (catches systemic coverage gaps).
