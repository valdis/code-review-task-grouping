# Density Calibration (stub)

Sets `lines_per_issue` — the sparse, realistic issue density a composed case targets
(`docs/corpus-spec.md` §3–4, `methodology.md` §4). **A knob, not a constant** — record the value used
and its basis.

## Calibrated target

```
lines_per_issue: 80
tolerance: 0.25
```

**Basis:** empirical survey of the cal.com CRB cases (below) gives a per-case **median of ~72** and
**mean of ~81** added-lines-per-golden-issue; the pooled ratio (total added / total issues) is **82**.
The pre-existing `80` default (`corpus-spec.md` §3) sits between the median and mean and inside the
observed spread, so it is **kept as-is** — now evidence-backed rather than arbitrary. Deliberately sparse
to avoid the "everything here is a bug" shortcut that destroys precision measurement.

## Calibration survey (computed 2026-07-21)

Surveyed the 10 cal.com **CRB cases** at
`~/code/eggai/qualops/evals/datasets/crb/crb-cal_dot_com-*` (real reviewer-flagged issues with golden
comments in each case's `slice.json`: `diff` + `expected[]`). Per case:
`added_diff_lines / len(expected)`, where added lines are unified-diff `+` lines excluding `+++` file
headers.

| Case | Added lines | Golden issues | Lines/issue |
| ---- | ----------- | ------------- | ----------- |
| 1    | 82          | 2             | 41.0        |
| 2    | 280         | 4             | 70.0        |
| 3    | 368         | 5             | 73.6        |
| 4    | 114         | 2             | 57.0        |
| 5    | 241         | 2             | 120.5       |
| 6    | 111         | 2             | 55.5        |
| 7    | 375         | 5             | 75.0        |
| 8    | 38          | 2             | 19.0        |
| 9    | 555         | 5             | 111.0       |
| 10   | 379         | 2             | 189.5       |

**Aggregates:** 10 cases, 2543 added lines, 31 golden issues. Per-case median **71.8**, mean **81.2**;
pooled **82.0**. Range 19–190 (real PRs vary widely — case 8 is dense, case 10 sparse).

> Status: **computed.** `lines_per_issue: 80` confirmed against the empirical distribution.
