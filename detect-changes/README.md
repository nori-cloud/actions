# Detect Changes

## What am I looking at?

A composite action that selects changed apps from an inline JSON list or a
repository file. Input and output definitions live in [`action.yml`](action.yml).
Existing callers using `app-list`, `base`, and `ref` remain supported.

## How do I select apps for a pull request?

Check out the PR head with `fetch-depth: 0`, then call the action:

```yaml
- uses: nori-cloud/actions/detect-changes@<reviewed-commit>
  id: changes
  with:
    app-list-file: .github/apps.json
    base: ${{ github.event.pull_request.base.sha }}
    include-root-changes: 'true'
```

Provide exactly one of `app-list` and `app-list-file`. The file contains the same
array accepted by `app-list`; `paths` entries match exact paths or directory
prefixes, optionally ending in `/**`, not arbitrary globs.

Use `steps.changes.outputs.changed_apps` for the build matrix and
`steps.changes.outputs.has-changes` to skip empty matrices. The `apps` output
always contains the full configuration.

## How do I include missed deliveries?

For delivery on a branch push, check out that commit with full history, grant
`contents: read` and `actions: read`, then call:

```yaml
- uses: nori-cloud/actions/detect-changes@<reviewed-commit>
  id: changes
  with:
    app-list-file: .github/apps.json
    include-root-changes: 'true'
    delivery-workflow: cd.yml
    token: ${{ github.token }}
```

This compares against the last successful push run of that workflow on
`delivery-branch` (default `main`). It rejects a ref that does not match the
fetched branch tip. Do not supply `base` with `delivery-workflow`.

No previous successful run, or history rewritten past its commit, selects all
apps. Failed, cancelled, and replaced pending runs do not advance the base.
Only use this mode when workflow success means every selected app was delivered;
conditional deployment skips would otherwise hide undelivered changes.

## Which shared files select every app?

With `include-root-changes: 'true'`, any root file or file under `.github/`
selects all apps. This includes lockfiles and workflow changes. Other shared
directories must appear in each affected app's `paths`.

Without a base, all configured apps are selected. An empty list always returns
`has-changes=false`.
