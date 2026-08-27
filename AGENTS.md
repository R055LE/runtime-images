# runtime-images

Production runtime image composition for the R055LE fleet. Read
[runbook decision 0027](https://github.com/R055LE/runbook/blob/main/decisions/0027-own-runtime-image-composition.md)
before changing the image or release contract.

## Quick checks

```bash
make unit
make build
make verify
make scan
make ci
```

## Fleet rules that govern this repo

Descriptions and topics come from `R055LE/runbook/catalog/fleet.yaml`. Routine
dependency automation is Dependabot only. GitHub Action and Docker references
stay pinned by digest or full commit SHA.

Work in one branch and one worktree under `.claude/worktrees/<slug>`, land one
pull request, then prune the worktree. Install
`scripts/pre-commit-worktree-guard` in the repository hook directory after a
fresh clone.

## Invariants

- A runtime and build image form one release set. Shared package versions and
  checksums must match exactly.
- Production consumers never deploy the build image.
- The release workflow publishes the already-tested local images. It does not
  rebuild between scanning and pushing.
- Immutable tags move only by creating a new release ID. Rolling tags are
  discovery pointers and consumers do not pin them.
- Release identity covers the exact package sets, image definitions, pinned
  apko tool, and deterministic build date.
- HIGH and CRITICAL findings are always reported. No `.trivyignore`,
  `ignore-unfixed`, or equivalent suppression belongs here.
- Known-finding metadata contains only image-level evidence. Application
  reachability claims do not belong in a shared runtime.
- Generated package locks are retained as release assets, not committed as
  routine source churn.
- A daily no-op still resolves, builds, tests, and scans before checking whether
  the release already exists.
