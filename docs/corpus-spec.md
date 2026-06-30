# Corpus Spec — Commit Bank & Case Builder

This specifies how labeled issues live in git and how a review case is composed from them. The design goal is
that **git does the composition** (cherry-pick + diff), so there is no fragile manual patch-merging.

## 1. Repository layout

```
corpus/
  repo/                 ← clone of the chosen OSS codebase, pinned at BASE_SHA
  bank.jsonl            ← index of all labeled commits (mirrors the git trailers; queryable)
  cases/
    <case-id>/
      diff.patch        ← git diff BASE_SHA..tip  (the frozen review diff)
      manifest.json     ← ground truth for this case
```

- `BASE_SHA` — the pinned, known-good base commit. Recorded in `corpus/BASE_SHA`.
- The commit bank is a set of commits each parented (directly or via rebase) on `BASE_SHA`, never merged into
  it. They are *ingredients*, not history.

## 2. Commit trailer grammar

Every bank commit carries machine-readable [git trailers](https://git-scm.com/docs/git-interpret-trailers) in
its message, so commits are selectable by query without parsing prose. Required trailers:

```
<subject: human summary of what this commit introduces>

<body: rationale — for an issue commit, WHY this is an instance of the tagged item(s),
 and how it was injected; for a decoy, why it looks suspicious but is fine>

Kind: issue | decoy | clean
Area: <theme-tag>                # e.g. "auth-session", "config-loader"  (coherence unit)
Issue-Items: 16.4.4, 16.1.1      # checklist IDs (omit/empty for clean/decoy)
Near-Miss-Of: 16.7.6             # optional; for decoys that mimic a smell but are valid
Case-Hint: <free text>           # optional notes for case assembly
```

Rules:
- `Kind: issue` ⇒ `Issue-Items` non-empty (≥1 checklist ID). **Multiple IDs allowed** (multi-tag ground truth).
- `Kind: decoy` ⇒ `Issue-Items` empty; `Near-Miss-Of` may name the smell it mimics.
- `Kind: clean` ⇒ realistic filler with no defect and no near-miss.
- `Area` is required on every commit — it is the coherence unit a case is assembled within.
- One commit introduces **exactly one** planted issue (or none). This is what makes ground truth precise and
  the diff composable.

`bank.jsonl` is a generated mirror (one row per commit: `{sha, subject, kind, area, items[], nearMissOf,
files[], addedLines}`) so the case builder can query without shelling out to `git log` per commit.

## 3. Case-builder contract

Input: a **case spec** — the items the case must exercise, an area, and a target density.

```jsonc
// case-spec.json
{
  "id": "auth-session-C1-vs-D1",
  "area": "auth-session",
  "require_items": ["<every item in the C-group and D-group this case tests>"],
  "target_density": { "lines_per_issue": 80, "tolerance": 0.25 },
  "seed": 12345            // for reproducible decoy/clean padding selection
}
```

Algorithm:

1. **Select issue commits**: from `bank.jsonl`, pick the minimal set of `Kind: issue` commits in `Area` that
   together cover every ID in `require_items` (one planted instance per required item).
2. **Compute padding**: let `Lissue` = added lines from the issue commits; target total `Ltotal =
   issues × lines_per_issue`. Select `Kind: clean`/`decoy` commits in the same `Area` (seeded, deterministic)
   until added lines reach `Ltotal ± tolerance`. Always include ≥1 `decoy`/near-miss so precision is testable.
3. **Compose**: create a scratch branch at `BASE_SHA`; `git cherry-pick` the selected commits in a stable order
   (issues interleaved among padding so they don't cluster); resolve nothing manually — if a cherry-pick
   conflicts, the two commits touch overlapping lines and are **incompatible in one case** → the builder skips
   that pairing and reports it (commits in one case must be independently applicable).
4. **Emit**:
   - `diff.patch` = `git diff BASE_SHA..tip`
   - `manifest.json` (below)

The builder is a thin wrapper over `git cherry-pick` + `git diff`. No diff/patch merging logic.

### manifest.json (ground truth)

```jsonc
{
  "case_id": "auth-session-C1-vs-D1",
  "base_sha": "…",
  "area": "auth-session",
  "planted": [
    {
      "commit": "<sha>",
      "items": ["16.4.4", "16.1.1"],   // multi-tag: a report matching ANY is credited
      "files": ["src/auth/session.ts"],
      "lines": [142, 167],             // range in the COMPOSED diff (builder maps post-cherry-pick)
      "rationale": "…"
    }
  ],
  "decoys": [
    { "commit": "<sha>", "near_miss_of": "16.7.6", "files": ["…"], "lines": [...] }
  ],
  "stats": { "total_added_lines": 412, "planted_issues": 5, "lines_per_issue": 82 }
}
```

The scorer uses `planted[].items` as the credit set (any-tag match) and `decoys` to detect false positives
(a report landing on a decoy/near-miss is a precision miss).

## 4. Density calibration

`lines_per_issue` should be set from a quick survey of real PRs in the chosen repo's history (e.g. median added
lines per reviewer-flagged issue), recorded in `corpus/density-calibration.md`. The default starting target is
deliberately sparse (one planted issue per several dozen diff lines) to avoid the "everything is a bug"
shortcut. This is a knob, not a constant — record the value used and the basis for it.

## 5. Reproducibility

- Pin `BASE_SHA`, the model, temperature (0), and the frozen prompt preamble.
- Case assembly is **seeded** (decoy/clean selection is deterministic given the seed).
- `diff.patch` + `manifest.json` are committed to this project's repo so a case is replayable without the OSS
  clone present.
- The OSS `repo/` clone at `BASE_SHA` is referenced by SHA; a `make corpus` step (later) reproduces it.

## 6. Open implementation notes (for the later harness step, not this iteration)

- Choosing the OSS repo: needs permissive license, idiomatic code, and a domain with enough surface to plant
  the injectable items across a few areas. Candidate selection is its own task.
- Injecting clean instances of each item is the labor bottleneck; expect to iterate on `bank.jsonl` and to
  reject items that can't be injected convincingly (feed back into `item-universe.md`).
- Line-range mapping after cherry-pick: the builder must translate each planted issue's original line range to
  its range in the composed diff (git's patch offsets) — needed for `manifest.lines`.
