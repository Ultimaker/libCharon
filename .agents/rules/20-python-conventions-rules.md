---
name: python-conventions
description: Python conventions mined from this repository (typing, async, frameworks, formatting, logging).
trigger: glob
glob: "**/*.py"
paths:
  - "**/*.py"
---
# Python Conventions (27 files sampled)

> These rules are DISCOVERED from this repository's own sources by the agentic
> bootstrap — they are not organization-wide defaults. Re-run the bootstrap with
> `--update` after intentional convention changes.

0. **Load the `python-pro` skill** before implementing: it carries the type-safety, async, and packaging practices these conventions assume.
1. **Type Hints Mandatory**: 66% of sampled functions are annotated. ALL new/modified functions MUST have full parameter and return type annotations.
2. **I/O Discipline**: follow the existing synchronous patterns; do not introduce async frameworks without an explicit architecture decision.
3. **Framework Consistency**: detected frameworks: dbus. Reuse these — do not add competing frameworks for the same concern.
4. **Logging & Redaction**: `logging` is the established convention. Errors log to `sys.stderr` context and scripts exit non-zero (`sys.exit(1)`) on failure. Never write PII, credentials, or tokens to logs, stdout, or debug output.
5. **String Formatting**: the dominant style here is **.format()** (.format() 24, %-formatting 3). Use it consistently; do not mix formatting styles within a module.
