# Corpus Source

The Phase-1 corpus base codebase. See [`../docs/corpus-spec.md`](../docs/corpus-spec.md).

## Repo

- **Project:** cal.com
- **Upstream:** `https://github.com/calcom/cal.com.git`
- **BASE_SHA:** `92f44dcea7ff19e9123a30c63c167a2938df5a55` (also in [`BASE_SHA`](BASE_SHA))
- **Language:** pure TypeScript / TSX

## Why cal.com (vs other CRB repos)

Chosen from the CRB repos reused for qualops evals (cal.com, sentry, grafana, keycloak). cal.com is the
only **pure TS/TSX** option, so it can host the *entire* injectable item pool from
[`../item-universe.md`](../item-universe.md) — including the JS/TS-footgun symptom family (17.6.4,
17.6.6, 17.6.7, 17.6.9) that one Phase-1 cohesive group is built around. grafana (Go) and keycloak
(Java) structurally cannot host those items; sentry is half-Python. cal.com also matches the prior
experiment's TS/JS setting, keeping detection behavior comparable.

## License caveat — IMPORTANT

cal.com is **AGPLv3**, with commercial-only directories under `ee/` (and parts of
`packages/features/ee`). This is acceptable for **internal research / evaluation only** (we do not
redistribute the code or derived diffs publicly).

**Rule: plant issues only in non-`ee/` paths.** Case assembly and the commit bank must exclude `ee/`
directories.

Fallback if a permissive license becomes a hard requirement: **keycloak (Apache-2.0)** — at the cost of
the JS-footgun symptom family.

## Working clone

The working clone is the qualops CRB checkout at
`~/code/eggai/qualops/evals/datasets/crb/repos/calcom/cal.com`, already at `BASE_SHA`.

Per [`../docs/corpus-spec.md`](../docs/corpus-spec.md) §5, the corpus references the repo **by SHA, not
by copying it in**. To reproduce `corpus/repo/` independently:

```sh
git clone https://github.com/calcom/cal.com.git corpus/repo
git -C corpus/repo checkout 92f44dcea7ff19e9123a30c63c167a2938df5a55
```

A `make corpus` step automating this is later harness work (`corpus-spec.md` §6).
