---
id: new-view
version: 1.3.0
scope: chapter
type: workflow
chapter: mobile
description: Deterministic workflow for creating a Flutter view or screen from Figma, using DS components and the app's presentation layer. Do not use this to create a standalone DS component.
---

# Workflow: New View/Screen from Figma

## Prerequisites

- Figma URL with `node-id`.
- US with acceptance criteria (inline text or reference to a Markdown file).
- `.copilot/config/project.config.yaml` available.
- If reliable path/topology configuration is missing, run
  `@ds-orchestrator /bootstrap-workspace` first.
- Context resolved by orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_ROOT`
  - `TOPOLOGY_REPO_MODE`
  - `GENERATION_SCOPE`
  - `CONTRACTS_POLICY`
  - `ARCHITECTURE_CONTRACT_PATH`
  - `PIPELINE_SPEC_PATH = {TARGET_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {TARGET_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`

## Mandatory Gates

### Gate 0 — Topology

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate roots (`PROJECT_ROOT`, `TARGET_ROOT`).
3. In `monorepo_melos`, validate `melos.yaml`, scope, and target package.

### Gate 0.5 — App Repo Ownership

1. `project.config.yaml` must be the canonical one in the app repo:
   `{PROJECT_ROOT}/.copilot/config/project.config.yaml`.
2. `PROJECT_ROOT` cannot be a DS/shared/core library.
3. Minimum app signals:
   - `single_repo | multi_repo`: `lib/main.dart` or `lib/main_*.dart` exists,
     or an `android/` or `ios/` folder exists.
   - `monorepo_melos`: `melos.yaml` exists, valid target package, and the
     target package does not classify as DS/shared/core.
4. If it fails, block with:
   - `CONFIG_PROJECT_CONFIG_OUTSIDE_APP_REPO`
   - `CONFIG_PROJECT_ROOT_POINTS_TO_LIBRARY`
   - `CONFIG_APP_EXECUTABLE_SIGNAL_MISSING`

### Gate 1 — Architecture

1. If `architecture.require_contract_for_new_view=true`, require
   `ARCHITECTURE_CONTRACT_PATH`.
2. `ARCHITECTURE.md` is optional as visual support.

### Gate 2 — Contracts Policy

1. `optional`: continue.
2. `generate`: generate minimum contracts in `§4.C` before Phase 3b.
3. `required`: block if referenced domain/data contracts are missing.

If a gate fails, end with `blocked_input`.

## User Inputs

```text
@ds-orchestrator /new-view
Figma URL: https://www.figma.com/file/xxx/Screen?node-id=456
US: [Reference to the US or acceptance criteria text]
US_PATH: [Optional, Markdown path; e.g.: docs/us/US-123.md]
```

## Canonical Sequence

### PHASE 1 — Screen Analysis

**Agent**: `@figma-analyzer`
**Prompt**: `figma-analysis.prompt.md`

Mandatory output:
- `§1` in `PIPELINE_SPEC_PATH` (includes `§1.1b` literal texts,
  `§1.1c` constraints/overflow, `§1.4b`, `§1.3b`, and `§1.3c` if Development/
  vector annotations exist).
- Phase log entry in `PIPELINE_LOG_PATH`.

---

### PHASE 2 — Extended Inventory + DAG

**Agent**: `@component-planner`
**Prompt**: `atomic-inventory.prompt.md`

Mandatory output:
- `§2` and `§3` in `PIPELINE_SPEC_PATH`.
- Explicit DS vs App separation.

---

### PHASE 2.5 — Technical Architecture

**Agent**: `@component-architect`

Mandatory output:
- `§4` in `PIPELINE_SPEC_PATH` with view architecture and `§4.B` for literal
  texts/overflow.

---

### PHASE 2.6 — Minimum Contracts (only `CONTRACTS_POLICY=generate`)

**Agent**: `@component-architect`

Mandatory output:
- `§4.C` in `PIPELINE_SPEC_PATH` with minimum domain/data contracts for
  presentation consumption (no implementation).

---

### HUMAN CHECKPOINT (if applicable)

Condition: `pipeline.human_checkpoint: true`.

The orchestrator presents `§1`, `§2-§3`, `§4` and waits for explicit approval.

---

### PHASE 3a — DS Components Codegen

**Agent**: `@widget-developer`

Mandatory order: atoms → molecules → organisms.

---

### PHASE 3a.5 — DS Components Audit

**Agent**: `@code-auditor`

Loop with `@widget-developer` up to `pipeline.max_audit_retries`.

---

### PHASE 3b — App View Codegen

**Agent**: `@widget-developer`
**Prompt**: `codegen-view.prompt.md`

Output:
- View in `structure.views_path`.
- Private widgets in `structure.view_widgets_path`.

---

### PHASE 4a — DS Component Tests

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGET_TESTS`)

---

### PHASE 4b — DS Component Goldens

**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_GOLDEN_TESTS`)

---

### PHASE 4c — DS Components Widgetbook

**Agent**: `@widgetbook-developer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGETBOOK`)

---

### PHASE 4d — View Tests

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=VIEW_WIDGET_TESTS`)

Minimum coverage:
1. `loading`
2. `empty`
3. `error`
4. `populated`
5. critical navigation
6. literal texts and overflow mitigation when applicable

---

### PHASE 4e — Full View Golden Tests

**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=VIEW_GOLDEN_TESTS`)

Minimum coverage:
1. `loading`
2. `empty`
3. `error`
4. `populated`
5. `light/dark`
6. compact viewport if there is overflow risk

---

### PHASE 4f — App Screen Widgetbook

**Agent**: `@widgetbook-developer`
**Prompt**: `test-generation.prompt.md` (`MODE=APP_WIDGETBOOK_SCREENS`, `WIDGETBOOK_SCOPE=APP_SCREENS`)

Minimum coverage:
1. `Default`
2. `Loading`
3. `Empty` (if applicable)
4. `Error` (if applicable)
5. `Populated`

---

### PHASE 5 — Delivery

**Agent**: `@delivery-manager`
**Prompt**: `delivery-review.prompt.md`

Must:
1. validate DS/App structure in `TARGET_ROOT`
2. update DS barrel only for DS components
3. use branch prefix:
   - `naming.view_branch_prefix` if it exists
   - fallback `naming.branch_prefix`
4. generate `§7` in `PIPELINE_SPEC_PATH`
