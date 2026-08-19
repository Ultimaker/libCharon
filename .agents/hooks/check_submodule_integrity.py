#!/usr/bin/env python3
"""Pre-commit hook: Verify submodule tracking in git index."""

import configparser
import os
import subprocess
import sys

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



def get_base_branch() -> str:
    """THE base branch, detected at bootstrap — not a candidate list. The list
    that used to live here named release branches from one specific firmware
    repository, which resolved to nothing anywhere else."""
    try:
        subprocess.check_output(
            ["git", "rev-parse", "--verify", f"origin/{BASE_BRANCH}"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return BASE_BRANCH
    except (subprocess.CalledProcessError, OSError):
        return "HEAD"


def check_submodules() -> bool:
    base_branch = get_base_branch()
    # 1. Check if base branch has .gitmodules when current branch lacks it
    if not os.path.exists(".gitmodules"):
        try:
            base_modules = subprocess.check_output(
                ["git", "show", f"origin/{base_branch}:.gitmodules"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if base_modules.strip():
                print(f"SUBMODULE INTEGRITY ERROR: .gitmodules exists on 'origin/{base_branch}' but is missing on current branch!")
                print(f"Restore it with: git checkout origin/{base_branch} -- .gitmodules")
                return False
        except Exception:
            pass
        return True

    # 2. Parse .gitmodules
    config = configparser.ConfigParser()
    try:
        config.read(".gitmodules")
    except Exception as e:
        print(f"SUBMODULE INTEGRITY ERROR: Failed to parse .gitmodules: {e}")
        return False

    has_error = False
    for section in config.sections():
        if "path" in config[section]:
            submodule_path = config[section]["path"]
            try:
                ls_tree = subprocess.check_output(
                    ["git", "ls-tree", "HEAD", submodule_path], text=True
                ).strip()
                if not ls_tree or "160000" not in ls_tree:
                    print(f"SUBMODULE INTEGRITY ERROR: Submodule '{submodule_path}' is defined in .gitmodules but missing from git index!")
                    print(f"Restore it with: git checkout origin/{base_branch} -- {submodule_path}")
                    has_error = True
            except Exception:
                print(f"SUBMODULE INTEGRITY ERROR: Submodule '{submodule_path}' check failed in git index.")
                has_error = True

    return not has_error


if __name__ == "__main__":
    if not check_submodules():
        sys.exit(1)
    sys.exit(0)
