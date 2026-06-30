# Linter / Static-Analyzer Coverage of the Checklist Items

**Why this exists.** Before investing more effort planting items, assess which of our checklist error
classes are *already* caught by off-the-shelf linters / static analyzers. This matters two ways:

1. **Experiment validity** — if a deterministic linter solves an item *completely*, an LLM-grouping
   study on that item is low-value (you'd just run the linter). The interesting items for grouping are
   the ones static analysis can't fully catch — semantic/judgement smells.
2. **Realism** — cal.com already runs ESLint + `@typescript-eslint/recommended` + a custom
   `@calcom/eslint` plugin + Prettier (verified in `packages/config/eslint-preset.js`). A planted issue
   that the repo's own lint would flag is unrealistic (it wouldn't survive CI).

## Scale (ordinal)

Cells render the ordinal as an icon; **a blank cell means the language's tool has no detector for that
item** (kept blank for readability rather than writing a `0`/"None").

|  Cell   |   Ordinal    | Meaning                                                                                                                                |
| :-----: | :----------: | -------------------------------------------------------------------------------------------------------------------------------------- |
|   ✅    | 2 — Complete | A standard rule/analyzer detects essentially all instances deterministically (mechanical pattern).                                     |
|   ⚠️    | 1 — Partial  | A rule catches some special cases / a syntactic proxy, but misses the general semantic form (false negatives), or needs opt-in config. |
| (blank) |   0 — None   | No off-the-shelf detector; requires semantic/contextual judgement (LLM or human).                                                      |

## The big table

One row per Phase-1 item. **Group** = the cohesive (C) and incoherent (D) groups the item belongs to
(from [`groups.md`](groups.md)). Columns are grouped by **programming language** (top-10 by popularity +
Ruby); the sub-header names the representative linter / static-analysis tool used for that language:

| Column | Language   | Tool (sub-header)              |
| :----: | ---------- | ------------------------------ |
|   Py   | Python     | Ruff / Pylint / mypy           |
|   C    | C          | clang-tidy / cppcheck          |
|  C++   | C++        | clang-tidy / cppcheck          |
|  Java  | Java       | SpotBugs / PMD                 |
|   C#   | C#         | Roslyn / SonarC#               |
|   JS   | JavaScript | ESLint / SonarJS / Biome       |
|   TS   | TypeScript | tsc / TS-ESLint (cal.com host) |
|   Go   | Go         | staticcheck / golangci-lint    |
|  Rust  | Rust       | Clippy                         |
|  PHP   | PHP        | PHPStan / Psalm                |
|  Ruby  | Ruby       | RuboCop                        |

`Sem` = the language-agnostic security analyzer column (Semgrep / CodeQL), kept because boundary/taint
items only surface there.

| Item                                |  Group  | Py  |  C  | C++ | Java | C#  | JS  | TS  | Go  | Rust | PHP | Ruby | Sem |
| ----------------------------------- | :-----: | :-: | :-: | :-: | :--: | :-: | :-: | :-: | :-: | :--: | :-: | :--: | :-: |
| F1 — Data-flow / input-trust        |         |     |     |     |      |     |     |     |     |      |     |      |     |
| 18.6.4 Validate at boundaries       | C1 · D1 |     |     |     |      |     | ⚠️  |     |     |      | ⚠️  |      | ⚠️  |
| 17.6.2 Runtime schema validation    | C1 · D2 | ⚠️  |     |     |      |     | ⚠️  | ⚠️  |     |      | ⚠️  |      | ⚠️  |
| 16.7.7 Error Hiding                 | C1 · D3 | ✅  |     | ⚠️  |  ✅  | ✅  | ✅  | ⚠️  | ⚠️  |  ⚠️  | ✅  |  ✅  | ⚠️  |
| 17.4.4a Fallback semantics (a\|\|b) |   C1    |     |     |     |      |     |     |     |     |      |     |      |     |
| F2 — Structural / shape             |         |     |     |     |      |     |     |     |     |      |     |      |     |
| 16.1.1 Long Method                  | C2 · D1 | ✅  | ✅  | ✅  |  ✅  | ✅  | ✅  | ⚠️  | ✅  |  ✅  | ✅  |  ✅  |     |
| 16.1.4 Long Parameter List          | C2 · D2 | ✅  | ✅  | ✅  |  ✅  | ✅  | ✅  | ⚠️  | ✅  |  ✅  | ✅  |  ✅  |     |
| 15 Deep Nesting                     | C2 · D3 | ✅  | ✅  | ✅  |  ✅  | ✅  | ✅  | ⚠️  | ✅  |  ✅  | ✅  |  ✅  |     |
| 17.4.1 Do one thing (fn SRP)        |   C2    | ⚠️  |     |     |  ⚠️  | ⚠️  | ⚠️  |     | ⚠️  |      | ⚠️  |  ⚠️  |     |
| F3 — Dispensables / bloat           |         |     |     |     |      |     |     |     |     |      |     |      |     |
| 16.4.4 Dead Code                    | C3 · D1 | ✅  | ⚠️  | ⚠️  |  ✅  | ✅  | ✅  | ✅  | ✅  |  ✅  | ✅  |  ✅  |     |
| 16.4.1 Duplicate Code               | C3 · D2 | ✅  | ✅  | ✅  |  ✅  | ✅  | ✅  |     | ✅  |  ✅  | ✅  |  ✅  |     |
| 16.7.6 Magic Numbers / Strings      | C3 · D3 | ⚠️  | ⚠️  | ⚠️  |  ⚠️  | ⚠️  | ⚠️  |     | ⚠️  |  ⚠️  | ⚠️  |  ⚠️  |     |
| 16.8.5 Reinvent the Wheel           |   C3    | ⚠️  |     |     |      |     | ⚠️  |     |     |  ⚠️  |     |  ⚠️  |     |
| F4 — JS/TS footguns (D-groups only) |         |     |     |     |      |     |     |     |     |      |     |      |     |
| 17.6.4 Strict equality (==)         |   D1    | n/a |     |     |      |     | ✅  | ✅  | n/a | n/a  | ⚠️  | n/a  | ⚠️  |
| 17.6.6 this context loss            |   D2    | n/a |     |     |      |     | ⚠️  | ⚠️  | n/a | n/a  |     | n/a  |     |
| 17.6.7 var hoisting                 |   D3    | n/a |     |     |      |     | ✅  | ✅  | n/a | n/a  |     | n/a  |     |

> `n/a` = the construct does not exist in that language (e.g. loose `==`, `var` hoisting, JS `this`
> rebinding are JS/TS-only footguns), so there is nothing for the tool to detect — distinct from a blank
> (construct exists, but no detector).

### Per-item notes (the reasoning behind the icons)

- **18.6.4 Validate at boundaries** — Semgrep/CodeQL taint-track *unvalidated input → sink* for known
  sink shapes (SQL/exec/path); JS SonarJS + PHP PHPStan flag some injection patterns. "Should have run a
  schema parse" in general is semantic → most languages blank.
- **17.6.2 Runtime schema validation** — TS-ESLint `no-unsafe-*` / `no-explicit-any` (and Py mypy, PHP
  PHPStan strict) catch the *symptom* (raw `any`/untyped cast from external) partially; none can know a
  Zod/schema parse was *expected*. Our planted `as {…}` cast → `no-unsafe-member-access` would warn.
- **16.7.7 Error Hiding** — **Empty catch** is mechanical and broadly covered (Py `try/except: pass`
  via Pylint/Ruff `S110`, Java PMD `EmptyCatchBlock`, C# `S2486`, JS SonarJS `S2486`/`no-empty` + Biome
  `noEmptyBlockStatements`, PHP, Ruby RuboCop `Lint/SuppressedException`). A *logs-nothing-meaningful*
  swallow that isn't empty drops to ⚠️ (TS/Go/Rust/C++ here). ✅ Our TS plant was **revised** from
  `catch (e) {}` to exactly that non-empty swallow so it survives cal.com's lint (now ⚠️, not ✅).
- **17.4.4a Fallback semantics** — wrong-*actor* fallback is pure semantics; no detector in any language
  knows an attendee email ≠ organizer email. Fully blank. **Grouping-relevant.**
- **16.1.1 / 16.1.4 / 15 (length / params / nesting)** — pure metric thresholds, mechanical in every
  ecosystem (ESLint `max-lines-per-function`/`max-params`/`max-depth`, SonarJS, PMD, Pylint, Clippy,
  staticcheck, RuboCop `Metrics/*`). ✅ as a *metric*; the underlying smell ("too long to understand")
  is a proxy. Marked ⚠️ for TS only because cal.com's config does not enable these metric rules.
- **17.4.1 Do one thing (fn SRP)** — only *proxied* by complexity/length metrics; "does several
  unrelated things" is semantic → ⚠️ where a cognitive-complexity rule exists, blank where it doesn't.
  **Grouping-relevant.**
- **16.4.4 Dead Code** — unused locals/imports/params + unreachable code: complete almost everywhere
  (Py Pyflakes/Ruff, Java, C# Roslyn, JS `no-unused-vars`, TS `noUnusedLocals`, Go *compiler errors* on
  unused, Rust `dead_code` lint, RuboCop). C/C++ only ⚠️ (warnings, weaker reachability). **But** dead
  *across module boundaries* needs whole-program reachability → corpus must plant *cross-boundary* dead
  code or the repo's own lint flags it.
- **16.4.1 Duplicate Code** — token/AST clone detection: Sonar CPD, PMD CPD, `jscpd`, Py pylint
  `duplicate-code`, RuboCop. ✅ for copy-paste blocks above a token threshold; near-duplicate-with-edits
  = partial. Blank for TS because cal.com doesn't run a CPD pass in its lint.
- **16.7.6 Magic Numbers / Strings** — `no-magic-numbers` (JS), SonarJS `S109`, PMD `AvoidLiteralsInIfCondition`,
  Pylint `magic-value`, RuboCop exist but **high false-positive**, usually off; only "unnamed numeric
  literal" → ⚠️ everywhere (misses magic *strings*, allows config'd exceptions).
- **16.8.5 Reinvent the Wheel** — only narrow cases: `you-dont-need-lodash-underscore` (cal.com runs
  it!) flags hand-rolled lodash equivalents; Clippy/RuboCop/Ruff flag a few "use the stdlib" idioms.
  General "a lib already does this" = semantic → mostly blank. **Grouping-relevant.**
- **17.6.4 `==` / 17.6.6 `this` / 17.6.7 `var`** — JS/TS-only footguns. ESLint `eqeqeq`/`no-var`,
  SonarJS, Biome `noDoubleEquals`/`noVar` → ✅; `unbound-method`/`no-invalid-this` → ⚠️ (dynamic `this`
  rebinding is undecidable). PHP has a loose-`==` analogue (PHPStan ⚠️). Other languages: `n/a`.

## What this tells the experiment

Sorting by "least linter-solvable" = "most grouping-relevant" (where an LLM pass actually adds value):

- **Blank-row / grouping-relevant (no good detector):** 17.4.4a (fallback semantics), 17.4.1 (fn SRP),
  16.8.5 (reinvent-the-wheel), 18.6.4 (boundary validation, general form). These are the items where a
  grouping study is genuinely worth running — static analysis can't replace the model.
- **Mostly ✅ (linter ≈ complete):** 17.6.4 (`==`), 17.6.7 (`var`), 16.7.7 (empty catch),
  16.4.1 (duplicate blocks), 16.4.4 (unused locals/imports), 16.1.4 (param count). For these the LLM is
  competing with a deterministic rule — *lower* research value, but they're **still useful as Phase-1
  D-group filler / footgun strand** precisely because they're easy/cheap to detect (good for measuring
  whether an incoherent group *interferes* with easy items).

### Implications for the corpus (actionable now)

1. **Realism risk — make planted issues survive cal.com's own lint.** The repo runs `no-empty`-style,
   `eqeqeq`, `no-var`, `unused-imports`, `you-dont-need-lodash`. Several of our F3/F4 plants would be
   caught by `yarn lint` and thus be *unrealistic* (a real PR wouldn't merge them). Two options:
   - plant the **harder variant** that the rule misses (e.g. dead code *across* modules not unused
     locals; a swallowing catch that *logs something useless* rather than empty `{}`); or
   - explicitly accept them as "easy/mechanical" items and note that the experiment's interesting
     signal lives in the **0-scored items**.
   - ✅ **Resolved.** Our `16.7.7` plant was an **empty `catch (e) {}`** (✅ on JS/Java/Py/C#/PHP/Ruby).
     It has been **revised** to a *logs-nothing-meaningful* swallow (non-empty catch that logs a benign
     step-finished line and drops the error) so it survives `no-empty`/SonarJS `S2486`/Biome
     `noEmptyBlockStatements` — now a ⚠️ partial-detect, lint-realistic plant. (`issue/16.7.7-error-hiding`
     → `25d39411`, `bank.jsonl` updated.)
2. **Phase-1 framing.** The cohesive-vs-incoherent contrast is cleanest on the **blank-row semantic
   items** (C1's 17.4.4a, C2's 17.4.1, C3's 16.8.5). The mechanical items (F4 footguns) are fine as the
   D-group "incoherent strand" but their *solo* recall will be near-ceiling (easy), which is useful for
   detecting interference but contributes little lift headroom.

## Caveats

- Scores are **best-case off-the-shelf** with the rule enabled; defaults often disable the noisy ones
  (`no-magic-numbers`, `max-lines-per-function`), so *as-configured* coverage is usually lower.
- "Complete" means *deterministic pattern coverage*, not *zero false positives* — metric-threshold
  rules (length/params/depth) flag the metric, which is only a **proxy** for the smell.
- This is the Phase-1 subset. The full ~130-item table can be extended later if useful; the pattern
  holds: bloaters-by-metric and footguns are linter-solvable, semantic/design smells are not.
