---
title: Set up CI/CD
description: Configure checks, image publishing, and environment image-tag updates using Factory's workflows.
---

## What am I looking at?

Set up GitHub Actions using [Factory](https://github.com/nori-cloud/factory) as
the reference. The pipeline ends at updating image pins in `nori-cloud/apps`.

```mermaid
sequenceDiagram
    actor Developer
    participant Source as App repository
    participant Actions as GitHub Actions
    participant Registry as GHCR
    participant GitOps as nori-cloud/apps

    Developer->>Source: Open pull request
    Source->>Actions: CI checks and changed-app builds (no push)
    Actions-->>Source: Report results
    Developer->>Source: Merge to main
    Source->>Actions: Build changed apps
    Actions->>Registry: Push commit-SHA images
    Actions->>GitOps: Update dev image pins
    Actions->>Source: Update dev tags
    Developer->>Actions: Manually promote selected apps
    Actions->>Registry: Verify existing images (no rebuild)
    Actions->>GitOps: Update prod image pins
    Actions->>Source: Update prod tags and create releases
```

## What do I need?

- GitHub Actions enabled, with access to `nori-cloud/actions`.
- A pnpm project with `packageManager` in `package.json`, a committed lockfile,
  and a sanity command. `setup` uses Node.js 22 and installs with
  `--frozen-lockfile --ignore-scripts`.
- A Dockerfile per app, normally `apps/<app>/Dockerfile`.
- Dev and prod overlay files prepared using [Set up GitOps apps](set-up-gitops-apps.md).

## How do I configure access?

Use the existing [gh-action-gitops-app](https://github.com/organizations/nori-cloud/settings/apps/gh-action-gitops-app),
which has **Contents: Read and write**:

| Public identifier | Value |
| --- | --- |
| App ID | `5222975` |
| Client ID | `Iv23lioHkMjuxCBtDmA1` |

Install the App on `nori-cloud/apps`, then configure these Actions secrets in
the **application repository** (for example, `nori-cloud/koukou`), not the GitOps
repository:

Retrieve the Client ID and private key from the
[GitOps App credentials in Infisical](https://infisical.hoki-sole.ts.net/organizations/ebbe526b-20af-410a-a392-1a668e8208a4/projects/secret-management/ba06b3c1-1db1-4809-a433-74afbb6fafdf/overview).
Copy the private key directly into GitHub Actions secrets without printing it
in logs, pasting it into chat, or committing it.

- `GITOPS_APP_ID`: use the Client ID above (recommended by GitHub). The numeric
  App ID also works; the token action still calls this input `app-id`.
- `GITOPS_APP_PRIVATE_KEY`: the App's complete PEM private key from Infisical.
  New keys are generated from the App's settings page.

Both identifiers are safe to commit. The current workflow callers read
`GITOPS_APP_ID` from secrets for compatibility; it is not a confidential value.
The [installation-token flow](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app)
requires a private key to sign a JWT. An OAuth client secret cannot replace it.
If using environment secrets instead, configure every deployment environment
that needs access (`dev` and `prod`). Treat missing credentials as a setup
blocker, not a validated deployment.

Allow the App to push under the GitOps repository's branch rules. Allow the
workflow's `GITHUB_TOKEN` **packages: write** for GHCR and **contents: write**
for tags and releases. Tag rules must
permit moving `<app>-dev` and `<app>-prod`.

## Which workflow files should I copy?

Copy these into your application's `.github/workflows/`, keeping their names:

| Factory file | Purpose |
| --- | --- |
| [ci.yaml](https://github.com/nori-cloud/factory/blob/main/.github/workflows/ci.yaml) | Pull request checks |
| [cd.yaml](https://github.com/nori-cloud/factory/blob/main/.github/workflows/cd.yaml) | Dev image-pin updates on merge |
| [prod-promote.yaml](https://github.com/nori-cloud/factory/blob/main/.github/workflows/prod-promote.yaml) | Manual production promotion |

Image builds call the shared
[`build-image` action](../README.md#how-do-i-build-an-image) from `nori-cloud/actions`
under `steps`, after checkout; do not copy a local image workflow. Factory
references `@main`; pin a reviewed commit containing the action for production.

## What should I change?

1. Replace `app-list` in both CI and CD with your apps, or keep one JSON file
   and pass `app-list-file` to both calls. For example:

   ```json
   [{"app": "outpost", "paths": ["apps/outpost/**", "packages/ui/**"]}]
   ```

   `app` must match the image name and GitOps directory. `paths` are directory
   prefixes, not arbitrary globs; include shared packages. Set `dockerfile`
   when it is outside `apps/<app>/Dockerfile`. Every selected app needs overlays;
   Factory's `deploy` field does not filter the deployment matrix.
2. Replace `pnpm turbo lint typecheck build` if your sanity command differs.
3. Review change detection: CI uses `origin/main` with full history; Factory CD
   uses `HEAD^1` with two commits fetched, covering only the last commit.
   Adjust the comparison for multi-commit pushes. Its CD trigger only includes
   `apps/**` and `packages/**`, not root lockfile changes.
   The shared [change detector](../detect-changes/README.md) supports opt-in
   root-file detection and comparison against the last successful delivery.
   These require a commit containing the new inputs; change the caller's
   trigger and fetch depth as described there rather than copying local scripts.
4. Replace the promotion app inputs, `PROMOTE_*` variables, and matching shell
   selection lines together. Leave `sha` blank to follow each app's dev tag,
   or supply a full SHA with an existing image.

Two current limits: the GitOps action authenticates specifically for
`nori-cloud/apps`, and concurrent overlay pushes can conflict. Start with one
app and one update at a time.

## How do I verify it?

1. Open a PR changing the app: sanity and image builds pass without publishing.
2. Merge: confirm the full-SHA image in GHCR, the dev overlay's `newTag`, and
   `<app>-dev` plus its timestamped tag.
3. In **Actions → Prod Promote → Run workflow**, select the app and enable
   `dry-run`. Confirm the planned overlay and tag changes.
4. Run again without dry-run. Confirm the prod image pin, `<app>-prod`, its
   timestamped tag, and the GitHub Release.

## Is there any external references to this documentation?

- [Factory workflows](https://github.com/nori-cloud/factory/tree/main/.github/workflows) — complete examples.
- [Action definitions](../README.md#actions) — available shared actions.
