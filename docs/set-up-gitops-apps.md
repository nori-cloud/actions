---
title: Set up GitOps apps
description: Configure shared application bases, dev/prod overlays, and Argo CD source paths in nori-cloud/apps.
---

## What am I looking at?

Configure [nori-cloud/apps](https://github.com/nori-cloud/apps) using `outpost`
as the reference. This covers repository files and high-level Argo CD
registration—not installation or cluster operations.

## How do I organize an app?

```text
outpost/
├── base/           # Shared Deployment, Service, and secret references
└── overlays/
    ├── dev/        # Dev namespace, image pin, patches, and routing
    └── prod/       # Prod namespace, image pin, patches, and routing
```

1. Create `<app>/base/kustomization.yaml`, listing the shared resource files
   under `resources`. Use [Outpost's base](https://github.com/nori-cloud/apps/tree/main/outpost/base)
   as a reference; adapt resource names, ports, health checks, and secret mappings.
2. Set the Deployment image to `ghcr.io/nori-cloud/<app>`, matching CI/CD.
   Keep environment-specific tags and settings out of the base.
3. Create both overlay directories. Each includes `../../base` rather than
   copying its Deployment and Service.

## What belongs in each overlay?

Outpost's dev `kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: nori-cloud-dev

resources:
  - ../../base
  - ingress.yaml

images:
  - name: ghcr.io/nori-cloud/outpost
    newTag: 5159ebbdbc78fcd1b742b30eacc395ab6aa0aa5b

patches:
  - path: deployment-patch.yaml
```

- Match `images.name` to the base image and pin an already-published commit SHA.
- Put changed fields, such as resource limits, in patch files matching the
  base resource and container names.
- For prod, use `namespace: nori-cloud-prod` and keep its image pin independent.
  Outpost includes `httproute.yaml` instead of dev's `ingress.yaml`; adapt
  hostnames and routing references to your app.

CI/CD updates `<app>/overlays/<environment>/kustomization.yaml`. Its updater
replaces every `newTag:` line, so keep unrelated image pins out of that file.
See [Set up CI/CD](set-up-cicd.md) for publishing and promotion.

Reference existing shared dependencies (`ghcr-credentials`, `infisical-secret`,
`network`, and `pg-cluster`) rather than copying them into every app. Keep
credentials out of Git and check that secret references use the correct
namespace and environment.

## How do I configure Argo CD?

Assume Argo CD, the destination cluster, and namespaces already exist:

1. Connect `https://github.com/nori-cloud/apps.git`, using read-only credentials
   if private. This is separate from CI/CD's write credentials.
2. Create one Application per app and environment, using a project that permits
   the repository and destination:

   | Application | `source.path` | `destination.namespace` |
   | --- | --- | --- |
   | `outpost-dev` | `outpost/overlays/dev` | `nori-cloud-dev` |
   | `outpost-prod` | `outpost/overlays/prod` | `nori-cloud-prod` |

3. Set `source.repoURL` to the repository URL, `source.targetRevision` to `main`,
   and the destination to the intended registered cluster. The image SHA belongs
   in the overlay, not `targetRevision`.
4. Let Argo CD detect Kustomize from the overlay. Start with manual sync and
   review its diff; choose automated sync, pruning, and self-healing separately.
   Register prod only when its pinned image is approved.

Register shared dependency overlays separately if they are not already managed.
Adding a directory does not automatically create an Argo CD Application.

## How do I check it?

From the `nori-cloud/apps` checkout, replace `outpost` with your app and run:

```sh
kubectl kustomize outpost/overlays/dev
kubectl kustomize outpost/overlays/prod
```

Check each output's namespace, image, patches, secret references, and routes.
Rendering does not verify that external dependencies exist. Open a PR, then
review the matching Argo CD Application's manifests and diff before syncing.

## Is there any external references to this documentation?

- [Outpost overlays](https://github.com/nori-cloud/apps/tree/main/outpost/overlays) — complete environment examples.
- [Argo CD Application specification](https://argo-cd.readthedocs.io/en/stable/user-guide/application-specification/) — configuration fields.
