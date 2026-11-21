---
name: set-up-cicd
description: Set up or migrate repository CI/CD using nori-cloud composite actions and Factory's pipeline, including changed-app builds, GHCR publishing, GitOps updates, and manual production promotion.
---

## What am I looking at?

Configure a repository using the current nori-cloud CI/CD setup. Use shared
composite actions under job `steps`, not a reusable image-build workflow.

## What should I read first?

Read the target repository's instructions, existing workflows, package manager,
Dockerfiles, and GitOps configuration before editing anything.

Fetch the current sources below with GitHub CLI (`gh api repos/<owner>/<repo>/contents/<path> --jq '.content' | base64 --decode`),
or read a local checkout when available. Do not assume this installed skill's
directory contains the Actions repository or its documentation.

- [CI/CD guide](https://github.com/nori-cloud/actions/blob/main/docs/set-up-cicd.md) — setup requirements and known limits.
- [Actions reference](https://github.com/nori-cloud/actions/blob/main/README.md) — current usage and action contracts.
- [Factory workflows](https://github.com/nori-cloud/factory/tree/main/.github/workflows) — read `ci.yaml`, `cd.yaml`, and `prod-promote.yaml`.
- [GitOps guide](https://github.com/nori-cloud/actions/blob/main/docs/set-up-gitops-apps.md) — read when preparing overlays.

Inspect each action's `action.yml` at the ref you will use. If sources are
unavailable or disagree, report the blocker instead of inventing inputs or
silently restoring the old reusable workflow.

## How should I configure the repository?

1. Confirm apps, Dockerfile paths, shared-package paths, default branch,
   sanity command, and dev/prod overlay locations from the repository.
   Ask only for missing choices. Identify existing user changes and preserve them.
2. Adapt Factory's three workflows to the target repository. Keep the pipeline
   structure from the guide; do not blindly replace existing workflows.
   Keep app lists, promotion inputs, environment variables, and selection logic
   aligned. Do not assume an app's `deploy` field filters deployment.
3. Call `nori-cloud/actions/build-image` under `steps` after checkout, in a job
   with `runs-on`. Composite inputs are strings: CI builds without pushing;
   CD sets `push: 'true'` and passes `token: ${{ secrets.GITHUB_TOKEN }}`.
   Keep checkout and token permissions in the caller. Do not put `secrets`
   expressions inside composite action metadata.
4. Check change-detection refs and fetch depth, including multi-commit pushes,
   shared packages, and root lockfile changes. Explain any gaps rather than
   silently widening triggers. Check concurrent GitOps pushes and propose
   serialization where needed; selecting one app does not prevent overlapping runs.
5. Before declaring delivery ready, follow the guide's
   [access setup](https://github.com/nori-cloud/actions/blob/main/docs/set-up-cicd.md#how-do-i-configure-access).
   Use the existing GitOps App documented there, verify it is installed on
   `nori-cloud/apps`, and check that the application repository or each deployment
   environment provides `GITOPS_APP_ID` and `GITOPS_APP_PRIVATE_KEY`. The token
   action accepts the Client ID (recommended) or numeric App ID through its
   `app-id` input. Both identifiers are public; keep their values and settings
   link authoritative in the guide. This installation-token flow requires the
   private key, not an OAuth client secret. Never request secret values in chat
   or commit credentials.
   Also review GHCR access, branch/tag rules, and promotion. Report missing
   credentials and human-only setup as blockers. Do not claim deployment is
   verified merely because workflows were generated.
6. Pin shared actions to reviewed commits containing the required action.
   Verify refs instead of assuming every action is available at the same
   release tag. Never move release tags, publish, push, or trigger deployment
   unless explicitly requested.

## How do I verify completion?

- Validate workflow YAML and expressions with `actionlint`, and check that
  action paths, refs, inputs, checkout, and permissions match their contracts.
- Run the target repository's relevant sanity/build checks using its package
  manager. Report failures and anything you could not run.
- Follow the guide's end-to-end verification only when authorized. Promotion
  dry-run still accesses GHCR and the GitOps repository; it is not an offline test.
- Summarize changed files, configured apps, unresolved access requirements,
  checks performed, and remaining live verification. Do not push by default.
