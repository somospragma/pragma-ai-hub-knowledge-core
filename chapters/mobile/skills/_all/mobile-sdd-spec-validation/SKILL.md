---
id: mobile-sdd-spec-validation
version: 1.3.0
scope: chapter
type: skill
chapter: mobile
description: Validates Mobile Spec Packets, Bootstrap Spec Packets and anti-drift rules before changes are applied.
tags: [mobile, sdd, validation, bootstrap, drift]
---
# Mobile SDD Spec Validation

## When To Apply

Use this skill in any mobile workflow that generates or consumes a Spec Packet:

- `/bootstrap-workspace`
- `/new-component`
- `/new-view`
- `/new-feature`
- `/refactor-component`
- `/refactor-feature`
- `/test-plan`
- `/fix-pr-comments`

Validation happens before applying changes and before declaring any phase as
approved.

## Instruction

Validate the corresponding SDD packet with selective file reads. Do not paste
the full packet into handoffs; use file references.

Canonical chapter schemas:

- `../../docs/templates/schemas/mobile-spec.schema.yaml`
- `../../docs/templates/schemas/mobile-context.schema.json`
- `../../docs/templates/schemas/bootstrap-spec.schema.yaml`
- `../../docs/templates/schemas/project-config.schema.yaml`
- `../../docs/templates/schemas/architecture-contract.schema.yaml`
- `../../docs/templates/schemas/dependencies-contract.schema.yaml`

## Bootstrap Spec Packet

Expected files:

```text
<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}/
├── bootstrap-spec.yaml
├── context.json
├── review.md
├── proposed/
│   ├── project.config.yaml
│   ├── architecture-contract.yaml
│   └── dependencies-contract.yaml
└── evidence/
    ├── workspace-discovery-report.md
    ├── candidates.json
    ├── validation-report.md
    └── drift-analysis.md
```

Minimum checks:

1. `bootstrap-spec.yaml` exists and declares:
   - `workflow: bootstrap-workspace`
   - `mode: propose_then_apply`
   - `status: proposed | applied | blocked_input`
   - `schema_ref` references for every proposed file
2. `context.json` exists and can resume apply without conversational context.
3. `review.md` exists and is written in Spanish.
4. The three files under `proposed/` exist.
5. Resolved topology includes `APP_REPO_ROOT` and `targets.registry`.
6. `APP_REPO_ROOT` does not point to DS/shared/core unless it also has
   executable app signals.
7. Every `targets.registry.*.root` exists and, when it is a Dart/Flutter
   package, contains `pubspec.yaml`.
8. If a target uses `location_strategy=melos_package`, `repo_root/melos.yaml`
   and `repo_root/package_path` exist.
9. Every local dependency uses `source=target` and its `target_id` exists in
   `project.config.yaml.targets.registry`.
10. `validation-report.md` and `drift-analysis.md` exist.
11. The three proposed files declare `ownership.file`, `ownership.owns` and
    `ownership.must_not_define`.
12. If `bootstrap-spec.yaml.status=applied`, all critical flags under
    `validation` must be `true`: `schema_valid`,
    `app_root_has_executable_signal`, `no_dependency_root_selected`,
    `target_registry_paths_resolved` and `no_contract_drift_detected`.

## Mobile Spec Packet

Expected files for functional workflows:

```text
{ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/specs/{workflow_slug}/
├── spec.yaml
├── context.json
├── review.md
└── evidence/
```

Minimum checks:

1. `spec.yaml` declares `workflow`, `spec_level`, `execution_mode` and
   `success_criteria`.
   - Allowed `spec_level`: `mini | standard | full`.
   - If `schema_ref` exists, it points to `mobile-spec.schema.yaml`.
2. `execution_mode` defaults to `propose_then_apply`.
3. `context.json` declares `schema_ref` for `mobile-context.schema.json`, a
   `workflow_controller`, a global status and a `checkpoints` object.
   The controller must match the workflow `entry_agent`.
4. The initial checkpoint is required and execution continues only when
   `context.json.status=approved_for_execution` and
   `context.json.checkpoints.initial_spec.status=approved`.
5. `external_access` and `agent_permissions` always exist.
6. `human_review.initial_spec_approval=required`.
7. For `standard` and `full`, `human_review.layer_checkpoints=required`.
   For `mini`, it may be omitted or declared as `not_required`.
8. Workflows with stage checkpoints declare
   `human_review.stage_checkpoints=required`.
9. If a phase creates, modifies or deletes files, runs commands or calls
   external tools, `agent_permissions.<agent>` exists and is sufficient.
10. For Figma-driven workflows (`/new-component`, `/new-view` and
   `/new-feature` with `figma_url`), `external_access.figma_mcp.required=true`.
   Before analysis there must be preflight evidence at
   `evidence/figma-mcp-preflight.md`, and the preflight agent must include
   `figma_mcp` in `can_call_external_tools`.
11. `review.md` exists and is written in Spanish.
12. Every success criterion has at least one expected evidence path.
13. Every planned artifact declares `target_id`, and `target_id` exists in
    `project.config.yaml.targets.registry`.
14. Every `artifact_plan.planned[].path` is relative to its target and resolves
    inside `targets.registry[target_id].root`.
    If layer groups are used, they live in `artifact_plan.planned[].group`;
    `artifact_plan.planned` remains the canonical source for all files.
15. Every mandatory documentation or report file (`docs/testing`,
    `docs/refactoring`, base project documents) is declared in
    `artifact_plan.planned[]` with `group: docs` before it is created or
    modified.
16. Every phase states which spec sections it reads to reduce token usage.
17. `PIPELINE_SPEC_PATH`, if present, is treated only as a human report; it must
    not contradict `spec.yaml`.

### `/new-view` Plan Gate

Before presenting `review.md` or allowing the initial approval, verify that the
packet is a real executable plan, not an empty template. Require:

1. Figma MCP preflight evidence and `external_access.figma_mcp.status=verified`.
2. Non-empty `design_source`, `layout_constraints`, `view_states`, and
   `navigation`.
3. Non-empty `canonical_spec`, `inventory`, `dag`, and `technical_plan`.
4. A non-empty `artifact_plan.planned` that separates DS and app-view
   artifacts and assigns every artifact a `target_id`.
5. Non-placeholder success criteria with evidence paths.
6. `context.json.status=pending_human_review` and
   `checkpoints.initial_spec.status=pending`.

If any condition fails, use `CONFIG_SPEC_PACKET_INVALID`; do not present an
approval request and do not delegate to a code-producing agent.

Before any code-producing phase, require the same packet plus
`context.json.status=approved_for_execution` and
`checkpoints.initial_spec.status=approved`. Otherwise return
`CONFIG_SPEC_NOT_APPROVED` without modifying project files.

## Agent Permission Validation

For every handoff:

1. Resolve `agent_permissions.<agent>`.
2. Verify `can_read` covers the handoff `read_sections`.
3. If the phase writes files, require `can_create_files=true` or
   `can_modify_files=true` as appropriate.
4. Verify `can_write` is structured, not free text:
   - `generated_files_source: artifact_plan.planned` when the agent creates,
     modifies, moves or verifies project files.
   - `artifact_targets` contains every `target_id` the agent may touch.
   - `spec_sections` contains only spec sections the agent may update.
   - `context_sections` contains only compact `context.json` sections.
   - `evidence` contains reports the agent may produce.
5. Every file written by the agent exists in `artifact_plan.planned[]` with
   `owner=<agent>` or with an approved delegated owner.
6. If the phase deletes files or `artifact_plan.planned[].action=delete`,
   require `can_delete_files=true` and explicit human approval recorded in the
   packet. Without this elevation, block with `SPEC_DELETE_PERMISSION_MISSING`.
7. If the phase calls external tools, require the tool under
   `can_call_external_tools`.
8. If a phase proposes a branch, commit or PR without `git`/`gh` in
   `can_call_external_tools`, treat it only as human-facing delivery text, not
   as an executed action.
9. Require at least one path in `evidence_required`.

If validation fails, block with `SPEC_AGENT_PERMISSION_MISSING`.

## Figma MCP Validation

For `/new-component`, `/new-view` and `/new-feature` with `figma_url`:

1. `external_access.figma_mcp.required=true`.
2. `figma-analyzer` performs the preflight and is the only agent that calls
   Figma MCP. It records status `verified` before design analysis continues.
3. If it is not verified, block with `FIGMA_MCP_ACCESS_NOT_VERIFIED`.
4. If MCP lacks permissions for the file, node or assets, block with
   `FIGMA_MCP_PERMISSION_DENIED`.

## Anti-Drift Validation

Apply these rules before apply:

| Field Or Responsibility | Allowed Owner |
|---|---|
| `project.repository_local_path` | `project.config.yaml` |
| `workspace.*` | `project.config.yaml` |
| `topology.*` | `project.config.yaml` |
| `targets.registry.*` | `project.config.yaml` |
| `active_target_defaults.*` | `project.config.yaml` |
| `pipeline.*` | `project.config.yaml` |
| `targets.registry.<target_id>.structure.*_path` | `project.config.yaml` |
| `tokens.*` | `project.config.yaml` |
| layer rules | `architecture-contract.yaml` |
| generation policies | `architecture-contract.yaml` |
| domain/data contracts | `architecture-contract.yaml` |
| DS/core/shared catalog | `dependencies-contract.yaml` |
| dependency target_id/import/version | `dependencies-contract.yaml` |
| allowed dependency matrix | `dependencies-contract.yaml` |

Every final YAML must declare explicit ownership:

```yaml
ownership:
  file: project.config.yaml
  owns: [workspace, topology, targets, active_target_defaults, pipeline, naming, tokens, testing]
  must_not_define: [layers, generation_policies, dependency_catalog, package_sources]
```

```yaml
ownership:
  file: architecture-contract.yaml
  owns: [layer_rules, generation_policies, architecture_constraints, domain_data_contracts]
  must_not_define: [topology, targets, pipeline, dependency_catalog]
```

```yaml
ownership:
  file: dependencies-contract.yaml
  owns: [dependency_catalog, external_dependencies, internal_dependencies, allowed_dependency_matrix]
  must_not_define: [topology, targets, pipeline, layer_rules]
```

`dependencies-contract.yaml` must not define local physical target paths. If a
dependency lives in the workspace, it references `target_id`; the physical path
is resolved from `project.config.yaml.targets.registry`.

If a field appears under more than one owner with different meaning, block with
`CONFIG_CONTRACT_DRIFT_DETECTED` and write the explanation to
`evidence/drift-analysis.md`.

## Expected Output

Write or update a short validation report:

```markdown
# Validation Report

## Result
- Status: passed | blocked_input
- Spec: path/to/spec.yaml
- Context: path/to/context.json

## Checks
| Check | Status | Detail |
|---|---|---|

## Drift
| Field | Expected Owner | Conflicting Location | Action |
|---|---|---|---|
```

## Restrictions

- Do not apply final changes if the spec does not validate.
- For `/new-view`, the first invocation is plan-only. The response that
  presents `review.md` must end before a code-producing phase starts.
- Do not ask the human to write complete YAML; ask for focused natural-language
  adjustments.
- Do not copy long context between agents. Use `spec_ref`, `context_ref`,
  `phase` and `read_sections`.
- Do not require Kiro-only hooks or capabilities as part of the core flow.
