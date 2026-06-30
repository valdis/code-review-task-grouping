# Phase 1 — Sanity / Manipulation-Check Design

Phase 1 answers one question before any expensive search is built:

> **Does symptom-locality predict reinforcement?** I.e. do checklist items with *similar symptoms found in the
> same places* reinforce each other (positive lift) more than a deliberately mismatched set of items?

If yes → the premise behind a grouping search is sound; escalate to Phase 2. If no → stop and rethink; do not
build the search on a false premise.

## 0. Prerequisite — bound the item universe

Before choosing groups, produce the **single-commit-injectable subset** of the checklist. Many items are
*evolutionary* properties that cannot be planted in one tidy commit:

- Plantable in one commit (examples): Dead Code (16.4.4), Magic Numbers (16.7.6), Duplicate Code (16.4.1),
  Flag Arguments (16.7.9), Error Hiding (16.7.7), Long Method (16.1.1), Deep Nesting (§15), missing input
  validation, strict-equality bugs (17.6.4), `this`-context loss (17.6.6).
- **Not** single-commit-plantable (examples): Large Class (16.1.2), Divergent Change (16.3.1), Shotgun Surgery
  (16.3.2), Speculative Generality (16.4.5 — needs an unused-over-time hook), Parallel Inheritance (16.3.3).

Deliverable: a table `item-universe.md` listing each checklist ID with `injectable: yes|no|partial` and a
one-line note. **Only `injectable: yes` items are eligible for Phase-1 groups.**

## 1. Choose the six groups

From the injectable universe, hand-pick six groups of **comparable size** (target ~4–5 items each):

### Cohesive groups (predicted positive lift)

Each cohesive group shares a **scan strategy** — the same way a reviewer would hunt for them, looking at the
same kind of evidence in the same places. Illustrative (final selection recorded in `groups.md`):

- **C1 — Data-flow / input-trust**: missing input validation, injection-shaped sinks, unsafe deserialization,
  trust-boundary crossings. *Found by:* tracing a value from entry point to sink.
- **C2 — Structure / shape smells**: Long Method (16.1.1), Deep Nesting (§15), Long Parameter List (16.1.4),
  Large-ish functions. *Found by:* scanning function shape/size/indentation — purely structural, no data-flow.
- **C3 — Dispensables / bloat**: Dead Code (16.4.4), Duplicate Code (16.4.1), Magic Numbers (16.7.6),
  Reinvent-the-Wheel (16.8.5). *Found by:* spotting redundancy and unused/hardcoded artifacts.

### Incoherent groups (predicted ≈0 / negative lift)

Each incoherent group deliberately mixes items whose **symptoms manifest differently and live in different
places**, so no shared scan strategy can reinforce them. Built by drawing one item from each cohesive symptom
family so the group has no internal coherence:

- **D1** = {one data-flow item, one structural item, one bloat item, one JS-footgun item}
- **D2** = a different such mix
- **D3** = a different such mix

> Construction rule: D-groups are *stratified mixes* of the same items used in C-groups, so the **item
> difficulty is held roughly constant** across cohesive and incoherent conditions — the contrast is the
> *grouping*, not the items. (Each item appears in both a C-group and a D-group where possible.)

## 2. Build the cases

Per [`methodology.md`](methodology.md) §2–4 and [`corpus-spec.md`](corpus-spec.md):

- A **case** is a fixed, themed, PR-sized diff at realistic density containing a **planted instance of every
  item** that appears in the C-group and D-group it will test, plus decoys/near-misses.
- Because items are shared between C- and D-groups, a small number of cases can cover all six groups. Each case
  is reused across every condition that needs its planted items.
- Record per case: the diff (`base..tip`), and a **ground-truth manifest** mapping each planted issue →
  {item IDs, file, line range, rationale}.

## 3. The run matrix

For each item `i` in the universe under test, and each group `G ∈ {C1,C2,C3,D1,D2,D3}` containing `i`, against
the case(s) that plant `i`:

| Condition | Prompt checklist subset | Diff                  | Repeats |
| --------- | ----------------------- | --------------------- | ------- |
| Solo      | {i}                     | the case's fixed diff | N ≥ 3   |
| In-group  | the full group G        | the same fixed diff   | N ≥ 3   |

Only the checklist subset differs between Solo and In-group; the diff is identical (confound control). All other
prompt scaffolding (preamble, output schema, model, temperature 0) is constant — reuse a single frozen preamble
analogous to the prior experiment's `prompts/preamble.md`.

Compute per item: `lift_G(i) = recall_in_group(i) − recall_solo(i)`, then `lift(G) = mean_i lift_G(i)`.

## 4. Go / No-Go criterion

Phase 1 **passes** (→ escalate to Phase 2) iff:

1. **Direction**: `mean lift(C1,C2,C3) > mean lift(D1,D2,D3)`, and
2. **Beyond noise**: the gap exceeds the run-to-run spread — concretely, the cohesive-group mean lift is
   positive and its spread (across N repeats and across the 3 cohesive groups) does **not** overlap the
   incoherent-group mean lift. (With small N this is a descriptive separation, not a formal significance test;
   N and the separation margin are reported, not p-hacked.)
3. **Sanity**: solo baselines are non-degenerate (each item is found *sometimes* solo — if an item is never or
   always found regardless, its lift is uninformative and it is excluded from the headline number, with the
   exclusion reported).

Phase 1 **fails** (→ stop and rethink) if cohesive and incoherent lift are indistinguishable, or if incoherent
groups reinforce as much as cohesive ones. That would mean symptom-locality is *not* the axis that governs good
grouping — a valuable negative result that saves Phase 2 from chasing the wrong structure.

## 5. Deliverables of a completed Phase 1

- `item-universe.md` — injectability-filtered item table (the §0 prerequisite).
- `groups.md` — the final six groups with the symptom-family rationale for each.
- `cases/` — the frozen diffs + ground-truth manifests.
- `results/` — per-condition detection frequencies (N runs), per-item lift, per-group lift.
- `analysis.md` — the go/no-go evaluation against §4, mean ± spread, and the recommendation (escalate or
  rethink), plus a `learnings-entry.md` ready to append to `~/.claude/memory/code_review_learnings.md`.
