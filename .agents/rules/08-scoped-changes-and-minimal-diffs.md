---
name: scoped-changes-and-minimal-diffs
description: Scoped changes and minimal diff guidelines for code changes.
trigger: always_on
---
# Scoped Changes & Minimal Diffs

1. **Strict Scope Compliance**: Make changes strictly relevant to the active Jira ticket task. Avoid scope creep.
2. **Diff Relevance Validation**: Inspect `git diff --name-only` against the base branch before committing. Revert files touched only by formatters or side-effects: `git checkout origin/<base_branch> -- <file>`.
3. **No Unrelated Refactoring**: Do not modify whitespace, formatting, or code in files unrelated to the task. Never edit `vendor/`, `third_party/`, or submodule trees.


## Single Responsibility PRs & Boy Scouting Branch Isolation

Every Pull Request MUST deliver a single cohesive goal tied to a single primary topic or Jira issue. Combining multiple unrelated features, bug fixes, or opportunistic refactorings ("Boy Scouting") into a single PR creates scope coupling and increases reviewer cognitive load.

## 1. Single Responsibility Principle for PRs (SRP-PR)

- **One Goal per PR:** A Pull Request MUST serve a single, clear objective.
- **Intra-Module Intent Divergence:** Even if all code changes are located within the exact same directory or module (e.g. `src/components/` or `griffin/printer/`), edits MUST NOT fix multiple unrelated bugs or introduce opportunistic refactorings alongside a new feature.
- **Single Jira Key:** A PR SHOULD address a single Jira ticket key. Do NOT combine work for `UC-100` and `UC-200` into one PR.

## 2. Boy Scouting Isolation Protocol

When you discover an opportunistic bug, missing setting, or code cleanup ("Boy Scouting") while working on a primary task:

1. **Do NOT lump the opportunistic changes into the primary feature PR.**
2. **Extract onto a Boy Scouting Branch:**
   ```bash
   bash scripts/create_boyscout_branch_and_pr.sh <JIRA-KEY> <topic> <paths...>
   ```
3. **Open a Dedicated Draft PR:** Push the Boy Scouting branch to GitHub and open an independent Draft PR (`gh pr create --draft`).
4. **Link PRs in Descriptions:** Reference the Boy Scouting PR in your primary PR description so reviewers can inspect both independently.

## 3. Adversarial Scope Verification

Before submitting or updating a Pull Request, run the Adversarial Scope Judge:
```bash
python3 .agents/hooks/check_multi_intent_scope.py
```
It blocks exactly one thing — edits to trees this repository vendors but does not own — and otherwise **reports** the changed-file list grouped by area. It deliberately does not decide for you: a rename touches sixty files with one intent, while two files in two subsystems can still be two intents. Read the report and judge it; if part of the diff is opportunistic, extract it before requesting human review.
