#!/usr/bin/env python3
"""Refuse commits on branches this repository actually protects.

The protected list is NOT `["main", "master", "staging"]`. That guess was
simultaneously too wide (forbidding `master` in a repository that has none) and
too narrow (waving through a direct commit to the release branch this project
actually protects). The bootstrap asks GitHub for the real answer via
`gh api repos/{owner}/{repo}/branches` and renders it below.
"""

import os
import re
import subprocess
import sys

# Hook may be invoked from .agents/ (Antigravity sets cwd to the hooks.json
# directory) — always operate from the repository root.
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


# `KEY-123-short-description`: hyphens throughout, never underscores. A branch
# named `UC-123_short_description` reads as one token to every tool
# that splits on `-`, and the convention here is hyphenated.
BRANCH_NAME_RE = re.compile(r"^UC-\d+-[a-z0-9]+(-[a-z0-9]+)*$", re.I)


def check_branch():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    branch = result.stdout.strip()
    if branch in PROTECTED_BRANCHES:
        print(
            f"BRANCH GUARD ERROR: '{branch}' is a protected branch in this "
            f"repository (protected: {', '.join(PROTECTED_BRANCHES)}).\n"
            f"Create a feature branch: git switch -c UC-123-short-description"
        )
        sys.exit(1)

    if branch and not BRANCH_NAME_RE.match(branch):
        print(
            f"BRANCH NAMING NOTICE: '{branch}' does not match "
            f"`UC-<number>-short-description`.\n"
            "  Use hyphens, not underscores, between every part of the name.\n"
            "  This is advisory — rename with `git branch -m` if the branch is "
            "not yet published."
        )


if __name__ == "__main__":
    check_branch()
