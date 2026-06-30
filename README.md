# Code-Review Task Grouping

**Which code-review checklist items should be reviewed *together* in the same pass?**

When an LLM reviews a code change against a large checklist (~130 items across §1–18 of the
[master review checklist](docs/references.md)), it spends a finite *attention budget* across all the criteria
at once and reviews each shallowly. Splitting the checklist into a few **focused passes** — each carrying a
thematic subset of items — lets the model go deeper, and prior work found related criteria *reinforce* each
other (items in the same pass make each other easier to find). But which items belong together?

This project tries to answer that **systematically and cheaply**, treating the model as a **black box**.

## Why this exists

A review of the `code-review` skill against the master checklist found the skill's hand-authored agent grouping
covers only a slice of the catalog and misses several bloat smells (dead code, speculative generality/YAGNI,
premature optimization, reinvent-the-wheel). The grouping was frozen independently of the checklist. That
exposes the underlying open question this project addresses: grouping is currently guesswork.

A [prior experiment](docs/references.md#prior-art) already showed the payoff is real — one hand-picked 4-pass
grouping roughly **doubled recall (41% → 91%)** at 3.4× token cost on a single PR, and the most productive pass
worked *because* related criteria (resource-ownership + brittle-patterns + concurrency) reinforced each other.
This project generalizes that one-off result: *discover* good groupings instead of guessing one.

## The constraint that shapes everything

We do **not** have model weights or internal embeddings — only **behavioral** signal (what the model detects
under which grouping). So:

- We cannot read groupings off the model's "internal clustering." The only evidence is what gets found.
- Exhaustive pairwise testing is wasteful: ~8,400 pairs for 130 items, and pairwise testing can't even see the
  **3-way reinforcement** the prior experiment observed.

So the project is fundamentally about **efficient black-box experiment design**: discover good groupings in the
fewest review runs.

## Approach: start simple, escalate

**Phase 1 — sanity / manipulation check (this is what we design first).**
Before building any expensive search, confirm the signal is real and measurable. Hand-pick from the checklist:
- **3 "cohesive" groups** — items with *similar symptoms*, found by looking in the *same places*.
- **3 "incoherent" groups** — items deliberately mixed so symptoms manifest very differently.

Prediction to falsify: cohesive groups show clearly higher **reinforcement lift** than incoherent groups. If
they don't, the "symptom-locality drives good grouping" premise is shaky and we rethink. If they do, escalate.

**Phase 2 — rigorous group search (separate, later approval).**
Only once Phase 1 confirms the effect and tells us the noise level and per-run cost do we pick a principled
search method (greedy forward-selection baseline → screening design / Bayesian optimization / sparse-graph
community detection). See [`docs/escalation-phase-2.md`](docs/escalation-phase-2.md).

## How an experiment case is built (the realistic part)

Rather than reviewing toy snippets, cases are built from a **real codebase**:

1. Pick a good-quality OSS repo, pin a base commit.
2. Build a bank of labeled commits on top — each either an *injected issue* (tagged with checklist item IDs) or
   a *clean/decoy* commit, all tagged with an area/theme.
3. Compose a **plausible, PR-sized diff** for one coherent area at **realistic issue density** (sparse, like a
   real PR — not bug-dense) by `git cherry-pick`-ing selected commits and taking `git diff base..tip`.
4. **Hold that diff fixed** and run the review repeatedly, changing **only the checklist subset** in the prompt
   (solo item / cohesive group / incoherent group). Lift is then attributable to grouping alone.

See [`docs/corpus-spec.md`](docs/corpus-spec.md) and [`docs/methodology.md`](docs/methodology.md).

## Status

**Phase 1 designed, not yet run.** This repository currently contains the design and methodology only. The
harness, corpus, and experiment execution are the next, separately-approved step.

## Docs

| Doc                                                      | Contents                                                                                              |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| [docs/methodology.md](docs/methodology.md)               | Locked decisions: lift metric, fixed-case confound control, corpus design, density, variance, scoring |
| [docs/phase-1-design.md](docs/phase-1-design.md)         | The 3-cohesive/3-incoherent contrast, run matrix, go/no-go criterion                                  |
| [docs/corpus-spec.md](docs/corpus-spec.md)               | Commit-bank trailer grammar + the cherry-pick case-builder contract                                   |
| [docs/references.md](docs/references.md)                 | Prior art and reusable patterns (memory + qualops evals)                                              |
| [docs/escalation-phase-2.md](docs/escalation-phase-2.md) | Candidate rigorous search methods + the decision rule                                                 |
