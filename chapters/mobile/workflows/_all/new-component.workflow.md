---
id: new-component
version: 1.2.0
scope: chapter
type: workflow
chapter: mobile
description: Deterministic workflow for creating a new Design System component from Figma. Use this when a user requests a new component with a Figma URL and HU. Do not use this to create a full screen or to refactor without a new design.
---

# Workflow: New Component from Figma

## Prerequisites

- Figma component URL with `node-id`.
- User Story (US) with acceptance criteria (inline text or
  reference to a Markdown file).
- Valid `.copilot/config/project.config.yaml`.
- If reliable path/topology configuration is missing, run
  `@ds-orchestrator /bootstrap-workspace` first.
- Context resolved by orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_ROOT`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH = {TARGET_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {TARGET_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`

## Topology Gate (mandatory)

1. Valid `TOPOLOGY_REPO_MODE` (`single_repo | monorepo_melos | multi_repo`).
2. `PROJECT_ROOT` and `TARGET_ROOT` accessible.
3. If `monorepo_melos`: `melos_enabled=true`, `melos_root/melos.yaml`,
   `target_scope`, and `target_package_path` exist.

If any validation fails, end with `blocked_input`.

## App Repo Ownership Gate (mandatory)

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

## User Inputs

```text
@ds-orchestrator /new-component
Figma URL: https://www.figma.com/file/xxx/Component?node-id=123
US: [Reference to the US or acceptance criteria text]
US_PATH: [Optional, Markdown path; e.g.: docs/us/US-123.md]
```

## Execution Sequence

### PHASE 1 — Design Analysis

**Agent**: `@figma-analyzer`
**Prompt**: `figma-analysis.prompt.md`

Mandatory output: `§1` in `PIPELINE_SPEC_PATH` (includes `§1.1b` literal
texts, `§1.1c` constraints/overflow, `§1.3b` and `§1.3c` if Development/
vector annotations exist).

---

### PHASE 2 — Spec + Inventory + DAG

**Agent**: `@component-planner`
**Prompt**: `atomic-inventory.prompt.md`

Mandatory output: `§2` and `§3` in `PIPELINE_SPEC_PATH`.

---

### PHASE 2.5 — Technical Architecture

**Agent**: `@component-architect`

Mandatory output: `§4` in `PIPELINE_SPEC_PATH` with `§4.B` for literal
texts/overflow.

---

### HUMAN CHECKPOINT

Condition: `pipeline.human_checkpoint: true`.

Present to the developer:
1. `§1` analysis.
2. `§2-§3` inventory + DAG.
3. `§4` technical plan.

Wait for explicit approval to continue.

---

### PHASE 3 — DS Code Generation

**Agent**: `@widget-developer`
**Prompts**: `codegen-atom.prompt.md`, `codegen-molecule.prompt.md`, `codegen-organism.prompt.md`

Mandatory order: atoms → molecules → organisms.

Output: `.dart` files within the `TARGET_ROOT` scope.

---

### PHASE 3.5 — Quality Audit

**Agent**: `@code-auditor`

Loop with `@widget-developer` up to `pipeline.max_audit_retries`.

Mandatory output: `§5` in `PIPELINE_SPEC_PATH`.

---

### PHASE 4a — DS Widget Tests

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGET_TESTS`)

---

### PHASE 4b — DS Golden Tests

**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_GOLDEN_TESTS`)

---

### PHASE 4c — DS Widgetbook

**Agent**: `@widgetbook-developer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGETBOOK`)

---

### PHASE 5 — Delivery

**Agent**: `@delivery-manager`
**Prompt**: `delivery-review.prompt.md`

Mandatory output: `§7` in `PIPELINE_SPEC_PATH`.

## Rules

- Do not generate artifacts outside `TARGET_ROOT`.
- Do not skip mandatory phases.
- Log every phase in `PIPELINE_LOG_PATH`.
- If a phase does not apply, use `skipped` with an explicit reason.
