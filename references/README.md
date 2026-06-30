# References (frozen snapshots)

These are **verbatim, frozen copies** of external resources the project depends on, captured so the
project stays self-contained and results remain reproducible even if the source files change.

**Do not edit these snapshots.** If a source meaningfully changes and the project needs the newer
version, re-snapshot it (re-copy from the source) rather than hand-editing the copy here.

## Provenance

| Snapshot                             | Source                                                                       | Why kept                                                                                  |
| ------------------------------------ | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| prior-experiment/README.md           | ~/.claude/memory/experiments/single-vs-multi-pass-review/README.md           | Methodology + the 4-pass thematic grouping this project generalizes.                      |
| prior-experiment/analysis/summary.md | ~/.claude/memory/experiments/single-vs-multi-pass-review/analysis/summary.md | Headline result: multi-pass recall 41% → 91% at 3.4× token cost; documents reinforcement. |
| prior-experiment/learnings-entry.md  | ~/.claude/memory/experiments/single-vs-multi-pass-review/learnings-entry.md  | "For future experiments" list — effectively this project's backlog (N≥3 etc.).            |
| prior-experiment/prompts/preamble.md | ~/.claude/memory/experiments/single-vs-multi-pass-review/prompts/preamble.md | Reusable frozen preamble pattern for the run scaffolding.                                 |
| checklist.md                         | ~/.claude/memory/code_review_checklist.md                                    | The master taxonomy (§1–18, ~130 items) — the frozen item universe for group selection.   |

## Not snapshotted (cited by path only)

The qualops eval patterns (`evals/src/scorers/crb-pairwise.ts`, `evals/src/run-eval.ts`,
`evals/src/recall-report.ts`, `src/ai/shared/schemas/review-issue.ts`, and the agentic subagent
definitions) under `~/code/eggai/qualops` are **referenced as patterns, not copied** —
per `docs/references.md` ("cite the pattern, do not copy the repo"). They are consulted when the
harness is built (a later, separately-approved step).

See `docs/references.md` for the full rationale behind each entry.
