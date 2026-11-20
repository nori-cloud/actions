"""Check the shared change detector using an isolated Git repository."""

import json
import os
import subprocess
import tempfile
from pathlib import Path


script = Path(__file__).resolve().parents[1] / "detect-changes/detect.sh"
apps = [
    {"app": "boubou", "paths": ["apps/boubou/**", "packages/**"]},
    {"app": "koukou", "paths": ["apps/koukou", "packages"]},
]


with tempfile.TemporaryDirectory(prefix="detect-changes-") as directory:
    repo = Path(directory)

    def git(*args):
        return subprocess.check_output(
            ["git", *args], cwd=repo, text=True, stderr=subprocess.PIPE
        ).strip()

    def commit(path):
        file = repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(file.read_text() + "\n" if file.exists() else "fixture\n")
        git("add", ".")
        git("commit", "-qm", "fixture")
        return git("rev-parse", "HEAD")

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Detector validation")
    git("config", "user.email", "validation@example.invalid")
    (repo / "apps.json").write_text(json.dumps(apps))
    base = commit("apps/boubou/source.ts")
    app_commit = commit("apps/koukou/source.ts")
    shared_commit = commit("packages/client/source.ts")
    root_commit = commit("pnpm-lock.yaml")
    workflow_commit = commit(".github/workflows/ci.yml")
    docs_commit = commit("docs/guide.md")
    newline_commit = commit("apps/boubou/line\nbreak.ts")
    git("update-ref", "refs/remotes/origin/main", newline_commit)

    # Only delivery history is mocked; Git diffs and selection use the real script.
    binary = repo / "bin"
    binary.mkdir()
    gh = binary / "gh"
    gh.write_text(
        '#!/usr/bin/env bash\n'
        'printf "%s\\n" "${HISTORY_SHA:-}"\n'
    )
    gh.chmod(0o755)

    def detect(expected, *, success=True, **overrides):
        output = repo / "outputs"
        output.write_text("")
        env = {
            **os.environ,
            "PATH": f"{binary}:{os.environ['PATH']}",
            "APP_LIST": json.dumps(apps),
            "APP_LIST_FILE": "",
            "BASE": base,
            "REF": app_commit,
            "INCLUDE_ROOT_CHANGES": "false",
            "DELIVERY_WORKFLOW": "",
            "DELIVERY_BRANCH": "main",
            "GH_TOKEN": "",
            "GITHUB_REPOSITORY": "example/project",
            "GITHUB_OUTPUT": str(output),
            **overrides,
        }
        result = subprocess.run(
            ["bash", str(script)], cwd=repo, env=env, text=True, capture_output=True
        )
        assert (result.returncode == 0) == success, result.stderr + result.stdout
        if not success:
            return
        values = dict(line.split("=", 1) for line in output.read_text().splitlines())
        selected = json.loads(values["changed_apps"])
        assert [app["app"] for app in selected] == expected, values
        assert values["has-changes"] == str(bool(expected)).lower(), values
        assert json.loads(values["apps"]) == json.loads(env["APP_LIST"] or (repo / env["APP_LIST_FILE"]).read_text())

    detect(["koukou"])
    detect(["koukou"], APP_LIST="", APP_LIST_FILE="apps.json")
    detect(["boubou", "koukou"], BASE="")
    detect(["boubou", "koukou"], REF=shared_commit)
    detect([], BASE=shared_commit, REF=root_commit)
    detect(["boubou", "koukou"], BASE=shared_commit, REF=root_commit, INCLUDE_ROOT_CHANGES="true")
    detect(["boubou", "koukou"], BASE=root_commit, REF=workflow_commit, INCLUDE_ROOT_CHANGES="true")
    detect([], BASE=workflow_commit, REF=docs_commit)
    detect(["boubou"], BASE=docs_commit, REF=newline_commit)
    detect([], APP_LIST="[]", BASE="")
    detect([], success=False, APP_LIST_FILE="apps.json")
    detect([], success=False, APP_LIST="")
    detect([], success=False, APP_LIST="{}")

    delivery = {
        "BASE": "",
        "REF": newline_commit,
        "DELIVERY_WORKFLOW": "cd.yml",
        "GH_TOKEN": "fixture-token",
    }
    detect(["boubou"], **delivery, HISTORY_SHA=docs_commit)
    detect(["boubou", "koukou"], **delivery, HISTORY_SHA="")
    detect([], success=False, **{**delivery, "GH_TOKEN": ""})
    detect([], success=False, **{**delivery, "BASE": base})
    detect([], success=False, **{**delivery, "REF": app_commit})
    detect(["boubou", "koukou"], **delivery, HISTORY_SHA="f" * 40)

print("PASS: inline/file inputs, app/shared/root/workflow paths, empty lists, delivery history, and invalid requests")
