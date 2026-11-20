# nori-cloud/actions

Shared GitHub Actions for nori-cloud repositories.

## Actions

| Action | Purpose |
| --- | --- |
| `setup` | Install pnpm dependencies with Node.js caching |
| `detect-changes` | Filter an app matrix to changed applications |
| `gitops-update-overlay` | Update a Kustomize image tag in `nori-cloud/apps` |
| `move-tag` | Move an environment tag and create a timestamped tag |

## Usage

- [Set up CI/CD](docs/set-up-cicd.md): CI checks, image publishing, and promotion
  using Factory's pipeline.
- [Set up GitOps apps](docs/set-up-gitops-apps.md): repository layout,
  environment overlays, and high-level Argo CD configuration.

Reference a version tag or commit SHA from a workflow:

```yaml
- uses: nori-cloud/actions/setup@v1
  with:
    node-version: "22"
```

For production workflows, pin the action to a commit SHA and keep the
human-readable version tag in a comment.

## Versioning

Changes are released with major version tags such as `v1`. Breaking input or
output changes require a new major version.
