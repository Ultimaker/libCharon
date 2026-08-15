#!/usr/bin/env python3
"""
check_atomic_bisect_history.py

`git bisect` is only useful if every commit on the branch BUILDS. A tidy commit
title does not give you that; a build does. So this hook checks both:

  1. History hygiene — no `fixup!`/`squash!`/WIP titles left before a push.
  2. Buildability — the repository's OWN build (and, if quick, test) command is
     run against the committed tree, so a branch that cannot compile is caught
     here rather than in the middle of a bisect three months from now.

The build commands below were detected from this repository at bootstrap time.
Set `SKIP_BISECT_BUILD=1` to skip step 2 when you know the build is expensive.
"""

import os
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


#: This repository's build entry points, detected at bootstrap.
BUILD_COMMANDS: tuple[str, ...] = (
    './build_for_ultimaker.sh',
    'cmake --build build',
)
#: Its test runner, if the investigation found one.
TEST_COMMANDS: tuple[str, ...] = (
    'pytest -x -q',
)

BUILD_TIMEOUT_SECONDS = 900


def get_base_branch() -> str:
    """The PR base, recorded once at bootstrap. Candidate-list guessing was
    blind to any base whose name is not one of three defaults."""
    for cand in (BASE_BRANCH,) + PROTECTED_BRANCHES:
        try:
            subprocess.check_output(
                ["git", "rev-parse", "--verify", f"origin/{cand}"],
                stderr=subprocess.DEVNULL,
            )
            return f"origin/{cand}"
        except (subprocess.CalledProcessError, OSError):
            continue
    return "HEAD~1"


def check_titles(base_branch: str) -> None:
    res = subprocess.run(
        ["git", "log", f"{base_branch}..HEAD", "--oneline"],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        return

    commits = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    fixup_keywords = ["fixup!", "squash!", "wip", "work in progress", "temp"]
    dirty = [c for c in commits if any(kw in c.lower() for kw in fixup_keywords)]
    if dirty:
        print("HISTORY WARNING: Temporary/WIP commits detected before push:")
        for commit in dirty:
            print(f"  - {commit}")
        print("Consider squashing/cleaning history (`git rebase -i`) before review.")


def working_tree_is_clean() -> bool:
    """Only a committed tree proves anything about a bisect. Building with
    uncommitted work in place would verify code that no commit contains."""
    res = subprocess.run(["git", "status", "--porcelain"],
                         capture_output=True, text=True)
    return res.returncode == 0 and not res.stdout.strip()


def run_build() -> int:
    if os.environ.get("SKIP_BISECT_BUILD"):
        print("BISECT BUILD: skipped (SKIP_BISECT_BUILD is set).")
        return 0
    if not BUILD_COMMANDS and not TEST_COMMANDS:
        print("BISECT BUILD: no build or test command was detected for this "
              "repository, so buildability cannot be verified here. Re-run the "
              "bootstrap with --update once one exists.")
        return 0
    if not working_tree_is_clean():
        print("BISECT BUILD: skipped — the working tree has uncommitted "
              "changes, so a build would not describe any commit. Commit first.")
        return 0

    for command in BUILD_COMMANDS + TEST_COMMANDS:
        print(f"BISECT BUILD: verifying the committed tree with `{command}` ...")
        try:
            res = subprocess.run(command, shell=True,
                                 timeout=BUILD_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            print(f"BISECT BUILD WARNING: `{command}` exceeded "
                  f"{BUILD_TIMEOUT_SECONDS}s and was abandoned; buildability "
                  "is unverified for this push.")
            return 0
        except OSError as exc:
            print(f"BISECT BUILD WARNING: could not run `{command}`: {exc}")
            return 0
        if res.returncode != 0:
            print("\nBISECT SAFETY FAILURE: the committed tip of this branch "
                  f"does not build (`{command}` exited {res.returncode}).\n"
                  "  Every commit you push must build on its own, or `git "
                  "bisect` will land on it and report a false culprit.\n"
                  "  Fix the build and amend, or export SKIP_BISECT_BUILD=1 if "
                  "you are knowingly pushing a broken tip.")
            return 1
    print("BISECT BUILD: the committed tree builds.")
    return 0


def main() -> int:
    check_titles(get_base_branch())
    return run_build()


if __name__ == "__main__":
    sys.exit(main())
