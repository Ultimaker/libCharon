---
name: atomic-bisect-safe-commits
description: Atomic, bisect-safe commit rules.
trigger: always_on
---
# Atomic & Bisect-Safe Commits

1. **Atomic Commits**: Each commit must be a single self-contained, logical unit of work that compiles and passes tests independently.
2. **Bisect-Safe**: Never break the build or unit test suite in intermediate commits to preserve `git bisect` functionality.
3. **History Cleanup**: Squash WIP/fixup commits (`git rebase -i`) before a PR leaves DRAFT.
4. **Prove it, do not assert it**: "bisect-safe" is a claim about a build, not about a commit message. The pre-push hook runs this repository's own build/test command against the committed tree and fails the push if the tip does not build:

   ```bash
   python3 .agents/hooks/check_atomic_bisect_history.py
   ```

   Export `SKIP_BISECT_BUILD=1` only when you are knowingly pushing a tip you already know is broken — and say so in the pull request.
