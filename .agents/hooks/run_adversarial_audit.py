#!/usr/bin/env python3
"""
run_adversarial_audit.py
Automated Adversarial Security, Quality Gate & Intent Scope Audit Script.

Scans git diff and commit history for:
1. Hardcoded absolute paths (e.g. user home directories)
2. Private keys, API tokens, credentials
3. Python error swallowing
4. Raw hex colour literals in themeable sources — NOT just QML: React, Python
   UIs and stylesheets hardcode `#RRGGBB` just as readily
5. Interface changes that leave the API documentation behind
6. Edits to trees this repository vendors but does not own

Every folder list this script uses is discovered at bootstrap and rendered in
from ONE source (`hooks/partials/_repo_layout.py.j2`). Earlier revisions carried
private hardcoded copies of an interface directory, a vendor directory and a
default-branch list — literals lifted from one firmware repository, meaningless
in every other repository the bootstrap touched.
"""

import os
from pathlib import Path
import re
import subprocess
import sys

HOOKS_DIR = os.path.abspath(os.path.dirname(__file__))
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)
from secret_scanner import SecretScanner  # noqa: E402
from path_scanner import PathScanner  # noqa: E402

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


HEX_COLOR_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}\b")


def _git_lines(*args):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return [f.strip() for f in result.stdout.splitlines() if f.strip()]


def get_git_diff_files():
    """Everything this branch changes relative to its base, plus uncommitted
    work. Diffing only the working tree made this audit a no-op at pre-push
    time on a clean tree — committed changes were never audited at all."""
    files = set(_git_lines("diff", "--name-only", "HEAD"))
    files |= set(_git_lines("diff", "--cached", "--name-only"))
    merge_base = _git_lines("merge-base", "HEAD", f"origin/{BASE_BRANCH}")
    if merge_base:
        files |= set(_git_lines("diff", "--name-only", f"{merge_base[0]}..HEAD"))
    return sorted(files)


# Files where an absolute user path may legitimately appear as generated
# content rather than as something a human committed. Deliberately NOT
# `.md` wholesale: exempting every markdown file let absolute paths through
# in documentation, which the security-and-paths rule explicitly forbids, and
# documentation is exactly where a developer's home directory tends to be
# pasted from a terminal transcript.
_PATH_EXEMPT_PREFIXES = (".agents/rules/",)


def _path_exempt(filepath: str) -> bool:
    return filepath.startswith(_PATH_EXEMPT_PREFIXES)


def _check_line_patterns(filepath, idx, line, content, errors):
    if PathScanner.scan_line(line)[0] and not _path_exempt(filepath):
        errors.append(f"❌ [ABSOLUTE PATH] {filepath}:{idx}: {line.strip()}")

    if SecretScanner.scan_line(line):
        errors.append(f"❌ [SECRET DETECTED] {filepath}:{idx}")

    if filepath.endswith(".py"):
        c1 = "except Exception as e:" in line
        c2 = "except Exception:" in line
        if c1 or c2:
            w_start = max(0, idx - 1)
            w_end = min(len(content), idx + 5)
            window = "".join(content[w_start:w_end])
            has_exit = "sys.exit" in window or "file=sys.stderr" in window
            if not has_exit:
                errors.append(
                    f"⚠️ [PYTHON ERROR SWALLOWING] {filepath}:{idx}: "
                    "Exception caught without sys.exit or stderr output."
                )

    if is_themeable_source(filepath) and HEX_COLOR_PATTERN.search(line):
        errors.append(
            f"⚠️ [HARDCODED HEX COLOR] {filepath}:{idx}: "
            f"{line.strip()} (use this project's theme tokens instead)"
        )


def _check_architectural_limits(files, errors):
    # Only apply the API-doc coupling where those interface trees exist in
    # THIS repository; a foreign repo's layout is not evidence here.
    live_interfaces = [p for p in INTERFACE_PREFIXES if Path(p).is_dir()]
    interface_files = [f for f in files
                       if any(f.startswith(p) for p in live_interfaces)]
    api_doc_files = [f for f in files
                     if f in API_DOC_PATHS or "openapi" in f.lower()]
    if interface_files and API_DOC_PATHS and not api_doc_files:
        errors.append(
            f"❌ [API DOC DESYNC] Interface files modified "
            f"({len(interface_files)} files) but {', '.join(API_DOC_PATHS)} "
            "was not updated!"
        )

    vendor_files = [f for f in files if is_vendored(f)]
    if vendor_files:
        errors.append(
            f"❌ [VENDOR SDK MODIFIED] {len(vendor_files)} vendor files "
            f"modified (e.g. {vendor_files[0]}). Vendor code must remain untouched!"
        )


def _audit_single_file(filepath, errors):
    path = Path(filepath)
    if not path.exists() or path.is_dir():
        return

    # Guards whose own source must contain the patterns they detect, plus the
    # fire-proofing harness whose fixtures ARE violations by construction.
    # Without this the audit failed every bootstrap PR on the bootstrap's own
    # output, even on a clean tree. Exact filenames, never directory prefixes:
    # a blanket `.agents/hooks/` skip would be a place to hide a real secret.
    SELF_EXEMPT_NAMES = frozenset({
        "block-absolute-paths.py", "block-secrets.py", "path_scanner.py",
        "secret_scanner.py", "pretool_guard.py", "check_security_downgrades.py",
        "run_adversarial_audit.py", "verify_hooks_fire.py",
    })
    if path.name in SELF_EXEMPT_NAMES:
        return

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.readlines()

        for idx, line in enumerate(content, 1):
            _check_line_patterns(filepath, idx, line, content, errors)
    except OSError:
        return


def audit_diff():
    sec_hook = Path(__file__).parent / "check_security_downgrades.py"
    if sec_hook.exists():
        res = subprocess.run([sys.executable, str(sec_hook)])
        if res.returncode != 0:
            return 1

    files = get_git_diff_files()
    if not files:
        print("==> Adversarial Audit: No modified files detected in git diff.")
        return 0

    errors = []
    print("==> Running Adversarial Security, Quality & Intent Audit on "
          f"{len(files)} modified files...")

    for filepath in files:
        _audit_single_file(filepath, errors)

    _check_architectural_limits(files, errors)

    # Scope judgement lives in check_multi_intent_scope.py — one hook, one
    # question. Delegating rather than re-deriving it here keeps the two from
    # disagreeing about what "too wide" means.
    scope_hook = Path(__file__).parent / "check_multi_intent_scope.py"
    if scope_hook.exists():
        res = subprocess.run([sys.executable, str(scope_hook)])
        if res.returncode != 0:
            return 1

    if errors:
        print("\n" + "=" * 74)
        print("🚨 ADVERSARIAL AUDIT FINDINGS & INTENT EVALUATION:")
        print("=" * 74)
        for err in errors:
            print(err)
        print("=" * 74 + "\n")
        crit_keys = ["ABSOLUTE PATH", "SECRET DETECTED", "API DOC DESYNC",
                     "VENDOR SDK MODIFIED"]
        critical_errors = [e for e in errors if any(ck in e for ck in crit_keys)]
        if critical_errors:
            print("❌ Critical security findings must be resolved.")
            return 1

    print("✅ Adversarial Security, Quality & Intent Audit Passed Cleanly!")
    return 0


if __name__ == "__main__":
    sys.exit(audit_diff())
