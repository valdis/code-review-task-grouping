# Phase-1 Groups

The six hand-picked groups that Phase 1 contrasts: **3 cohesive** (predicted positive reinforcement
lift) vs **3 incoherent** (predicted ≈0 / negative). Per [`docs/phase-1-design.md`](docs/phase-1-design.md)
§1 and [`docs/methodology.md`](docs/methodology.md) §1. All items are `injectable: yes` from
[`item-universe.md`](item-universe.md), and all are plantable in cal.com (TS/TSX,
[`corpus/SOURCE.md`](corpus/SOURCE.md)), avoiding `ee/` paths.

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
family is the 4th strand of each D-mix, per §1):

- **F1 Data-flow / input-trust** — *found by:* tracing a value entry-point → sink.
- **F2 Structural / shape** — *found by:* scanning function shape/size/indentation; no data-flow.
- **F3 Dispensables / bloat** — *found by:* spotting redundancy, unused/hardcoded artifacts.
- **F4 JS/TS footguns** — *found by:* recognizing language-specific idioms (`==`, `var`, `this`).

## Cohesive groups

### C1 — Data-flow / input-trust (F1)
*Scan strategy:* follow each externally-derived value from where it enters to where it's used; ask "is
it validated / trusted / safely handled at every hop?"

| ID      | Item                      | injection sketch (cal.com)                                          |
| ------- | ------------------------- | ------------------------------------------------------------------- |
| 18.6.4  | Validate at boundaries    | a handler/router consumes req input without validating it           |
| 17.6.2  | Runtime schema validation | external/API data used without a Zod parse                          |
| 16.7.7  | Error Hiding              | a try/catch around the data path swallows the error                 |
| 17.4.4a | Fallback value semantics  | input ?? somethingUnrelated — wrong-semantics fallback on the value |

Host areas: `apps/web/lib`, `packages/trpc/server` ([`corpus/areas.md`](corpus/areas.md)).

### C2 — Structural / shape (F2)
*Scan strategy:* read function shape — length, parameter count, indentation depth — purely structural,
no data-flow reasoning.

| ID     | Item                | injection sketch (cal.com)                          |
| ------ | ------------------- | --------------------------------------------------- |
| 16.1.1 | Long Method         | one over-long function doing several steps          |
| 16.1.4 | Long Parameter List | a function with 6+ positional params                |
| 15     | Deep Nesting        | deeply-nested conditionals (≈ 17.4.7 guard clauses) |
| 17.4.1 | Do one thing        | a function mixing unrelated responsibilities (≈ 3)  |

Host areas: `packages/lib/server`, `packages/features/bookings`.

### C3 — Dispensables / bloat (F3)
*Scan strategy:* spot redundancy and unused/hardcoded artifacts — duplicated blocks, dead code,
unexplained literals, hand-rolled equivalents of known libs.

| ID     | Item                    | injection sketch (cal.com)                         |
| ------ | ----------------------- | -------------------------------------------------- |
| 16.4.4 | Dead Code               | an unused variable/function/branch                 |
| 16.4.1 | Duplicate Code          | a block copied to a second location (≈ 17.1.12)    |
| 16.7.6 | Magic Numbers / Strings | unexplained literal(s) with no named constant      |
| 16.8.5 | Reinvent the Wheel      | hand-rolled util that a known lib already provides |

Host areas: `packages/app-store/routing-forms`, `packages/emails/src`.

## Incoherent groups

Each D-group takes **one item from each of F1/F2/F3/F4**. The F1–F3 picks are *reused from C1–C3* (so
difficulty is held constant); the F4 (JS-footgun) item is the deliberately-mismatched 4th strand whose
symptom lives somewhere unrelated.

### D1 — stratified mix
| ID     | Item                    | family | reused from    |
| ------ | ----------------------- | ------ | -------------- |
| 18.6.4 | Validate at boundaries  | F1     | C1             |
| 16.1.1 | Long Method             | F2     | C2             |
| 16.4.4 | Dead Code               | F3     | C3             |
| 17.6.4 | Strict equality (==/!=) | F4     | — (JS-footgun) |

### D2 — stratified mix
| ID     | Item                      | family | reused from    |
| ------ | ------------------------- | ------ | -------------- |
| 17.6.2 | Runtime schema validation | F1     | C1             |
| 16.1.4 | Long Parameter List       | F2     | C2             |
| 16.4.1 | Duplicate Code            | F3     | C3             |
| 17.6.6 | this context loss         | F4     | — (JS-footgun) |

### D3 — stratified mix
| ID     | Item                    | family | reused from    |
| ------ | ----------------------- | ------ | -------------- |
| 16.7.7 | Error Hiding            | F1     | C1             |
| 15     | Deep Nesting            | F2     | C2             |
| 16.7.6 | Magic Numbers / Strings | F3     | C3             |
| 17.6.7 | var hoisting            | F4     | — (JS-footgun) |

## Item-sharing matrix (confound check)

Every cohesive item (except C-group 4th members 17.4.4a, 17.4.1, 16.8.5) also appears in a D-group, so
its solo baseline difficulty is exercised under both a cohesive and an incoherent grouping. The three
F4 JS-footgun items (17.6.4, 17.6.6, 17.6.7) appear **only** in D-groups by design — they are the
incoherence-inducing strand and have no cohesive counterpart here.

| Item    | in C | in D |
| ------- | ---- | ---- |
| 18.6.4  | C1   | D1   |
| 17.6.2  | C1   | D2   |
| 16.7.7  | C1   | D3   |
| 17.4.4a | C1   | —    |
| 16.1.1  | C2   | D1   |
| 16.1.4  | C2   | D2   |
| 15      | C2   | D3   |
| 17.4.1  | C2   | —    |
| 16.4.4  | C3   | D1   |
| 16.4.1  | C3   | D2   |
| 16.7.6  | C3   | D3   |
| 16.8.5  | C3   | —    |
| 17.6.4  | —    | D1   |
| 17.6.6  | —    | D2   |
| 17.6.7  | —    | D3   |

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

15 distinct items (the commit bank must plant a clean instance of each, all non-`ee/`):

`18.6.4, 17.6.2, 16.7.7, 17.4.4a, 16.1.1, 16.1.4, 15, 17.4.1, 16.4.4, 16.4.1, 16.7.6, 16.8.5, 17.6.4,
17.6.6, 17.6.7`

Multi-tag note ([`methodology.md`](docs/methodology.md) §5): some plant as instances of more than one ID
— e.g. 16.4.1 also tags 17.1.12 (DRY); 15 also tags 17.4.7; 16.7.6 also tags item 10. The commit bank
records all valid tags per planted issue.
