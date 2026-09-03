---
id: new-component
version: 1.5.0
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
| Step IDs | `topology-gate`, `app-repo-ownership-gate`, `figma-mcp-gate`, `phase-0-spec-packet`, `phase-1-design-analysis`, `phase-2-spec-inventory-dag`, `phase-2-1-architecture-technical`, `phase-2-2-validation-human-review`, `phase-3-ds-code-generation`, `phase-3-1-quality-audit`, `phase-4-1-widget-tests-ds`, `phase-4-2-golden-tests-ds`, `phase-4-3-widgetbook-ds`, `phase-5-delivery` |

## Workflow Execution Contract

**This document is not reference material — you are executing it.** Every fenced `bash` block is a real shell tool call your agent MUST issue. Do not paraphrase, summarize, describe, or narrate them; emit the exact command via your shell tool.

The following rules bind every phase in this workflow and are enforced by the Response Contract embedded at the top of each phase:

1. **Telemetry integrity.** Every executed step (the three pre-flight gates and every phase) emits exactly one `--status started` before its work and exactly one terminal status on completion — `--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when the human rejects and the phase must be regenerated — via `pragma-ai workflow report`. Skipping any of these is a workflow violation.
2. **Step-id integrity.** The `--step-id` and `--workflow-id` values are the ONLY valid identifiers. Copy them **verbatim** from the `Step IDs` table above — never invent, translate, abbreviate, paraphrase, pluralize, or re-case them. `--workflow-id` MUST be exactly `new-component`. The CLI silently rejects unknown step-ids.
3. **Human approval per phase.** After every `finished`, present the approval prompt block (Aprobado / Ediciones / Rechazado) VERBATIM as the last thing in your response and yield. Silence is not approval. `phase-2-2-validation-human-review` is the aggregate approval gate for the planning set (PHASE 0 through PHASE 2.1). See *Human approval gate* for the aggregate rejection replay protocol.
4. **Gap report per file-producing phase.** After the human approves a phase that produced files (`--output-file`), run the two-phase gap report against the same step-id. The three pre-flight gates and `phase-2-2-validation-human-review` produce no files; do NOT run their gap report.
5. **Conditional phases.** `phase-4-2-golden-tests-ds` is conditional on `golden_tests=true`. When `false`, skip the phase entirely — do not emit `started` or `finished`. Record the skip as `skipped_by_input` in `context.json`, `spec.yaml` and `PIPELINE_LOG_PATH`.
6. **cwd assumption.** Commands assume the shell's cwd is the project root. `--project-dir` is only needed when running from elsewhere.

Violating any of these rules is a Response Contract Violation (see the section of that name at the end of this document).

## Instructions to the executing agent

You are the workflow controller. Before every phase:

1. **Load and read** this document into context (if not already loaded) and re-scan the phase's Response Contract at the top of that phase. The Response Contract binds the shape of your response.
2. **Do not skip** any Response Contract step. Doing so is a workflow violation.
3. **Do not begin** the phase's work until you have emitted its `--status started` command via your shell tool and it has returned.
4. **Do not begin** the next phase until the human has explicitly answered the approval prompt with **1** (Aprobado), **2** (Ediciones), or **3** (Rechazado).
5. **End your response** with the approval prompt block, verbatim, and yield. Do not add prose after it. Do not continue past it in the same response.

Both `Human approval gate` and `Response Contract Violations` at the end of this document apply to every phase and are non-negotiable.

---

## Setup — Mint the workflow instance

> ⚡ **MANDATORY** — Always run this at the start, before any step.

### Resolve user-story-id (mandatory)

`hu_id` is a **required** invocation input for this workflow (see *User Inputs*), so the agent already has the user story identifier at the start. The agent MUST map it to `user-story-id` before running `workflow create`:

1. **Invocation input (canonical):** Use the `hu_id` value provided in the invocation. This is the required path.
2. **Fallback — Session context:** If `hu_id` was not supplied but a `user-story-id` is already available from a parent flow or another sub-workflow in this session, reuse it silently.
3. **Fallback — Project file:** If neither of the above is available, read the ID from `output/.active-user-story` when it exists.
4. **Last resort — Ask the user:** If no source yields an ID, ask explicitly and refuse to proceed without a value:

```
Kratos: To track progress I need the user-story-id.
  What is the active user story? (e.g. US-12345, HU-678)
```

> Once resolved, the agent MUST persist the value to `output/.active-user-story` so downstream workflows inherit it automatically.

```bash
# 1. Take the required hu_id from the invocation and use it as user-story-id
USER_STORY_ID="$hu_id"

# 2. Persist for other workflows so they don't have to ask again
echo "$USER_STORY_ID" > output/.active-user-story

# 3. Mint the instance
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

## Topology Gate (required)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this gate MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Perform the validation checks described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success or `--status failed` on unrecoverable blocker) via a real shell tool call.
> 4. This gate produces no output files — do NOT run the gap report.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin the next gate until the user replies.
>
> ```
> He completado Topology Gate. ¿Apruebas el resultado?
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
  --step-id topology-gate \
  --status started
```

1. `TOPOLOGY_REPO_MODE` valid (`single_repo | monorepo_melos | multi_repo`).
2. `PROJECT_ROOT` and `ACTIVE_TARGET_ROOT` accessible.
3. `ACTIVE_TARGET_ID` exists in `targets.registry` and its `kind` is
   `design_system`.
4. If `location_strategy=melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

If any validation fails, finish with `blocked_input`.

> ⚡ **MANDATORY (conditional)** — If any check fails and the step ends with `blocked_input`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id topology-gate \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id topology-gate \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, continue to the App Repo Ownership Gate. *(This step produces no output files — no gap report required.)*

## App Repo Ownership Gate (required)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this gate MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Perform the validation checks described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success or `--status failed` on unrecoverable blocker) via a real shell tool call.
> 4. This gate produces no output files — do NOT run the gap report.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin the next gate until the user replies.
>
> ```
> He completado App Repo Ownership Gate. ¿Apruebas el resultado?
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
  --step-id app-repo-ownership-gate \
  --status started
```

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

> ⚡ **MANDATORY (conditional)** — If any of the above blocking codes triggers:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id app-repo-ownership-gate \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id app-repo-ownership-gate \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, continue to the Figma MCP Gate. *(This step produces no output files — no gap report required.)*

## Figma MCP Gate (required)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this gate MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Perform the Figma MCP preflight described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success or `--status failed` on unrecoverable blocker) via a real shell tool call.
> 4. On the success path this gate produces no output files — do NOT run the gap report. (On failure, the diagnostic file is captured by the `failed` branch and does not go through the gap report either.)
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 0 until the user replies.
>
> ```
> He completado Figma MCP Gate. ¿Apruebas el resultado?
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
  --step-id figma-mcp-gate \
  --status started
```

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
persist `evidence/figma-mcp-preflight.md` and finish with `blocked_input`.

> ⚡ **MANDATORY (conditional)** — If preflight fails (persists `evidence/figma-mcp-preflight.md` and ends with `blocked_input`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id figma-mcp-gate \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion (successful preflight produces no artifact — the diagnostic file is only written on failure, and the failure branch already reported `failed`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id figma-mcp-gate \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, continue to PHASE 0. *(On the success path this step produces no output files — no gap report required.)*

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

### PHASE 0 — Mobile Spec Packet (`mini`)

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 1 until the user replies.
>
> ```
> He completado PHASE 0 — Mobile Spec Packet. ¿Apruebas el resultado?
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
  --step-id phase-0-spec-packet \
  --status started
```

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

> ⚡ **MANDATORY (success path)** — Report `finished` with all four packet artifacts. Substitute `${SPEC_PACKET_PATH}` with the resolved run path:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-0-spec-packet \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/review.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/validation-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.

---

### PHASE 1 — Design Analysis

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below, including downloading every visible Figma source asset.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 2 until the user replies.
>
> ```
> He completado PHASE 1 — Design Analysis. ¿Apruebas el resultado?
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
  --step-id phase-1-design-analysis \
  --status started
```

**Agent**: `@figma-analyzer`
**Prompt**: `figma-analysis.prompt.md`

Required output: update in `spec.yaml` only `design_source`,
`literal_texts`, `layout_constraints`, `assets` and `success_criteria.visual`.
Download every visible Figma icon, image, illustration, logo, and image-fill
source into `{SPEC_PACKET_PATH}/source-assets/figma/`, recording node id,
format, archive path and SHA-256 in `assets`. A screenshot, temporary export
URL, existing local asset, or similar icon is not a substitute.
Persist evidence in `evidence/figma-analysis.md`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated spec, the analysis evidence, and every source asset archived under `source-assets/figma/`. Expand `${FIGMA_SOURCE_ASSETS[@]}` from the paths recorded in `spec.yaml.assets[].archive_path`:

```bash
# Build --output-file flags for every archived Figma source asset
FIGMA_ASSET_FLAGS=()
while IFS= read -r asset; do
  FIGMA_ASSET_FLAGS+=(--output-file "$asset")
done < <(yq -r '.assets[].archive_path' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-1-design-analysis \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/evidence/figma-analysis.md" \
  "${FIGMA_ASSET_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.

---

### PHASE 2 — Spec + Inventory + DAG

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 2.1 until the user replies.
>
> ```
> He completado PHASE 2 — Spec + Inventory + DAG. ¿Apruebas el resultado?
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
  --step-id phase-2-spec-inventory-dag \
  --status started
```

**Agent**: `@component-planner`
**Prompt**: `atomic-inventory.prompt.md`

Update in `spec.yaml` only `canonical_spec`, `inventory`, `dag` and
`artifact_plan.planned[group=ds_components]`.

> ⚡ **MANDATORY (success path)** — Report `finished`. This phase updates `spec.yaml` in place — declare it as the output file so the gap report can diff this phase's contribution:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-spec-inventory-dag \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.1.

---

### PHASE 2.1 — Architecture Technical

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 2.2 until the user replies.
>
> ```
> He completado PHASE 2.1 — Architecture Technical. ¿Apruebas el resultado?
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
  --step-id phase-2-1-architecture-technical \
  --status started
```

**Agent**: `@component-architect`

Update in `spec.yaml` only `technical_plan`, `artifact_plan`,
`contracts.text_overflow`, `success_criteria` and `handoffs`.

> ⚡ **MANDATORY (success path)** — Report `finished`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-1-architecture-technical \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.2.

---

### PHASE 2.2 — Validation + Human Review

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call.
> 4. This phase produces no output files — do NOT run the gap report.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. This is the aggregate planning gate: PHASE 3 may only begin after explicit approval.
>
> ```
> He completado PHASE 2.2 — Validation + Human Review. ¿Apruebas el resultado?
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
  --step-id phase-2-2-validation-human-review \
  --status started
```

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
  --step-id phase-2-2-validation-human-review \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` once validation passes and the human review is presented (approval itself happens in the gate that follows):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-2-validation-human-review \
  --status finished
```

> **Stop here.** This is the **domain aggregate approval gate** for the whole planning set (PHASE 0 through PHASE 2.1). If the human requests changes to `design_source`, `literal_texts`, `assets`, `inventory`, `dag`, `technical_plan`, or `artifact_plan`, the flow must return to the phase that owns that section: report `re_started` on the affected earlier phase, apply changes, report `finished` again for that phase, re-run its gap report, and re-enter PHASE 2.2 (which itself gets `re_started` → `finished` again). Only when `context.json` marks the spec as approved may PHASE 3 begin. *(PHASE 2.2 produces no new output files — no gap report required.)*

---

### PHASE 3 — DS Code Generation

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below, generating atoms → molecules → organisms in order.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 3.1 until the user replies.
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
  --workflow-id new-component \
  --step-id phase-3-ds-code-generation \
  --status started
```

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

> ⚡ **MANDATORY (success path)** — Report `finished` with one `--output-file` per `.dart` file declared in `artifact_plan.planned[group=ds_components]`. Paths must be relative to `--project-dir` (project root). Expand the array from the spec:

```bash
# Build --output-file flags from the artifact plan
DS_FILE_FLAGS=()
while IFS= read -r f; do
  DS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_components") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-ds-code-generation \
  --status finished \
  "${DS_FILE_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 3.1.

---

### PHASE 3.1 — Quality Audit

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 4.1 until the user replies.
>
> ```
> He completado PHASE 3.1 — Quality Audit. ¿Apruebas el resultado?
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
  --step-id phase-3-1-quality-audit \
  --status started
```

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
  --step-id phase-3-1-quality-audit \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the audit evidence:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-1-quality-audit \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/audit-report.md"
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
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 4.2 / 4.3 until the user replies.
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

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.2 (only when `golden_tests=true`) or directly to PHASE 4.3.

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
> 6. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 4.3 until the user replies.
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

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.3.

---

### PHASE 4.3 — Widgetbook DS

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below — start with the Widgetbook cold-init preflight (Step -1 of the `flutter-ds-widgetbook` skill) if the host project is uninitialized.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below (use cases + any bootstrap files from Step -1).
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 5 until the user replies.
>
> ```
> He completado PHASE 4.3 — Widgetbook DS. ¿Apruebas el resultado?
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
  --step-id phase-4-3-widgetbook-ds \
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
> If any initialization command fails, report `phase-4-3-widgetbook-ds` as
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
  --step-id phase-4-3-widgetbook-ds \
  --status finished \
  "${DS_WIDGETBOOK_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 5.

---

### PHASE 5 — Delivery

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
> He completado PHASE 5 — Delivery. ¿Apruebas el resultado?
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
  --step-id phase-5-delivery \
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
  --step-id phase-5-delivery \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the delivery report:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-5-delivery \
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
- Ending a phase response without the approval prompt block, or adding prose after it.
- Starting the next phase's work before the user has explicitly answered the approval prompt.
- Running the gap report on `topology-gate`, `app-repo-ownership-gate`, `figma-mcp-gate` (successful path) or `phase-2-2-validation-human-review` (they produce no files).
- Emitting `started` or `finished` for `phase-4-2-golden-tests-ds` when `golden_tests=false`.
- Reporting `phase-1-design-analysis --status finished` without the archived Figma source assets referenced by `spec.yaml.assets[].archive_path`.

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
- **If edits are requested:** Apply the changes in place on the artifact, keep `finished` (the baseline is already captured), and re-present for approval. The gap report will capture those edits as the diff against the agent's first draft.
- **If rejected:** Report `re_started`, regenerate the artifact from scratch, report `finished` again (recapturing the baseline), and restart the gate. Repeat until approved.

> **PHASE 2.2 aggregate rejection.** When PHASE 2.2 hosts the plan-approval decision, a rejection of a specific planning section (design analysis, inventory/DAG, technical plan) must first replay the phase that owns that section: report `re_started` on the affected earlier phase (PHASE 1, PHASE 2, or PHASE 2.1), regenerate its output, report `finished` again with the same `--output-file` set, re-run that phase's gap report, and then report `re_started` → `finished` on PHASE 2.2 itself before re-entering this gate. Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

> ⚡ **MANDATORY** — On rejection, example using `phase-3-ds-code-generation`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-ds-code-generation \
  --status re_started

# 2. ... regenerate the artifacts ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
DS_FILE_FLAGS=()
while IFS= read -r f; do
  DS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_components") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-ds-code-generation \
  --status finished \
  "${DS_FILE_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow:
> `phase-0-spec-packet`, `phase-1-design-analysis`, `phase-2-spec-inventory-dag`, `phase-2-1-architecture-technical`, `phase-3-ds-code-generation`, `phase-3-1-quality-audit`, `phase-4-1-widget-tests-ds`, `phase-4-2-golden-tests-ds` (only when executed), `phase-4-3-widgetbook-ds`, `phase-5-delivery`.
> The three pre-flight gates (`topology-gate`, `app-repo-ownership-gate`, `figma-mcp-gate`) and `phase-2-2-validation-human-review` do NOT run a gap report.

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
  --summary "<summary of the detected gap or 'no changes'>"
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
| `pragma-ai workflow report ... --step-id <step> --status started` | When each step begins (gates, PHASE 0–5; PHASE 4.2 only if `golden_tests=true`) |
| `pragma-ai workflow report ... --step-id <step> --status finished` | On completion of `topology-gate`, `app-repo-ownership-gate`, `figma-mcp-gate`, `phase-2-2-validation-human-review` (no `--output-file`) |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of file-producing phases: `phase-0-spec-packet`, `phase-1-design-analysis`, `phase-2-spec-inventory-dag`, `phase-2-1-architecture-technical`, `phase-3-ds-code-generation`, `phase-3-1-quality-audit`, `phase-4-1-widget-tests-ds`, `phase-4-2-golden-tests-ds` (when executed), `phase-4-3-widgetbook-ds`, `phase-5-delivery` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When a gate blocks (`topology-gate`, `app-repo-ownership-gate`, `figma-mcp-gate`), validation fails (`phase-2-2-validation-human-review`), the audit loop exhausts retries (`phase-3-1-quality-audit`), tests can't pass (`phase-4-1-widget-tests-ds`, `phase-4-2-golden-tests-ds`), or delivery preconditions fail (`phase-5-delivery`) — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably PHASE 2.2 aggregate rejection) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding file-producing step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
