---
name: ultimaker-skill-discovery
description: Skills from the UltiCortex catalogue that apply to this repository, and when to load them.
trigger: always_on
---
# UltiMaker Skill Discovery & Usage

This repository has been matched against the UltiCortex skill catalogue. Loading
the relevant skill is **not optional** for the work it covers: these skills carry
the standards, idioms, and tooling knowledge that the rules in this directory
assume you already have.

```bash
# Search the catalogue
gh skill search ultimaker --owner Ultimaker

# Install a specific skill
gh skill install Ultimaker/UltiCortex <skill-name>
```

Load the skill **before** designing or implementing, not after review comments
arrive. If a skill contradicts a rule in this directory, raise the conflict
rather than silently picking one.

## Skills Matched To This Repository

### `cmake` — when touching `**/CMakeLists.txt`, `**/*.cmake`, `**/CMakePresets.json`

Modern target-centric C/C++ engineering with CMake 3 & 4.

**Why it applies here:** Target-centric CMake, presets, and CTest wiring — avoid reinventing build logic or reaching for directory-scoped commands.

```bash
gh skill install Ultimaker/UltiCortex cmake
```

### `python-pro` — when touching `**/*.py`

Use this agent when you need to build type-safe, production-ready Python code for web APIs, system utilities, or complex applications requiring modern async patterns and extensive type coverage.

**Why it applies here:** Type-safe, production-ready Python: typing coverage, async patterns, and the conventions mined into the Python rule.

```bash
gh skill install Ultimaker/UltiCortex python-pro
```

### `ultimaker-gcode-architecture` — when touching `**/*gcode*`, `**/gcode/**`, `docs/api_documentation.json`

Canonical Marlin & UltiMaker custom G/M-code registry, dispatch map, and ecosystem synchronization protocol.

**Why it applies here:** This repository has a real G-code dispatch surface; the skill carries the canonical command registry, dispatch map and the mandatory ecosystem synchronization protocol.

```bash
gh skill install Ultimaker/UltiCortex ultimaker-gcode-architecture
```

### `software-architect` — always relevant

Expert software-architecture advisor: design patterns (GoF), SOLID/DRY, enterprise patterns (Fowler PoEAA), DDD/CQRS, evolutionary architecture (monolith-first, strangler fig, microservices), distributed systems, C4 diagrams, C++….

**Why it applies here:** SOLID, DRY and the design-pattern catalogue — the reference to consult when a change needs decomposition rather than more lines in an existing module.

```bash
gh skill install Ultimaker/UltiCortex software-architect
```

### `ultimaker-firmware-development` — always relevant

Cross-repository guide to UltiMaker printer firmware: product lines, the repo constellation, the jedi build/release pipeline, and interface discipline.

**Why it applies here:** This repository is part of the printer firmware constellation. The skill carries the product/platform map, the jedi build and release pipeline, and the cross-repository interface discipline (D-Bus, packaging, recipes) that a change here may cross.

```bash
gh skill install Ultimaker/UltiCortex ultimaker-firmware-development
```

### `ultimaker-printer-ssh` — when touching `**/*.recipe`

SSH debugging, systemd-dbus, and hardware mocking on S-line, Next-Gen, and Factor 4(+) printers.

**Why it applies here:** Deploying packages to a test printer, inspecting DBus properties, and debugging services over SSH.

```bash
gh skill install Ultimaker/UltiCortex ultimaker-printer-ssh
```

### `ultimaker-printer-logs` — always relevant

Diagnostic log parser for Ultimaker 3D printers, diagnosing reboots, OOMs, and mechanical anomalies.

**Why it applies here:** Parsing printer log dumps when diagnosing reboots, crashes, or service failures.

```bash
gh skill install Ultimaker/UltiCortex ultimaker-printer-logs
```

## Other Catalogue Skills

20 further skill(s) exist that no automatic trigger matched.
They are indexed in `.agents/rules/40-skill-discovery-index-rules.md` (a
model-decision rule, loaded only when judged relevant) rather than here,
because by construction they are the ones static detection judged irrelevant —
and this file is loaded every session.

```bash
gh skill search ultimaker --owner Ultimaker
```
