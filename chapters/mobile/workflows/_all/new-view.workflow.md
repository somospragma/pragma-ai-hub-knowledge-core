---
id: new-view
version: 1.4.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: ds-orchestrator
input_contract: ../docs/templates/spec-packets/new-view.overlay.yaml
invocation_mode: explicit_agent
description: >
  Deterministic workflow to create a Flutter view or screen from Figma using DS components and the app presentation layer. Use when the user requests a Figma-driven app screen with view states, tests, Widgetbook, and audit gates.
---
# Workflow: New View/Screen from Figma

## Evidence Mode

Accept `evidence_mode: minimal | standard`; default to `minimal` and persist it
as `spec.yaml.evidence_mode` before validation. In `minimal`, retain gate
evidence and record every other phase as a compact
`context.json.phase_results` entry. `standard` additionally writes detailed
phase reports. Neither mode may omit a gate, approval, test result, blocker or
delivery result.

## Initial Invocation Is Plan-Only

The initial `/new-view` response may write only the Mobile Spec Packet and its
evidence. It must complete analysis, DS/App inventory, DAG, and technical plan
inside `spec.yaml`, then present `review.md` in Spanish and end the response.
It must not generate Flutter code, tests, assets, routes, Widgetbook files, or
project configuration in that response.

Only a later human turn that explicitly approves the pending packet may change
`context.json` to `approved_for_execution` and unlock Phase 3.1. Approval is
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
  - `APP_TARGET_ID = target_id` when supplied; otherwise
    `active_target_defaults.app_target_id`, falling back to
    `active_target_defaults.app`
  - `DESIGN_SYSTEM_TARGET_ID = active_target_defaults.design_system_target_id`,
    falling back to `active_target_defaults.design_system`
  - `SPEC_PACKET_OWNER_TARGET_ID = APP_TARGET_ID` (immutable for the run)
  - `SPEC_PACKET_OWNER_ROOT = targets.registry[SPEC_PACKET_OWNER_TARGET_ID].root`
  - `ACTIVE_TARGET_ID` per implementation phase (`DESIGN_SYSTEM_TARGET_ID` for
    DS, `APP_TARGET_ID` for the view)
  - `ACTIVE_TARGET_ROOT`
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `GENERATION_SCOPE`
  - `CONTRACTS_POLICY`
  - `ARCHITECTURE_CONTRACT_PATH`
  - `PIPELINE_SPEC_PATH = {SPEC_PACKET_OWNER_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {SPEC_PACKET_OWNER_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`
  - `SPEC_PACKET_PATH = {SPEC_PACKET_OWNER_ROOT}/{pipeline.output_dir}/specs/{view_slug}`

## Gates required

### Gate 0 - Canonical Configuration

Before any packet, log, Figma request, or code generation:

1. Resolve `PROJECT_ROOT` from optional `project_root`, then the IDE workspace
   root, then the current repository root.
2. Inspect only `<candidate>/.sopp/config/` for the three final configuration
   files.
3. Require one valid configuration triplet whose
   `project.repository_local_path` matches the resolved app repository.
4. Ignore runtime-looking files under any tool-specific KB folder; only
   `<APP_REPO_ROOT>/.sopp/` may contain project runtime state.
5. If the triplet is missing, partial, invalid, or ambiguous, finish with
   `blocked_input`. Do not create a bootstrap proposal or write any YAML.

### Gate 0.1 - Topology

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate roots (`PROJECT_ROOT`, `APP_TARGET_ID` and
   `DESIGN_SYSTEM_TARGET_ID` if DS components will be created).
3. In targets `location_strategy=melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

### Gate 0.2 - Spec Packet Ownership

Before writing any packet, log, report or Figma evidence:

1. Resolve `APP_TARGET_ID` from `target_id` or the app default. It must exist
   in `targets.registry` and have `kind: app`.
2. Set `SPEC_PACKET_OWNER_TARGET_ID = APP_TARGET_ID` and
   `SPEC_PACKET_OWNER_ROOT = targets.registry[APP_TARGET_ID].root`.
3. Compute every packet-state path from `SPEC_PACKET_OWNER_ROOT` only.
   `ACTIVE_TARGET_ID` may change for DS and app implementation phases, but it
   must never change `SPEC_PACKET_PATH`, `PIPELINE_LOG_PATH` or
   `PIPELINE_SPEC_PATH`.
4. If the resolved packet root differs from `SPEC_PACKET_OWNER_ROOT`, stop with
   `CONFIG_SPEC_PACKET_ROOT_MISMATCH`. If the target is missing or is not an
   app, stop with `CONFIG_SPEC_PACKET_OWNER_INVALID`.

### Gate 0.5 — Ownership of the Repo App

1. `project.config.yaml` must be the canonical config for the app repo:
   `{PROJECT_ROOT}/.sopp/config/project.config.yaml`.
2. `PROJECT_ROOT` cannot be a library DS/shared/core.
3. Minimum app signals:
   - `single_repo | multi_repo`: exists `lib/main.dart` or `lib/main_*.dart`
     or folder `android/` or `ios/`.
   - `monorepo_melos`: Melos resolver passes, package target is valid and the
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
   `spec.yaml.contracts.minimal_domain_data` before Phase 3.4.
3. `required`: block if referenced domain/data contracts are missing.

If it fails a gate, finish with `blocked_input`.

### Gate 3 — Figma MCP

Before PHASE 1, `@ds-orchestrator` prefers `@figma-analyzer` for Figma MCP
preflight. When the active surface cannot delegate natively, it executes the
figma-analyzer role contract itself only when the packet grants Figma MCP,
packet-write and source-archive permissions. The preflight verifies that Figma
MCP is configured and has permissions for the file/screen; otherwise stop with
`PLATFORM_CONTROLLER_ROLE_CAPABILITY_MISSING`.

Minimum checklist:

1. URL parseable with `fileKey` and `nodeId`.
2. Figma MCP is available in the active tool.
3. `get_design_context(fileKey, nodeId)` responds.
4. `get_screenshot(...)` responds for the main frame.
5. Access is confirmed for required components, styles, variables and assets.
6. The active agent can write the packet-only Figma source archive at
   `{SPEC_PACKET_PATH}/source-assets/figma/`.
7. `get_images(...)` exports can be persisted by the active tool surface; a
   screenshot or temporary URL alone does not satisfy source-asset access.

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
golden_tests: false  [Optional; default false]
evidence_mode: minimal  [Optional; default minimal]
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

Record `packet_owner_target_id: APP_TARGET_ID` and
`packet_root: SPEC_PACKET_PATH` in `context.json`. Verify that the packet path
is inside `SPEC_PACKET_OWNER_ROOT` before the first write. DS phases may write
only their planned artifacts under `DESIGN_SYSTEM_TARGET_ID`; they must keep
all packet state and evidence under this app-owned packet.

The initial spec records inputs, Figma URL, user story, contracts policy,
architecture required, success criteria for DS + view and checkpoints
required. Must include `external_access.figma_mcp.required=true` and
`agent_permissions` per agent. Normalize an omitted `golden_tests` input to
`false` and persist the resolved boolean in `spec.yaml.inputs`. Plan golden
artifacts and golden success criteria only when it is `true`. Do not generate
code in this phase.

---

### PHASE 1 — Analysis of Screen

**Preferred specialist role**: `@figma-analyzer`
**Execution owner**: `@ds-orchestrator` when native delegation is unavailable
and the approved packet grants the figma-analyzer role permissions.
**Prompt**: `figma-analysis.prompt.md`

Update in `spec.yaml` only `design_source`, `literal_texts`,
`layout_constraints`, `view_states`, `navigation`, `assets`, and
`visual_manifest`, and `layout_manifest`. Download every visible Figma icon, image, illustration,
logo, and image-fill source into `{SPEC_PACKET_PATH}/source-assets/figma/` and
record its node id, format, archive path and SHA-256 in `assets`. Do not accept
a screenshot, URL, existing local asset, or similar icon as a substitute.
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

### PHASE 2.1 — Architecture Technical

**Agent**: `@component-architect`

Update in `spec.yaml` only `technical_plan`, `artifact_plan`,
`contracts.text_overflow`, `contracts.asset_rendering`,
`contracts.icon_mapping`, `contracts.typography_mapping`,
`contracts.screen_chrome`, `visual_manifest`, `success_criteria`, `handoffs`
and `checkpoints`.

---

### PHASE 2.2 — Contracts Minimum (only `CONTRACTS_POLICY=generate`)

**Agent**: `@component-architect`

Update in `spec.yaml` only `contracts.minimal_domain_data`.

---

### PHASE 2.3 — Validation + Human Review

**Skill**: `mobile-sdd-spec-validation`

The orchestrator validates the `/new-view` plan gate in
`mobile-sdd-spec-validation`, presents `review.md` and waits for explicit
approval.

Present:

1. visual analysis, texts, constraints and states view.
2. visual manifest reconciliation: cropped assets, exact icon mappings,
   typography mappings, and bottom-navigation ownership.
3. layout manifest reconciliation: viewport, parent-child order, bounds,
   direction, padding, gap, clipping, four-corner radii, border width, and
   fixed fidelity tolerances.
4. inventory + DAG with DS/App separation.
5. technical plan.
6. success criteria of DS, view, tests, goldens and Widgetbook.

If the human requests adjustments, update only `spec.yaml`, `review.md` and the
affected sections. Do not generate code until `context.json` marks the spec as
approved.

The response that presents this review must end here. Code generation begins
only in a later human turn with explicit approval of this pending packet.

---

### PHASE 3.1 — Codegen of Components DS

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
  - assets
  - source-assets/figma
  - contracts.text_overflow
  - contracts.technical_vectors
  - contracts.asset_rendering
  - contracts.icon_mapping
  - contracts.typography_mapping
  - visual_manifest
  - layout_manifest
  - success_criteria
```

---

### PHASE 3.2 — Audit of Components DS

**Agent**: `@code-auditor`

Loop with `@widget-developer` up to `pipeline.max_audit_retries`.

Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_component_audit
read_sections:
  - artifact_plan.planned[group=ds_components]
  - technical_plan
  - contracts.technical_vectors
  - contracts.asset_rendering
  - contracts.icon_mapping
  - contracts.typography_mapping
  - visual_manifest
  - layout_manifest
  - success_criteria
```

---

### PHASE 3.3 — Checkpoint Human of Layer DS

**Agent**: `@ds-orchestrator`

Present a compact review in Spanish before generating the app view:

1. DS components created/modified
2. audit result DS
3. covered visual criteria
4. risks or fallbacks pending

Wait for explicit approval. If the human requests adjustments, return to
PHASE 3.1 or PHASE 3.2 as applicable. Do not continue to PHASE 3.4 until
`context.json.checkpoints.ds_layer.status=approved` and
`context.json.status=approved_for_execution`.

---

### PHASE 3.4 — Codegen of View App

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
  - contracts.asset_rendering
  - contracts.icon_mapping
  - contracts.typography_mapping
  - contracts.screen_chrome
  - source-assets/figma
  - visual_manifest
  - layout_manifest
  - success_criteria
```

Output:
- View in `targets.registry[APP_TARGET_ID].structure.views_path`.
- Private widgets in `targets.registry[APP_TARGET_ID].structure.view_widgets_path`.

---

### PHASE 3.5 — Audit of App View

**Agent**: `@code-auditor`

Loop with `@widget-developer` up to `pipeline.max_audit_retries`.
The audit must reconcile every `visual_manifest` entry. A missing downloaded
Figma source archive, checksum mismatch, missing exact icon, unrecreated
`explicit_clip_transform` crop, unresolved typography, or incorrect
bottom-navigation ownership is a blocker.
It must also reject a missing/changed `layout_manifest` child order, geometry
outside `1 dp`, incorrect corner radii or border width, or a fidelity report
over `2%` global / `4%` regional pixel difference.

Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: app_view_audit
read_sections:
  - artifact_plan.planned[group=app_view]
  - technical_plan.view
  - literal_texts
  - assets
  - source-assets/figma
  - visual_manifest
  - layout_manifest
  - contracts.asset_rendering
  - contracts.icon_mapping
  - contracts.typography_mapping
  - contracts.screen_chrome
  - success_criteria
```

---

### PHASE 3.6 — Human Checkpoint of App View

**Agent**: `@ds-orchestrator`

Present the app-view audit and wait for explicit approval before tests. Include
the resolved bottom-navigation ownership, every Figma source archive result,
any crop/icon/typography mapping, and `evidence/figma-fidelity-report.json`.
The fidelity report is required for every view and compares the canonical Figma
screenshot with Flutter at `layout_manifest.viewport`. It must pass `1 dp`
geometry, `2%` global pixel difference, and `4%` regional pixel difference. If
capture or comparison cannot be completed, stop with
`FIGMA_FIDELITY_COMPARISON_UNAVAILABLE`.

Do not continue until `context.json.checkpoints.app_view_layer.status=approved`
and `context.json.status=approved_for_execution`.

---

### PHASE 4.1 — Tests of Components DS

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

### PHASE 4.2 — Golden of Components DS (conditional)

**Condition**: `golden_tests=true`.
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

When `golden_tests=false`, do not invoke `@golden-test-engineer` or create DS
golden artifacts. Record the single run outcome `golden_tests: skipped_by_input`
with `reason: golden_tests=false` in `context.json`, `spec.yaml` and
`PIPELINE_LOG_PATH`.

---

### PHASE 4.3 — Widgetbook of Components DS

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

### PHASE 4.4 — Tests of View

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
  - visual_manifest
  - layout_manifest
  - contracts.text_overflow
  - contracts.screen_chrome
  - success_criteria
```

Minimum coverage:
1. `loading`
2. `empty`
3. `error`
4. `populated`
5. critical navigation
6. bottom-navigation ownership when applicable
7. literal text and mitigation of overflow when applicable

---

### PHASE 4.5 — Golden Tests of Complete View (conditional)

**Condition**: `golden_tests=true`.
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
  - assets
  - source-assets/figma
  - visual_manifest
  - layout_manifest
  - contracts.asset_rendering
  - contracts.icon_mapping
  - contracts.typography_mapping
  - contracts.screen_chrome
  - contracts.text_overflow
  - success_criteria
```

When `golden_tests=false`, this phase is already represented by the single
`golden_tests: skipped_by_input` outcome recorded in Phase 4.2. Do not invoke
the agent or create view golden artifacts.

Minimum coverage:
1. `loading`
2. `empty`
3. `error`
4. `populated`
5. `light/dark`
6. compact viewport if overflow risk exists

---

### PHASE 4.6 — Widgetbook of Screen App

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
  - visual_manifest
  - layout_manifest
  - contracts.screen_chrome
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
6. require passing `evidence/widget-tests.md` and
   `evidence/view-widget-tests.md`
7. require passing `evidence/golden-tests.md` when `golden_tests=true`, or the
   recorded `golden_tests: skipped_by_input` outcome when false
8. require completed visual-manifest and layout-manifest reconciliation plus a
   passing `evidence/figma-fidelity-report.json` at the manifest viewport:
   exact text/hierarchy/assets/typography/shape values, at most `1 dp`
   geometry delta, `2%` global pixel difference and `4%` regional pixel
   difference
