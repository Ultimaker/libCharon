---
name: pull-request-lifecycle
description: Pull request lifecycle rules, draft PR policy, PR template enforcement, review workflows, and subagent delegation guardrails.
trigger: always_on
---
# Pull Request Lifecycle Rules

1. **Pre-PR Verification & Gate**: Run `scripts/verify_and_create_pr.sh` (pre-commit + orientation check + adversarial audit) before creating or updating any PR.
2. **Draft PR Policy**: Always open PRs in **DRAFT** state (`gh pr create --draft`). Merging is strictly restricted to human developers; AI agents must never auto-merge.
3. **Mandatory PR Template & Comprehensive Description**:
   - Every PR description **MUST** strictly follow the repository's PR template (its location is recorded as `pr_template.path` in `.agents/bootstrap-profile.json`; GitHub also honours a repository-root or `docs/` template) and answer the core review questions:
     - **Why**: The problem, user request, Jira ticket (`[UC-123]`), and business context driving the change.
     - **What**: High-level overview of introduced changes.
     - **How**: Architecture decisions, implementation details, and modified modules.
     - **Verification & Validation (V&V)**: Empirical test results (unit tests, integration tests, E2E checks, and visual screenshots/recordings for UI changes).
     - **PR Checklist**: Human reviewer checklist (`- [ ] Initiating developer reviewed AI-generated code`).
   - Vague, brief, or 1-sentence PR descriptions are strictly prohibited.
4. **Empirical Proof Mandate**: Verification is ONLY valid when concrete empirical proof (a DOM text snapshot, test execution log, or screenshot uploaded via `gh image` attached to the walkthrough and PR body) is delivered. Agents must NEVER claim a UI feature or fix is verified without delivering empirical proof.
5. **Updating Existing PRs on Follow-up Commits**:
   - When pushing follow-up commits to an active branch with an existing Pull Request, agents **MUST** inspect the existing PR (`gh pr view` or `gh pr list --head <branch>`).
   - If the new commits add new scope, alter architecture (**How**), or require updated testing/screenshots (**V&V**), run `gh pr edit <PR_NUMBER> --body-file <updated_template>` to update the PR description so it always reflects the current state of the branch.
6. **CI Watch Loop**: After creating or updating a PR, actively monitor status checks (`gh pr checks <PR> --watch`) and fix any linter or test failures immediately before handing off to human review.
7. **Upstream Base Branch Alignment**:
   - Before staging changes, opening PRs, or pushing follow-up commits, agents **MUST** ensure the local feature branch is completely up-to-date with its base branch (`origin/staging`, `origin/main`, or `origin/master`).
   - Run `git fetch origin` and `git merge origin/<base_branch>` (or use `/sync-base` command) to resolve any upstream changes or conflicts before proposing PR updates.
8. **Subagent Delegation Guardrails**:
   - Delegation moves the work, not the responsibility. Everything a subagent reports is a claim until verified via `git log` and `git diff` in the subagent's tree.
   - Specify the target PR state explicitly in subagent instructions (draft vs ready). Verify that subagents commit and push all work before reporting completion.


## Git Merge Topology Preservation

This repository preserves merge topology for pull requests and feature branches to maintain ISO-27001 auditability and review history:
1. **No Force-Pushing Published Review Branches**: Do NOT rewrite history or force-push rebased commits on published branches that have already been opened for PR review.
2. **Integrate Upstream via Merge**: Integrate upstream base branch updates using `git merge origin/main` (or `/sync-base`) rather than rebasing published history.
3. **Draft PR Lifecycle**: PRs must remain in DRAFT status until all status checks pass and human review is complete. Merging is strictly restricted to human developers.
