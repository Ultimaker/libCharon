---
name: gcode-architecture
description: G-code surface detected in this repository — load the ultimaker-gcode-architecture skill before touching parsing, dispatch, or custom G/M-codes.
trigger: glob
glob: "**/*gcode*,**/gcode/**,**/GCode*,docs/api_documentation.json"
paths:
  - "**/*gcode*"
  - "**/gcode/**"
  - "**/GCode*"
  - "docs/api_documentation.json"
---
# G-Code Architecture — Load the Canonical Skill

This repository has a real G-code dispatch surface (evidence recorded in
`.agents/bootstrap-profile.json` under `evidence.gcode_evidence`). The G-code
contract — the full Marlin command profile, the UltiMaker custom G/M-code
registry, parameter bounds and buffer-sanitization invariants, the
cross-repository dispatch map, and the mandatory ecosystem synchronization
protocol — lives in **one place**, the `ultimaker-gcode-architecture` skill:

```bash
gh skill install Ultimaker/UltiCortex ultimaker-gcode-architecture
```

Load it **before** designing or implementing any change to G-code parsing,
dispatch, handlers, or custom codes. Do not restate its content here: per-repo
copies of the registry drifted apart across five repositories, and agents then
followed the stale copy.

Hard floor mirrored by the generated hooks (`check-gcode-handler-validation`,
`check-gcode-parameter-bounds`, `check-custom-mcode-registry`):

1. Every parsed parameter is bounds-validated before any hardware call; no
   un-clamped `atof()`/`atoi()` in parsers.
2. Every new or changed custom G/M-code is registered in
   `docs/api_documentation.json` and synchronized across every sibling
   repository on its dispatch path, per the skill's ecosystem protocol.
