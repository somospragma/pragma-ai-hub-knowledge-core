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

For layer and stage transitions, validation is executable rather than
narrative. Use `../../scripts/sopp_gate.rb`; do not directly author approval
state in `context.json` or reconstruct it at delivery time. A successful schema
read without a successful gate transition does not authorize implementation.

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

## Evidence Mode

Every packet declares `evidence_mode: minimal | standard`; normalize an omitted
invocation value to `minimal` before packet validation. This setting controls
only additional narrative files, never a gate or decision.

In `minimal`, persist the required packet files, validation, Figma preflight
when applicable, human decisions, audit, executed test results, enabled
optional-stage results and delivery. For every other phase, the controller
writes a compact `context.json.phase_results.<phase>` object with `status`, a
summary of at most 280 characters and references. A success criterion may point
to that context entry instead of a verbose evidence file.

In `standard`, retain those guarantees and also write detailed analysis,
inventory, planning, code-generation, Widgetbook and checkpoint reports. The
`agent_permissions.*.evidence_required` list authorizes gate evidence; it does
not force standard-only reports in `minimal`.

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
10. `validation-report.md` and `drift-analysis.md` exist. Detailed discovery
    and candidates files exist only in `standard`; `minimal` records their
    compact result in `context.json.phase_results`.
11. The three proposed files declare `ownership.file`, `ownership.owns` and
    `ownership.must_not_define`.
12. If `bootstrap-spec.yaml.status=applied`, all critical flags under
    `validation` must be `true`: `schema_valid`,
    `app_root_has_executable_signal`, `no_dependency_root_selected`,
    `target_registry_paths_resolved` and `no_contract_drift_detected`.

## Mobile Spec Packet

Expected files for functional workflows:

```text
{SPEC_PACKET_OWNER_ROOT}/{pipeline.output_dir}/specs/{workflow_slug}/
├── spec.yaml
├── context.json
├── review.md
├── source-assets/
│   └── figma/                 # required only for Figma-driven packets
└── evidence/
```

Minimum checks:

1. `spec.yaml` declares `workflow`, `spec_level`, `execution_mode` and
   `evidence_mode` and `success_criteria`.
   - Allowed `spec_level`: `mini | standard | full`.
   - If `schema_ref` exists, it points to `mobile-spec.schema.yaml`.
2. `execution_mode` defaults to `propose_then_apply`.
3. `context.json` declares `schema_ref` for `mobile-context.schema.json`, a
   `workflow_controller`, `packet_owner_target_id`, `packet_root`, a global
   status and a `checkpoints` object.
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
   The analyzer must also have `can_create_files=true`,
   `can_modify_files=true`, and `can_write.packet_paths` including
   `source-assets/figma`.
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
18. `context.json.phase_results` exists. Every completed, failed, blocked or
    skipped phase has a compact result with a status, summary and references.
19. Every `schema_ref` resolves to an existing file from the file that declares
    it. A correct basename pointing to a missing path is invalid.
20. Every approved checkpoint has `decision_ref`, `artifact_hash`,
    `approval_ref`, and `approved_at`; the approval record exists and contains
    the challenge repeated by a later human turn. Bare `{status: approved}`
    objects are invalid.
21. Domain, Data and Presentation evidence exists before their checkpoints can
    open. Before entering a phase, run the executable `can-enter` transition.
22. `pipeline.log.md` is derived from append-only packet events. It is not
    acceptable evidence for an approval that has no structured approval event.

### Deterministic Change Requests

At a pending checkpoint, a human response has exactly one of three effects:

- explicit approval: approve the exact reviewed artifact hash;
- explicit change request: record `changes_requested` and create no code yet;
- question or ambiguous feedback: leave the checkpoint pending.

For a change request, persist the verbatim request, propose a bounded artifact
plan, and wait for a later human authorization. After authorization, apply the
revision, regenerate validation evidence and calculate a new artifact hash.
Return to `pending_human_review`; authorization to revise is not approval of the
revised layer. If the proposal reaches an earlier layer, mark every dependent
checkpoint `stale` and resume from the earliest affected layer.

### `/new-view` Plan Gate

Before presenting `review.md` or allowing the initial approval, verify that the
packet is a real executable plan, not an empty template. Require:

1. Figma MCP preflight evidence and `external_access.figma_mcp.status=verified`.
2. Non-empty `design_source`, `layout_constraints`, `view_states`, and
   `navigation`.
3. Non-empty `canonical_spec`, `inventory`, `dag`, and `technical_plan`.
4. A non-empty `artifact_plan.planned` that separates DS and app-view
   artifacts and assigns every artifact a `target_id`.
5. A complete `visual_manifest`: a captured main-node Figma screenshot,
   reconciled visible elements with no unresolved ids, asset render strategies,
   a downloaded `figma_mcp` source archive record for every visible asset and
   icon, exact icon mappings or archived Figma SVGs, exact-project-font
   typography mappings, and a resolved bottom-navigation ownership.
6. For every asset with `crop.required=true`, require
   `render_strategy=explicit_clip_transform`; frame exports do not satisfy the
   contract. For every icon, permit `ds_icon_exact` only with a named exact DS
   catalog match; otherwise require `figma_svg_asset`.
7. Every `visual_manifest.assets[].asset_id` and
   `visual_manifest.icons[].asset_id` resolves to `assets[].id`, whose
   `figma_export.status=downloaded`, archive path exists under
   `source-assets/figma/`, and SHA-256 matches the archived file. Every
   typography entry has `figma_source.source=figma_mcp` and
   `font_resolution=exact_project_font`.
8. `visual_manifest.reconciliation.visual_verification_required=true` when the
   packet includes a crop, exported Figma icon, or visible bottom navigation.
9. Non-placeholder success criteria with evidence paths.
10. `context.json.status=pending_human_review` and
   `checkpoints.initial_spec.status=pending`.
11. `packet_owner_target_id` resolves to the requested app target or the
   configured app default, its target kind is `app`, and `packet_root` is under
   that target root. The packet owner must not be the Design System target,
   even while DS artifacts are planned or generated.

If any condition fails, use `CONFIG_SPEC_PACKET_INVALID`; do not present an
approval request and do not delegate to a code-producing agent.

Before any code-producing phase, require the same packet plus
`context.json.status=approved_for_execution` and
`checkpoints.initial_spec.status=approved`. Otherwise return
`CONFIG_SPEC_NOT_APPROVED` without modifying project files.

### `/new-feature` Test And Optional-Stage Gate

Before the initial review, require planned artifacts and success criteria for
`unit_tests`, `widget_tests` and `integration_tests`. Their owners must be
`test-engineer`, and the packet must grant that agent sufficient read, write,
target and evidence permissions.

Before audit and delivery, require passed evidence at:

1. `evidence/unit-tests.md`
2. `evidence/widget-tests.md`
3. `evidence/integration-tests.md`

When `inputs.golden_tests=true`, also require planned `golden_tests` artifacts,
`golden-test-engineer` permissions and a passing `evidence/golden-tests.md`.
When false, require the recorded `skipped_by_input` outcome instead.

When `inputs.documentation=true`, require planned `docs` artifacts and
`evidence/documentation-report.md`. When false, require the recorded
`skipped_by_input` outcome instead. Never accept a missing optional-stage
outcome as an implicit skip.

If an integration environment is unavailable, return `blocked_input`; it does
not satisfy the required integration-test evidence.

### `/new-component` And `/new-view` Golden Gate

Normalize an omitted `inputs.golden_tests` to `false` before the initial
review. When it is true, require planned `golden_tests` artifacts,
`golden-test-engineer` permissions and passing `evidence/golden-tests.md`
before delivery. When false, require a single recorded
`golden_tests: skipped_by_input` outcome with its reason; do not plan golden
artifacts or invoke the golden-test agent.

Widget tests remain mandatory: `/new-component` requires
`evidence/widget-tests.md`; `/new-view` additionally requires
`evidence/view-widget-tests.md`.

## Shared Figma UI Fidelity Gate

For `/new-view` and `/new-feature` with `inputs.figma_scope=view`, require a
completed `visual_manifest` and `layout_manifest` before audit and delivery.
The layout reconciliation must cover every visible structural node and leaf,
with no unresolved ids and verified parent-child order. It records bounds,
layout, clipping, four corner radii and border width.

Require `evidence/figma-fidelity-report.json` validated against
`docs/templates/schemas/figma-fidelity-report.schema.json`. Its exact
invariants are literal text, hierarchy/order, asset identity, typography and
declared shape values. Its measured tolerances are at most `1 dp` geometry,
`2%` global pixel difference and `4%` regional pixel difference. Capture and
comparison failures block with `FIGMA_FIDELITY_COMPARISON_UNAVAILABLE`; an
incomplete manifest blocks with `FIGMA_LAYOUT_MANIFEST_INCOMPLETE`; a measured
failure blocks with `FIGMA_FIDELITY_TOLERANCE_EXCEEDED`.

`figma_scope=component_inventory` is intentionally exempt from the screen
layout and pixel-comparison gate, while retaining Figma preflight and asset
provenance rules that apply to its planned components.

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

In `minimal`, do not require a standard-only report merely because its path is
authorized. Require its compact controller-owned phase result instead.

If validation fails, block with `SPEC_AGENT_PERMISSION_MISSING`.

## Figma MCP Validation

For `/new-component`, `/new-view` and `/new-feature` with `figma_url`:

1. `external_access.figma_mcp.required=true`.
2. `figma-analyzer` performs the preflight by default. For `/new-feature` only,
   when `execution_capabilities.subagent_delegation=unavailable`,
   `feature-builder` may execute the same role contract if its packet
   permission explicitly grants `figma_mcp`. It records status `verified`
   before design analysis continues.
3. If it is not verified, block with `FIGMA_MCP_ACCESS_NOT_VERIFIED`.
4. If MCP lacks permissions for the file, node or assets, block with
   `FIGMA_MCP_PERMISSION_DENIED`.
5. For every visible icon, image, illustration, logo, or image-fill source,
   require a matching `assets[]` entry with `figma_export.source=figma_mcp`, a
   downloaded archive file under `source-assets/figma/`, and a matching
   SHA-256. An image URL, screenshot, local replacement, or visually similar
   icon cannot satisfy this check. Otherwise block with
   `FIGMA_ASSET_DOWNLOAD_UNAVAILABLE`.
6. For every visible text node in `/new-view`, require Figma source metadata
   and `font_resolution=exact_project_font`. A close family or weight must
   block with `FIGMA_TYPOGRAPHY_UNAVAILABLE`, not silently fall back.

## Portable Role Execution

For `/new-feature`, validate `execution_capabilities` before any specialized
phase. `fallback_policy` must be `delegate_or_controller_executes`.

- If native delegation is available, a specialist agent may execute its phase.
- If it is unavailable, `feature-builder` is the execution owner and must
  execute the named specialist role contract itself when its packet permissions
  cover the files, commands, evidence, target, and external tools needed.
- Mandatory unit, widget, and integration phases can never be `skipped` due to
  unavailable delegation. Missing permissions or a missing runtime capability
  are `blocked_input: PLATFORM_CONTROLLER_ROLE_CAPABILITY_MISSING`, not
  success.

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
