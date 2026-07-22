#!/usr/bin/env python3
"""Compose a Phase-1 review case from the labeled commit bank (corpus-spec.md §3).

A *case* is a fixed, PR-sized diff at realistic issue density that plants a clean
instance of every item a (C-group, D-group) contrast needs, padded with decoy/clean
commits so the density looks like a real PR. This builder is a thin, deterministic
wrapper over `git cherry-pick` + `git diff`:

  1. read a case-spec (id, area, require_items, target_density, seed)
  2. from bank.jsonl, pick the minimal set of Kind:issue commits IN `area` covering
     every id in require_items (one planted instance per required item)
  3. seed-select Kind:decoy/clean commits in the same area until added lines reach
     issues * lines_per_issue (within tolerance); always include >=1 decoy
  4. cherry-pick issues interleaved among padding onto a scratch branch at BASE_SHA
  5. emit  diff.patch = git diff BASE_SHA..tip
     and   manifest.json = ground truth (planted[], decoys[], stats)

No patch/merge logic: if a cherry-pick conflicts, the two commits are incompatible in
one case; the builder aborts and reports the offending pair (commits in one case must be
independently applicable — the bank is built so they are).

Operates on the nested corpus repo (default corpus/repo); never touches the project repo.
Deterministic given `seed`. Safe to run anywhere (pure git, no network / no `claude`).
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def git(repo, *args, check=True, capture=True):
    """Run a git command in `repo`. Returns stdout (stripped) when capturing."""
    res = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=capture,
        text=True,
    )
    if check and res.returncode != 0:
        err = (res.stderr or res.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed:\n{err}")
    return (res.stdout or "").strip() if capture else ""


def load_bank(path):
    rows = []
    with open(path) as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                die(f"{path}:{ln}: invalid JSON ({e})")
    return rows


def select_issue_commits(bank, area, require_items):
    """Minimal set of Kind:issue commits in `area` covering every required item.

    Greedy set cover: repeatedly pick the commit covering the most still-uncovered
    required items (deterministic tie-break by sha). Each required item must be covered
    by at least one planted instance.
    """
    candidates = [
        r for r in bank
        if r["kind"] == "issue" and r["area"] == area and set(r["items"]) & set(require_items)
    ]
    need = set(require_items)
    chosen = []
    chosen_shas = set()
    while need:
        best = None
        best_gain = -1
        for r in sorted(candidates, key=lambda r: r["sha"]):
            if r["sha"] in chosen_shas:
                continue
            gain = len(set(r["items"]) & need)
            if gain > best_gain:
                best, best_gain = r, gain
        if best is None or best_gain == 0:
            die(
                f"cannot cover items {sorted(need)} with issue commits in area '{area}'. "
                f"Plant them (or fix require_items)."
            )
        chosen.append(best)
        chosen_shas.add(best["sha"])
        need -= set(best["items"])
    return chosen


def select_padding(bank, area, chosen_shas, issue_lines, num_issues, density, rng):
    """Seed-select decoy/clean commits in `area` to reach the target density.

    Target total added lines = num_issues * lines_per_issue. Pick padding commits
    (decoys preferred first so precision is always testable, then clean) in a shuffled,
    seeded order, stopping once we are within tolerance of the target or run out.
    Returns (padding_rows, shortfall_lines) — shortfall > 0 means the area lacks enough
    padding to hit density (a case-builder input, per density-calibration.md).
    """
    lpi = density["lines_per_issue"]
    tol = density.get("tolerance", 0.25)
    target = num_issues * lpi
    low = target * (1 - tol)

    pool_decoy = [r for r in bank if r["kind"] == "decoy" and r["area"] == area and r["sha"] not in chosen_shas]
    pool_clean = [r for r in bank if r["kind"] == "clean" and r["area"] == area and r["sha"] not in chosen_shas]
    rng.shuffle(pool_decoy)
    rng.shuffle(pool_clean)

    padding = []
    total = issue_lines
    # Always seed at least one decoy if any exist (precision needs a near-miss target).
    ordered = pool_decoy + pool_clean
    for r in ordered:
        if total >= low:
            break
        padding.append(r)
        total += r["addedLines"]

    have_decoy = any(p["kind"] == "decoy" for p in padding)
    if not have_decoy and pool_decoy:
        padding.insert(0, pool_decoy[0])
        total += pool_decoy[0]["addedLines"]

    shortfall = max(0, int(round(low - total)))
    return padding, shortfall, target


def interleave(issues, padding, rng):
    """Order commits so issues don't cluster: shuffle padding, then insert issues at
    evenly-spaced positions among them. Deterministic given rng."""
    padding = list(padding)
    rng.shuffle(padding)
    out = list(padding)
    if not issues:
        return out
    step = (len(out) + 1) / (len(issues) + 1)
    for idx, iss in enumerate(issues):
        pos = int(round((idx + 1) * step)) + idx
        pos = min(max(pos, 0), len(out))
        out.insert(pos, iss)
    return out


DIFF_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def added_line_ranges(patch_text):
    """Map each file in a unified diff to the list of [start,end] added-line ranges in
    the NEW file (post-composition). Used for manifest.lines."""
    ranges = {}
    cur_file = None
    new_ln = 0
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            cur_file = line[6:]
            ranges.setdefault(cur_file, [])
            continue
        m = DIFF_HUNK_RE.match(line)
        if m:
            new_ln = int(m.group(1))
            continue
        if cur_file is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            rs = ranges[cur_file]
            if rs and rs[-1][1] == new_ln - 1:
                rs[-1][1] = new_ln
            else:
                rs.append([new_ln, new_ln])
            new_ln += 1
        elif line.startswith(" "):
            new_ln += 1
        # '-' lines don't advance the new-file counter
    return ranges


def commit_added_blocks(repo, sha):
    """The exact added-content lines a single commit introduces, per file, as a list of
    contiguous blocks (each a list of text lines). Used to locate the commit's own added
    text within the composed new-file, so ground-truth line ranges are per-commit even
    when several commits touch the same file."""
    patch = git(repo, "show", "--format=", "--unified=0", sha)
    blocks = {}
    cur_file = None
    cur = None
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            cur_file = line[6:]
            blocks.setdefault(cur_file, [])
            cur = None
            continue
        if line.startswith("@@"):
            cur = None
            continue
        if cur_file is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            if cur is None:
                cur = []
                blocks[cur_file].append(cur)
            cur.append(line[1:])
        elif line.startswith((" ", "-")):
            cur = None
    return blocks


def locate_blocks_in_composed(composed_new_lines, added_blocks, used):
    """Given the composed new-file's lines and a commit's added text blocks, return the
    [start,end] (1-based) ranges where each block sits in the composed file. `used` is a
    set of already-claimed line numbers so identical blocks from different commits don't
    collide. Returns [] if a block can't be located (shouldn't happen for non-overlapping
    commits)."""
    ranges = []
    n = len(composed_new_lines)
    for block in added_blocks:
        b = len(block)
        found = None
        for start in range(n - b + 1):
            if any((start + 1 + k) in used for k in range(b)):
                continue
            if composed_new_lines[start:start + b] == block:
                found = (start + 1, start + b)
                break
        if found:
            for k in range(found[0], found[1] + 1):
                used.add(k)
            ranges.append([found[0], found[1]])
    return ranges


def resolve_base(repo, spec, bank):
    """The local base commit onto which the case is composed.

    corpus/BASE_SHA records the *upstream* provenance SHA, but the corpus repo was seeded
    (git archive) so its base commit has a different local SHA. The base is the merge-base
    of the bank commits (all parented on it). `spec.base` (a ref/sha) overrides.
    """
    if spec.get("base"):
        return git(repo, "rev-parse", spec["base"])
    shas = [r["sha"] for r in bank]
    if not shas:
        die("bank is empty; cannot derive base commit")
    base = git(repo, "merge-base", *shas) if len(shas) > 1 else git(repo, "rev-parse", shas[0] + "^")
    return base


def read_provenance_sha():
    with open(os.path.join(PROJECT_ROOT, "corpus", "BASE_SHA")) as f:
        return f.read().strip()


def build(spec, repo, bank_path, out_dir, keep_branch):
    bank = load_bank(bank_path)
    base_sha = resolve_base(repo, spec, bank)
    provenance_sha = read_provenance_sha()

    by_sha = {r["sha"]: r for r in bank}
    area = spec["area"]
    require = spec["require_items"]
    density = spec.get("target_density", {"lines_per_issue": 80, "tolerance": 0.25})
    rng = random.Random(spec.get("seed", 0))

    issues = select_issue_commits(bank, area, require)
    chosen = {r["sha"] for r in issues}
    issue_lines = sum(r["addedLines"] for r in issues)
    padding, shortfall, target = select_padding(
        bank, area, chosen, issue_lines, len(issues), density, rng
    )
    order = interleave(issues, padding, rng)

    # Compose on a scratch branch at BASE_SHA.
    branch = f"case/{spec['id']}"
    git(repo, "checkout", base_sha, "--quiet")  # detach
    existing = git(repo, "branch", "--list", branch)
    if existing:
        git(repo, "branch", "-D", branch)
    git(repo, "checkout", "-b", branch, "--quiet")
    try:
        for r in order:
            res = subprocess.run(
                ["git", "-C", repo, "cherry-pick", r["sha"]],
                capture_output=True, text=True,
            )
            if res.returncode != 0:
                git(repo, "cherry-pick", "--abort", check=False)
                die(
                    f"cherry-pick conflict on {r['sha'][:10]} ({r['subject']!r}). "
                    f"Commits in one case must be independently applicable; this pairing "
                    f"is incompatible in area '{area}'."
                )
        tip = git(repo, "rev-parse", "HEAD")
        patch = git(repo, "diff", f"{base_sha}..{tip}")
        # Snapshot the composed new-file contents (for per-commit line-range mapping) and
        # each planted/decoy commit's own added blocks, before leaving the branch.
        touched_files = set()
        for r in issues + [p for p in padding if p["kind"] == "decoy"]:
            touched_files.update(r["files"])
        composed_files = {}
        for fpath in touched_files:
            composed_files[fpath] = git(repo, "show", f"{tip}:{fpath}").split("\n")
        own_blocks = {r["sha"]: commit_added_blocks(repo, r["sha"]) for r in issues + padding}
    finally:
        git(repo, "checkout", base_sha, "--quiet")
        if not keep_branch:
            git(repo, "branch", "-D", branch, check=False)

    total_added = sum(
        1 for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++")
    )

    # Ground truth: map each commit's OWN added text blocks onto the composed new-file, so
    # ranges are per-commit even when several commits touch the same file. `used_lines`
    # per file prevents two commits from claiming the same lines.
    used_lines = {f: set() for f in composed_files}

    def ranges_for(r):
        out = []
        for fpath in r["files"]:
            blocks = own_blocks.get(r["sha"], {}).get(fpath, [])
            out.extend(
                locate_blocks_in_composed(composed_files.get(fpath, []), blocks, used_lines.setdefault(fpath, set()))
            )
        return sorted(out)

    planted = []
    for r in issues:
        planted.append({
            "commit": r["sha"],
            "items": r["items"],
            "files": r["files"],
            "lines": ranges_for(r),
            "subject": r["subject"],
        })
    decoys = []
    for r in padding:
        if r["kind"] != "decoy":
            continue
        decoys.append({
            "commit": r["sha"],
            "near_miss_of": r["nearMissOf"],
            "files": r["files"],
            "lines": ranges_for(r),
        })

    manifest = {
        "case_id": spec["id"],
        "base_sha": base_sha,
        "upstream_base_sha": provenance_sha,
        "area": area,
        "planted": planted,
        "decoys": decoys,
        "clean": [
            {"commit": r["sha"], "files": r["files"]}
            for r in padding if r["kind"] == "clean"
        ],
        "stats": {
            "total_added_lines": total_added,
            "planted_issues": len(issues),
            "lines_per_issue": round(total_added / len(issues), 1) if issues else None,
            "target_lines_per_issue": density["lines_per_issue"],
            "target_total_added": target,
            "padding_shortfall_lines": shortfall,
            "in_density_band": shortfall == 0,
        },
        "commit_order": [r["sha"] for r in order],
        "require_items": require,
        "seed": spec.get("seed", 0),
    }

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "diff.patch"), "w") as f:
        f.write(patch + "\n")
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="path to case-spec.json")
    ap.add_argument("--repo", default=os.path.join(PROJECT_ROOT, "corpus", "repo"),
                    help="path to the corpus git repo (default corpus/repo)")
    ap.add_argument("--bank", default=os.path.join(PROJECT_ROOT, "corpus", "bank.jsonl"),
                    help="path to bank.jsonl")
    ap.add_argument("--out", default=None,
                    help="output dir (default corpus/cases/<case-id>)")
    ap.add_argument("--keep-branch", action="store_true",
                    help="keep the scratch case/<id> branch instead of deleting it")
    ap.add_argument("--print-manifest", action="store_true",
                    help="print the manifest to stdout too")
    args = ap.parse_args()

    if not os.path.isdir(os.path.join(args.repo, ".git")):
        die(f"--repo {args.repo} is not a git repo (seed it via corpus/SOURCE.md)")

    with open(args.spec) as f:
        spec = json.load(f)
    out_dir = args.out or os.path.join(PROJECT_ROOT, "corpus", "cases", spec["id"])

    manifest = build(spec, args.repo, args.bank, out_dir, args.keep_branch)
    s = manifest["stats"]
    print(f"built case '{spec['id']}' → {out_dir}")
    print(f"  planted {s['planted_issues']} issues, {s['total_added_lines']} added lines "
          f"({s['lines_per_issue']} lines/issue; target {s['target_lines_per_issue']})")
    if not s["in_density_band"]:
        print(f"  ⚠ density shortfall: need ~{s['padding_shortfall_lines']} more padding lines in "
              f"area '{manifest['area']}' to reach the target band")
    if args.print_manifest:
        print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
