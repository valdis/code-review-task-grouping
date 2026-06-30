# References

All paths verified to exist at project-creation time. Where this project needs a *frozen* version (so results
remain reproducible if the source changes), copy a snapshot into the project rather than relying on the live
file — noted per entry.

## Prior art (the experiment this project generalizes)

### `~/.claude/memory/experiments/single-vs-multi-pass-review/`
The direct predecessor: one hand-picked 4-pass grouping tested on a single PR (QualOps OpenTelemetry
instrumentation, 17 files, +1647/−254).

- `README.md` — methodology and the **4-pass thematic grouping** (Correctness & Safety / Design & Architecture
  / Type Safety, Concurrency & Contracts / Testing & Observability), plus the measurement table (recall,
  precision, depth, cost). Note its prompt structure: `preamble.md` + condition-specific checklist subset +
  the **same frozen diff** — the confound control this project formalizes.
- `analysis/summary.md` — the headline result: multi-pass found **2.4× more true positives** (20 vs 9),
  recall **41% → 91%**, precision 82% → 77%, at **3.4× token cost**. Confirms the *attention-budget
  hypothesis* and documents **reinforcement** (Pass 3 was most productive because §18.4.5 + §13 + §18.4 paired
  to direct attention at resource lifecycle). This is the effect Phase 1 re-tests under controlled conditions.
- `learnings-entry.md` — condensed results + the **"For future experiments"** list (run N≥3 for variance,
  harder PRs, try a 2-pass variant, test pass-ordering effects). That list is effectively this project's
  backlog; Phase 1 adopts the N≥3 point directly.
- `prompts/preamble.md` — a reusable frozen preamble pattern to mirror for our run scaffolding.

> **Snapshot:** copy this directory's `README.md`, `analysis/summary.md`, `learnings-entry.md`, and
> `prompts/preamble.md` into `references/prior-experiment/` so the project is self-contained.

## The checklist (the item universe)

### `~/.claude/memory/code_review_checklist.md`
The master taxonomy: §1–18, ~130 numbered items. §16 Code Smells (Bloaters, OO Abusers, Change Preventers,
Dispensables, Couplers, OO/General/Architectural anti-patterns) and §17 Good Practices (SOLID, GoF, Beck
DRY/YAGNI, Clean/Hexagonal architecture, function/testing/scripting practices) are the bloat-relevant core. The
**item universe** for grouping; each ID is a unit.

> **Snapshot:** copy as `references/checklist.md` — Phase-1 group selection must reference *frozen* item IDs.

### `~/.claude/memory/code_review_heuristics.md`
Narrative review heuristics (orchestrators vs leaf units, fallback semantics, composition-over-configuration
worked example). Complements specific checklist items; useful when writing per-item injection rationales.

### `~/.claude/memory/code_review_learnings.md`
Running log of which criteria applied in which contexts and which were accepted/rejected. Contains the
field note that *grouping related criteria amplifies each item's effectiveness* — the qualitative seed of this
project. Phase 1's `learnings-entry.md` deliverable is written to append here.

## Reusable eval patterns (from qualops — cite the pattern, do not copy the repo)

Located in `~/code/eggai/qualops`. These are proven approaches to reference when the harness is
built (a later step).

- `evals/src/scorers/crb-pairwise.ts` — **LLM-judge semantic matcher**. For each (reference, candidate) pair,
  an LLM judge returns `{reasoning, match, confidence}`; aggregated into `crb_precision = tp/(tp+fp)`,
  `crb_recall = tp/(tp+fn)`, `crb_f1`. Matches **ignoring exact line numbers** — exactly the matcher our
  multi-tag scorer needs (credit a report if it matches any planted item ID).
- `evals/src/run-eval.ts` + `evals/qualopsrc/{fast,security,sonnet-agentic,thorough}.json` — **preset-driven
  A/B configuration**: a run is a preset × model × mode, and experiments are named
  `{preset}:{model}:{mode}:{timestamp}`. Pattern for expressing our solo-vs-group conditions as named,
  comparable runs.
- `evals/src/recall-report.ts` — **per-reference match-rate aggregation across runs** (always-detected /
  never-detected / flaky). Directly applicable to our N≥3 variance reporting and per-item detection frequency.
- `src/ai/shared/schemas/review-issue.ts` — the `ReviewIssue` schema (`type ∈ {security, performance, bug,
  maintainability}`, `severity`, `confidence`, `location`, …). A reference shape for what a "reported finding"
  looks like.
- `src/stages/review/agentic/subagents/definitions.ts` (+ `src/config/agents/*.md`) — the existing
  `security-analyzer` / `dependency-tracer` / `breaking-change-detector` / `pattern-validator` agents are an
  *existing grouping of review concerns into agents* — a baseline grouping worth comparing against once Phase 2
  produces data-driven groups.

## The thing that prompted this project

`~/.claude/skills/code-review/SKILL.md` — the skill whose hand-authored agent grouping (Agent 5: SRP / nesting
/ long-functions / flag-args; Agent 6: duplication / structure) covers only a slice of the checklist and was
the motivating gap. The end consumer of a validated grouping: a better-justified agent partition here.
