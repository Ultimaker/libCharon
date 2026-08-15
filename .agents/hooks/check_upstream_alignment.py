#!/usr/bin/env python3
"""
check_upstream_alignment.py
---------------------------
Deterministic pre-PR check verifying that the local branch is up-to-date with
its base branch.
"""

import os
import subprocess
import sys

_ROOT = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
).stdout.strip()
if _ROOT:
    os.chdir(_ROOT)

# --- this repository's layout, discovered at bootstrap (generated) ---------
# ONE source for the folder lists. Several hooks used to carry their own
# hardcoded copies of a vendor-directory list and of a default-branch list,
# which was both duplication and wrong: a firmware repository vendors into its
# own SDK directory and protects a release branch under a project-specific
# name, and no hardcoded copy could know either.
#
# Every value below comes from the investigation the bootstrap ran against THIS
# repository — not from a default list. Re-run the bootstrap with `--update`
# after the layout changes.

#: Trees this repository consumes but does not own. Never reformat or edit.
VENDORED_PREFIXES: tuple[str, ...] = (
    'ci/',
)

#: Branches nobody may commit to directly. Discovered from the remote's own
#: protection settings via `gh`, falling back to the detected base branch.
PROTECTED_BRANCHES: tuple[str, ...] = (
    'main',
    'rc_8.4',
)

#: The PR base for this repository, recorded once so no script has to guess.
BASE_BRANCH: str = "main"

#: Directories holding a published interface whose docs must move with it.
INTERFACE_PREFIXES: tuple[str, ...] = (
    'tests/filetypes/',
)

#: Where this repository documents that interface.
API_DOC_PATHS: tuple[str, ...] = ()

#: Sources where a raw #RRGGBB literal belongs in a theme token instead.
#: Not QML-only: React, Python UIs and stylesheets hardcode colours too.
THEMEABLE_SUFFIXES: tuple[str, ...] = (
    '.qml',
    '.py',
    '.css',
    '.scss',
    '.less',
)

#: The theme/token definitions themselves — the one place literals belong.
THEME_DEFINITION_FILES: tuple[str, ...] = (
    'Theme.qml',
    'theme.ts',
    'tokens.css',
)


def is_vendored(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in VENDORED_PREFIXES)


def is_themeable_source(path: str) -> bool:
    return (path.endswith(THEMEABLE_SUFFIXES)
            and not any(name in path for name in THEME_DEFINITION_FILES))



def run_cmd(cmd, timeout=5) -> str:
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return ""


def main():
    # Detect current branch
    current_branch = run_cmd(["git", "branch", "--show-current"])
    if not current_branch or current_branch in PROTECTED_BRANCHES:
        sys.exit(0)

    # Fetch origin silently with short timeout
    run_cmd(["git", "fetch", "origin"], timeout=8)

    # THE base branch, not a guess from a candidate list. Ask git what this
    # branch actually tracks first — in a stacked-PR workflow the base is the
    # branch below, not the repository's default branch. Only then fall back to
    # the base the bootstrap recorded.
    upstream = run_cmd(["git", "rev-parse", "--abbrev-ref",
                        "--symbolic-full-name", "@{upstream}"])
    base_branch = ""
    if upstream and upstream != current_branch and not upstream.endswith(
            "/" + current_branch):
        base_branch = upstream
    if not base_branch and run_cmd(
            ["git", "rev-parse", "--verify", f"origin/{BASE_BRANCH}"]):
        base_branch = f"origin/{BASE_BRANCH}"

    if not base_branch:
        print(f"⚠️  BRANCH ALIGNMENT: base branch 'origin/{BASE_BRANCH}' is not "
              "available locally; run `git fetch origin` and re-run.")
        sys.exit(0)

    # Check how many commits current branch is behind base_branch
    behind_count = run_cmd(["git", "rev-list", "--count", f"HEAD..{base_branch}"])
    if behind_count and behind_count.isdigit() and int(behind_count) > 0:
        print(f"\n⚠️  BRANCH ALIGNMENT WARNING: current branch "
              f"'{current_branch}' is {behind_count} commit(s) behind "
              f"'{base_branch}'.")
        print(f"    Please integrate changes from '{base_branch}' before "
              "opening or updating PRs:")
        print(f"    git merge {base_branch}  (or run /sync-base)\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
