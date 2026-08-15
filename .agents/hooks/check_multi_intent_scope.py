#!/usr/bin/env python3
"""
check_multi_intent_scope.py — the repository's single scope gate.

This absorbs the old `check-relevant-scope.py`. The two hooks asked the same
question ("is this change one thing?") and answered it twice: one counted files
against an arbitrary threshold, the other clustered directories. A count is not
evidence of scope creep — a rename touches sixty files with one intent, and two
files in unrelated subsystems are two intents. So this hook does exactly two
things:

  * BLOCKS the one objective violation — staged edits to trees this repository
    vendors but does not own.
  * REPORTS the changed-file list, grouped by where those files live, and hands
    the judgement to the agent. No threshold, no guessing.
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



def _git_lines(*args) -> list:
    res = subprocess.run(["git", *args], capture_output=True, text=True)
    if res.returncode != 0:
        return []
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]


def changed_files() -> list:
    """Staged first — that is what a pre-commit run is about to record."""
    for args in (("diff", "--cached", "--name-only"),
                 ("diff", "--name-only", "HEAD")):
        files = _git_lines(*args)
        if files:
            return files
    return []


def block_vendored(files: list) -> list:
    return [f for f in files if is_vendored(f)]


def group_by_area(files: list) -> dict:
    """Two path components deep: deep enough to separate `src/parser` from
    `src/transport`, shallow enough not to call every file its own area."""
    areas = {}
    for path in files:
        parts = path.split("/")
        area = "/".join(parts[:2]) if len(parts) > 1 else "(repository root)"
        areas.setdefault(area, []).append(path)
    return areas


def report(files: list) -> None:
    areas = group_by_area(files)
    print("\n" + "=" * 74)
    print("SCOPE REPORT — {} changed file(s) across {} area(s)".format(
        len(files), len(areas)))
    print("=" * 74)
    for area, paths in sorted(areas.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        print("  {} ({} file(s))".format(area, len(paths)))
        for path in sorted(paths):
            print("      {}".format(path))

    jira_keys = sorted(set(re.findall(r"\b[A-Z]{2,10}-\d+\b",
                                      "\n".join(_git_lines("log", "-n", "5",
                                                           "--oneline")))))
    if len(jira_keys) > 1:
        print("\n  Recent commits reference more than one ticket: {}".format(
            ", ".join(jira_keys)))
        print("  One pull request should serve one ticket.")

    print("\n  JUDGE THIS YOURSELF — the hook deliberately does not decide:")
    print("    * Does every file above serve the ONE task this branch is for?")
    print("    * Is anything here an opportunistic fix or cleanup you noticed")
    print("      along the way ('boy scouting')? That belongs on its own branch:")
    print("        bash scripts/create_boyscout_branch_and_pr.sh "
          "UC-123 <topic> <paths...>")
    print("    * Files spread over unrelated areas are a signal, not a verdict:")
    print("      a rename legitimately touches many; two files in two subsystems")
    print("      may still be two intents.")
    print("=" * 74 + "\n")


def main() -> int:
    files = changed_files()
    if not files:
        return 0

    vendored = block_vendored(files)
    if vendored:
        print("SCOPE ERROR: this change edits vendored trees this repository "
              "consumes but does not own:")
        for path in sorted(vendored):
            print("  - {}".format(path))
        print("Vendored code is updated upstream, never patched in place. "
              "Unstage these files.")
        return 1

    report(files)
    return 0


if __name__ == "__main__":
    sys.exit(main())
