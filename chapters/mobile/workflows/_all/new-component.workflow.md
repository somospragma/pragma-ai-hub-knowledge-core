---
id: new-component
version: 1.3.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: ds-orchestrator
input_contract: ../docs/templates/spec-packets/overlays/new-component.yaml
invocation_mode: explicit_agent
description: >
  Deterministic workflow to create a new Design System component from Figma. Use when the user requests a reusable atom, molecule, or organism with spec packet validation, Figma MCP preflight, human review, code generation, tests, Widgetbook, and audit gates.
---
# Workflow: New Component from Figma

## Prerequisites

- URL for the component in Figma with `node-id`.
- User Story (user story) with acceptance criteria (inline text or
  reference to a Markdown file).
- `.sopp/config/project.config.yaml` valid.
- If missing reliable path/topology configuration, run first
  `@workspace-discovery /bootstrap-workspace`.
- Context resolved by the orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `ACTIVE_TARGET_ID = active_target_defaults.design_system`
  - `ACTIVE_TARGET_ROOT = targets.registry[ACTIVE_TARGET_ID].root`
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`
  - `SPEC_PACKET_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/specs/{component_slug}`

## Topology Gate (required)

1. `TOPOLOGY_REPO_MODE` valid (`single_repo | monorepo_melos | multi_repo`).
2. `PROJECT_ROOT` and `ACTIVE_TARGET_ROOT` accessible.
3. `ACTIVE_TARGET_ID` exists in `targets.registry` and its `kind` is
   `design_system`.
4. If `location_strategy=melos_package`: `repo_root/melos.yaml` and
   `repo_root/package_path` exist.

If any validation fails, finish with `blocked_input`.

## App Repo Ownership Gate (required)

1. `project.config.yaml` must be the canonical config for the app repo:
   `{PROJECT_ROOT}/.sopp/config/project.config.yaml`.
2. `PROJECT_ROOT` cannot be a library DS/shared/core.
3. Minimum app signals:
   - `single_repo | multi_repo`: exists `lib/main.dart` or `lib/main_*.dart`
     or folder `android/` or `ios/`.
   - `monorepo_melos`: exists `melos.yaml`, package target valid and package
     target is not classified as DS/shared/core.
4. If it fails, block with:
   - `CONFIG_PROJECT_CONFIG_OUTSIDE_APP_REPO`
   - `CONFIG_PROJECT_ROOT_POINTS_TO_LIBRARY`
   - `CONFIG_APP_EXECUTABLE_SIGNAL_MISSING`

## Figma MCP Gate (required)

Before PHASE 1, `@ds-orchestrator` must delegate Figma MCP preflight to
`@figma-analyzer`. The analyzer verifies that Figma MCP is available and that
the user/agent has access to the file and `node-id`.

Minimum checklist:

1. URL parseable with `fileKey` and `nodeId`.
2. Figma MCP is configured in the active tool.
3. `get_design_context(fileKey, nodeId)` returns context for the node.
4. `get_screenshot(...)` returns a screenshot for the main node.
5. Sufficient permissions to read components, styles, variables and assets.

If it fails, update `spec.yaml.external_access.figma_mcp.status=blocked_input`,
persist `evidence/figma-mcp-preflight.md` and finish with `blocked_input`.

## User Inputs

```text
@ds-orchestrator /new-component
component_name: ds_status_badge
figma_url: https://www.figma.com/file/xxx/Component?node-id=123
user_story: [Optional acceptance context]
user_story_path: [Optional Markdown path; e.g. docs/user-stories/story-123.md]
atomic_hint: [Optional atom|molecule|organism]
```

## Execution Sequence

### PHASE 0 — Mobile Spec Packet (`mini`)

**Agent**: `@ds-orchestrator`
**Skill**: `mobile-sdd-spec-validation`

Create `SPEC_PACKET_PATH` with:

1. `spec.yaml` (`schema_ref: ../docs/templates/schemas/mobile-spec.schema.yaml`,
   `spec_level: mini`, `execution_mode: propose_then_apply`)
2. `context.json`
3. `review.md` in Spanish
4. `evidence/validation-report.md`

The initial spec records inputs, acceptance criteria, Figma URL, user story,
expected success criteria (`widget_tests`, `goldens`, `widgetbook`,
`audit`), `external_access.figma_mcp.required=true`, permissions per agent and
sections that each agent must read.

Minimum packet permissions:

- `figma-analyzer`: can call `figma_mcp` and write only analysis of design
  in `spec.yaml` + evidence.
- `component-planner` and `component-architect`: cannot call Figma MCP; only
  enrich the spec and evidence.
- `widget-developer`: can create/modify files declared in
  `artifact_plan.planned[]` for `target_id=design_system`; cannot delete
  files.
- test agents: can create/modify tests and evidence for the scope.
- `code-auditor` and `delivery-manager`: verify and report; do not generate UI.

---

### PHASE 1 — Design Analysis

**Agent**: `@figma-analyzer`
**Prompt**: `figma-analysis.prompt.md`

Required output: update in `spec.yaml` only `design_source`,
`literal_texts`, `layout_constraints`, `assets` and `success_criteria.visual`.
Persist evidence in `evidence/figma-analysis.md`.

---

### PHASE 2 — Spec + Inventory + DAG

**Agent**: `@component-planner`
**Prompt**: `atomic-inventory.prompt.md`

Update in `spec.yaml` only `canonical_spec`, `inventory`, `dag` and
`artifact_plan.planned[group=ds_components]`.

---

### PHASE 2.5 — Architecture Technical

**Agent**: `@component-architect`

Update in `spec.yaml` only `technical_plan`, `artifact_plan`,
`contracts.text_overflow`, `success_criteria` and `handoffs`.

---

### PHASE 2.7 — Validation + Human Review

**Skill**: `mobile-sdd-spec-validation`

Validate `spec.yaml` and present `review.md`.

Present to the developer:
1. visual analysis and literal text.
2. inventory, DAG and planned artifacts.
3. technical plan.
4. success criteria from `review.md`.

Wait for explicit approval to continue.
If the human requests adjustments, update only `spec.yaml`, `review.md` and the
affected sections. Do not generate code until `context.json` marks the spec
as approved.

---

### PHASE 3 — DS Code Generation

**Agent**: `@widget-developer`
**Prompts**: `codegen-atom.prompt.md`, `codegen-molecule.prompt.md`, `codegen-organism.prompt.md`

Required order: atoms → molecules → organisms.
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_codegen
read_sections:
  - technical_plan
  - artifact_plan.planned[group=ds_components]
  - literal_texts
  - layout_constraints
  - contracts.text_overflow
  - contracts.technical_vectors
  - success_criteria
```

Output: files `.dart` bajo
`targets.registry[artifact_plan.planned[].target_id].root`.

---

### PHASE 3.5 — Quality Audit

**Agent**: `@code-auditor`

Loop with `@widget-developer` up to `pipeline.max_audit_retries`.

Required output: `evidence/audit-report.md` and a summary in the human report.

---

### PHASE 4a — Widget Tests DS

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGET_TESTS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_widget_tests
read_sections:
  - artifact_plan.planned[group=ds_components]
  - technical_plan
  - literal_texts
  - contracts.text_overflow
  - success_criteria
```

---

### PHASE 4b — Golden Tests DS

**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_GOLDEN_TESTS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_golden_tests
read_sections:
  - artifact_plan.planned[group=ds_components]
  - technical_plan
  - layout_constraints
  - contracts.text_overflow
  - success_criteria
```

---

### PHASE 4c — Widgetbook DS

**Agent**: `@widgetbook-developer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGETBOOK`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_widgetbook
read_sections:
  - artifact_plan.planned[group=ds_components]
  - technical_plan
  - literal_texts
  - contracts.text_overflow
  - success_criteria
```

---

### PHASE 5 — Delivery

**Agent**: `@delivery-manager`
**Prompt**: `delivery-review.prompt.md`

Required output: `evidence/delivery-report.md` and a summary in the human report.

## Rules

- Do not generate code before approving `review.md`.
- `spec.yaml` is the machine source; `PIPELINE_SPEC_PATH` remains a readable
  cumulative report.
- Handoffs by reference; do not copy full human reports between agents.
- Do not generate artifacts outside the resolved root for
  `artifact_plan.planned[].target_id`.
- No skip phases required.
- Record each phase in `PIPELINE_LOG_PATH`.
- If a phase does not apply, use `skipped` with an explicit reason.
