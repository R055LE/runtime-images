# runtime-images

Production language runtime images for the R055LE fleet. This repository owns
the composition, validation, publication, and rebuild cadence. It does not
pretend to remove every dependency: Python, OpenSSL, Wolfi, apko, GitHub
Actions, and GHCR remain explicit trust boundaries.

The first release family is Python 3.14 on amd64:

| Tag | Purpose | Contract |
| --- | --- | --- |
| `3.14` | Production runtime discovery | Non-root, no shell, package manager, pip, or compiler |
| `3.14-build` | ABI-matched dependency builder | Root build environment with `uv` and a compiler |

The build image is never a production runtime. Rolling tags are for discovery.
Consumers pin both variants by digest and verify the producing workflow before
building.

## Use an image

Choose the immutable digest from a GitHub release, then verify its origin and
attestations:

```bash
image='ghcr.io/r055le/runtime-python@sha256:<digest>'
identity='https://github.com/R055LE/runtime-images/.github/workflows/release.yml@refs/heads/main'

cosign verify \
  --certificate-identity "$identity" \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  "$image"
gh attestation verify "oci://$image" --repo R055LE/runtime-images
```

Use the matching runtime and build records from one release manifest. Do not
combine independently selected tags.

## Develop

Requirements are Docker, Python 3, and Trivy. The apko tool itself runs from a
digest-pinned container.

```bash
make unit    # policy and mutation tests, no Docker
make build   # resolve locks, build images, and load them locally
make verify  # runtime and native-extension build contracts
make scan    # exact Trivy reports and the fleet vulnerability gate
make ci      # the complete validation path
```

`make ci` scans the exact local images later pushed by the release workflow.
No scanner finding is suppressed. HIGH and CRITICAL findings are recorded in
[`docs/known-findings.md`](docs/known-findings.md) and evaluated using CISA KEV,
EPSS, fix age, and evidence-review age. Missing evidence fails closed.

## Release contract

The release workflow runs daily, after relevant changes reach `main`, and on
manual dispatch. It resolves signed Wolfi packages, checks that shared packages
match exactly, builds both variants, exercises the contracts, and runs the risk
gate. It then publishes immutable image tags, signs their digests, attaches
provenance and SBOM attestations, moves the rolling discovery tags, and creates
a GitHub release containing:

- both exact package locks
- both SPDX SBOMs and Trivy reports
- full package inventories and the delta from the prior release
- source revision, artifact hashes, and immutable image digests

An unchanged release is still rebuilt and scanned against current vulnerability
data before it becomes a no-op. A failure leaves the last verified release in
place and opens or updates one issue.

The boundary and its tradeoffs are recorded in
[runbook decision 0027](https://github.com/R055LE/runbook/blob/main/decisions/0027-own-runtime-image-composition.md).

## License

MIT, see [LICENSE](LICENSE).
