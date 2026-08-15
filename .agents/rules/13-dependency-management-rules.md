---
name: dependency-management
description: Reuse before rebuild — search existing and published dependencies, and check licence compatibility, before writing new code.
trigger: always_on
---
# Dependency Management — Do Not Reinvent the Wheel

Hand-rolled implementations of solved problems are the most expensive code in a
repository: they carry no upstream security fixes, no community documentation,
and no tests but the ones you happen to write. Before implementing any
non-trivial capability, establish that it does not already exist.

This applies at **four** points, not just while typing.

## 1. During Design

Before choosing an approach, state in the design or plan **which existing
dependency provides this, or why none does**. "We will write our own X" is a
decision that needs a reason — an unmet requirement, a licence conflict, or an
unmaintained ecosystem — not a default.

## 2. Before Adding Anything — Check What Is Already Here

The cheapest dependency is one already in the manifest: no new supply chain, no
new licence, no new review.

- **Python** — already-declared dependencies live in `pyproject.toml / requirements.txt`. Search them first:
  ```bash
  pip list  # or: uv pip list
  ```

Also check the internal ecosystem: a sibling UltiMaker repository or a shared
library may already solve this, and reusing it keeps behaviour consistent across
products.

## 3. If Nothing Exists Internally — Search the Registry

- **Python**:
  ```bash
  pip index versions <package>
  # Inspect metadata and licence before adding:
  pip show <package>  # or: uv add --dry-run <package>
  ```

Judge a candidate on evidence, not popularity alone:

- **Maintenance**: recent releases, issues being answered, no unpatched CVEs.
- **Fit**: solves the actual problem without dragging in a framework.
- **Weight**: for frontend code, check the bundle cost; for embedded and WASM
  targets, check binary size and whether it allocates.
- **Transitive cost**: a package with a large dependency tree imports every one
  of that tree's licences and vulnerabilities too.

Prefer the option this repository or its siblings already use over an equivalent
alternative — consistency is worth more than a marginal feature advantage.

## 4. Licence Compatibility — Check Before Adding, Not After

This project is licensed **GNU GENERAL PUBLIC** (declared in `LICENSE`).


Verify that each new dependency's licence is compatible with this project's
licence and its distribution model. Strong copyleft licences (GPL, AGPL) impose
obligations on distributed software; a package with no declared licence is "all
rights reserved" and cannot be used at all.

Record the licence of every dependency you add. If you cannot determine it, that
is itself a blocker.

## 5. When Opening the Pull Request

Any new dependency must be called out explicitly in the PR description with:

- **What it replaces** — the code you did not write.
- **Why this one** — maintenance status and the alternatives rejected.
- **Its licence**, and why that is compatible with the GNU GENERAL PUBLIC licence.
- **Its transitive footprint** — how many packages it actually pulls in.

Pin the version, commit the updated lockfile in the same change, and never add a
dependency as a drive-by in a change about something else.


## Industry Best Practices & GitHub Code Search Rules

1. **Industry Best Practices First**:
   - Before implementing complex algorithms, security/crypto routines, hardware protocol drivers, or architectural abstractions, agents **MUST investigate industry best practices and existing open-source implementations**.
   - Do NOT write bespoke, custom implementations when verified, licensed open-source packages, standard library routines, or internal UltiMaker utilities already exist.

2. **Multi-Dimensional Code Evaluation (`code-best-practices-search`)**:
   - Load and execute `UltiCortex/skills/software/code-best-practices-search` when researching architectural design patterns, security postures, or benchmarking open-source implementations.
   - Candidate implementations MUST be evaluated across 7 core dimensions:
     1. **Security Posture** (OWASP, parameterization, input sanitization, safe memory bounds)
     2. **Reliability & Resilience** (Fail-secure behavior, explicit error propagation, zero swallowed exceptions)
     3. **Agentic Readiness** (Decomposed <400 line modules, strongly typed signatures, decoupled seams for AI testing)
     4. **Execution Efficiency** (Async/concurrency models, thread safety, memory allocation footprint)
     5. **Dependency Weight** (Minimal third-party dependencies, standard library utilization)
     6. **Coupling & Cohesion** (SOLID principles, DRY, separation of domain logic from boilerplate)
     7. **Tech Stack Fit** (Strict alignment with target codebase rules and standards)

3. **Skill Discovery & Execution (`github-search-code`)**:
   - Load and execute `UltiCortex/skills/software/github-search-code` when executing precise `gh search code` CLI queries, handling exclusions (`-filename:` vs `-path:`), or using `-w` for browser regex search.
   - Use the GitHub CLI (`gh search code`) to audit existing code bases, discover architectural patterns, and extract verified idioms across the organization and GitHub:
     ```bash
     # Search across the organization for existing code patterns or utilities
     gh search code "search_term" --owner="Ultimaker" --language="python"

     # Search for specific cryptographic or security configurations
     gh search code "crypto/md5" --owner="Ultimaker" --language="go"

     # Exclude test files using query syntax with --
     gh search code -- "function language:python -filename:test"
     ```

4. **Programmatic Hydration & Raw Blob Review**:
   - Use the `search_and_hydrate.sh` script or `gh api` with `-H "Accept: application/vnd.github.raw+json"` to fetch untruncated file blobs and perform pairwise Elo evaluations across implementations:
     ```bash
     UltiCortex/skills/software/code-best-practices-search/scripts/search_and_hydrate.sh "ClientName" --language python -L 5
     ```
