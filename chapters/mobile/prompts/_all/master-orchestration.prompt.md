---
id: master-orchestration
version: 1.1.0
scope: chapter
type: prompt
chapter: mobile
description: >
  Shared phase-sequencing prompt for functional Mobile SDD workflows. Use it only from a workflow controller after bootstrap has completed.
---
# Master Pipeline (Deterministic)

## Objective

Execute the pipeline in strict order, with required gates per topology,
architecture and contracts, using a single route of artifacts per execution.
This prompt does not control `/bootstrap-workspace`; that workflow is owned only
by `@workspace-discovery` and `workspace-discovery.prompt.md`.

## Required Pre-Execution

1. Receive `PROJECT_ROOT` and `PROJECT_CONFIG_PATH` from the workflow
   controller after its canonical configuration gate. Do not rediscover
   configuration from the current directory and never use `.copilot/config` or
   `.kiro/config` as a fallback.
2. Require the final `.sopp/config` triplet to be valid and owned by
   `PROJECT_ROOT`. If it is missing, partial, invalid, or ambiguous, return the
   matching `CONFIG_*` blocker without creating pipeline outputs.
3. Resolve constants:
   - `PROJECT_ROOT = project.repository_local_path` (fallback `"."`)
   - `TOPOLOGY_REPO_MODE = topology.repo_mode` (fallback `single_repo`)
   - `TOPOLOGY_FEATURE_LOCATION_MODE = topology.feature_location_mode` (fallback `lib_only`)
   - `TOPOLOGY_SHARED_CORE_MODE = topology.shared_core_mode` (fallback `none`)
   - `TOPOLOGY_DS_MODE = topology.ds_mode` (fallback `external_ds_package`)
   - `TARGET_REGISTRY = targets.registry`
   - `APP_TARGET_ID = workflow-resolved app target` (for `/new-view`, use
     `inputs.target_id` when present, otherwise
     `active_target_defaults.app_target_id`, falling back to
     `active_target_defaults.app`)
   - `DESIGN_SYSTEM_TARGET_ID = active_target_defaults.design_system_target_id`
     (fallback `active_target_defaults.design_system`)
   - `SPEC_PACKET_OWNER_TARGET_ID = workflow-resolved target before Phase 0`.
     It is immutable for the run and is not the same concept as
     `ACTIVE_TARGET_ID`.
   - `SPEC_PACKET_OWNER_ROOT = targets.registry[SPEC_PACKET_OWNER_TARGET_ID].root`
   - `ACTIVE_TARGET_ID` per implementation phase
   - `ACTIVE_TARGET_ROOT = targets.registry[ACTIVE_TARGET_ID].root`
   - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
   - `PIPELINE_ROOT = {SPEC_PACKET_OWNER_ROOT}/{pipeline.output_dir}`
   - `PIPELINE_LOG_PATH = {PIPELINE_ROOT}/{pipeline.log_file}`
   - `PIPELINE_SPEC_PATH = {PIPELINE_ROOT}/{pipeline.spec_file}`
   - `WIDGETBOOK_COMPONENTS_ROOT = targets.registry[DESIGN_SYSTEM_TARGET_ID].structure.widgetbook_components_path` (fallback `widgetbook`)
   - `WIDGETBOOK_SCREENS_ROOT = targets.registry[APP_TARGET_ID].structure.widgetbook_screens_path` (fallback `widgetbook`)
   - `ARCHITECTURE_MERMAID_PATH = {PROJECT_ROOT}/{architecture.mermaid_doc_path}`
   - `ARCHITECTURE_CONTRACT_PATH = {PROJECT_ROOT}/{architecture.contract_path}`
   - `DEPENDENCIES_CONTRACT_PATH = {PROJECT_ROOT}/{dependencies.contract_path}` (fallback `.sopp/config/dependencies-contract.yaml`)
   - `REQUIRE_ARCHITECTURE_CONTRACT_FOR_NEW_VIEW = architecture_contract.generation_policies.view_generation.require_architecture_contract`
   - `MELOS_ENABLED = monorepo.melos_enabled`
   - `MELOS_ROOT = {PROJECT_ROOT}/{monorepo.melos_root}`
   - `MELOS_TARGET_SCOPE = monorepo.target_scope`
   - `GENERATION_SCOPE = architecture_contract.generation_policies.default_generation_scope` (fallback `presentation_only`)
   - `CONTRACTS_POLICY = architecture_contract.generation_policies.contracts_policy.default` (fallback `optional`)
   - `DETERMINISTIC_MODE = pipeline.deterministic_mode`
   - `ENFORCE_PHASE_CONTRACTS = pipeline.enforce_phase_contracts`
   - `STOP_ON_MISSING_ARTIFACTS = pipeline.stop_on_missing_artifacts`
   - `EVIDENCE_MODE = invocation.evidence_mode` (default `minimal`; allowed
     `minimal | standard`)
4. Resolve `SPEC_PACKET_OWNER_TARGET_ID` before creating any packet, log or
   report. The target must exist in `TARGET_REGISTRY` and its root must be
   accessible. Create `PIPELINE_LOG_PATH` and `PIPELINE_SPEC_PATH` only after
   the canonical configuration gate succeeds.
5. Apply Gate 0 - Topology Gate:
   - Validate `TOPOLOGY_REPO_MODE` in `single_repo | monorepo_melos | multi_repo`.
   - Require `PROJECT_ROOT`, `SPEC_PACKET_OWNER_TARGET_ID`,
     `SPEC_PACKET_OWNER_ROOT`, `ACTIVE_TARGET_ID` and `ACTIVE_TARGET_ROOT`
     accessible.
   - If `monorepo_melos`: require `MELOS_ENABLED=true`, `MELOS_ROOT/melos.yaml`,
     `MELOS_TARGET_SCOPE` and `TARGET_PACKAGE_PATH` valid.
   - If `TOPOLOGY_SHARED_CORE_MODE=external_core_package`: require
     `external_dependencies.shared_core.enabled=true`.
6. Apply Gate 0.5 - App Repo Ownership Gate:
   - Require `PROJECT_CONFIG_PATH` canonical in `{PROJECT_ROOT}/.sopp/config/project.config.yaml`.
   - In `single_repo | multi_repo`: require signal app executable in `PROJECT_ROOT`
     (`lib/main.dart` or `lib/main_*.dart` or `android/` or `ios/`).
   - In `monorepo_melos`: require `melos.yaml`, a valid package target and reject a
     DS/core/shared target.
   - If `PROJECT_ROOT` or `TARGET_PACKAGE_NAME` look like a library (`design_system`,
     `ui_kit`, `shared`, `core`, `common`) and there is no executable app signal, block.
   - Use codes: `CONFIG_PROJECT_CONFIG_OUTSIDE_APP_REPO`,
     `CONFIG_PROJECT_ROOT_POINTS_TO_LIBRARY`,
     `CONFIG_APP_EXECUTABLE_SIGNAL_MISSING`.
8. For `/new-view`, apply Gate 1 - Architecture Gate:
   - If `REQUIRE_ARCHITECTURE_CONTRACT_FOR_NEW_VIEW=true`, require
     `ARCHITECTURE_CONTRACT_PATH`.
   - Treat `ARCHITECTURE_MERMAID_PATH` as an optional reference.
9. For `/new-view`, apply Gate 2 - Contracts Policy Gate:
   - `CONTRACTS_POLICY=optional`: continue without block.
   - `CONTRACTS_POLICY=generate`: create/update contracts minimum in spec
     before `Phase 3b`.
   - `CONTRACTS_POLICY=required`: require references of contracts domain/data
     existing before `Phase 3b`.
10. If it fails a gate, stop with `blocked_input` and explicit reason.
10. Treat the initial functional invocation as plan-only. Require a Mobile Spec
    Packet before any implementation:
   - `SPEC_PACKET_ROOT = {PIPELINE_ROOT}/specs`
   - `SPEC_PACKET_PATH = {SPEC_PACKET_ROOT}/{workflow_slug}`
   - files required: `spec.yaml`, `context.json`, `review.md`,
     `evidence/validation-report.md`.
   - `spec.yaml` must validate against
     `../docs/templates/schemas/mobile-spec.schema.yaml`.
   - `execution_mode=propose_then_apply`.
   - `evidence_mode=EVIDENCE_MODE`.
   - `review.md` always in Spanish.
   - validate with `mobile-sdd-spec-validation`.
   - Do not derive `SPEC_PACKET_ROOT`, `SPEC_PACKET_PATH`,
     `PIPELINE_LOG_PATH` or `PIPELINE_SPEC_PATH` from `ACTIVE_TARGET_ROOT`.
     Changing the active target for an implementation phase must never move
     packet state or evidence.
12. Assign `spec_level` per workflow:
   - `mini`: `/new-component`, `/refactor-component`, `/fix-pr-comments`
   - `standard`: `/new-view`
   - `full`: `/new-feature`, `/refactor-feature`, `/test-plan`
12. Require initial human approval of the Spec Packet in a later human turn:
   - do not generate code, tests, or changes before
     `context.json.status=approved_for_execution` and
     `context.json.checkpoints.initial_spec.status=approved`.
   - in `standard` and `full`, require checkpoints per layer/stage.
   - the handoffs must send `spec_ref`, `context_ref`, `phase` and
     `read_sections`, no complete content of the spec.
   - the response that presents `review.md` must end; it cannot continue into
     a code-producing phase in the same response.
13. Require permissions per agent:
   - if a phase writes files, executes commands, or calls external tools,
     `spec.yaml.agent_permissions.<agent>` must allow it.
   - if the permission does not exist or does not cover the action, stop with
     `blocked_input` and record the missing.
14. Require Figma MCP preflight for Figma-driven workflows:
   - `/new-component`
   - `/new-view`
   - `/new-feature` only if it has `figma_url`
   - block if `external_access.figma_mcp.status` is not `verified`.
15. Define workflow:
   - `/bootstrap-workspace`
   - `/new-component`
   - `/new-view`
   - `/refactor-component`
   - `/fix-pr-comments`
   - `/new-feature`
   - `/refactor-feature`
   - `/test-plan`

## Standard Blocking Codes

- `BOOTSTRAP_WORKSPACE_ROOT_MISSING`
- `BOOTSTRAP_SCAN_ROOTS_EMPTY`
- `BOOTSTRAP_APP_REPO_NOT_RESOLVED`
- `BOOTSTRAP_APP_REPO_AMBIGUOUS`
- `BOOTSTRAP_APP_REPO_MISMATCH_HINT`
- `BOOTSTRAP_APP_REPO_POINTS_TO_LIBRARY`
- `BOOTSTRAP_APP_PACKAGE_NOT_FOUND`
- `BOOTSTRAP_TOPOLOGY_AMBIGUOUS`
- `BOOTSTRAP_MELOS_INVALID`
- `BOOTSTRAP_PROPOSAL_ROOT_UNWRITABLE`
- `BOOTSTRAP_ARCH_CONTRACT_PROPOSAL_INVALID`
- `BOOTSTRAP_PATH_DEPENDENCY_MISSING`
- `BOOTSTRAP_APPLY_NOT_APPROVED`
- `CONFIG_PROJECT_CONFIG_MISSING`
- `CONFIG_PROJECT_ROOT_MISSING`
- `CONFIG_TOPOLOGY_INVALID`
- `CONFIG_MELOS_ROOT_MISSING`
- `CONFIG_TARGET_PACKAGE_MISSING`
- `CONFIG_EXTERNAL_CORE_REQUIRED_MISSING`
- `CONFIG_ARCH_CONTRACT_MISSING`
- `CONFIG_CONTRACTS_POLICY_UNSATISFIED`
- `CONFIG_PROJECT_CONFIG_OUTSIDE_APP_REPO`
- `CONFIG_PROJECT_ROOT_POINTS_TO_LIBRARY`
- `CONFIG_APP_EXECUTABLE_SIGNAL_MISSING`
- `CONFIG_SPEC_PACKET_INVALID`
- `CONFIG_SPEC_PACKET_OWNER_INVALID`
- `CONFIG_SPEC_PACKET_ROOT_MISMATCH`
- `CONFIG_SPEC_NOT_APPROVED`

## Orchestration Contract

- Do not advance to the next phase without validating the required output of the previous phase.
- If a phase returns `blocked_input`, stop the pipeline immediately.
- Record each phase in `PIPELINE_LOG_PATH`.
- Keep `SPEC_PACKET_OWNER_TARGET_ID`, `SPEC_PACKET_OWNER_ROOT`,
  `SPEC_PACKET_PATH`, `PIPELINE_LOG_PATH` and `PIPELINE_SPEC_PATH` immutable
  for the run. Only `ACTIVE_TARGET_ID` and `ACTIVE_TARGET_ROOT` may change by
  phase.
- Update `context.json` and `spec.yaml` after each functional phase.
- Update `PIPELINE_SPEC_PATH` only as the cumulative human report.
- Update `context.json` of the Mobile Spec Packet after each functional phase.
- Record every phase in `context.json.phase_results` with a compact status,
  summary and references. This state is mandatory in both evidence modes.
- If a phase is conditional (`if applicable`), record `skipped` with reason.
- Keep handoffs silent, complete and reference-based.
- Include the resolved `evidence_mode` scalar in every handoff.
- `minimal` writes only gate evidence: validation, required Figma preflight,
  required human decisions, audit, executed tests, enabled optional stages and
  delivery. Record all other completed phases in `context.json.phase_results`
  instead of creating narrative evidence files.
- `standard` additionally writes phase analysis, inventory, planning, codegen,
  Widgetbook and detailed checkpoint reports.
- Do not use `PIPELINE_SPEC_PATH` as the machine source when there is
  `spec_context`.

## Workflow Flow

### `/new-component`

1. Phase 0 → create Mobile Spec Packet `mini`.
2. Phase 1 → `@figma-analyzer` (`figma-analysis.prompt.md`) → update spec with visual analysis, texts, constraints and assets.
3. Phase 2 → `@component-planner` (`atomic-inventory.prompt.md`) → update inventory, DAG and DS artifact plan.
4. Phase 2.5 → `@component-architect` → update technical plan and success criteria.
5. Phase 2.7 → validate Spec Packet and ask human approval required.
6. Phase 3 → `@widget-developer` (`codegen-atom/molecule/organism`) with a compact handoff.
7. Phase 3.5 → `@code-auditor` → audits against `spec_ref` (loop up to `pipeline.max_audit_retries`).
8. Phase 4a → `@test-engineer` (`MODE=DS_WIDGET_TESTS`).
9. Phase 4b → `@golden-test-engineer` (`MODE=DS_GOLDEN_TESTS`) only when
   `golden_tests=true`; otherwise record `skipped_by_input`.
10. Phase 4c → `@widgetbook-developer` (`MODE=DS_WIDGETBOOK`).
11. Phase 5 → `@delivery-manager` (`delivery-review.prompt.md`) → final evidence and human report.

### `/new-view`

1. Gate architecture and contracts policy.
2. Phase 0 → create Mobile Spec Packet `standard`.
3. Phase 1 → `@figma-analyzer` (`figma-analysis.prompt.md`) → update spec with visual analysis, states, texts, constraints and assets.
4. Phase 2 → `@component-planner` (`atomic-inventory.prompt.md`) → update inventory DS vs App, DAG and artifacts.
5. Phase 2.5 → `@component-architect` → update architecture view and technical plan.
6. Phase 2.6 (only `CONTRACTS_POLICY=generate`) → add minimal contracts to the spec.
7. Phase 2.7 → validate Spec Packet and ask human approval required.
8. Phase 3a → `@widget-developer` (`codegen-atom/molecule/organism`) → DS components with a compact handoff.
9. Phase 3a.5 → `@code-auditor` → audits DS against `spec_ref`.
10. A human checkpoint is required after the DS layer.
11. Phase 3b → `@widget-developer` (`codegen-view.prompt.md`) → view app with handoff compact.
12. Phase 4a → `@test-engineer` (`MODE=DS_WIDGET_TESTS`).
13. Phase 4b → `@golden-test-engineer` (`MODE=DS_GOLDEN_TESTS`) only when
    `golden_tests=true`; otherwise record `skipped_by_input`.
14. Phase 4c → `@widgetbook-developer` (`MODE=DS_WIDGETBOOK`).
15. Phase 4d → `@test-engineer` (`MODE=VIEW_WIDGET_TESTS`).
16. Phase 4e → `@golden-test-engineer` (`MODE=VIEW_GOLDEN_TESTS`) only when
    `golden_tests=true`; otherwise reuse the recorded `skipped_by_input` outcome.
17. Phase 4f → `@widgetbook-developer` (`MODE=APP_WIDGETBOOK_SCREENS`, `WIDGETBOOK_SCOPE=APP_SCREENS`).
18. Phase 5 → `@delivery-manager` (`delivery-review.prompt.md`) → final evidence and human report.

### `/refactor-component`

1. Phase 0 → create Mobile Spec Packet `mini`.
2. Phase 1 → `@component-planner` → update the spec with impact, current state and plan.
3. Phase 2 → `@component-architect` → update technical plan and criteria.
4. Phase 2.5 → validate Spec Packet and ask human approval required.
5. Phase 3 → `@widget-developer` → applies the refactor with a compact handoff.
6. Phase 3.5 → `@code-auditor` → audits against `spec_ref`.
7. Phase 4a → `@test-engineer` (`MODE=DS_WIDGET_TESTS`).
8. Phase 4b → `@golden-test-engineer` (`MODE=DS_GOLDEN_TESTS`) if visual impact.
9. Phase 5 → `@delivery-manager` → final evidence and human report.

### `/fix-pr-comments`

1. Phase 0 → create Mobile Spec Packet `mini`.
2. Phase 1 → `@component-planner` → update spec with inventory comment-to-action.
3. Phase 1.5 → validate Spec Packet and ask human approval required.
4. Phase 2 → `@widget-developer` → applies fixes with a compact handoff.
5. Phase 3 → `@code-auditor` → checks comment-to-change coverage against `spec_ref`.
6. Phase 4a → `@test-engineer` (`MODE=DS_WIDGET_TESTS`) if functional impact.
7. Phase 4b → `@golden-test-engineer` (`MODE=DS_GOLDEN_TESTS`) if visual impact.
8. Phase 5 → `@delivery-manager` → final evidence and human report.

### `/new-feature`

1. Phase S0 → `@feature-builder` creates Mobile Spec Packet `full`.
2. Phase 0 → conditional UI/DS inventory; delegate missing components to `@ds-orchestrator`.
3. Phase 1 → scaffold with handoff compact and evidence.
4. Phase 1.5 → API contract analysis; update `spec.yaml.contracts`.
5. Phase 2 → Domain; human checkpoint required.
6. Phase 3 → Data; human checkpoint required.
7. Phase 4 → Presentation; human checkpoint required.
8. Phase 5 → wiring and validation.
9. Phase 6a → `@test-engineer` (`MODE=FEATURE_UNIT_TESTS`); required.
10. Phase 6b → `@test-engineer` (`MODE=FEATURE_WIDGET_TESTS`); required.
11. Phase 6c → `@test-engineer` (`MODE=FEATURE_INTEGRATION_TESTS`); required.
12. Phase 6d → `@golden-test-engineer` (`MODE=FEATURE_GOLDEN_TESTS`) only
    when `golden_tests=true`; otherwise record `skipped_by_input`.
13. Phase 7 → `@code-auditor` audits implementation and required test evidence.
14. Human checkpoint → final build review; required.
15. Phase 8 → project documentation only when `documentation=true`; otherwise
    record `skipped_by_input`.
16. Phase 9 → `@delivery-manager` validates all required evidence and emits the
    final delivery report.

### `/refactor-feature`

1. Phase S0 → `@refactoring-advisor` creates Mobile Spec Packet `full`.
2. Phase 1 → current-state analysis; update `current_state`.
3. Phase 2 → impact and risks; update `impact_analysis`.
4. Phase 3 → plan atomic; update `refactoring_plan`.
5. Phase 4 → required human-readable review in `review.md`.
6. Phase 5 → iterative execution with compact handoffs and required checkpoints.
7. Phase 6 → tests.
8. Phase 7 → audit against `spec_ref`.
9. Phase 8 -> report and documentation.

### `/test-plan`

1. Phase S0 → `@test-coverage-engineer` creates Mobile Spec Packet `full`.
2. Phase 1 → inventory of coverage; update `coverage_inventory`.
3. Phase 2 → test plan; required human-readable review.
4. Phase 3 → test generation with a compact handoff.
5. Phase 4 → execution and validation.
6. Phase 5 → report in `docs/testing/` and final evidence.

## Human checkpoint

For functional workflows, the first checkpoint is always Mobile Spec Packet
approval. Present `review.md` in Spanish, not the complete YAML.

For `mini` (`/new-component`, `/refactor-component`, `/fix-pr-comments`),
this checkpoint enables implementation.

For `standard` and `full`, in addition to the initial checkpoint, request
layer/stage checkpoints according to the workflow:

- `/new-view`: after DS and before the app view.
- `/new-feature`: after Domain, Data and Presentation.
- `/refactor-feature`: after architectural or contract steps.
- `/test-plan`: before generation of tests.

Base question:

"I prepared the spec and success criteria. Do you approve continuing with the next stage?"

Do not continue until receiving explicit approval and recording it in `context.json`.

## Handoff standard (required)

Each delegation includes:

- `workflow`
- `phase_id` and `phase_name`
- `mode` (if the phase prompt is multi-mode)
- `scope` (if the phase agent requires it)
- `project_root`
- `topology` (`repo_mode`, `feature_location_mode`, `shared_core_mode`, `ds_mode`)
- `target` (`package_name`, `package_path`, `target_root`, `feature_root`)
- `execution_context` (`melos_enabled`, `melos_root`, `target_scope`)
- `contracts_context` (`generation_scope`, `contracts_policy`)
- `architecture_refs` (`ARCHITECTURE_CONTRACT_PATH`, `ARCHITECTURE_MERMAID_PATH` optional)
- `spec_context` (`spec_ref`, `context_ref`, `review_ref`, `spec_level`, `phase`, `read_sections`) for functional workflows
- `input_refs`
- `expected_output`
- `output_paths` (`PIPELINE_SPEC_PATH`, `PIPELINE_LOG_PATH`)

If any required field for the current workflow is missing, do not delegate.

## Rules

- Do not code or audit directly; always delegate.
- Include `project_root` and `target_root` in all handoffs.
- In `/new-view`, include always `architecture_refs`.
- In functional workflows, do not include complete specs in handoffs; use
  `spec_context`.
- If there are errors or blocks, record in log and stop.
