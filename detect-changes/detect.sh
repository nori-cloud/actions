#!/usr/bin/env bash
set -euo pipefail

if [[ -n "$APP_LIST" && -n "$APP_LIST_FILE" ]] || [[ -z "$APP_LIST" && -z "$APP_LIST_FILE" ]]; then
  echo '::error::Provide exactly one of app-list or app-list-file.'
  exit 1
fi

if [[ -n "$APP_LIST_FILE" ]]; then
  apps=$(jq -c '.' "$APP_LIST_FILE")
else
  apps=$(jq -c '.' <<< "$APP_LIST")
fi
jq -e 'type == "array" and all(.[]; type == "object" and (.app | type == "string"))' \
  <<< "$apps" > /dev/null
echo "apps=$apps" >> "$GITHUB_OUTPUT"

if [[ -n "$DELIVERY_WORKFLOW" ]]; then
  if [[ -n "$BASE" || -z "$GH_TOKEN" ]]; then
    echo '::error::delivery-workflow requires token and cannot be combined with base.'
    exit 1
  fi
  if [[ $(git rev-parse "$REF^{commit}") != $(git rev-parse "origin/$DELIVERY_BRANCH^{commit}") ]]; then
    echo '::error::Delivery is outdated. Run the workflow for the latest branch commit.'
    exit 1
  fi
  # Include changes missed by failed or superseded deliveries.
  BASE=$(gh api "repos/$GITHUB_REPOSITORY/actions/workflows/$DELIVERY_WORKFLOW/runs" \
    --method GET -f "branch=$DELIVERY_BRANCH" -f event=push -f status=success -f per_page=1 \
    --jq '.workflow_runs[0].head_sha // ""')
  if [[ -n "$BASE" ]] && ! git merge-base --is-ancestor "$BASE" "$REF"; then
    BASE=''
  fi
fi

matrix="$apps"
if [[ -n "$BASE" ]]; then
  files=$(git diff --name-only -z "$BASE...$REF" | jq -Rs 'split("\u0000") | map(select(length > 0))')
  matrix=$(jq -c --argjson files "$files" --arg root "$INCLUDE_ROOT_CHANGES" '
    if $root == "true" and any($files[]; (contains("/") | not) or startswith(".github/")) then .
    else
      [.[] |
        (if .paths then (.paths | map(rtrimstr("/**")))
         elif .dockerfile then [(.dockerfile | split("/") | .[:-1] | join("/"))]
         else ["apps/" + .app] end) as $prefixes |
        select(any($files[]; . as $file |
          any($prefixes[]; . as $prefix | $file == $prefix or ($file | startswith($prefix + "/")))))
      ]
    end' <<< "$apps")
fi

echo "changed_apps=$matrix" >> "$GITHUB_OUTPUT"
echo "has-changes=$(jq 'length > 0' <<< "$matrix")" >> "$GITHUB_OUTPUT"
