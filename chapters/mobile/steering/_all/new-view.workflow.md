---
id: new-view
version: 1.4.0
scope: chapter
type: steering
chapter: mobile
entry_agent: ds-orchestrator
input_contract: ../docs/templates/spec-packets/overlays/new-view.yaml
invocation_mode: explicit_agent
description: >
  Deterministic workflow to create a Flutter view or screen from Figma using DS components and the app presentation layer. Use when the user requests a Figma-driven app screen with view states, tests, Widgetbook, and audit gates.
---
# Workflow: New View/Screen from Figma

## Initial Invocation Is Plan-Only

The initial `/new-view` response may write only the Mobile Spec Packet and its
evidence. It must complete analysis, DS/App inventory, DAG, and technical plan
inside `spec.yaml`, then present `review.md` in Spanish and end the response.
It must not generate Flutter code, tests, assets, routes, Widgetbook files, or
project configuration in that response.

Only a later human turn that explicitly approves the pending packet may change
`context.json` to `approved_for_execution` and unlock Phase 3a. Approval is
invalid when the packet lacks the required plan or when
`checkpoints.initial_spec.status` is not `pending`.

Invoke this workflow through `@ds-orchestrator`. A bare workflow name or a
request that lacks the controller must not authorize implementation; respond
with the canonical invocation instead of generating code.

## Prerequisites

- URL from Figma with `node-id`.
- user story with acceptance criteria (inline text or reference to a Markdown file).
- A valid final configuration triplet in the app repository:
  `.sopp/config/project.config.yaml`, `architecture-contract.yaml`, and
  `dependencies-contract.yaml`.
- This workflow never starts bootstrap automatically. If configuration is
  missing, partial, invalid, ambiguous, or legacy-only, finish with
  `blocked_input` and the relevant configuration code. The human must invoke
  `@workspace-discovery /bootstrap-workspace` explicitly.
- Context resolved by the orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `ACTIVE_TARGET_ID` per phase (`design_system` for DS, `app` for the view)
  - `ACTIVE_TARGET_ROOT`
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `GENERATION_SCOPE`
  - `CONTRACTS_POLICY`
  - `ARCHITECTURE_CONTRACT_PATH`
  - `PIPELINE_SPEC_PATH = {targets.registry[app].root}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {targets.registry[app].root}/{pipeline.output_dir}/{pipeline.log_file}`
  - `SPEC_PACKET_PATH = {targets.registry[app].root}/{pipeline.output_dir}/specs/{view_slug}`

## Gates required

### Gate 0 - Canonical Configuration

Before any packet, log, Figma request, or code generation:

1. Resolve `PROJECT_ROOT` from optional `project_root`, then the IDE workspace
   root, then the current repository root.
2. Inspect only `<candidate>/.sopp/config/` for the three final configuration
   files.
3. Require one valid configuration triplet whose
   `project.repository_local_path` matches the resolved app repository.
4. Ignore `.copilot/config/` and `.kiro/config/`; they are not project runtime
   state.
5. If the triplet is missing, partial, invalid, or ambiguous, finish with
   `blocked_input`. Do not create a bootstrap proposal or write any YAML.

### Gate 0.1 - Topology

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate roots (`PROJECT_ROOT`, target `app` and target `design_system` if
   DS components will be created).
3. In targets `location_strategy=melos_package`, validate `repo_root/melos.yaml`
   and `repo_root/package_path`.

### Gate 0.5 — Ownership of the Repo App

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

### Gate 1 — Architecture

1. If `architecture_contract.generation_policies.view_generation.require_architecture_contract=true`, require
   `ARCHITECTURE_CONTRACT_PATH`.
2. `architecture.md` is optional visual support.

### Gate 2 — Policy of contracts

1. `optional`: continue.
2. `generate`: generate contracts minimum in
   `spec.yaml.contracts.minimal_domain_data` before Phase 3b.
3. `required`: block if referenced domain/data contracts are missing.

If it fails a gate, finish with `blocked_input`.

### Gate 3 — Figma MCP

Before PHASE 1, `@ds-orchestrator` must delegate Figma MCP preflight to
`@figma-analyzer`. The analyzer verifies that Figma MCP is configured and has
permissions for the file/screen.

Minimum checklist:

1. URL parseable with `fileKey` and `nodeId`.
2. Figma MCP is available in the active tool.
3. `get_design_context(fileKey, nodeId)` responds.
4. `get_screenshot(...)` responds for the main frame.
5. Access is confirmed for required components, styles, variables and assets.

If it fails, update `spec.yaml.external_access.figma_mcp.status=blocked_input`,
persist `evidence/figma-mcp-preflight.md` and finish with `blocked_input`.

## User Inputs

```text
@ds-orchestrator /new-view
view_name: product_catalog_view
figma_url: https://www.figma.com/file/xxx/Screen?node-id=456
user_story: [User story or acceptance criteria]
user_story_path: [Optional Markdown path; e.g. docs/user-stories/story-123.md]
route_name: [Optional route name or path]
target_id: [Optional app target id]
project_root: [Optional absolute app repository root when the IDE opens a multi-root workspace]
```

## Canonical Sequence

### PHASE 0 — Mobile Spec Packet (`standard`)

**Agent**: `@ds-orchestrator`
**Skill**: `mobile-sdd-spec-validation`

Create `SPEC_PACKET_PATH` with:

1. `spec.yaml` (`schema_ref: ../docs/templates/schemas/mobile-spec.schema.yaml`,
   `spec_level: standard`, `execution_mode: propose_then_apply`)
2. `context.json`
3. `review.md` in Spanish
4. `evidence/validation-report.md`

The initial spec records inputs, Figma URL, user story, contracts policy,
architecture required, success criteria for DS + view and checkpoints
required. Must include `external_access.figma_mcp.required=true` and
`agent_permissions` per agent. Do not generate code in this phase.

---

### PHASE 1 — Analysis of Screen

**Agent**: `@figma-analyzer`
**Prompt**: `figma-analysis.prompt.md`

Update in `spec.yaml` only `design_source`, `literal_texts`,
`layout_constraints`, `view_states`, `navigation` and `assets`.
Persist evidence in `evidence/figma-analysis.md` and record phase in
`PIPELINE_LOG_PATH`.

---

### PHASE 2 — Extended Inventory + DAG

**Agent**: `@component-planner`
**Prompt**: `atomic-inventory.prompt.md`

Update in `spec.yaml` only `canonical_spec`, `inventory`, `dag`,
`artifact_plan.planned[group=ds_components]` and `artifact_plan.planned[group=app_view]`.
The DS vs App separation must remain explicit in `inventory` and `artifact_plan`.

---

### PHASE 2.5 — Architecture Technical

**Agent**: `@component-architect`

Update in `spec.yaml` only `technical_plan`, `artifact_plan`,
`contracts.text_overflow`, `success_criteria`, `handoffs` and `checkpoints`.

---

### PHASE 2.6 — Contracts Minimum (only `CONTRACTS_POLICY=generate`)

**Agent**: `@component-architect`

Update in `spec.yaml` only `contracts.minimal_domain_data`.

---

### PHASE 2.7 — Validation + Human Review

**Skill**: `mobile-sdd-spec-validation`

The orchestrator validates the `/new-view` plan gate in
`mobile-sdd-spec-validation`, presents `review.md` and waits for explicit
approval.

Present:

1. visual analysis, texts, constraints and states view.
2. inventory + DAG with DS/App separation.
3. technical plan.
4. success criteria of DS, view, tests, goldens and Widgetbook.

If the human requests adjustments, update only `spec.yaml`, `review.md` and the
affected sections. Do not generate code until `context.json` marks the spec as
approved.

The response that presents this review must end here. Code generation begins
only in a later human turn with explicit approval of this pending packet.

---

### PHASE 3a — Codegen of Components DS

**Agent**: `@widget-developer`

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

---

### PHASE 3a.5 — Audit of Components DS

**Agent**: `@code-auditor`

Loop with `@widget-developer` up to `pipeline.max_audit_retries`.

---

### PHASE 3a.7 — Checkpoint Human of Layer DS

**Agent**: `@ds-orchestrator`

Present a compact review in Spanish before generating the app view:

1. DS components created/modified
2. audit result DS
3. covered visual criteria
4. risks or fallbacks pending

Wait for explicit approval. If the human requests adjustments, return to
PHASE 3a or PHASE 3a.5 as applicable. Do not continue to PHASE 3b until
`context.json.checkpoints.ds_layer.status=approved` and
`context.json.status=approved_for_execution`.

---

### PHASE 3b — Codegen of View App

**Agent**: `@widget-developer`
**Prompt**: `codegen-view.prompt.md`
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: app_view_codegen
read_sections:
  - technical_plan.view
  - artifact_plan.planned[group=app_view]
  - contracts
  - view_states
  - navigation
  - literal_texts
  - layout_constraints
  - contracts.text_overflow
  - contracts.technical_vectors
  - success_criteria
```

Output:
- View in `targets.registry[app].structure.views_path`.
- Private widgets in `targets.registry[app].structure.view_widgets_path`.

---

### PHASE 4a — Tests of Components DS

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
  - contracts.text_overflow
  - success_criteria
```

---

### PHASE 4b — Golden of Components DS

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

### PHASE 4c — Widgetbook of Components DS

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

### PHASE 4d — Tests of View

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=VIEW_WIDGET_TESTS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: view_widget_tests
read_sections:
  - artifact_plan.planned[group=app_view]
  - technical_plan.view
  - view_states
  - navigation
  - contracts.text_overflow
  - success_criteria
```

Minimum coverage:
1. `loading`
2. `empty`
3. `error`
4. `populated`
5. critical navigation
6. literal text and mitigation of overflow when applicable

---

### PHASE 4e — Golden Tests of Complete View

**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=VIEW_GOLDEN_TESTS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: view_golden_tests
read_sections:
  - artifact_plan.planned[group=app_view]
  - technical_plan.view
  - view_states
  - layout_constraints
  - contracts.text_overflow
  - success_criteria
```

Minimum coverage:
1. `loading`
2. `empty`
3. `error`
4. `populated`
5. `light/dark`
6. compact viewport if overflow risk exists

---

### PHASE 4f — Widgetbook of Screen App

**Agent**: `@widgetbook-developer`
**Prompt**: `test-generation.prompt.md` (`MODE=APP_WIDGETBOOK_SCREENS`, `WIDGETBOOK_SCOPE=APP_SCREENS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: app_widgetbook
read_sections:
  - artifact_plan.planned[group=app_view]
  - technical_plan.view
  - view_states
  - literal_texts
  - contracts.text_overflow
  - success_criteria
```

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
1. validate the DS/App structure against `targets.registry` and
   `artifact_plan.planned[].target_id`
2. update the DS barrel only for components DS
3. use branch prefix:
   - `naming.view_branch_prefix` if it exists
   - fallback `naming.branch_prefix`
4. generate `evidence/delivery-report.md` and a summary in the human report
5. validate that the delivery satisfies `SPEC_PACKET_PATH/spec.yaml`
