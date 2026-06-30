You are reviewing a pull request that adds OpenTelemetry distributed tracing to QualOps, a multi-stage AI code review pipeline. The PR touches 17 files (+1647/-254 lines) across:
- New observability module: src/observability/ (tracing.ts, attributes.ts, pr-metadata.ts, index.ts)
- CLI orchestration: src/cli/commands/all-command.ts
- Review pipeline: src/stages/review/processors/pipeline-executor.ts, file-reviewer.ts
- Agentic review: src/stages/review/agentic/agentic-executor.ts
- Eval runner: evals/src/run-eval.js, evals/src/qualops-bridge/provider.ts
- Tests: tests/unit/observability/*.spec.ts
- Dependencies: package.json

For each issue found, report:
- **File & line(s)**
- **Criterion** — which checklist item applies (use the § number)
- **Severity** — critical / high / medium / low / info
- **Confidence** — 1-10 (how sure are you this is a real problem?)
- **Description** — what's wrong and why it matters
- **Suggestion** — how to fix it

Be skeptical. Only report issues you're confident about (confidence >= 7). Do not report style/formatting nits.
