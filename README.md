# nori-cloud/actions

Shared GitHub Actions for nori-cloud repositories.

## Actions

| Action | Purpose |
| --- | --- |
| `setup` | Install pnpm dependencies with Node.js caching |
| `detect-changes` | Filter an app matrix to changed applications |
| `build-image` | Build and optionally publish an app image to GHCR |
| `gitops-update-overlay` | Update a Kustomize image tag in `nori-cloud/apps` |
| `move-tag` | Move an environment tag and create a timestamped tag |

## How do I build an image?

Call [`build-image`](build-image/action.yml) under `steps` after checking out
your repository:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: nori-cloud/actions/build-image@main
        with:
          app: outpost
          push: 'true'
          token: ${{ secrets.GITHUB_TOKEN }}
```

`app` is required. `dockerfile` defaults to `apps/<app>/Dockerfile`; `push`
defaults to `'false'`. Set `push: 'true'` and pass `token` to publish; build-only
runs skip registry login and need no token. Published images use full and 7-character commit-SHA tags
under `ghcr.io/<repository-owner>/<app>`.

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

For production workflows, pin actions to a commit SHA
containing them and keep the human-readable version in a comment.

## Versioning

Changes are released with major version tags such as `v1`. Breaking input or
output changes require a new major version.

## How do I install the OpenCode skill?

Add this catalog to the `skills` array in your OpenCode configuration, keeping
existing entries:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["https://raw.githubusercontent.com/nori-cloud/actions/main/skills/"]
}
```

Ask OpenCode to use `@set-up-cicd` to configure a repository with the shared
composite actions. The skill reads the current guide and Factory workflows
instead of shipping duplicate templates. GitHub CLI access to those repositories
is required.

The catalog works after its files are published at the configured ref. For a
reviewed, fixed version, replace `main` in the URL with a commit SHA.

When changing a skill, increment its `version` in [`skills/index.json`](skills/index.json)
so OpenCode refreshes its cache. Run `python3 tests/validate-skills.py` before publishing.
