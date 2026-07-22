# Phase-1 Groups

The six hand-picked groups that Phase 1 contrasts: **3 cohesive** (predicted positive reinforcement
lift) vs **3 incoherent** (predicted ≈0 / negative). Per [`docs/phase-1-design.md`](docs/phase-1-design.md)
§1 and [`docs/methodology.md`](docs/methodology.md) §1. All items are `injectable: yes` from
[`item-universe.md`](item-universe.md), and all are plantable in cal.com (TS/TSX,
[`corpus/SOURCE.md`](corpus/SOURCE.md)), avoiding `ee/` paths.

## Static-gap constraint (why these items, not others)

**Every item here is one that off-the-shelf TS/JS static analysis does *not* fully catch** — its best-case
coverage across cal.com's linters (tsc, ts-eslint, eslint, sonarjs, biome) is `none` or `partial` in
[`docs/issue-detection-tool-capabilities-matrix.md`](docs/issue-detection-tool-capabilities-matrix.md).
This is deliberate and load-bearing:

- **Experiment validity** — an item a linter solves `complete` (e.g. `no-var`, `eqeqeq`,
  `max-lines-per-function`, `no-unused-vars`) is low-value for an LLM-grouping study: you'd just run the
  linter. The interesting items are the semantic/judgement smells static analysis can't fully reach.
- **Realism** — cal.com runs ESLint + `@typescript-eslint` + a custom `@calcom/eslint` plugin in CI. A
  planted issue its own lint would flag wouldn't survive a real PR, so planting one is unrealistic.

An earlier draft of these groups included several linter-solved items (16.1.1, 16.1.4, 15, 16.4.4, 16.4.1,
16.7.7, 17.6.4, 17.6.7); they were **removed and replaced** with static-gap items sharing the same scan
strategy. Each item's tier is shown in the group tables (`none` = no TS/JS detector; `partial` = a linter
catches special cases but misses the general form).

## Design rules (from phase-1-design.md §1)

- **Cohesive (C):** items sharing a **scan strategy** — the same way a reviewer hunts for them, same
  evidence in the same places. Predicted to reinforce.
- **Incoherent (D):** **stratified mixes** drawing one item from each symptom family, so no shared scan
  strategy can reinforce them — but **item difficulty is held constant** vs the C-groups because the
  D-groups reuse the *same items*.
- **Each item appears in both a C-group and a D-group** where possible → the contrast isolates the
  *grouping*, not the items.
- Target ~4 comparable items per group.

## Symptom families

Four families (three seed the cohesive groups; all four supply the incoherent mixes — the JS-footgun
family is the 4th strand of each D-mix, per §1). All family members are static-gap items:

- **F1 Data-flow / input-trust** — *found by:* tracing a value entry-point → sink.
- **F2 Structural / responsibility** — *found by:* reading a function's responsibility and abstraction
  level (does it do one thing, at one level, without flag-dispatch or nesting-as-logic?).
- **F3 Dispensables / bloat** — *found by:* spotting redundancy, unjustified artifacts, hand-rolled
  equivalents of known libs.
- **F4 JS/TS footguns** — *found by:* recognizing language-specific idioms static tools can't fully judge
  (`this`-binding loss, prototype pollution, implicit request-context reach).

## Cohesive groups

### C1 — Data-flow / input-trust (F1)
*Scan strategy:* follow each externally-derived value from where it enters to where it's used; ask "is
it validated / trusted / narrowed / safely handled at every hop?"

| ID      | Item                      | tier    | injection sketch (cal.com)                                          |
| ------- | ------------------------- | ------- | ------------------------------------------------------------------- |
| 18.6.4  | Validate at boundaries    | partial | a handler/router consumes req input without validating it           |
| 17.6.2  | Runtime schema validation | partial | external/API data used without a Zod parse                          |
| 17.6.3  | Type narrowing            | partial | operate on an uncertain/union type without a runtime narrow         |
| 17.4.4a | Fallback value semantics  | none    | input ?? somethingUnrelated — wrong-semantics fallback on the value |

Host areas: `apps/web/lib`, `packages/trpc/server` ([`corpus/areas.md`](corpus/areas.md)).

### C2 — Structural / responsibility (F2)
*Scan strategy:* read what a function *is responsible for* and *at what level* — does it do one thing, at
one level of abstraction, with early returns instead of nesting, without a boolean that splits it into two
functions? Judgement about responsibility, not a line/param count a linter can threshold.

| ID     | Item                                   | tier    | injection sketch (cal.com)                                   |
| ------ | -------------------------------------- | ------- | ------------------------------------------------------------ |
| 17.4.1 | Do one thing (SRP)                     | partial | a function mixing fetch + transform + side-effect (≈ 3)      |
| 17.4.2 | One level of abstraction per function  | none    | high-level policy interleaved with low-level detail          |
| 17.4.7 | Guard Clauses (vs nested conditionals) | partial | deeply-nested conditionals where early returns would flatten |
| 17.4.5 | Remove Flag Argument                   | partial | a boolean param that dispatches two behaviours (≈ 16.7.9)    |

Host areas: `packages/lib/server`, `packages/features/bookings`.

### C3 — Dispensables / bloat (F3)
*Scan strategy:* spot redundancy and unjustified artifacts — duplicated knowledge, unexplained literals,
hand-rolled equivalents of known libs, code propped up by explanatory comments.

| ID      | Item                        | tier    | injection sketch (cal.com)                              |
| ------- | --------------------------- | ------- | ------------------------------------------------------- |
| 16.7.6  | Magic Numbers / Strings     | partial | unexplained literal(s) with no named constant (≈ 10)    |
| 16.8.5  | Reinvent the Wheel          | partial | hand-rolled util a known lib already provides           |
| 17.1.12 | Beck — No duplication (DRY) | partial | duplicated knowledge/logic across two sites (≈ 16.4.1)  |
| 16.4.6  | Comments (over-reliance)    | partial | confusing code propped up by explanatory comments (≈ 1) |

Host areas: `packages/app-store/routing-forms`, `packages/emails/src`.

## Incoherent groups

Each D-group takes **one item from each of F1/F2/F3/F4**. The F1–F3 picks are *reused from C1–C3* (so
difficulty is held constant); the F4 (JS-footgun) item is the deliberately-mismatched 4th strand whose
symptom lives somewhere unrelated. All F4 items are static-gap (`none`/`partial`).

### D1 — stratified mix
| ID     | Item                    | family | tier    | reused from    |
| ------ | ----------------------- | ------ | ------- | -------------- |
| 18.6.4 | Validate at boundaries  | F1     | partial | C1             |
| 17.4.1 | Do one thing (SRP)      | F2     | partial | C2             |
| 16.7.6 | Magic Numbers / Strings | F3     | partial | C3             |
| 17.6.6 | this context loss       | F4     | partial | — (JS-footgun) |

### D2 — stratified mix
| ID     | Item                                  | family | tier    | reused from    |
| ------ | ------------------------------------- | ------ | ------- | -------------- |
| 17.6.2 | Runtime schema validation             | F1     | partial | C1             |
| 17.4.2 | One level of abstraction per function | F2     | none    | C2             |
| 16.8.5 | Reinvent the Wheel                    | F3     | partial | C3             |
| 17.6.8 | Prototype pollution (JS)              | F4     | partial | — (JS-footgun) |

### D3 — stratified mix
| ID      | Item                                   | family | tier    | reused from    |
| ------- | -------------------------------------- | ------ | ------- | -------------- |
| 17.6.3  | Type narrowing                         | F1     | partial | C1             |
| 17.4.7  | Guard Clauses (vs nested conditionals) | F2     | partial | C2             |
| 17.1.12 | Beck — No duplication (DRY)            | F3     | partial | C3             |
| 17.6.10 | Explicit over implicit (request ctx)   | F4     | none    | — (JS-footgun) |

## Item-sharing matrix (confound check)

Every cohesive item (except C-group 4th members 17.4.4a, 17.4.5, 16.4.6) also appears in a D-group, so
its solo baseline difficulty is exercised under both a cohesive and an incoherent grouping. The three
F4 JS-footgun items (17.6.6, 17.6.8, 17.6.10) appear **only** in D-groups by design — they are the
incoherence-inducing strand and have no cohesive counterpart here.

| Item    | in C | in D |
| ------- | ---- | ---- |
| 18.6.4  | C1   | D1   |
| 17.6.2  | C1   | D2   |
| 17.6.3  | C1   | D3   |
| 17.4.4a | C1   | —    |
| 17.4.1  | C2   | D1   |
| 17.4.2  | C2   | D2   |
| 17.4.7  | C2   | D3   |
| 17.4.5  | C2   | —    |
| 16.7.6  | C3   | D1   |
| 16.8.5  | C3   | D2   |
| 17.1.12 | C3   | D3   |
| 16.4.6  | C3   | —    |
| 17.6.6  | —    | D1   |
| 17.6.8  | —    | D2   |
| 17.6.10 | —    | D3   |

## Case coverage

Per [`methodology.md`](docs/methodology.md) §2, a case must plant **every item in the C-group and
D-group it tests** (`C ∪ D`). The reuse pattern lets a small number of cases cover all six groups:

- A case planting **C1 ∪ D1 ∪ D2 ∪ D3** in one area covers C1 and all three D-groups' F1 strand.
- Cleanest split (one versatile area each, mixing families — `apps/web/lib` or
  `packages/features/bookings`):
  - **Case A** (data-flow-led area): plants C1 items + the D-groups' F1 strands + the F4 JS-footgun
    items that co-occur → covers C1, D1/D2/D3 partially.
  - **Case B** (structural/bloat-led area): plants C2 + C3 items → covers C2, C3, and the F2/F3 strands
    of D1–D3.
  - Exact case partition (which items land in which `Area`) is fixed during commit-bank construction;
    the only hard rule is each tested (C,D) pair's `C ∪ D` is fully planted in its case.

## Total item set to inject

15 distinct items (the commit bank must plant a clean instance of each, all non-`ee/`, **all static-gap**):

`18.6.4, 17.6.2, 17.6.3, 17.4.4a, 17.4.1, 17.4.2, 17.4.7, 17.4.5, 16.7.6, 16.8.5, 17.1.12, 16.4.6, 17.6.6,
17.6.8, 17.6.10`

Multi-tag note ([`methodology.md`](docs/methodology.md) §5): some plant as instances of more than one ID
— e.g. 17.1.12 also tags 16.4.1 / 10 (DRY / duplicated literals); 16.7.6 also tags item 10; 17.4.1 also
tags 3; 17.4.5 also tags 16.7.9 (flag argument); 16.4.6 also tags item 1. The commit bank records all
valid tags per planted issue.

## Planting status

All 15 items are planted as `Kind: issue` commits on independent `issue/*` branches off `main`, each
compose-tested to cherry-pick cleanly (no conflicts) and mirrored to [`corpus/bank.jsonl`](corpus/bank.jsonl).

- **C1 (area `daily-webhook`)** — 3 commits: 18.6.4 (+17.6.2), 17.4.4a, 17.6.2 (+17.6.3). The former
  16.7.7 plant was dropped (linter-solved, no longer in the group set).
- **C2 (area `packages/lib/server`)** — 4 commits: 17.4.1, 17.4.2, 17.4.7, 17.4.5.
- **C3 (areas `packages/app-store/routing-forms`, `packages/emails/src`)** — 4 commits: 16.7.6 (+10),
  16.8.5, 17.1.12 (+16.4.1), 16.4.6 (+1).
- **F4 (area `daily-webhook`)** — 3 commits: 17.6.6, 17.6.8, 17.6.10.

Remaining for TODO #3: C1 decoys / near-misses + clean padding, and running density calibration to size
the padding for case composition.
