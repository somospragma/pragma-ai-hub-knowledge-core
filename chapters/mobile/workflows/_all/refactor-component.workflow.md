---
id: refactor-component
version: 1.3.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: ds-orchestrator
input_contract: ../docs/templates/spec-packets/refactor-component.overlay.yaml
invocation_mode: explicit_agent
description: >
  Deterministic workflow to refactor an existing Design System component. Use when the user requests implementation, API, visual, accessibility, or maintainability changes to an existing component with review and audit gates.
---
# Workflow: Refactor Component

## Evidence Mode

Accept `evidence_mode: minimal | standard`; default to `minimal` and persist it
as `spec.yaml.evidence_mode` before validation. In `minimal`, retain gate
evidence and record every other phase as a compact
`context.json.phase_results` entry. `standard` additionally writes detailed
phase reports. Neither mode may omit a gate, approval, test result, blocker or
delivery result.

## Prerequisites

- Path for the component to refactor.
- Description of the refactor: what to change and why.
- `.sopp/config/project.config.yaml` valid.
- Context resolved by the orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `ACTIVE_TARGET_ID = active_target_defaults.design_system`
  - `ACTIVE_TARGET_ROOT = targets.registry[ACTIVE_TARGET_ID].root`
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`
  - `SPEC_PACKET_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/specs/{component_slug}-refactor`

## Topology Gate

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate `PROJECT_ROOT` and `ACTIVE_TARGET_ROOT`.
3. Validate that `ACTIVE_TARGET_ID` exists in `targets.registry` and its `kind` is
   `design_system`.
4. In `location_strategy=melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

If it fails, finish with `blocked_input`.

## User Inputs

```text
@ds-orchestrator /refactor-component
component_path: lib/src/organisms/cards/product_card.dart
refactor_goal: Extract the header into a separate molecule and add support for the compact variant.
compatibility_policy: no_public_api_change
evidence_mode: minimal
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

The spec records target component, refactor intent, compatibility constraints
in `constraints.compatibility`, success criteria,
expected tests/goldens, permissions per agent and sections that each agent must
read.

---

### PHASE 1 — Current Component Analysis

**Agent**: `@component-planner`

Required output: update in `spec.yaml` `current_state`,
`impact_analysis`, `inventory` and `artifact_plan`.

---

### PHASE 2 — Technical Refactor Plan

**Agent**: `@component-architect`

Required output: update in `spec.yaml` `technical_plan`,
`success_criteria` and `handoffs`.

---

### PHASE 2.5 — Validation + Human Review

**Skill**: `mobile-sdd-spec-validation`

Present:
1. impact analysis
2. change plan
3. breaking changes, if any
4. success criteria from `review.md`

Wait for explicit approval. Do not apply changes until `context.json`
marks the spec as approved.

---

### PHASE 3 — Apply Changes

**Agent**: `@widget-developer`
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: refactor_component
read_sections:
  - technical_plan
  - artifact_plan
  - constraints.compatibility
  - success_criteria
```

Rules:
- Preserve backward compatibility when viable.
- If there are transition APIs, use `@Deprecated`.
- Restrict changes to the resolved root for `artifact_plan.planned[].target_id`.

---

### PHASE 3.5 — Audit

**Agent**: `@code-auditor`

Required output: `evidence/audit-report.md` and a summary in the human report.

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

Required output: `evidence/delivery-report.md` and a summary in the human report.

## Verification (topology-aware)

- `single_repo` or `multi_repo`:
  - `flutter analyze`
  - `flutter test`
  - `flutter test --tags golden`
- `monorepo_melos`:
  - `melos exec --scope={monorepo.target_scope} -- flutter analyze`
  - `melos exec --scope={monorepo.target_scope} -- flutter test`
  - `melos exec --scope={monorepo.target_scope} -- flutter test --tags golden`

## Rules

- Do not apply changes before approving `review.md`.
- `spec.yaml` is the machine source; `PIPELINE_SPEC_PATH` remains a readable
  cumulative report.
- Handoffs by reference; do not copy full analysis between agents.
- Validate `agent_permissions` before create, modify or delete files.
