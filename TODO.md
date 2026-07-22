# TODO

Candidate starting tasks, ordered by dependency (each later task needs the earlier ones). See the
referenced docs for the governing spec.

- [x] **1. Snapshot references** — copy the prior-experiment files and master checklist into
  `references/` so the project is self-contained and reproducible.
  → `docs/references.md`

- [x] **2. Build `item-universe.md`** — classify each checklist item as
  `injectable: yes | no | partial` with a one-line note. Only `injectable: yes` items are eligible
  for Phase-1 groups. (Phase-1 §0 prerequisite — bounds the item universe.)
  → `docs/phase-1-design.md` §0

- [~] **3. Pick OSS repo + build commit bank** — choose a permissive, idiomatic OSS codebase, pin
  `BASE_SHA`, and start the labeled commit bank using the trailer grammar
  (`Kind` / `Area` / `Issue-Items`). Mirror to `bank.jsonl`.
  → `docs/corpus-spec.md`
  - [x] Repo selected: **cal.com** @ `92f44dce` (pure TS/TSX) + corpus scaffold (`corpus/`:
    `BASE_SHA`, `SOURCE.md`, `areas.md`, `density-calibration.md`, `bank.jsonl` placeholder).
  - [x] Phase-1 group selection: **`groups.md`** — 3 cohesive (C1–C3) + 3 incoherent (D1–D3),
    15 distinct `yes` items, all plantable in cal.com non-`ee/`. (Unblocks the commit bank.)
  - [x] Corpus repo seeded: `corpus/repo` = fresh git repo with cal.com@BASE_SHA tree as the base
    commit (source clone had pack corruption; seeded via `git archive`, host files verified identical).
  - [~] Build the labeled commit bank — plant the 15 items from `groups.md` as `Kind: issue` commits
    + decoys/clean padding; mirror to `bank.jsonl`.
    - [x] **C1 data-flow (area `daily-webhook`)**: 3 issue commits on `issue/*` branches, all
      independently cherry-pickable (compose-tested, no conflicts), recorded in `bank.jsonl`:
      18.6.4 (+17.6.2), 17.4.4a, 17.6.2 (+17.6.3). (Former 16.7.7 dropped — linter-solved.)
    - [x] **C2 structural (area `packages/lib/server`)**: 4 issue commits: 17.4.1, 17.4.2, 17.4.7, 17.4.5.
    - [x] **C3 bloat (areas `packages/app-store/routing-forms`, `packages/emails/src`)**: 4 issue commits:
      16.7.6 (+10), 16.8.5, 17.1.12 (+16.4.1), 16.4.6 (+1).
    - [x] **D-group JS-footgun items (area `daily-webhook`)**: 3 issue commits: 17.6.6, 17.6.8, 17.6.10.
    - [ ] C1 decoys / near-misses (valid `||` fallback, logging catch, validated branch) + clean padding.
  - [ ] Run density calibration from cal.com CRB cases (`corpus/density-calibration.md`) — sizes the
    clean/decoy padding for case composition.

- [ ] **4. Build the harness** — case-builder (cherry-pick + `git diff`), the solo-vs-in-group run
  matrix (N≥3, temp 0, frozen preamble), and the LLM-judge semantic scorer that computes
  reinforcement lift.
  → `docs/methodology.md`, `docs/phase-1-design.md` §3

- [x] **5. Tool-capabilities matrix** — assess which checklist items off-the-shelf linters /
  static analyzers already catch, so grouping effort focuses on the **static gap** (items needing
  semantic/LLM judgement). 176 items × 24 tools, fully researched.
  → `docs/issue-detection-tool-capabilities-matrix.md`, `data/issue-detection-tool-capabilities-matrix.json`

- [x] **6. Prompt-grouping method** — specify the process that turns the static-gap item pool into
  grouped **agent prompts** (pool → similarity-seeded candidate groups → Phase-2 lift validation →
  prompt synthesis). Method only; no groups or prompts produced yet.
  → `docs/prompt-grouping-method.md`

- [ ] **7. Run the prompt-grouping method** (gated on Phase 1 pass + Phase 2) — derive the static-gap
  pool, seed + validate candidate groups via the lift search, and synthesize one agent prompt per
  validated group for the `code-review` skill.
  → `docs/prompt-grouping-method.md`
