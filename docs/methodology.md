# Methodology

These are the locked design decisions. They exist to make one specific result trustworthy: **a measured
difference in reinforcement lift between cohesive and incoherent checklist groups, attributable to the grouping
and not to a confound.**

## 1. Metric — reinforcement lift

The quantity of interest is whether putting an item *in a group* with other items makes the model find it more
often than reviewing it *alone*.

For a checklist item `i` and a group `G` (a set of items) reviewed against a fixed case:

```
recall_solo(i)      = P(model reports a valid instance of i | prompt's checklist = {i})
recall_in_group(i)  = P(model reports a valid instance of i | prompt's checklist = G, with i ∈ G)
lift_G(i)           = recall_in_group(i) − recall_solo(i)
lift(G)             = mean over i ∈ G of lift_G(i)
```

- **Cohesive groups** are predicted to have **lift(G) > 0** — the items reinforce each other.
- **Incoherent groups** are predicted to have **lift(G) ≈ 0 or < 0** — no reinforcement, possibly interference
  (attention spread across unrelated symptom types).

The headline Phase-1 result is the contrast `mean lift(cohesive groups)` vs `mean lift(incoherent groups)`.

Probabilities are estimated as detection frequencies over **N ≥ 3** repeated runs per condition (see §6).

> **Why lift, not just group recall.** Raw group recall conflates "this group is easy" with "this grouping
> helps." Lift isolates the *grouping effect* by differencing against each item's own solo baseline.

## 2. Confound control — fixed case, vary only the checklist

The single most important design choice. To attribute a recall difference to *grouping*, every other variable
must be held constant — above all, **the code under review**.

- A **case** is a fixed diff with a fixed set of planted issues and decoys.
- Within one case, every condition (each solo item, each cohesive group, each incoherent group) reviews the
  **identical diff**. The **only** thing that changes between runs is the **checklist subset injected into the
  prompt**.
- This rules out the obvious confound: a group that reviews *more changed code* would find more simply because
  there is more to inspect. Here there is no such difference — the code is identical; only the instructions
  differ.

This mirrors the prior single-vs-multi-pass experiment, which varied checklist slices over the same frozen
diff.

### Consequence for case construction

Because the diff is fixed, a case can only exercise items whose issues are actually *present* in it. To compare
a cohesive group `C` and an incoherent group `D` against the same held-constant code, the case must contain a
**planted instance of every item in `C ∪ D`** (plus decoys/near-misses). So a case is built *around* the
specific group contrast it will be used to test (see [`phase-1-design.md`](phase-1-design.md)).

## 3. Corpus — inject labeled issues into a real codebase

Cases come from a real, good-quality OSS codebase, not toy snippets, so that "did the model look in the right
place" is a meaningful question (a planted issue must hide in plausible surrounding code, not in an obvious
10-line snippet).

- Pick one good-quality OSS repo; pin a **base commit**.
- Build a **bank of labeled commits** on top of the base. Each commit is exactly one of:
  - an **injected issue** — introduces one planted defect, tagged with one-or-more checklist item IDs and a
    rationale; or
  - a **clean / decoy** commit — realistic code with no defect, or a *near-miss* (code that superficially looks
    like a smell but is actually fine).
- Every commit also carries an **area/theme** tag so a case can be assembled from one coherent region of the
  codebase.

Conventions (trailer grammar, builder contract) are specified in [`corpus-spec.md`](corpus-spec.md).

## 4. The review diff — a plausible, PR-sized chunk at realistic density

The diff under review must read like **one real code change touching a related area**, not the whole repo and
not a bug-dense gauntlet.

- **Coherence**: composed from commits sharing an area/theme tag, so the diff looks like a single feature/fix.
- **Realistic issue density**: the ratio of *lines of diff* to *planted issues* is calibrated to real-world
  norms (planted issues are **sparse**). Clean/decoy commits pad the diff to the target density.
- **Why density matters**: a bug-dense diff lets the model succeed with the "everything here is suspicious"
  shortcut, which destroys precision measurement and inflates recall. Sparse, realistic density forces genuine
  localization — exactly the ability that grouping is hypothesized to help.

## 5. Scoring — multi-tag ground truth + semantic matching

- **Multi-tag labels.** A planted defect can legitimately be an instance of more than one checklist item (a
  "Dead Code" block may also be a "Long Method"). Ground truth therefore allows **multiple item IDs per planted
  issue**, and a report is credited if it matches **any** valid tag.
- **Semantic matching, not line-exact.** Match each reported finding to a planted issue with an **LLM-judge
  semantic matcher** that ignores exact line numbers and compares meaning. This reuses the *pattern* (not the
  code) of qualops's `crb-pairwise` scorer, which yields precision / recall / F1 from pairwise judge matches.
  See [`references.md`](references.md).
- From the matcher we compute, per condition:
  - **recall** = matched planted issues / total planted issues (this feeds the lift metric);
  - **precision** = valid reports / total reports (decoys/near-misses make this meaningful);
  - per-item detection (matched / not) — needed for per-item lift.

## 6. Variance — N ≥ 3 at temperature 0

LLM reviews are nondeterministic even at temperature 0 (a prior nondeterminism study documented significant
run-to-run variation). Therefore:

- Every condition is run **N ≥ 3** times; recall/detection are frequencies over those runs.
- Report **mean ± spread** for every lift number.
- A lift claim only counts if the cohesive-vs-incoherent gap **exceeds run-to-run noise** — the go/no-go
  criterion in [`phase-1-design.md`](phase-1-design.md) is stated in terms of this margin, not a bare
  point estimate.

## 7. Out of scope for Phase 1 (deliberately)

To keep the sanity check cheap and unconfounded, Phase 1 does **not** attempt:

- **Pass ordering effects** (does a group find more when run later?) — a known open question, deferred.
- **Cost optimization** — Phase 1 measures the *effect*, not the cost/benefit frontier.
- **The rigorous group search itself** — that is Phase 2, gated on Phase 1's result
  ([`escalation-phase-2.md`](escalation-phase-2.md)).
- **Generalization to many real PRs** — Phase 1 uses controlled injected cases precisely because real PRs don't
  let us control which items co-occur. External-validity replay is a later phase.
