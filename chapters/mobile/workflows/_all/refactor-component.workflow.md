---
id: refactor-component
version: 1.2.0
scope: chapter
type: workflow
chapter: mobile
description: Deterministic workflow for refactoring an existing DS component. Use this when the user requests changes to an implementation that has already been deployed.
---

# Workflow: Refactor Component

## Prerequisites

- Path of the component to refactor.
- Refactor description (what to change and why).
- Valid `.copilot/config/project.config.yaml`.
- Context resolved by orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_ROOT`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH = {TARGET_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {TARGET_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`

## Topology Gate

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate `PROJECT_ROOT` and `TARGET_ROOT`.
3. In `monorepo_melos`, validate `melos.yaml`, scope, and target package.

If it fails, end with `blocked_input`.

## User Inputs

```text
@ds-orchestrator /refactor-component lib/src/organisms/cards/product_card.dart
Description: Extract the header into a separate molecule and add support for a "compact" variant.
```

## Execution Sequence

### PHASE 1 — Current Component Analysis

**Agent**: `@component-planner`

Mandatory output: `§2` and `§3` in `PIPELINE_SPEC_PATH`.

---

### PHASE 2 — Technical Refactor Plan

**Agent**: `@component-architect`

Mandatory output: `§4` in `PIPELINE_SPEC_PATH`.

---

### HUMAN CHECKPOINT (if enabled)

Present:
1. impact analysis
2. change plan
3. breaking changes (if any)

---

### PHASE 3 — Apply Changes

**Agent**: `@widget-developer`

Rules:
- Maintain backward compatibility when feasible.
- If APIs are in transition, use `@Deprecated`.
- Restrict changes to the `TARGET_ROOT` scope.

---

### PHASE 3.5 — Audit

**Agent**: `@code-auditor`

Mandatory output: `§5` in `PIPELINE_SPEC_PATH`.

---

### PHASE 4a — Update Widget Tests

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGET_TESTS`)

---

### PHASE 4b — Update Golden Tests (if visual impact)

**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_GOLDEN_TESTS`)

---

### PHASE 5 — Delivery

**Agent**: `@delivery-manager`

Mandatory output: `§7` in `PIPELINE_SPEC_PATH`.

## Verification (topology-aware)

- `single_repo` or `multi_repo`:
  - `flutter analyze`
  - `flutter test`
  - `flutter test --tags golden`
- `monorepo_melos`:
  - `melos exec --scope={monorepo.target_scope} -- flutter analyze`
  - `melos exec --scope={monorepo.target_scope} -- flutter test`
  - `melos exec --scope={monorepo.target_scope} -- flutter test --tags golden`
