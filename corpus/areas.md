# Candidate Coherent Areas (cal.com)

Area/theme units a case can be assembled within (`docs/corpus-spec.md` §1 — `Area` trailer = coherence
unit). All non-`ee/` (license rule, see [`SOURCE.md`](SOURCE.md)). Counts are TS/TSX file counts at
`BASE_SHA`. "Affinity" = which `item-universe.md` `yes` families inject most naturally there.

| Area path                        | ~files | Symptom-family affinity                                                                                                                                                                  |
| -------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| apps/web/lib                     | 71     | Data-flow / input-trust (18.6.4 boundary validation, 17.6.2 schema validation, 17.4.4a fallback semantics, 16.7.7 error hiding); JS-footgun (17.6.4, 17.6.6). Request/handler glue code. |
| packages/lib/server              | 44     | Structural (16.1.1 long method, 16.1.4 long params, 15 deep nesting, 17.4.1 do-one-thing); bloat (16.4.1 duplicate, 16.7.6 magic numbers). Server utilities.                             |
| packages/features/bookings       | 141    | Structural + bloat + data-flow mix; rich domain logic — good for a coherent feature-sized diff. Avoid any nested ee/.                                                                    |
| packages/trpc/server             | 449    | Data-flow (trust-boundary crossings, input validation at routers); structural (procedure handlers). Large surface.                                                                       |
| packages/app-store/routing-forms | 66     | Bloat (16.4.4 dead code, 16.8.5 reinvent-the-wheel, 16.4.1 duplicate) + structural. Self-contained app-store module.                                                                     |
| packages/emails/src              | 65     | Bloat / structural (template builders: duplication, magic strings, long methods). Low coupling → easy clean composition.                                                                 |

## Usage notes

- Each Phase-1 case is built within **one** area so the diff reads as a single coherent change
  (`methodology.md` §4).
- The JS-footgun cohesive family needs request/handler-style TS — `apps/web/lib` and
  `packages/trpc/server` are the best hosts.
- A single area should be able to host both a cohesive group and its paired incoherent group (the case
  must plant `C ∪ D` — `phase-1-design.md` §2). `packages/features/bookings` and `apps/web/lib` are the
  most versatile for that because they mix families.
- Revisit `partial`-injectability items (`item-universe.md`) per area: some `partial` items (e.g. 17.2.x
  layering, 16.5.x couplers) may become injectable here if the area already provides the host pattern.

These are candidates; the final per-case area is fixed during case construction (next sub-task).
