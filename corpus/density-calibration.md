# Density Calibration (stub)

Sets `lines_per_issue` — the sparse, realistic issue density a composed case targets
(`docs/corpus-spec.md` §3–4, `methodology.md` §4). **A knob, not a constant** — record the value used
and its basis.

## Default target (until calibrated)

```
lines_per_issue: 80
tolerance: 0.25
```

From `corpus-spec.md` §3's default `case-spec`. Deliberately sparse to avoid the "everything here is a
bug" shortcut that destroys precision measurement.

## Calibration method (to run)

Survey the cal.com **CRB cases** at
`~/code/eggai/qualops/evals/datasets/crb/crb-cal_dot_com-*` (10 cases, real reviewer-flagged
issues with golden comments). Compute, per case: `added_diff_lines / number_of_golden_issues`; take the
**median** across cases as the empirical `lines_per_issue`. Record the per-case numbers and the chosen
median here, then update the default above if it differs materially.

> Status: **not yet computed.** The 80-line default is in effect until this survey is run.
