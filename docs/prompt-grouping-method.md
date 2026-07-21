# Method — From the Static Gap to Grouped Agent Prompts

This is a **method spec**, not an experiment writeup. It describes the research *process* that turns the
tool-capabilities matrix into a small set of **grouped agent prompts** for the `code-review` skill. It
produces **no groups and no prompts itself** — those are the output of *running* this method later.

## 1. Purpose & scope

**Goal.** Produce a small set of agent prompts, each covering a *group* of checklist items that (a) static
tools miss or only partially catch, and (b) share enough symptom similarity that **one LLM pass should find
them together**. Grouping — rather than one prompt per checklist item — is the whole point: it keeps the
number of review passes small while still covering the checklist, on the premise that **similar symptoms →
same scan strategy → findable in the same run**. That premise is exactly the Phase-1 hypothesis
([`phase-1-design.md`](phase-1-design.md) line 5 and §1, "shared scan strategy").

**Where this sits relative to the other docs** (it *uses* them, it does not restate them):

| Concern                              | Owned by                                                                                                                                                             |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| What static tools do / don't catch   | [issue-detection-tool-capabilities-matrix.md](issue-detection-tool-capabilities-matrix.md)                                                                           |
| The reinforcement-lift metric        | [methodology.md](methodology.md) §1                                                                                                                                  |
| Does symptom-locality predict lift?  | [phase-1-design.md](phase-1-design.md)                                                                                                                               |
| Discovering good groups (the search) | [escalation-phase-2.md](escalation-phase-2.md)                                                                                                                       |
| This doc                             | The pipeline that scopes the pool to the static gap, seeds candidate groups, delegates validation to the Phase-2 search, and synthesizes prompts from the survivors. |

The pipeline, end to end:

```
static gap (matrix)  →  similarity-seeded candidate groups  →  lift-validated groups  →  agent prompts
   §2                         §3                                  §4 (Phase 2)              §5
```

## 2. Step 1 — Define the pool (the static gap)

The pool is the set of checklist items **worth spending an LLM pass on** — those a linter does *not* already
solve. It is derived mechanically from the matrix source of truth,
[`data/issue-detection-tool-capabilities-matrix.json`](../data/issue-detection-tool-capabilities-matrix.json).

**Selection predicate (reproducible).** For each item, look at its `coverage` map (tool id → code, where a
missing tool defaults to `none`). Using the matrix scale
([`issue-detection-tool-capabilities-matrix.md`](issue-detection-tool-capabilities-matrix.md) §Scale:
`complete` / `partial` / `none` / `na` / `idk`):

- **Include** an item in the pool if **any** applicable tool cell is `none` or `partial` — i.e. no tool
  fully solves it in at least one language of interest.
- **Exclude** an item only if it is `complete` across every applicable tool (a linter already catches it
  everywhere; running the linter is cheaper and more reliable than an LLM pass — the *experiment-validity*
  argument, [`issue-detection-tool-capabilities-matrix.md`](issue-detection-tool-capabilities-matrix.md)
  "Why this exists" line 6).
- `na` cells are ignored for inclusion (the construct doesn't exist in that language); `idk` cells should
  not exist once research is complete — if any remain, resolve them before freezing the pool.

Concretely: `in_pool(item) ⇔ ∃ tool with coverage[tool] ∈ {none, partial}`.

**Two sub-tiers** (record the tier per item; it later informs how emphatic the prompt should be):

- **`none`-dominant** — no off-the-shelf detector in any tool; **LLM/human-only**. The highest-value LLM
  targets (the ~23 items where *every* tool is `none` are the purest of these).
- **`partial`-dominant** — a leaky linter exists; the LLM's job is to **backstop** the false negatives the
  linter misses, not to find the item from scratch.

**Validation scope vs shipping scope.** The *shipped* prompts may cover items that cannot be planted in one
tidy commit. The *validated* subset is narrower: only `injectable: yes|partial` items
([`item-universe.md`](../item-universe.md)) can be measured in-corpus. So the pool carries an
`injectable` flag; lift measurement (§4) runs only on the injectable part, and coverage of the
non-injectable remainder is argued by symptom-family analogy, not measured. Record this split explicitly so
the evidence basis of each shipped group is auditable.

**Output of this step:** a pool artifact listing each in-pool item with `{id, tier, injectable, families}`
— the input universe for §3. (Deferred: produced when the method is run, not in this doc.)

## 3. Step 2 — Similarity signal (seed candidate groups)

The Phase-2 search (§4) is the ground truth for grouping, but it costs review runs. To spend that budget
well, **seed** it with cheap candidate groups drawn from priors already in the repo — hypotheses about which
items share a scan strategy. "Similar symptoms → same run" is operationalized from three existing signals:

1. **Symptom families** — the 25 families in the matrix `families` (F1–F4 + the `S*` section families).
   Items in the same family are a first-cut candidate group.
2. **Shared "why static misses it" rationale** — the researched per-item rationales
   ([`data/tool-capability-research.jsonl`](../data/tool-capability-research.jsonl) and the generated
   per-item notes). Two items missed by linters *for the same reason* (e.g. "requires tracing a value across
   calls", "requires whole-file structural judgement") likely share a reviewer scan strategy even if they
   sit in different checklist sections. This is the signal most specific to the *LLM's* job, so weight it.
3. **Shared scan strategy** — the explicit framing from [`phase-1-design.md`](phase-1-design.md) §1:
   *trace-a-value-to-a-sink* (data-flow), *scan-function-shape* (structural), *spot-redundancy* (bloat).
   Every candidate group should name the single scan strategy that makes it one coherent pass.

**Seeding procedure.** Cluster the pool by the signals above (family + rationale-kind + nameable scan
strategy), then cut into candidate groups of **comparable size (~4–5 items)** per the Phase-1 sizing
convention. Each candidate group is recorded with its **hypothesized shared scan strategy** — the sentence
a reviewer would use to hunt all its items at once.

**These are hypotheses, not answers.** The candidate groups are explicitly provisional; §4 keeps, merges,
or splits them by measured lift. Do not synthesize prompts from unvalidated seeds.

**Output of this step:** a candidate-group artifact: `group → {items[], scan_strategy, tier_mix}`.

## 4. Step 3 — Validate & refine via lift (delegate to Phase 2)

Candidate groups are handed to the Phase-2 group search
([`escalation-phase-2.md`](escalation-phase-2.md)) as its **starting partition / seeds**, and kept, merged,
or split by measured **reinforcement lift** ([`methodology.md`](methodology.md) §1, estimated over N ≥ 3
runs). This doc does **not** restate the Phase-2 mechanics (greedy baseline → screening design / adaptive
search / community detection, and the decision rule) — it only states the **contract**:

- **Inputs:** the static-gap pool (§2, injectable subset for measurement) and the candidate groups (§3).
- **Objective:** maximize per-group reinforcement lift / recall at acceptable run cost, capturing
  higher-order (3+-way) reinforcement, treating the model as a black box.
- **Constraint carried in from here:** the pool is *scoped to the static gap* — the search ranges over
  gap items only, not the whole injectable universe.
- **Exit condition:** a set of **validated groups**, each with a measured lift ≥ its members' solo baselines
  (positive reinforcement) and a retained, now-confirmed shared scan strategy.

Gate: Phase 2 runs only if Phase 1 passes its go/no-go
([`phase-1-design.md`](phase-1-design.md) §4). If Phase 1 fails (symptom-locality does *not* predict lift),
this whole method is built on a false premise and must be reconsidered before any prompts are shipped.

## 5. Step 4 — Synthesize the agent prompt from a validated group

Each validated group becomes **one agent prompt**. The group's items supply the *what to look for*; the
shared scan strategy supplies the *how to look*. Structure (mirroring the frozen preamble pattern in
[`references/prior-experiment/prompts/preamble.md`](../references/prior-experiment/prompts/preamble.md)):

1. **Preamble / role** — a frozen, group-agnostic header (task framing, the diff under review, "be
   skeptical", confidence threshold). Held constant across all agent prompts so differences are attributable
   to the item set, not the scaffolding.
2. **Scan-strategy framing** — the group's one shared strategy, stated up front as the connective tissue
   ("trace each externally-derived value to where it is used", etc.). This is what makes the group *one
   coherent pass* rather than a checklist stapled together.
3. **Per-item injection** — for each item in the group: its checklist text (the criterion) **plus** its
   researched "what static misses" rationale as the concrete *what to look for*. For `partial`-tier items,
   phrase the instruction as *backstop the linter's false negatives*; for `none`-tier items, phrase it as
   *the primary detector*.
4. **Shared output schema** — one report shape across all agents (file/line, criterion §id, severity,
   confidence, description, suggestion), so downstream aggregation and scoring are uniform.

**End consumer.** These prompts are the better-justified agent partition for the `code-review` skill — the
motivating gap of this whole project (`~/.claude/skills/code-review/SKILL.md`, cited via
[`references.md`](references.md)). A validated, coverage-complete set of grouped prompts replaces the
skill's hand-authored Agent-5/Agent-6 grouping.

## 6. Outputs & open questions

**Artifacts a *run* of this method produces** (none created by this doc):

| Artifact         | From | Contents                                                             |
| ---------------- | ---- | -------------------------------------------------------------------- |
| static-gap pool  | §2   | in-pool items with {tier, injectable, families}                      |
| candidate groups | §3   | group → {items[], scan_strategy, tier_mix} (hypotheses)              |
| validated groups | §4   | Phase-2 survivors with measured lift + confirmed scan strategy       |
| agent prompts    | §5   | one prompt per validated group, frozen preamble + per-item injection |

**Open questions inherited from Phase 2** ([`escalation-phase-2.md`](escalation-phase-2.md) "Deferred
questions"):

- **Group size / number of passes (`k`)** — is there an optimal group size? Measured, not assumed.
- **Cross-model stability** — do the validated groups (and thus the prompts) transfer across models, or are
  they model-specific? A real risk given the black-box, behavioral basis.
- **Pass ordering** — does a group find more when run later in a multi-pass sequence? Held out of Phase 1.
- **Non-injectable coverage** — how confidently can family-analogy justify shipping prompts for items that
  were never measured in-corpus?
