# Phase 2 — Rigorous Group Search (gated on Phase 1)

Phase 2 runs **only if Phase 1 passes** its go/no-go ([`phase-1-design.md`](phase-1-design.md) §4): cohesive
groups must show clearly higher reinforcement lift than incoherent ones, beyond run-to-run noise. Phase 1 also
hands Phase 2 two numbers that determine which method is affordable: the **per-run cost** and the **noise
level** (variance of lift estimates).

The goal of Phase 2: from the injectable item universe, **discover groupings that maximize reinforcement lift
(and downstream recall) at acceptable cost** — without exhaustive pairwise testing, and capturing 3+-way
reinforcement, treating the model as a black box.

## Why not exhaustive pairwise

~130 items → ~8,400 pairs; the injectable subset is smaller but still large. Worse, pairwise lift cannot see
the **higher-order reinforcement** Phase 1/prior work observed (a trio reinforcing where no pair does). So the
method must probe *groups*, not pairs, and spend probes adaptively.

## Step 0 (always) — greedy constructive baseline

Regardless of which rigorous method is chosen, start with a cheap **greedy forward-selection** baseline to
calibrate and to provide a reference grouping:

- Seed each group with one "anchor" item; repeatedly add the candidate item whose addition most increases the
  group's measured lift/recall, until a stop rule (no item adds positive lift, or size cap).
- Cheap, interpretable, and establishes the cost/variance reality at small scale. Its output is the baseline
  every fancier method must beat.

Phase 1's result + this baseline together decide which (if any) heavier method is warranted.

## Candidate rigorous methods

Pick **one** for the first rigorous pass based on the decision rule below. They differ in run cost, assumptions,
and what they can capture.

### A. Screening design → effects model
Run `O(items)` — not `O(pairs)` — carefully **designed** group compositions (e.g. a definitive-screening or
D-optimal design), then fit `detection ~ items + interactions` and read groupings off the estimated positive
interactions.
- **Pros:** most sample-efficient; gives an interpretable interaction structure.
- **Cons:** assumes effects are roughly additive with sparse interactions; **can miss high-order (3+)
  reinforcement** — which is exactly what we care about. Mitigate by adding targeted 3-way probes for the
  strongest pairwise interactions.
- **Best when:** per-run cost is high and noise is low (designs are fragile under heavy noise).

### B. Adaptive search (bandit / Bayesian optimization)
Treat "which partition" as black-box optimization: propose a grouping → evaluate lift/recall → update a
surrogate (or bandit) → propose the next; use **successive halving** to kill weak groupings early.
- **Pros:** directly optimizes the real objective; **captures high-order effects** without modeling them; robust
  to a moderately noisy objective (with enough repeats).
- **Cons:** more runs than screening; gives a good grouping but less *explanation* of why.
- **Best when:** per-run cost is moderate and we mainly want the winning grouping, not a theory.

### C. Sparse interaction graph → community detection
Run a **sparse, smartly chosen** set of multi-item probes (not all pairs) to estimate a reinforcement weight
between items; build a weighted item graph; run **Louvain / spectral community detection**; communities = groups.
- **Pros:** interpretable + **reusable** artifact (the graph); communities naturally allow variable group sizes;
  partial high-order capture via group-probe co-detection.
- **Cons:** result quality depends on the sparsity pattern chosen for probes (the key risk); still an
  approximation of true higher-order structure.
- **Best when:** we want a reusable, inspectable map and can afford a modest sparse probe budget.

## Decision rule (which method, after Phase 1)

| Phase-1 signal                                            | Per-run cost | Noise (lift variance) | → Method                                                   |
| --------------------------------------------------------- | ------------ | --------------------- | ---------------------------------------------------------- |
| Strong, clean separation                                  | High         | Low                   | A. Screening design (max efficiency)                       |
| Strong                                                    | Moderate     | Moderate              | B. Adaptive search (robust, captures high-order)           |
| Strong but high-order-looking (trios matter, pairs don't) | Any          | Any                   | B, or C for an interpretable map                           |
| Present but noisy                                         | Any          | High                  | B with more repeats; avoid A (designs fragile under noise) |
| Want a reusable, inspectable artifact                     | Low–moderate | Low–moderate          | C. Graph + communities                                     |

Whichever is chosen, **validate the discovered grouping** the same way Phase 1 measures lift (held-out cases,
N≥3), and compare against (a) the greedy baseline and (b) the qualops agentic-subagent grouping and the prior
4-pass grouping as reference points.

## External-validity phase (later still)

Once a data-driven grouping wins on injected cases, replay the best groupings on **mined real PRs with golden
reviewer comments** (CRB-style, per [`references.md`](references.md)) to check the controlled finding
generalizes. Injection gives control; real-PR replay gives realism — both are needed for a grouping we'd
actually ship into the `code-review` skill.

## Deferred questions (named so they aren't forgotten)

- **Pass ordering** — does a group find more when run later in a multi-pass sequence? (Held out of Phase 1.)
- **Cost/recall frontier** — the *value* of each additional pass, not just whether grouping helps.
- **Group size / number of passes** — is there an optimal `k`? The prior experiment guessed 4; this should be
  measured, not assumed.
- **Cross-model stability** — do good groupings transfer across models, or are they model-specific (a real risk
  given the black-box, behavioral basis)?
