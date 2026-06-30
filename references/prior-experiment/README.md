# Experiment: Single-Pass vs Multi-Pass Code Review

Date: 2026-04-15
Model: claude-sonnet-4-5-20250929 (temperature 0)
Target: eggai-tech/qualops, branch observability-instrumentation
Commit: f528309395403b7ed54ff3e224396facd33a6722
Merge base: e80c2fffef37442ac2d6ed934f837093879f0981
Checklist: ~/.claude/memory/code_review_checklist.md (snapshot in checklist/)
Heuristics: ~/.claude/memory/code_review_heuristics.md (snapshot in checklist/)

## Summary

Compares finding recall, precision, and depth between:
- **Condition A (single-pass):** One review call with the full 18-section checklist
- **Condition B (multi-pass):** Four focused calls, each with a thematic subset of the checklist

Target PR: adds OpenTelemetry distributed tracing to QualOps. 17 files, +1647/-254 lines across:
- New observability module: src/observability/ (tracing.ts, attributes.ts, pr-metadata.ts, index.ts)
- CLI orchestration: src/cli/commands/all-command.ts
- Review pipeline: src/stages/review/processors/pipeline-executor.ts, file-reviewer.ts
- Agentic review: src/stages/review/agentic/agentic-executor.ts
- Eval runner: evals/src/run-eval.js, evals/src/qualops-bridge/provider.ts
- Tests: tests/unit/observability/*.spec.ts
- Dependencies: package.json

## Reproduce

1. `cd repo && git checkout experiment/otel-observability-2026-04-15`
2. `git diff e80c2ff..f528309 -- . ':(exclude)package-lock.json' > ../input/diff.patch`
3. Run each prompt in `prompts/` against the diff with the specified model at temperature 0
4. Each prompt = `preamble.md` + condition-specific checklist sections + diff

## Directory Layout

```
├── README.md                    ← this file
├── repo/                        ← clone with annotated tag at experiment commit
├── input/
│   └── diff.patch               ← frozen diff (1561 lines)
├── checklist/
│   ├── full-checklist.md        ← snapshot of code_review_checklist.md
│   └── heuristics.md            ← snapshot of code_review_heuristics.md
├── prompts/
│   ├── preamble.md              ← common preamble for all conditions
│   ├── condition-a-single.md    ← full prompt for single-pass
│   ├── condition-b-pass1.md     ← Correctness & Safety
│   ├── condition-b-pass2.md     ← Design & Architecture
│   ├── condition-b-pass3.md     ← Type Safety, Concurrency & Contracts
│   └── condition-b-pass4.md     ← Testing & Observability
├── results/
│   ├── condition-a-single.md    ← raw LLM output
│   ├── condition-b-pass1.md
│   ├── condition-b-pass2.md
│   ├── condition-b-pass3.md
│   ├── condition-b-pass4.md
│   └── condition-b-merged.md    ← deduplicated union
├── analysis/
│   ├── comparison-table.md
│   ├── issue-validation.md
│   └── summary.md
└── learnings-entry.md           ← ready to append to code_review_learnings.md
```

## Checklist Grouping (Multi-Pass)

### Pass 1: Correctness & Safety
§1, §6, §10, §16.4, §16.7, §18.6

### Pass 2: Design & Architecture
§3, §4, §15, §16.1, §16.3, §16.5, §16.6, §17.1, §17.2, §17.3, §17.4

### Pass 3: Type Safety, Concurrency & Contracts
§11, §12, §13, §14, §16.2, §16.8, §17.6, §18.2, §18.3, §18.4

### Pass 4: Testing & Observability
§2, §5, §8, §9, §17.5, §18.1, §18.5

## Measurement

| Metric      | How measured                                                              |
| ----------- | ------------------------------------------------------------------------- |
| Recall      | Unique valid issues found / total valid issues (union of both conditions) |
| Precision   | Valid issues / total issues reported                                      |
| Depth       | Average severity of valid issues; presence of cross-cutting findings      |
| Specificity | Do issues reference exact lines and have actionable suggestions?          |
| Cost        | Total tokens consumed (input + output) per condition                      |
