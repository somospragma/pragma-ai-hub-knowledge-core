---
id: new-view
version: 2.2.0
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

## Telemetry — Workflow metadata

| Field | Value |
|---|---|
| `workflow-id` | `new-view` |
| `user-story-id` | Value of the required `hu_id` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `phase-0-preflight-gates`, `phase-1-spec-design-analysis`, `phase-2-planning`, `phase-3-ds-code-generation`, `phase-4-view-code-generation`, `phase-5-1-ds-widget-tests`, `phase-5-2-ds-golden-tests`, `phase-6-ds-widgetbook`, `phase-7-1-view-widget-tests`, `phase-7-2-view-golden-tests`, `phase-8-view-widgetbook`, `phase-9-delivery` |

## Workflow Execution Contract

**This document is not reference material — you are executing it.** Every fenced `bash` block is a real shell tool call your agent MUST issue. Do not paraphrase, summarize, describe, or narrate them; emit the exact command via your shell tool.

The following rules bind every phase in this workflow and are enforced by the Response Contract embedded at the top of each phase:

1. **Telemetry integrity.** Every executed step (`phase-0-preflight-gates` and every phase) emits exactly one `--status started` before its work and exactly one terminal status on completion — `--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when the human rejects and the phase must be regenerated — via `pragma-ai workflow report`. Skipping any of these is a workflow violation.
2. **Step-id and phase-name integrity.** The `--step-id` and `--workflow-id` values are the ONLY valid identifiers. Copy them **verbatim** from the `Step IDs` table above — never invent, translate, abbreviate, paraphrase, pluralize, or re-case them. `--workflow-id` MUST be exactly `new-view`. The CLI silently rejects unknown step-ids. This also governs every phase name you narrate, header, or put in an approval prompt: it MUST match, verbatim, a `### PHASE` header (or its embedded `#### Step`) tied to one of the `Step IDs` above. Never execute, narrate, or present a phase that is not in that table — including a phase from a previous version of this document, from memory, or from a different workflow. If a phase you are about to run does not appear there, stop and re-read the `Step IDs` table before continuing.
3. **Human approval per phase.** After every `finished`, present the approval prompt block (Aprobado / Ediciones / Rechazado) VERBATIM as the last thing in your response and yield. Silence is not approval. Three phases embed aggregate approval gates: `phase-2-planning` (initial spec plan), `phase-3-ds-code-generation` (DS layer), `phase-4-view-code-generation` (app view layer). See *Human approval gate* for the aggregate rejection replay protocol.
4. **Gap report per file-producing phase.** After the human approves a phase that produced files (`--output-file`), run the two-phase gap report against the same step-id. `phase-0-preflight-gates` produces no files; do NOT run its gap report.
5. **Conditional phases.** Inside `phase-2-planning`, the Contracts Minimum step only runs when `CONTRACTS_POLICY=generate`. `phase-5-2-ds-golden-tests` and `phase-7-2-view-golden-tests` require `golden_tests=true`. When a guard is false, skip that portion/phase entirely — do not emit `started` or `finished` for a fully-skipped phase. Record the skip in `context.json`, `spec.yaml` and `PIPELINE_LOG_PATH`.
6. **cwd assumption.** Commands assume the shell's cwd is the project root. `--project-dir` is only needed when running from elsewhere.

Violating any of these rules is a Response Contract Violation (see the section of that name at the end of this document).

## Instructions to the executing agent

You are the workflow controller. Before every phase:

1. **Load and read** this document into context (if not already loaded) and re-scan the phase's Response Contract at the top of that phase. The Response Contract binds the shape of your response. Before naming or running any phase, confirm it is listed verbatim in the `Step IDs` table above — do not rely on memory of a previous version of this workflow, a similar workflow, or general conventions.
2. **Do not skip** any Response Contract step. Doing so is a workflow violation.
3. **Do not begin** the phase's work until you have emitted its `--status started` command via your shell tool and it has returned.
4. **Do not begin** the next phase until the human has explicitly answered the approval prompt with **1** (Aprobado), **2** (Ediciones), or **3** (Rechazado).
5. **End your response** with the approval prompt block, verbatim, and yield. Do not add prose after it. Do not continue past it in the same response.

Both `Human approval gate` and `Response Contract Violations` at the end of this document apply to every phase and are non-negotiable.

---

## Setup — Mint the workflow instance

> ⚡ **MANDATORY** — Always run this at the start, before any step.

### Input preflight (mandatory)

Before any other action, build a temporary YAML or JSON object containing only
the values explicitly supplied in this invocation and assign its path to
`WORKFLOW_INPUTS_FILE`. Do **not** read session state or
`output/.active-user-story` to complete a missing input. Run the preflight
command below. If it exits with `blocked_input`, return its missing-input list
to the user and stop; do not run `workflow create`. This local check must not
use an MCP server, subagent or AI-assisted analysis. It is the first executable
workflow action: do not inspect the workspace, plan, emit telemetry or invoke
any other tool before it succeeds. If `hu_id` is absent or blank, return only
the `blocked_input` result. Never generate, guess, infer, autocomplete, derive
or offer an example or alternative `hu_id`.

```bash
# Validate all required invocation inputs before creating an instance.
ruby docs/scripts/validate_workflow_inputs.rb \
  --workflow-id new-view \
  --inputs-file "$WORKFLOW_INPUTS_FILE"

# The preflight succeeded; use the explicitly supplied hu_id for telemetry.
USER_STORY_ID="$hu_id"

# Persist only after a valid invocation has started.
echo "$USER_STORY_ID" > output/.active-user-story

# Mint the instance.
INSTANCE_ID=$(pragma-ai workflow create \
  --workflow-id new-view \
  --user-story-id "$USER_STORY_ID")
```

---

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
`context.json` to `approved_for_execution` and unlock PHASE 3. Approval is
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

## Preflight Gates (required)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this gate MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Perform, in order, the Canonical Configuration, Topology, Spec Packet Ownership, Ownership of the Repo App, Architecture, Contracts Policy, and Figma MCP checks described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success or `--status failed` on the first unrecoverable blocker) via a real shell tool call.
> 4. This gate produces no output files — do NOT run the gap report.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 1 until the user replies.
>
> ```
> He completado Preflight Gates. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-0-preflight-gates \
  --status started
```

### Check 1 — Canonical Configuration

Before any packet, log, Figma request, or code generation:

1. Resolve `PROJECT_ROOT` from optional `project_root`, then the IDE workspace
   root, then the current repository root.
2. Inspect only `<candidate>/.sopp/config/` for the three final configuration
   files.
3. Require one valid configuration triplet whose
   `project.repository_local_path` matches the resolved app repository.
4. Ignore runtime-looking files under any tool-specific KB folder; only
   `<APP_REPO_ROOT>/.sopp/` may contain project runtime state.
5. If the triplet is missing, partial, invalid, or ambiguous, stop with
   `blocked_input`. Do not create a bootstrap proposal or write any YAML.

### Check 2 — Topology

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate roots (`PROJECT_ROOT`, `APP_TARGET_ID` and
   `DESIGN_SYSTEM_TARGET_ID` if DS components will be created).
3. In targets `location_strategy=melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

If any validation fails, stop with `blocked_input`.

### Check 3 — Spec Packet Ownership

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

### Check 4 — Ownership of the Repo App

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

### Check 5 — Architecture

1. If `architecture_contract.generation_policies.view_generation.require_architecture_contract=true`, require
   `ARCHITECTURE_CONTRACT_PATH`.
2. `architecture.md` is optional visual support.

If the required `ARCHITECTURE_CONTRACT_PATH` is missing, stop with `blocked_input`.

### Check 6 — Policy of Contracts

1. `optional`: continue.
2. `generate`: generate contracts minimum in
   `spec.yaml.contracts.minimal_domain_data` before PHASE 4.
3. `required`: block if referenced domain/data contracts are missing.

If it fails a check, stop with `blocked_input`.

### Check 7 — Figma MCP

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
persist `evidence/figma-mcp-preflight.md` and stop with `blocked_input`.

> ⚡ **MANDATORY (conditional)** — If any check fails (persisting `evidence/figma-mcp-preflight.md` when the failure is in Check 7) and the gate ends with `blocked_input` or `PLATFORM_CONTROLLER_ROLE_CAPABILITY_MISSING`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-0-preflight-gates \
  --status failed
```

> ⚡ **MANDATORY (success path)** — Report `finished` once all seven checks pass (this gate produces no artifact on the success path — the Figma MCP diagnostic file is only written on failure, and the failure branch already reported `failed`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-0-preflight-gates \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, continue to PHASE 1. *(This step produces no output files — no gap report required.)*

## User Inputs

`hu_id` is **required**: it identifies the user story this view belongs to and
is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied, the
workflow refuses to start.

```text
@ds-orchestrator /new-view
hu_id: US-12345                                             [Required]
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

### PHASE 1 — Spec Packet + Analysis of Screen (`standard`)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below: create the spec packet, then run the Figma screen analysis, including downloading every visible Figma source asset.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 2 until the user replies.
>
> ```
> He completado PHASE 1 — Spec Packet + Analysis of Screen. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-1-spec-design-analysis \
  --status started
```

#### Step 1 — Mobile Spec Packet

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

#### Step 2 — Analysis of Screen

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

> ⚡ **MANDATORY (success path)** — Report `finished` with all packet artifacts, the analysis evidence, and every source asset archived under `source-assets/figma/`. Expand `${FIGMA_ASSET_FLAGS[@]}` from the paths recorded in `spec.yaml.assets[].archive_path`:

```bash
# Build --output-file flags for every archived Figma source asset
FIGMA_ASSET_FLAGS=()
while IFS= read -r asset; do
  FIGMA_ASSET_FLAGS+=(--output-file "$asset")
done < <(yq -r '.assets[].archive_path' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-1-spec-design-analysis \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/review.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/validation-report.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/figma-analysis.md" \
  "${FIGMA_ASSET_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.

---

### PHASE 2 — Planning

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below: Extended Inventory + DAG, Architecture Technical, Contracts Minimum (only when `CONTRACTS_POLICY=generate`), and Validation + Human Review.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. This is the aggregate planning gate: PHASE 3 may only begin after explicit approval AND `checkpoints.initial_spec.status=approved` in `context.json`.
>
> ```
> He completado PHASE 2 — Planning. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-planning \
  --status started
```

#### Step 1 — Extended Inventory + DAG

**Agent**: `@component-planner`
**Prompt**: `atomic-inventory.prompt.md`

Update in `spec.yaml` only `canonical_spec`, `inventory`, `dag`,
`artifact_plan.planned[group=ds_components]` and `artifact_plan.planned[group=app_view]`.
The DS vs App separation must remain explicit in `inventory` and `artifact_plan`.

#### Step 2 — Architecture Technical

**Agent**: `@component-architect`

Update in `spec.yaml` only `technical_plan`, `artifact_plan`,
`contracts.text_overflow`, `contracts.asset_rendering`,
`contracts.icon_mapping`, `contracts.typography_mapping`,
`contracts.screen_chrome`, `visual_manifest`, `success_criteria`, `handoffs`
and `checkpoints`.

#### Step 3 — Contracts Minimum (only `CONTRACTS_POLICY=generate`)

**Guard check.** Only run this step when `CONTRACTS_POLICY=generate`. When the
policy is `optional` or `required`, skip it entirely — do not persist a
`contracts.minimal_domain_data` block for it.

**Agent**: `@component-architect`

Update in `spec.yaml` only `contracts.minimal_domain_data`.

#### Step 4 — Validation + Human Review

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

> ⚡ **MANDATORY (conditional)** — If the plan gate cannot be validated (schema/business failure that cannot be repaired in-review):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-planning \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` once validation passes and the human review is presented (approval itself happens at this phase's own gate). This phase updates `spec.yaml` in place — declare it as the output file so the gap report can diff this phase's contribution:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-planning \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** This is the **domain aggregate approval gate** for the initial spec plan (Inventory + DAG, Architecture Technical, Contracts Minimum, Validation + Human Review). If the human requests changes to `inventory`, `dag`, `technical_plan`, `contracts.minimal_domain_data`, or `artifact_plan`, apply the changes in place within this same phase, report `re_started` → `finished` again, re-run its gap report, and re-present this gate. If the requested changes belong to `design_source`, `literal_texts`, `assets`, `view_states`, `navigation`, `visual_manifest` or `layout_manifest`, the flow must return to PHASE 1 instead: report `re_started` on PHASE 1, apply changes, report `finished` again for PHASE 1, re-run its gap report, and re-enter this gate (`re_started` → `finished` again on `phase-2-planning`). Only when `context.json.status=approved_for_execution` and `checkpoints.initial_spec.status=approved` may PHASE 3 begin. Once approved, run this step's **gap report** and then continue to PHASE 3.

---

### PHASE 3 — DS Code Generation

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below: Codegen of Components DS (atoms → molecules → organisms), Audit of Components DS, and the DS-layer human checkpoint.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. This is the DS-layer aggregate gate: PHASE 4 may only begin after explicit approval AND `checkpoints.ds_layer.status=approved` in `context.json`.
>
> ```
> He completado PHASE 3 — DS Code Generation. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-ds-code-generation \
  --status started
```

#### Step 1 — Codegen of Components DS

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

#### Step 2 — Audit of Components DS

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

#### Step 3 — Checkpoint Human of Layer DS

**Agent**: `@ds-orchestrator`

Present a compact review in Spanish before generating the app view:

1. DS components created/modified
2. audit result DS
3. covered visual criteria
4. risks or fallbacks pending

Wait for explicit approval. If the human requests adjustments, return to
Step 1 or Step 2 of this same phase as applicable. Do not continue to PHASE 4
until `context.json.checkpoints.ds_layer.status=approved` and
`context.json.status=approved_for_execution`.

> ⚡ **MANDATORY (conditional)** — If the audit loop exceeds `pipeline.max_audit_retries` without passing:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-ds-code-generation \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with one `--output-file` per `.dart` file declared in `artifact_plan.planned[group=ds_components]` plus the DS audit evidence. Paths must be relative to `--project-dir` (project root). Expand the array from the spec:

```bash
# Build --output-file flags from the artifact plan
DS_FILE_FLAGS=()
while IFS= read -r f; do
  DS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_components") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-ds-code-generation \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/ds-component-audit.md" \
  "${DS_FILE_FLAGS[@]}"
```

> **Stop here.** This is the **domain aggregate approval gate** for the DS layer (Codegen of Components DS and Audit of Components DS). On rejection of the DS layer, apply the requested changes in place within this same phase (regenerate the affected components and/or re-audit), report `re_started` → `finished` again, and re-present this gate. Only when `context.json.checkpoints.ds_layer.status=approved` and `context.json.status=approved_for_execution` may PHASE 4 begin. Once approved, run this step's **gap report** and then continue to PHASE 4.

---

### PHASE 4 — View Code Generation

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below: Codegen of View App, Audit of App View (including writing `evidence/figma-fidelity-report.json`), and the app-view human checkpoint (presenting the fidelity report to the user).
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. This is the app-view aggregate gate: PHASE 5.1 may only begin after explicit approval AND `checkpoints.app_view_layer.status=approved` in `context.json`.
>
> ```
> He completado PHASE 4 — View Code Generation. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-view-code-generation \
  --status started
```

#### Step 1 — Codegen of View App

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

#### Step 2 — Audit of App View

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

#### Step 3 — Human Checkpoint of App View

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

> ⚡ **MANDATORY (conditional)** — If the audit loop exceeds `pipeline.max_audit_retries` without passing, an audit blocker (missing Figma archive, checksum mismatch, missing exact icon, unrecreated crop, unresolved typography, incorrect bottom-navigation ownership, `layout_manifest` geometry outside `1 dp`, incorrect corner radii/border width, or fidelity report over `2%` global / `4%` regional pixel difference) cannot be resolved, or capture/comparison cannot be completed (`FIGMA_FIDELITY_COMPARISON_UNAVAILABLE`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-view-code-generation \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with one `--output-file` per file declared in `artifact_plan.planned[group=app_view]`, plus the app-view audit evidence and the Figma fidelity report. Expand the array from the spec:

```bash
APP_VIEW_FLAGS=()
while IFS= read -r f; do
  APP_VIEW_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="app_view") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-view-code-generation \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/app-view-audit.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/figma-fidelity-report.json" \
  "${APP_VIEW_FLAGS[@]}"
```

> **Stop here.** This is the **domain aggregate approval gate** for the app view layer (Codegen of View App and Audit of App View). On rejection of the app view layer, apply the requested changes in place within this same phase (regenerate the view and/or re-audit), report `re_started` → `finished` again, and re-present this gate. Only when `context.json.checkpoints.app_view_layer.status=approved` and `context.json.status=approved_for_execution` may PHASE 5.1 begin. Once approved, run this step's **gap report** and then continue to PHASE 5.1.

---

### PHASE 5.1 — Tests of Components DS

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 5.2 / 6 until the user replies.
>
> ```
> He completado PHASE 5.1 — Tests of Components DS. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-5-1-ds-widget-tests \
  --status started
```

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

> ⚡ **MANDATORY (conditional)** — Widget tests are required for delivery. If they cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-5-1-ds-widget-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed without a passing `evidence/widget-tests.md`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated test files and the widget-tests evidence. Expand the file array from `artifact_plan.planned[group=ds_widget_tests]`:

```bash
DS_TEST_FLAGS=()
while IFS= read -r f; do
  DS_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_widget_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-5-1-ds-widget-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/widget-tests.md" \
  "${DS_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 5.2 (only when `golden_tests=true`) or directly to PHASE 6.

---

### PHASE 5.2 — Golden of Components DS (conditional)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. **Guard check.** Only proceed with this phase when `golden_tests=true`. If `false`, skip the phase entirely — do not emit `started` or `finished`. Record `skipped_by_input` in `context.json`, `spec.yaml` and `PIPELINE_LOG_PATH`.
> 2. Emit the `--status started` command below as a real shell tool call.
> 3. Do the work described under *Instructions* below.
> 4. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 5. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 6. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 6 until the user replies.
>
> ```
> He completado PHASE 5.2 — Golden of Components DS. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 6 without a user reply is a workflow violation.

> ⚡ **MANDATORY only when `golden_tests=true`.** When `golden_tests=false`, skip this phase entirely — do not emit `started`/`finished` for it. The workflow's own `skipped_by_input` record in `context.json`, `spec.yaml` and `PIPELINE_LOG_PATH` covers the skip.

> ⚡ **EXECUTE NOW (when executed)** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-5-2-ds-golden-tests \
  --status started
```

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

> ⚡ **MANDATORY (conditional)** — If DS golden tests were requested but cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-5-2-ds-golden-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed with a failing golden outcome when `golden_tests=true`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated DS golden files and the golden-tests evidence:

```bash
DS_GOLDEN_FLAGS=()
while IFS= read -r f; do
  DS_GOLDEN_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_golden_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-5-2-ds-golden-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/golden-tests.md" \
  "${DS_GOLDEN_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 6.

---

### PHASE 6 — Widgetbook of Components DS

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below — start with the Widgetbook cold-init preflight if the host project is uninitialized.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below (use cases + any bootstrap files).
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 7.1 until the user replies.
>
> ```
> He completado PHASE 6 — Widgetbook of Components DS. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-6-ds-widgetbook \
  --status started
```

**Agent**: `@widgetbook-developer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGETBOOK`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_widgetbook
preflight:
  - ensure_widgetbook_initialized  # Step -1 of flutter-ds-widgetbook
read_sections:
  - artifact_plan.planned[group=ds_components]
  - technical_plan
  - literal_texts
  - contracts.text_overflow
  - success_criteria
```

> **Preflight bootstrap.** Before generating any use case, `@widgetbook-developer`
> runs Step -1 of the `flutter-ds-widgetbook` skill. When the Widgetbook host
> project is not initialized, it executes the cold-init sequence from
> `references/setup.md` (single/multi-repo) or `references/monorepo.md`
> (`monorepo_melos`) and appends every bootstrapped file to the phase's
> `--output-file` set. Typical bootstrap files (paths depend on repo mode; see
> the "Bootstrap output files" section in each reference):
>
> Widgetbook is a nested Flutter project created with
> `flutter create widgetbook --empty --platforms=android,ios,web` from the app
> root, so files live under `<app-root>/widgetbook/` (single/multi-repo) or
> `<host-package-path>/widgetbook/` in a monorepo:
>
> - `widgetbook/pubspec.yaml` (monorepo: `<host-package-path>/widgetbook/pubspec.yaml`)
> - `widgetbook/lib/main.dart`
> - `widgetbook/lib/main.directories.g.dart`
> - `widgetbook/lib/ui_system/.gitkeep`
> - `widgetbook/lib/features/.gitkeep`
> - `widgetbook/lib/shared/.gitkeep`
> - Root `pubspec.yaml` and/or `melos.yaml` only when a monorepo workspace list was edited.
>
> If any initialization command fails, report `phase-6-ds-widgetbook` as
> `failed` with the captured error and stop the workflow — do not fall back
> to writing use cases against an uninitialized project.
> The DS phase owns the first Widgetbook bootstrap; PHASE 8 must find the
> project already initialized and only add screen use cases.

> ⚡ **MANDATORY (success path)** — Report `finished` with the DS Widgetbook use-case files **plus** any bootstrap files produced by Step -1. Expand the use-case array from `artifact_plan.planned[group=ds_widgetbook]` and, when Step -1 bootstrapped Widgetbook, append the bootstrap files reported by `@widgetbook-developer`:

```bash
DS_WIDGETBOOK_FLAGS=()
while IFS= read -r f; do
  DS_WIDGETBOOK_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_widgetbook") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

# Optional: append bootstrap files when Step -1 initialized Widgetbook.
# The agent lists them in evidence/widgetbook.md under a "bootstrap_files" block.
if [ -f "${SPEC_PACKET_PATH}/evidence/widgetbook.bootstrap-files.txt" ]; then
  while IFS= read -r f; do
    DS_WIDGETBOOK_FLAGS+=(--output-file "$f")
  done < "${SPEC_PACKET_PATH}/evidence/widgetbook.bootstrap-files.txt"
fi

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-6-ds-widgetbook \
  --status finished \
  "${DS_WIDGETBOOK_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 7.1.

---

### PHASE 7.1 — Tests of View

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 7.2 / 8 until the user replies.
>
> ```
> He completado PHASE 7.1 — Tests of View. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-7-1-view-widget-tests \
  --status started
```

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

> ⚡ **MANDATORY (conditional)** — View widget tests are required for delivery. If they cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-7-1-view-widget-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed without a passing `evidence/view-widget-tests.md`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated view test files and the view-widget-tests evidence. Expand the file array from `artifact_plan.planned[group=view_widget_tests]`:

```bash
VIEW_TEST_FLAGS=()
while IFS= read -r f; do
  VIEW_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="view_widget_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-7-1-view-widget-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/view-widget-tests.md" \
  "${VIEW_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 7.2 (only when `golden_tests=true`) or directly to PHASE 8.

---

### PHASE 7.2 — Golden Tests of Complete View (conditional)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. **Guard check.** Only proceed with this phase when `golden_tests=true`. If `false`, skip the phase entirely — do not emit `started` or `finished`. The `skipped_by_input` outcome recorded in PHASE 5.2 already represents this decision.
> 2. Emit the `--status started` command below as a real shell tool call.
> 3. Do the work described under *Instructions* below.
> 4. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 5. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 6. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 8 until the user replies.
>
> ```
> He completado PHASE 7.2 — Golden Tests of Complete View. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 6 without a user reply is a workflow violation.

> ⚡ **MANDATORY only when `golden_tests=true`.** When `golden_tests=false`, skip this phase entirely — do not emit `started`/`finished` for it. The single `golden_tests: skipped_by_input` outcome recorded in PHASE 5.2 already represents this decision.

> ⚡ **EXECUTE NOW (when executed)** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-7-2-view-golden-tests \
  --status started
```

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
`golden_tests: skipped_by_input` outcome recorded in PHASE 5.2. Do not invoke
the agent or create view golden artifacts.

Minimum coverage:
1. `loading`
2. `empty`
3. `error`
4. `populated`
5. `light/dark`
6. compact viewport if overflow risk exists

> ⚡ **MANDATORY (conditional)** — If view golden tests were requested but cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-7-2-view-golden-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed with a failing view-golden outcome when `golden_tests=true`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated view golden files and the view-golden-tests evidence:

```bash
VIEW_GOLDEN_FLAGS=()
while IFS= read -r f; do
  VIEW_GOLDEN_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="view_golden_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-7-2-view-golden-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/view-golden-tests.md" \
  "${VIEW_GOLDEN_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 8.

---

### PHASE 8 — Widgetbook of Screen App

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 9 until the user replies.
>
> ```
> He completado PHASE 8 — Widgetbook of Screen App. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-8-view-widgetbook \
  --status started
```

**Agent**: `@widgetbook-developer`
**Prompt**: `test-generation.prompt.md` (`MODE=APP_WIDGETBOOK_SCREENS`, `WIDGETBOOK_SCOPE=APP_SCREENS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: app_widgetbook
preflight:
  - ensure_widgetbook_initialized  # Step -1 of flutter-ds-widgetbook
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

> **Preflight bootstrap.** `@widgetbook-developer` re-runs Step -1 of the
> `flutter-ds-widgetbook` skill as a defensive check. In the normal flow the
> DS phase (PHASE 6) already initialized Widgetbook, so this check must be a
> no-op that only verifies the four signals. When PHASE 8 is entered in
> isolation (rerun, `re_started`, or a workflow that skipped PHASE 6), the
> bootstrap runs here and appends the bootstrap files reported by the agent to
> the phase's `--output-file` set. A failing initialization reports
> `phase-8-view-widgetbook` as `failed`; do not fall back to writing screen
> use cases against an uninitialized project.

> ⚡ **MANDATORY (success path)** — Report `finished` with the app-screen Widgetbook use-case files **plus** any bootstrap files produced by Step -1 (usually empty here because PHASE 6 already initialized Widgetbook). Expand the file array from `artifact_plan.planned[group=app_widgetbook]`:

```bash
APP_WIDGETBOOK_FLAGS=()
while IFS= read -r f; do
  APP_WIDGETBOOK_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="app_widgetbook") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

# Optional: append bootstrap files when Step -1 initialized Widgetbook in
# this phase (normally empty because PHASE 6 already handled it).
if [ -f "${SPEC_PACKET_PATH}/evidence/widgetbook.bootstrap-files.txt" ]; then
  while IFS= read -r f; do
    APP_WIDGETBOOK_FLAGS+=(--output-file "$f")
  done < "${SPEC_PACKET_PATH}/evidence/widgetbook.bootstrap-files.txt"
fi

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-8-view-widgetbook \
  --status finished \
  "${APP_WIDGETBOOK_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 9.

---

### PHASE 9 — Delivery

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Once approved, the workflow is complete.
>
> ```
> He completado PHASE 9 — Delivery. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-9-delivery \
  --status started
```

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

> ⚡ **MANDATORY (conditional)** — If any delivery precondition is not met (missing/failing DS or view widget tests, inconsistent golden outcome, incomplete visual/layout reconciliation, or failing fidelity report):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-9-delivery \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the delivery report:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-9-delivery \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/delivery-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** — the workflow is complete.

---

## Response Contract Violations

The following are workflow violations. If your response for a phase contains any of them, you have failed the workflow contract for that phase:

- Omitting the `--status started` tool call before starting the phase's work.
- Omitting the terminal status tool call (`--status finished`, `--status failed`, or `--status re_started`) at the end of the phase.
- Emitting `--status finished` without every declared `--output-file` flag (spec, evidence, generated `.dart` files, tests, Widgetbook use cases + bootstrap files, fidelity report).
- Using a `--step-id` or `--workflow-id` value that does not appear in the `Step IDs` table above, character-for-character.
- Narrating, presenting, or executing a phase (in a header, approval prompt, or telemetry call) whose name does not correspond verbatim to an entry in the `Step IDs` table above — including a phase that existed in a previous version of this document.
- Ending a phase response without the approval prompt block, or adding prose after it.
- Starting the next phase's work before the user has explicitly answered the approval prompt.
- Running the gap report on `phase-0-preflight-gates` (it produces no files).
- Emitting `started` or `finished` for the Contracts Minimum step of `phase-2-planning` when `CONTRACTS_POLICY` is `optional` or `required`, or for `phase-5-2-ds-golden-tests` / `phase-7-2-view-golden-tests` when `golden_tests=false`.
- Starting PHASE 3 before `checkpoints.initial_spec.status=approved`, PHASE 4 before `checkpoints.ds_layer.status=approved`, or PHASE 5.1 before `checkpoints.app_view_layer.status=approved`.

Report any violation immediately by stopping the workflow and asking the user how to proceed. Do not try to "correct" a missed emission after the fact; re-run the phase.

---

## Human approval gate

> ⚡ **MANDATORY** — Always runs after each `finished`. It cannot be skipped, and approval cannot be inferred from silence.

At the end of each step, present the result and request **explicit** approval:

```
Agent: I've completed [step name]. Do you approve the result?
  1. ✅ Approved — continue
  2. ✏️ Edits — tell me what to change
  3. ❌ Rejected — redo from scratch
```

- **If approved:** If the step produces files, proceed to the gap report and then to the next step. If it produces no files, proceed directly to the next step.
- **If edits are requested:** First **verify the baseline is valid** before editing (see *Baseline integrity* below). Only when the baseline is confirmed valid, apply the changes in place on the artifact, keep `finished` (the baseline is already captured), and re-present for approval. The gap report will then capture those edits as the diff against the agent's first draft. If the baseline is missing, was captured late, or was reconstructed in a later session, do **not** edit in place: treat it as a rejection (regenerate to re-anchor a clean baseline) so the diff stays honest.
- **If rejected:** Report `re_started`, regenerate the artifact from scratch, report `finished` again (recapturing the baseline), and restart the gate. Repeat until approved.

> **Baseline integrity (mandatory).** A step's baseline is valid only when its `finished` was persisted in the same session/turn that produced the first draft, before any edit touched the artifact. Before applying edits, the controller MUST verify with `pragma-ai workflow status "$INSTANCE_ID"` that the step reports a persisted `finished`; if the CLI did not return success for that `finished`, the phase is not complete and the approval gate must not be presented. A baseline reconstructed in a later session, or pulled at gap-report time over an already-edited artifact, is **invalid**: a `No changes detected` result with a same-time "Baseline pulled" while edits were in fact requested is the signature of an invalid baseline. In that case do not `--submit` a false `no changes`; report `re_started`, regenerate to re-anchor a clean baseline, and restart the gate.

> **Three domain aggregate approval gates**, embedded within their own merged phase:
> - **`phase-2-planning` (initial spec plan)** — approves the aggregate of the Inventory + DAG, Architecture Technical, Contracts Minimum, and Validation + Human Review steps within PHASE 2. On rejection of `inventory`, `dag`, `technical_plan`, `contracts.minimal_domain_data`, or `artifact_plan`, apply the changes in place within PHASE 2 (`re_started` → `finished` → gap report) and re-present this gate. On rejection of `design_source`, `literal_texts`, `assets`, `view_states`, `navigation`, `visual_manifest` or `layout_manifest`, return to PHASE 1 instead (`re_started` → `finished` → gap report) and then re-report `re_started` → `finished` on `phase-2-planning`. Only when `checkpoints.initial_spec.status=approved` and `context.json.status=approved_for_execution` may PHASE 3 begin.
> - **`phase-3-ds-code-generation` (DS layer checkpoint)** — approves the aggregate of the Codegen of Components DS and Audit of Components DS steps within PHASE 3. Rejection regenerates and/or re-audits in place within PHASE 3, then reports `re_started` → `finished` again before re-entering this gate. Only when `checkpoints.ds_layer.status=approved` and `context.json.status=approved_for_execution` may PHASE 4 begin.
> - **`phase-4-view-code-generation` (app view layer checkpoint)** — approves the aggregate of the Codegen of View App and Audit of App View steps within PHASE 4. Rejection regenerates and/or re-audits in place within PHASE 4, then reports `re_started` → `finished` again before re-entering this gate. Only when `checkpoints.app_view_layer.status=approved` and `context.json.status=approved_for_execution` may PHASE 5.1 begin.

> Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

> ⚡ **MANDATORY** — On rejection, example using `phase-4-view-code-generation`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-view-code-generation \
  --status re_started

# 2. ... regenerate the artifacts ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
APP_VIEW_FLAGS=()
while IFS= read -r f; do
  APP_VIEW_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="app_view") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-view-code-generation \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/app-view-audit.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/figma-fidelity-report.json" \
  "${APP_VIEW_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow:
> `phase-1-spec-design-analysis`, `phase-2-planning`, `phase-3-ds-code-generation`, `phase-4-view-code-generation`, `phase-5-1-ds-widget-tests`, `phase-5-2-ds-golden-tests` (only when executed), `phase-6-ds-widgetbook`, `phase-7-1-view-widget-tests`, `phase-7-2-view-golden-tests` (only when executed), `phase-8-view-widgetbook`, `phase-9-delivery`.
> `phase-0-preflight-gates` produces no files and does NOT run a gap report.

> Run this immediately after the corresponding step's approval gate passes — not batched at the end of the workflow.

**Phase A — Generate the gap report:**
```bash
pragma-ai workflow gap-report \
  --instance-id "$INSTANCE_ID" \
  --step-id <step-id>
```

**Phase B — Submit the gap report interpretation:**
```bash
pragma-ai workflow gap-report \
  --instance-id "$INSTANCE_ID" \
  --step-id <step-id> \
  --submit \
  --report-id <report-id> \
  --summary "<summary of the detected gap; use 'no edits after approval' only when the human approved without requesting edits — never report 'no changes' when edits were requested (that signals an invalid baseline; regenerate instead of submitting)>"
```

---

## Progress reporting (instance-level)

Use at any point to check overall state:

```bash
pragma-ai workflow list --user-story-id "$USER_STORY_ID"
pragma-ai workflow status "$INSTANCE_ID"
```

---

## Summary of commands for this workflow

| Command | When |
|---|---|
| `pragma-ai workflow create --workflow-id new-view --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each executed step begins (`phase-0-preflight-gates` + PHASE 1–9; the Contracts Minimum step inside `phase-2-planning` only if `CONTRACTS_POLICY=generate`; `phase-5-2-ds-golden-tests` and `phase-7-2-view-golden-tests` only if `golden_tests=true`) |
| `pragma-ai workflow report ... --step-id <step> --status finished` | On completion of `phase-0-preflight-gates` (produces no output files) |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of file-producing phases: `phase-1-spec-design-analysis`, `phase-2-planning`, `phase-3-ds-code-generation`, `phase-4-view-code-generation`, `phase-5-1-ds-widget-tests`, `phase-5-2-ds-golden-tests` (when executed), `phase-6-ds-widgetbook`, `phase-7-1-view-widget-tests`, `phase-7-2-view-golden-tests` (when executed), `phase-8-view-widgetbook`, `phase-9-delivery` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When `phase-0-preflight-gates` blocks with `blocked_input`, `phase-2-planning` cannot validate, an audit exhausts `pipeline.max_audit_retries` or hits an unresolvable blocker (`phase-3-ds-code-generation`, `phase-4-view-code-generation`), fidelity capture is unavailable (`phase-4-view-code-generation`), tests can't pass (`phase-5-1-*`, `phase-5-2-*`, `phase-7-1-*`, `phase-7-2-*`), or delivery preconditions fail (`phase-9-delivery`) — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably at the `phase-2-planning`, `phase-3-ds-code-generation`, or `phase-4-view-code-generation` aggregate rejections) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding file-producing step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
