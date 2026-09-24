---
id: new-component
version: 2.2.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: ds-orchestrator
input_contract: ../docs/templates/spec-packets/new-component.overlay.yaml
invocation_mode: explicit_agent
description: >
  Deterministic workflow to create a new Design System component from Figma. Use when the user requests a reusable atom, molecule, or organism with spec packet validation, Figma MCP preflight, human review, code generation, tests, Widgetbook, and audit gates.
---
# Workflow: New Component from Figma

## Telemetry — Workflow metadata

| Field | Value |
|---|---|
| `workflow-id` | `new-component` |
| `user-story-id` | Value of the required `hu_id` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `phase-0-preflight-gates`, `phase-1-spec-design-analysis`, `phase-2-planning`, `phase-3-code-generation`, `phase-4-1-widget-tests-ds`, `phase-4-2-golden-tests-ds`, `phase-5-widgetbook-ds`, `phase-6-delivery` |

## Workflow Execution Contract

**This document is not reference material — you are executing it.** Every fenced `bash` block is a real shell tool call your agent MUST issue. Do not paraphrase, summarize, describe, or narrate them; emit the exact command via your shell tool.

The following rules bind every phase in this workflow and are enforced by the Response Contract embedded at the top of each phase:

1. **Telemetry integrity.** Every executed step (`phase-0-preflight-gates` and every phase) emits exactly one `--status started` before its work and exactly one terminal status on completion — `--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when the human rejects and the phase must be regenerated — via `pragma-ai workflow report`. Skipping any of these is a workflow violation.
2. **Step-id and phase-name integrity.** The `--step-id` and `--workflow-id` values are the ONLY valid identifiers. Copy them **verbatim** from the `Step IDs` table above — never invent, translate, abbreviate, paraphrase, pluralize, or re-case them. `--workflow-id` MUST be exactly `new-component`. The CLI silently rejects unknown step-ids. This also governs every phase name you narrate, header, or put in an approval prompt: it MUST match, verbatim, a `### PHASE` header (or its embedded `#### Step`) tied to one of the `Step IDs` above. Never execute, narrate, or present a phase that is not in that table — including a phase from a previous version of this document, from memory, or from a different workflow. If a phase you are about to run does not appear there, stop and re-read the `Step IDs` table before continuing.
3. **Human approval per phase.** After every `finished`, present the approval prompt block (Aprobado / Ediciones / Rechazado) VERBATIM as the last thing in your response and yield. Silence is not approval. `phase-2-planning` embeds the aggregate approval gate for the whole planning set (inventory/DAG, technical plan and spec validation). See *Human approval gate* for the aggregate rejection replay protocol.
4. **Gap report per file-producing phase.** After the human approves a phase that produced files (`--output-file`), run the two-phase gap report against the same step-id. `phase-0-preflight-gates` produces no files; do NOT run its gap report.
5. **Conditional phases.** `phase-4-2-golden-tests-ds` is conditional on `golden_tests=true`. When `false`, skip the phase entirely — do not emit `started` or `finished`. Record the skip as `skipped_by_input` in `context.json`, `spec.yaml` and `PIPELINE_LOG_PATH`.
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
  --workflow-id new-component \
  --inputs-file "$WORKFLOW_INPUTS_FILE"

# The preflight succeeded; use the explicitly supplied hu_id for telemetry.
USER_STORY_ID="$hu_id"

# Persist only after a valid invocation has started.
echo "$USER_STORY_ID" > output/.active-user-story

# Mint the instance.
INSTANCE_ID=$(pragma-ai workflow create \
  --workflow-id new-component \
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

## Preflight Gates (required)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this gate MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Perform, in order, the Topology check, the App Repo Ownership check, and the Figma MCP preflight described under *Instructions* below.
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
  --workflow-id new-component \
  --step-id phase-0-preflight-gates \
  --status started
```

### Check 1 — Topology

1. `TOPOLOGY_REPO_MODE` valid (`single_repo | monorepo_melos | multi_repo`).
2. `PROJECT_ROOT` and `ACTIVE_TARGET_ROOT` accessible.
3. `ACTIVE_TARGET_ID` exists in `targets.registry` and its `kind` is
   `design_system`.
4. If `location_strategy=melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

If any validation fails, stop with `blocked_input`.

### Check 2 — App Repo Ownership

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

### Check 3 — Figma MCP

Before PHASE 1, `@ds-orchestrator` must delegate Figma MCP preflight to
`@figma-analyzer`. The analyzer verifies that Figma MCP is available and that
the user/agent has access to the file and `node-id`.

Minimum checklist:

1. URL parseable with `fileKey` and `nodeId`.
2. Figma MCP is configured in the active tool.
3. `get_design_context(fileKey, nodeId)` returns context for the node.
4. `get_screenshot(...)` returns a screenshot for the main node.
5. Sufficient permissions to read components, styles, variables and assets.
6. The active agent can write the packet-only Figma source archive at
   `{SPEC_PACKET_PATH}/source-assets/figma/`.
7. `get_images(...)` exports can be persisted by the active tool surface; a
   screenshot or temporary URL alone does not satisfy source-asset access.

If it fails, update `spec.yaml.external_access.figma_mcp.status=blocked_input`,
persist `evidence/figma-mcp-preflight.md` and stop with `blocked_input`.

> ⚡ **MANDATORY (conditional)** — If any check fails (Topology, App Repo Ownership, or Figma MCP preflight — the latter persists `evidence/figma-mcp-preflight.md`) and the gate ends with `blocked_input`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-0-preflight-gates \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` once all three checks pass (this gate produces no artifact on the success path — the Figma MCP diagnostic file is only written on failure, and the failure branch already reported `failed`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-0-preflight-gates \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, continue to PHASE 1. *(This step produces no output files — no gap report required.)*

## User Inputs

`hu_id` is **required**: it identifies the user story this component belongs to
and is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied, the
workflow refuses to start.

```text
@ds-orchestrator /new-component
hu_id: US-12345                                              [Required]
component_name: ds_status_badge
figma_url: https://www.figma.com/file/xxx/Component?node-id=123
user_story: [Optional acceptance context]
user_story_path: [Optional Markdown path; e.g. docs/user-stories/story-123.md]
atomic_hint: [Optional atom|molecule|organism]
golden_tests: false  [Optional; default false]
evidence_mode: minimal  [Optional; default minimal]
```

## Execution Sequence

### PHASE 1 — Spec Packet + Design Analysis (`mini`)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below: create the spec packet, then run the Figma design analysis, including downloading every visible Figma source asset.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 2 until the user replies.
>
> ```
> He completado PHASE 1 — Spec Packet + Design Analysis. ¿Apruebas el resultado?
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
  --workflow-id new-component \
  --step-id phase-1-spec-design-analysis \
  --status started
```

#### Step 1 — Mobile Spec Packet

**Agent**: `@ds-orchestrator`
**Skill**: `mobile-sdd-spec-validation`

Create `SPEC_PACKET_PATH` with:

1. `spec.yaml` (`schema_ref: ../docs/templates/schemas/mobile-spec.schema.yaml`,
   `spec_level: mini`, `execution_mode: propose_then_apply`)
2. `context.json`
3. `review.md` in Spanish
4. `evidence/validation-report.md`

The initial spec records inputs, acceptance criteria, Figma URL, user story,
expected success criteria (`widget_tests`, optional `goldens`, `widgetbook`,
`audit`), `external_access.figma_mcp.required=true`, permissions per agent and
sections that each agent must read. Normalize an omitted `golden_tests` input to
`false` and persist the resolved boolean in `spec.yaml.inputs` before
validation. Plan golden artifacts and golden success criteria only when it is
`true`.

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

#### Step 2 — Design Analysis

**Agent**: `@figma-analyzer`
**Prompt**: `figma-analysis.prompt.md`

Required output: update in `spec.yaml` only `design_source`,
`literal_texts`, `layout_constraints`, `assets` and `success_criteria.visual`.
Download every visible Figma icon, image, illustration, logo, and image-fill
source into `{SPEC_PACKET_PATH}/source-assets/figma/`, recording node id,
format, archive path and SHA-256 in `assets`. A screenshot, temporary export
URL, existing local asset, or similar icon is not a substitute.
Persist evidence in `evidence/figma-analysis.md`.

> ⚡ **MANDATORY (success path)** — Report `finished` with all packet artifacts, the design-analysis evidence, and every source asset archived under `source-assets/figma/`. Expand `${FIGMA_ASSET_FLAGS[@]}` from the paths recorded in `spec.yaml.assets[].archive_path`:

```bash
# Build --output-file flags for every archived Figma source asset
FIGMA_ASSET_FLAGS=()
while IFS= read -r asset; do
  FIGMA_ASSET_FLAGS+=(--output-file "$asset")
done < <(yq -r '.assets[].archive_path' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
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

### PHASE 2 — Planning (Inventory + DAG + Architecture + Validation)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below: build the inventory/DAG, define the technical plan, then validate the spec and present `review.md` for human review.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. This is the aggregate planning gate: PHASE 3 may only begin after explicit approval.
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
  --workflow-id new-component \
  --step-id phase-2-planning \
  --status started
```

#### Step 1 — Spec + Inventory + DAG

**Agent**: `@component-planner`
**Prompt**: `atomic-inventory.prompt.md`

Update in `spec.yaml` only `canonical_spec`, `inventory`, `dag` and
`artifact_plan.planned[group=ds_components]`.

#### Step 2 — Architecture Technical

**Agent**: `@component-architect`

Update in `spec.yaml` only `technical_plan`, `artifact_plan`,
`contracts.text_overflow`, `success_criteria` and `handoffs`.

#### Step 3 — Validation + Human Review

**Skill**: `mobile-sdd-spec-validation`

Validate `spec.yaml` and present `review.md`.

Present to the developer:
1. visual analysis, literal text, and the Figma source archive for every visible asset.
2. inventory, DAG and planned artifacts.
3. technical plan.
4. success criteria from `review.md`.

Wait for explicit approval to continue.
If the human requests adjustments, update only `spec.yaml`, `review.md` and the
affected sections. Do not generate code until `context.json` marks the spec
as approved.

> ⚡ **MANDATORY (conditional)** — If the spec fails schema/business validation and cannot continue:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-planning \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` once inventory, DAG, technical plan and validation are complete. This phase updates `spec.yaml` in place — declare it as the output file so the gap report can diff this phase's contribution:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-planning \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** This is the **domain aggregate approval gate** for the whole planning set (spec packet through technical plan). If the human requests changes to `design_source`, `literal_texts`, `assets`, or the underlying design analysis, the flow must return to PHASE 1: report `re_started` on `phase-1-spec-design-analysis`, apply changes, report `finished` again for that phase with the same `--output-file` set, re-run its gap report, and then report `re_started` → `finished` again on this phase (`phase-2-planning`) before re-entering this gate. Only when `context.json` marks the spec as approved may PHASE 3 begin. Once approved, run this step's **gap report** and then continue to PHASE 3.

---

### PHASE 3 — Code Generation + Quality Audit

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below: generate atoms → molecules → organisms in order, then run the quality audit loop.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 4.1 until the user replies.
>
> ```
> He completado PHASE 3 — Code Generation + Quality Audit. ¿Apruebas el resultado?
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
  --workflow-id new-component \
  --step-id phase-3-code-generation \
  --status started
```

#### Step 1 — DS Code Generation

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
  - assets
  - source-assets/figma
  - contracts.text_overflow
  - contracts.technical_vectors
  - success_criteria
```

Output: files `.dart` bajo
`targets.registry[artifact_plan.planned[].target_id].root`.

#### Step 2 — Quality Audit

**Agent**: `@code-auditor`

Loop with `@widget-developer` up to `pipeline.max_audit_retries`.

Required output: `evidence/audit-report.md` and a summary in the human report.
The audit must block a missing Figma source archive, a checksum mismatch for a
runtime asset, an undeclared DS exact-icon mapping, or a substituted font.

> ⚡ **MANDATORY (conditional)** — If the audit loop exceeds `pipeline.max_audit_retries` without passing, or hits an audit-blocker (missing archive, checksum mismatch, undeclared DS icon mapping, substituted font) that cannot be resolved:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-code-generation \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with one `--output-file` per `.dart` file declared in `artifact_plan.planned[group=ds_components]` plus the audit evidence. Paths must be relative to `--project-dir` (project root). Expand the array from the spec:

```bash
# Build --output-file flags from the artifact plan
DS_FILE_FLAGS=()
while IFS= read -r f; do
  DS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_components") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-code-generation \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/audit-report.md" \
  "${DS_FILE_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.1.

---

### PHASE 4.1 — Widget Tests DS

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 4.2 until the user replies.
>
> ```
> He completado PHASE 4.1 — Widget Tests DS. ¿Apruebas el resultado?
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
  --workflow-id new-component \
  --step-id phase-4-1-widget-tests-ds \
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
  - literal_texts
  - contracts.text_overflow
  - success_criteria
```

> ⚡ **MANDATORY (conditional)** — Widget tests are required. If they cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-4-1-widget-tests-ds \
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
  --workflow-id new-component \
  --step-id phase-4-1-widget-tests-ds \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/widget-tests.md" \
  "${DS_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.2 (only when `golden_tests=true`) or directly to PHASE 5.

---

### PHASE 4.2 — Golden Tests DS (conditional)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. **Guard check.** Only proceed with this phase when `golden_tests=true`. If `golden_tests=false`, skip the phase entirely — do not emit `started` or `finished`. Record `skipped_by_input` in `context.json`, `spec.yaml` and `PIPELINE_LOG_PATH`.
> 2. Emit the `--status started` command below as a real shell tool call.
> 3. Do the work described under *Instructions* below.
> 4. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 5. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 6. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 5 until the user replies.
>
> ```
> He completado PHASE 4.2 — Golden Tests DS. ¿Apruebas el resultado?
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
  --workflow-id new-component \
  --step-id phase-4-2-golden-tests-ds \
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

When `golden_tests=false`, do not invoke `@golden-test-engineer` or create
golden artifacts. Record `golden_tests: skipped_by_input` with
`reason: golden_tests=false` in `context.json`, `spec.yaml` and
`PIPELINE_LOG_PATH`.

> ⚡ **MANDATORY (conditional)** — If golden tests were requested but cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-4-2-golden-tests-ds \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed with a failing golden outcome when `golden_tests=true`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated golden test files and the golden-tests evidence:

```bash
DS_GOLDEN_FLAGS=()
while IFS= read -r f; do
  DS_GOLDEN_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_golden_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-4-2-golden-tests-ds \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/golden-tests.md" \
  "${DS_GOLDEN_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 5.

---

### PHASE 5 — Widgetbook DS

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below — start with the Widgetbook cold-init preflight (Step -1 of the `flutter-ds-widgetbook` skill) if the host project is uninitialized.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below (use cases + any bootstrap files from Step -1).
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 6 until the user replies.
>
> ```
> He completado PHASE 5 — Widgetbook DS. ¿Apruebas el resultado?
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
  --workflow-id new-component \
  --step-id phase-5-widgetbook-ds \
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
> If any initialization command fails, report `phase-5-widgetbook-ds` as
> `failed` with the captured error and stop the workflow — do not fall back
> to writing use cases against an uninitialized project.

> ⚡ **MANDATORY (success path)** — Report `finished` with the Widgetbook use-case files **plus** any bootstrap files produced by Step -1. Expand the use-case array from `artifact_plan.planned[group=ds_widgetbook]` and, when Step -1 bootstrapped Widgetbook, append the bootstrap files reported by `@widgetbook-developer`:

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
  --workflow-id new-component \
  --step-id phase-5-widgetbook-ds \
  --status finished \
  "${DS_WIDGETBOOK_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 6.

---

### PHASE 6 — Delivery

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
> He completado PHASE 6 — Delivery. ¿Apruebas el resultado?
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
  --workflow-id new-component \
  --step-id phase-6-delivery \
  --status started
```

**Agent**: `@delivery-manager`
**Prompt**: `delivery-review.prompt.md`

Required output: `evidence/delivery-report.md` and a summary in the human report.

Delivery requires passing `evidence/widget-tests.md` and exactly one golden
outcome: passing `evidence/golden-tests.md` when `golden_tests=true`, or the
recorded `golden_tests: skipped_by_input` outcome when false.

> ⚡ **MANDATORY (conditional)** — If delivery preconditions are not met (missing/failing `evidence/widget-tests.md`, or an inconsistent golden outcome):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-6-delivery \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the delivery report:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-6-delivery \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/delivery-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** — the workflow is complete.

## Rules

- Do not generate code before approving `review.md`.
- `spec.yaml` is the machine source; `PIPELINE_SPEC_PATH` remains a readable
  cumulative report.
- Handoffs by reference; do not copy full human reports between agents.
- Do not generate artifacts outside the resolved root for
  `artifact_plan.planned[].target_id`.
- Widget tests are required. Golden tests are conditional and must be recorded
  as executed or `skipped_by_input`.
- Record each phase in `PIPELINE_LOG_PATH`.
- If a phase does not apply, use `skipped` with an explicit reason.

---

## Response Contract Violations

The following are workflow violations. If your response for a phase contains any of them, you have failed the workflow contract for that phase:

- Omitting the `--status started` tool call before starting the phase's work.
- Omitting the terminal status tool call (`--status finished`, `--status failed`, or `--status re_started`) at the end of the phase.
- Emitting `--status finished` without every declared `--output-file` flag (spec, evidence, generated `.dart` files, tests, Widgetbook use cases + bootstrap files).
- Using a `--step-id` or `--workflow-id` value that does not appear in the `Step IDs` table above, character-for-character.
- Narrating, presenting, or executing a phase (in a header, approval prompt, or telemetry call) whose name does not correspond verbatim to an entry in the `Step IDs` table above — including a phase that existed in a previous version of this document.
- Ending a phase response without the approval prompt block, or adding prose after it.
- Starting the next phase's work before the user has explicitly answered the approval prompt.
- Running the gap report on `phase-0-preflight-gates` (it produces no files).
- Emitting `started` or `finished` for `phase-4-2-golden-tests-ds` when `golden_tests=false`.
- Reporting `phase-1-spec-design-analysis --status finished` without the archived Figma source assets referenced by `spec.yaml.assets[].archive_path`.

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

> **PHASE 2 aggregate rejection.** When PHASE 2 hosts the plan-approval decision, a rejection of a specific planning section (spec/design analysis, inventory/DAG, technical plan) must first replay the phase that owns that section: report `re_started` on `phase-1-spec-design-analysis` when the rejected section is spec or design analysis, regenerate its output, report `finished` again with the same `--output-file` set, re-run that phase's gap report, and then report `re_started` → `finished` on `phase-2-planning` itself before re-entering this gate. Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

> ⚡ **MANDATORY** — On rejection, example using `phase-3-code-generation`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-code-generation \
  --status re_started

# 2. ... regenerate the artifacts and re-run the audit ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
DS_FILE_FLAGS=()
while IFS= read -r f; do
  DS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_components") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-code-generation \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/audit-report.md" \
  "${DS_FILE_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow:
> `phase-1-spec-design-analysis`, `phase-2-planning`, `phase-3-code-generation`, `phase-4-1-widget-tests-ds`, `phase-4-2-golden-tests-ds` (only when executed), `phase-5-widgetbook-ds`, `phase-6-delivery`.
> `phase-0-preflight-gates` does NOT run a gap report.

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
| `pragma-ai workflow create --workflow-id new-component --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each step begins (`phase-0-preflight-gates`, PHASE 1–6; PHASE 4.2 only if `golden_tests=true`) |
| `pragma-ai workflow report ... --step-id <step> --status finished` | On completion of `phase-0-preflight-gates` (no `--output-file`) |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of file-producing phases: `phase-1-spec-design-analysis`, `phase-2-planning`, `phase-3-code-generation`, `phase-4-1-widget-tests-ds`, `phase-4-2-golden-tests-ds` (when executed), `phase-5-widgetbook-ds`, `phase-6-delivery` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When the preflight gate blocks (`phase-0-preflight-gates`), spec validation fails (`phase-2-planning`), the audit loop exhausts retries (`phase-3-code-generation`), tests can't pass (`phase-4-1-widget-tests-ds`, `phase-4-2-golden-tests-ds`), or delivery preconditions fail (`phase-6-delivery`) — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably PHASE 2 aggregate rejection) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding file-producing step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
