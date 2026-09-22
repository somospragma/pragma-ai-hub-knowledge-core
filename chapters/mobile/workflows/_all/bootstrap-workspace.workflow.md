---
id: bootstrap-workspace
version: 2.2.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: workspace-discovery
input_contract: ../docs/templates/spec-packets/bootstrap-workspace.overlay.yaml
invocation_mode: explicit_agent
description: >
  SDD-aware workflow to discover workspace topology and paths, propose the initial configuration, and apply it only after human approval. Use when project roots or target configuration are missing, ambiguous, or multi-repo.
---
# Workflow: Bootstrap Workspace

## Telemetry — Workflow metadata

| Field | Value |
|---|---|
| `workflow-id` | `bootstrap-workspace` |
| `user-story-id` | Value of the required `hu_id` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `phase-0-discovery`, `phase-1-proposal`, `phase-2-validate-apply`, `phase-3-post-validation` |

## Workflow Execution Contract

**This document is not reference material — you are executing it.** Every fenced `bash` block is a real shell tool call your agent MUST issue. Do not paraphrase, summarize, describe, or narrate them; emit the exact command via your shell tool.

The following rules bind every phase in this workflow and are enforced by the Response Contract embedded at the top of each phase:

1. **Telemetry integrity.** Every executed phase emits exactly one `--status started` before its work and exactly one terminal status on completion — `--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when the human rejects and the phase must be regenerated — via `pragma-ai workflow report`. Skipping any of these is a workflow violation.
2. **Step-id and phase-name integrity.** The `--step-id` and `--workflow-id` values are the ONLY valid identifiers. Copy them **verbatim** from the `Step IDs` table above — never invent, translate, abbreviate, paraphrase, pluralize, or re-case them. `--workflow-id` MUST be exactly `bootstrap-workspace`. The CLI silently rejects unknown step-ids. This also governs every phase name you narrate, header, or put in an approval prompt: it MUST match, verbatim, a `### PHASE` header (or its embedded `#### Step`) tied to one of the `Step IDs` above. Never execute, narrate, or present a phase that is not in that table — including a phase from a previous version of this document, from memory, or from a different workflow. If a phase you are about to run does not appear there, stop and re-read the `Step IDs` table before continuing.
3. **Human approval per phase.** After every `finished`, present the approval prompt block (Aprobado / Ediciones / Rechazado) VERBATIM as the last thing in your response and yield. Silence is not approval. `phase-2-validate-apply` embeds the domain-specific **HUMAN CHECKPOINT (Required)** as a mid-phase pause between its validation and apply steps: report `--status paused` on reaching it (a real, CLI-supported status distinct from `re_started`) and only continue to Step 3 once the human explicitly approves — see *Human approval gate* for the aggregate rejection replay protocol.
4. **Gap report per file-producing phase.** After the human approves a phase that produced files (`--output-file`), run the two-phase gap report against the same step-id. In this workflow, only `phase-1-proposal` and `phase-2-validate-apply` produce files. Skip the gap report for `phase-0-discovery` and `phase-3-post-validation`.
5. **Conditional phases.** When a phase's guard is false, skip the phase entirely — do not emit `started` or `finished`. Record the skip in `context.json`, `bootstrap-spec.yaml` and the pipeline log.
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
  --workflow-id bootstrap-workspace \
  --inputs-file "$WORKFLOW_INPUTS_FILE"

# The preflight succeeded; use the explicitly supplied hu_id for telemetry.
USER_STORY_ID="$hu_id"

# Persist only after a valid invocation has started.
echo "$USER_STORY_ID" > output/.active-user-story

# Mint the instance.
INSTANCE_ID=$(pragma-ai workflow create \
  --workflow-id bootstrap-workspace \
  --user-story-id "$USER_STORY_ID")
```

---

## Evidence Mode

Accept `EVIDENCE_MODE: minimal | standard`; default to `minimal` and persist it
as `bootstrap-spec.yaml.evidence_mode` before validation. In `minimal`, retain
the proposal, validation, drift analysis, human decision and apply result; use
compact `context.json.phase_results` for other phases. `standard` additionally
writes detailed discovery reports and candidates. Neither mode may omit a
topology, ownership or schema gate.

## When To Use It

Use this workflow when:

1. the app, Design System, and/or core package live in different physical paths
2. the workspace is a Melos monorepo or a multi-repo setup without reliable configuration
3. the user wants to remove path ambiguity before creating a view or component

Do not use it to re-create a valid canonical `.sopp/config` triplet. Bootstrap
reuses a valid applied configuration by default. Use `FORCE_RECONFIGURE: true`
only for an explicit migration or repair proposal.

## Prerequisites

- Accessible `WORKSPACE_ROOT`.
- Optional `*.code-workspace` file for the IDE workspace.
- Optional expected package names for the app, Design System, and core package.
- Recommended for multi-repo workspaces: `EXPECTED_APP_REPO_ROOT`, so the workflow can explicitly identify where `.sopp/config` must be created.

## User Inputs

`hu_id` is **required**: it identifies the user story this bootstrap belongs to
and is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied, the
workflow refuses to start.

```text
@workspace-discovery /bootstrap-workspace
hu_id: US-12345                                             # required
WORKSPACE_ROOT: /Users/user/dev/mobile-workspace
WORKSPACE_FILE: /Users/user/dev/mobile-workspace/mobile.code-workspace
EXPECTED_APP_REPO_ROOT: /Users/user/dev/mobile-workspace/mand-app-monorepo
EXPECTED_APP_PACKAGE: my_app
EXPECTED_DS_PACKAGE: design_system
EXPECTED_CORE_PACKAGE: core
EXPECTED_REPO_MODE: multi_repo
APPLY_MODE: propose_then_apply
FORCE_RECONFIGURE: false
EVIDENCE_MODE: minimal
```

## Canonical Sequence

### PHASE 0 — Discovery

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under Steps 1–2 below: if `APP_REPO_ROOT` is already known, run Step 1 first, then Step 2 only when Step 1 did not short-circuit with `reused_existing_config`. If `APP_REPO_ROOT` is not yet known, run Step 2 first to resolve it, then evaluate Step 1's gate.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call.
> 4. This phase produces no output files — do NOT run the gap report.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin the next phase until the user replies.
>
> ```
> He completado PHASE 0 — Discovery. ¿Apruebas el resultado?
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
  --workflow-id bootstrap-workspace \
  --step-id phase-0-discovery \
  --status started
```

#### Step 1 — Reuse Or Diagnose Canonical Configuration

**Agent**: `@workspace-discovery`

Run this gate as soon as `APP_REPO_ROOT` is known: either it was supplied
explicitly (directly or via `EXPECTED_APP_REPO_ROOT`), or Step 2 (Full
Discovery) already resolved it. If `APP_REPO_ROOT` is not yet known when this
phase begins, run Step 2 first to resolve it (and the rest of discovery), then
evaluate this gate before continuing to PHASE 1. Inspect only the final
canonical files in `<APP_REPO_ROOT>/.sopp/config/`.

1. If the complete triplet is valid, matches `APP_REPO_ROOT`, and resolves all
   target roots, return `reused_existing_config` and stop — this ends the
   phase (and the workflow) here. Do not create a bootstrap packet, proposal,
   backup, or replacement configuration, and do not proceed to Step 2.
2. If the triplet is partial, finish with
   `blocked_input: CONFIG_BOOTSTRAP_INCOMPLETE`.
3. If the triplet is complete but fails schema, ownership, root, or target
   validation, finish with `blocked_input: CONFIG_BOOTSTRAP_CONFIG_INVALID`.
4. Continue after either failure only when the human explicitly re-invokes with
   `FORCE_RECONFIGURE: true`; record a compact diff against the prior canonical
   configuration in the proposal.
5. Runtime-looking files under tool-specific KB folders are non-canonical.
   They are never configuration inputs or write destinations. If no canonical
   triplet exists, report `CONFIG_NON_CANONICAL_TOOL_STATE_FOUND`.

#### Step 2 — Full Discovery

**Guard check.** Run this step when `APP_REPO_ROOT` is not yet known at the
start of the phase (to resolve it, along with the rest of discovery), or when
Step 1 ran first (because `APP_REPO_ROOT` was already known) and did not
short-circuit with `reused_existing_config`. If Step 2 already ran first to
resolve `APP_REPO_ROOT` and Step 1's subsequent gate did not short-circuit,
its results are already complete — do not re-run it.

**Agent**: `@workspace-discovery`
**Prompt**: `workspace-discovery.prompt.md`

Resolve:

1. app, Design System, core, and Melos candidates
2. `APP_REPO_ROOT`
3. `TOPOLOGY_REPO_MODE`
4. `targets.registry` with logical targets (`app`, `design_system`, `core`, `project_docs`, `feature_*`) and their resolved roots
5. `active_target_defaults`
6. ambiguity risks

If deterministic resolution fails, finish with `blocked_input`.

> ⚡ **MANDATORY (conditional)** — If Step 1 ends with `blocked_input: CONFIG_BOOTSTRAP_INCOMPLETE` or `CONFIG_BOOTSTRAP_CONFIG_INVALID` and the human does NOT re-invoke with `FORCE_RECONFIGURE: true`, or if Step 2's deterministic resolution fails:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-0-discovery \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion (applies both to Step 1 ending in `reused_existing_config` as a successful terminal outcome, and to completing Step 2 and continuing on to PHASE 1):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-0-discovery \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved: if the outcome was `reused_existing_config`, the workflow ends; otherwise, continue to PHASE 1. *(This step produces no output files — no gap report required.)*

---

### PHASE 1 — Bootstrap Spec Packet + Proposal

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin the next phase until the user replies.
>
> ```
> He completado PHASE 1 — Bootstrap Spec Packet + Proposal. ¿Apruebas el resultado?
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
  --workflow-id bootstrap-workspace \
  --step-id phase-1-proposal \
  --status started
```

**Agent**: `@workspace-discovery`
**Prompt**: `workspace-discovery.prompt.md`

Required output in `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}`:

1. `bootstrap-spec.yaml`
2. `context.json`
3. `review.md`
4. `proposed/project.config.yaml`
5. `proposed/architecture-contract.yaml`
6. `proposed/dependencies-contract.yaml`
7. `evidence/validation-report.md` (required in both modes)
8. `evidence/drift-analysis.md` (required in both modes)
9. `evidence/workspace-discovery-report.md` (only `evidence_mode=standard`)
10. `evidence/candidates.json` (only `evidence_mode=standard`)

In `minimal`, persist discovery selections, rejected candidates and references
as compact `context.json.phase_results` entries instead of files 9-10.

`bootstrap-spec.yaml` must declare `schema_ref: ../docs/templates/schemas/bootstrap-spec.schema.yaml` and is the machine-readable source for the proposal. `review.md` is the human-readable Spanish review.

Generate the proposal from the canonical templates in `../docs/templates/`; do not rebuild the three configuration files from scratch when a template exists.

Minimum agent permissions:

- PHASE 0-1: may read the workspace and write only inside `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}`.
- PHASE 2: may write inside `<APP_REPO_ROOT>/.sopp/config/` only after the human checkpoint is approved and backups are created.
- Must never delete existing configuration files.
- Must never apply changes if the resolved root points to a Design System, shared, or core package instead of the app repository.

> ⚡ **MANDATORY (success path)** — Report `finished` with ALL generated files (add `evidence/workspace-discovery-report.md` and `evidence/candidates.json` only if `evidence_mode=standard`). Substitute `${APP_REPO_ROOT}` and `${RUN_ID}` with the run's actual values:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-1-proposal \
  --status finished \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/bootstrap-spec.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/context.json" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/review.md" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/proposed/project.config.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/proposed/architecture-contract.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/proposed/dependencies-contract.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/evidence/validation-report.md" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/evidence/drift-analysis.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** (this step produces output files) and then continue to PHASE 2.

---

### PHASE 2 — Validate + Apply

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below: run Pre-Apply Validation, then present the embedded HUMAN CHECKPOINT (Required), emit `--status paused` for this step, and end your response there — do not run Apply With Backup in the same turn as the checkpoint.
> 3. Only after the user explicitly answers the HUMAN CHECKPOINT's question with approval, run Apply With Backup.
> 4. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 5. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 6. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 3 until the user replies.
>
> ```
> He completado PHASE 2 — Validate + Apply. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 6 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool as your first action in this phase. Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-2-validate-apply \
  --status started
```

#### Step 1 — Pre-Apply Validation

**Agent**: `@workspace-discovery`
**Skill**: `mobile-sdd-spec-validation`

Validate:

1. `bootstrap-spec.yaml` is parseable and has `mode=propose_then_apply`.
2. The three files in `proposed/` exist.
3. Each `proposed/*.yaml` file declares `schema_version`, `schema_ref`, and `ownership`.
4. `project.repository_local_path` exists.
5. Each `targets.registry.*.root` resolves to an existing directory.
6. Each Dart/Flutter target declares `pubspec.yaml`.
7. If a target uses `location_strategy=melos_package`, run
   `docs/scripts/melos_workspace.rb resolve` with `repo_root` and
   `package_path`; require `ok=true` and persist the returned configuration
   source. Do not require `melos.yaml` by itself.
8. `app` targets have executable app signals (`lib/main.dart`, `lib/main_*.dart`, `android/`, or `ios/`).
9. `design_system` targets have Design System signals (`atoms`, `molecules`, `organisms`, or a DS barrel file).
10. Dependencies with `source=target` reference an existing `target_id` in `project.config.yaml.targets.registry`.
11. `APP_REPO_ROOT` does not point to a Design System, shared, or core package.
12. No anti-drift rule is violated:
    - physical paths and pipeline settings live only in `project.config.yaml`
    - layer rules live only in `architecture-contract.yaml`
    - dependency catalog and import rules live only in `dependencies-contract.yaml`
    - `dependencies-contract.yaml` does not define physical target paths

If validation fails, finish with `blocked_input`.

#### Step 2 — HUMAN CHECKPOINT (Required)

The orchestrator presents:

1. topology proposal
2. proposed app, Design System, and core paths
3. key differences from the current configuration, if any
4. explicit confirmation that `APP_REPO_ROOT` is not a Design System, shared, or core package
5. summary of `review.md`

Ask exactly:

"I generated the workspace configuration proposal. Do you approve applying the changes with backup?"

> ⚡ **MANDATORY** — Emit this as soon as the question above is asked, before yielding to the user:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-2-validate-apply \
  --status paused
```

Without explicit approval, do not proceed to Step 3 and end this response here — this phase remains `paused`, with no `finished`/`failed` yet. Do not write final files outside `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}`.

Operational note: `paused` (not `re_started`) is the correct status for this mid-phase wait — the phase already reported `started` before Step 1 and has not yet produced a first draft to restart. The phase resumes with Step 3 only once the human explicitly approves here; Step 3 then reports the phase's `finished`.

If the human rejects the proposal at this checkpoint, report `re_started` on `phase-1-proposal` (see *Human approval gate*), regenerate the proposal, re-report `finished` on `phase-1-proposal` (recapturing the baseline), and return to Step 1 of this phase.

#### Step 3 — Apply With Backup

**Agent**: `@workspace-discovery`
**Prompt**: `workspace-discovery.prompt.md` with `APPLY_MODE=apply_with_backup`

Required output:

1. `<APP_REPO_ROOT>/.sopp/config/project.config.yaml`
2. `<APP_REPO_ROOT>/.sopp/config/architecture-contract.yaml`
3. `<APP_REPO_ROOT>/.sopp/config/dependencies-contract.yaml`
4. `.bak` backups for the three files, if they existed
5. `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}/apply-report.md`

> ⚡ **MANDATORY (conditional)** — If Step 1 validation fails and the step ends with `blocked_input`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-2-validate-apply \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with ALL generated files from Step 3. Add one `--output-file` per `.bak` actually created (only if the originals existed). Substitute `${APP_REPO_ROOT}` and `${RUN_ID}` with the run's actual values:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-2-validate-apply \
  --status finished \
  --output-file "${APP_REPO_ROOT}/.sopp/config/project.config.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/config/architecture-contract.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/config/dependencies-contract.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/apply-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** (this step produces output files) and then continue to PHASE 3.

---

### PHASE 3 — Post-Bootstrap Validation

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under *Instructions* below.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call.
> 4. This phase produces no output files — do NOT run the gap report.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Once approved, the workflow is complete.
>
> ```
> He completado PHASE 3 — Post-Bootstrap Validation. ¿Apruebas el resultado?
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
  --workflow-id bootstrap-workspace \
  --step-id phase-3-post-validation \
  --status started
```

**Agent**: `@workspace-discovery`
**Skill**: `mobile-sdd-spec-validation`

Validate:

1. `project.repository_local_path` exists.
2. Each target in the registry resolves and keeps its expected signals.
3. Dependencies with `source=target` point to existing targets.
4. Final `<APP_REPO_ROOT>/.sopp/config/architecture-contract.yaml` exists.
5. Final `<APP_REPO_ROOT>/.sopp/config/dependencies-contract.yaml` exists.
6. `<APP_REPO_ROOT>/.sopp/flow_result` can be created.
7. `architecture.contract_path` and `dependencies.contract_path` resolve.
8. No anti-drift rule is violated across the three final YAML files.
9. Future `artifact_plan.planned[].target_id` values can resolve against `targets.registry`.

If validation fails, finish with `blocked_input` and an explicit code.

> ⚡ **MANDATORY (conditional)** — If validation fails and the step ends with `blocked_input`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-3-post-validation \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-3-post-validation \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, the workflow is complete. *(This step produces no output files — no gap report required.)*

## Expected Result

If PHASE 0-3 succeed:

1. the project is ready for `/new-view` or `/new-component`
2. the configuration no longer depends on `cwd`
3. the main pipeline operates with deterministic paths

## Rules

- Do not overwrite files without backup.
- Do not infer low-confidence paths without human approval.
- Validate agent permissions before writing in `bootstrap/` or `config/`.
- Default operation: `propose_then_apply`.
- `review.md` must be in Spanish.
- Handoffs must use references (`bootstrap-spec.yaml`, `context.json`); do not copy the full discovery into each phase.
- If the resolved root points to a Design System, shared, or core package, block with an explicit code and do not apply changes.
- Do not execute `/new-view` or `/new-component` if bootstrap ended in `blocked_input`.

---

## Response Contract Violations

The following are workflow violations. If your response for a phase contains any of them, you have failed the workflow contract for that phase:

- Omitting the `--status started` tool call before starting the phase's work.
- Omitting the terminal status tool call (`--status finished`, `--status failed`, or `--status re_started`) at the end of the phase.
- Emitting `--status finished` without every declared `--output-file` flag (for `phase-1-proposal` and `phase-2-validate-apply`).
- Using a `--step-id` or `--workflow-id` value that does not appear in the `Step IDs` table above, character-for-character.
- Narrating, presenting, or executing a phase (in a header, approval prompt, or telemetry call) whose name does not correspond verbatim to an entry in the `Step IDs` table above — including a phase that existed in a previous version of this document.
- Ending a phase response without the approval prompt block, or adding prose after it.
- Starting the next phase's work before the user has explicitly answered the approval prompt.
- Running the gap report on `phase-0-discovery` or `phase-3-post-validation` (they produce no files).
- Running Step 3 (Apply With Backup) of `phase-2-validate-apply` before the embedded HUMAN CHECKPOINT (Required) has been explicitly approved.
- Reaching the HUMAN CHECKPOINT in `phase-2-validate-apply` without emitting `--status paused` for that step before yielding to the user.

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

- **If approved:** If the step produces files (`phase-1-proposal`, `phase-2-validate-apply`), proceed to the gap report and then to the next step. If it produces no files, proceed directly to the next step.
- **If edits are requested:** First **verify the baseline is valid** before editing (see *Baseline integrity* below). Only when the baseline is confirmed valid, apply the changes in place on the artifact, keep `finished` (the baseline is already captured), and re-present for approval. The gap report will then capture those edits as the diff against the agent's first draft. If the baseline is missing, was captured late, or was reconstructed in a later session, do **not** edit in place: treat it as a rejection (regenerate to re-anchor a clean baseline) so the diff stays honest.
- **If rejected:** Report `re_started`, regenerate the artifact from scratch, report `finished` again (recapturing the baseline), and restart the gate. Repeat until approved.

> **Baseline integrity (mandatory).** A step's baseline is valid only when its `finished` was persisted in the same session/turn that produced the first draft, before any edit touched the artifact. Before applying edits, the controller MUST verify with `pragma-ai workflow status "$INSTANCE_ID"` that the step reports a persisted `finished`; if the CLI did not return success for that `finished`, the phase is not complete and the approval gate must not be presented. A baseline reconstructed in a later session, or pulled at gap-report time over an already-edited artifact, is **invalid**: a `No changes detected` result with a same-time "Baseline pulled" while edits were in fact requested is the signature of an invalid baseline. In that case do not `--submit` a false `no changes`; report `re_started`, regenerate to re-anchor a clean baseline, and restart the gate.

> For the mid-phase transition from Step 1/2 to Step 3 within `phase-2-validate-apply`, the domain-specific **HUMAN CHECKPOINT (Required)** in the Canonical Sequence applies in addition to the generic approval gate (same explicit-approval rule).

> ⚡ **MANDATORY** — On rejection, example using `phase-1-proposal`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-1-proposal \
  --status re_started

# 2. ... regenerate the artifact ...

# 3. Report finished again (recaptures baseline; include the same --output-file set as the original attempt)
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-1-proposal \
  --status finished \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/bootstrap-spec.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/context.json" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/review.md" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/proposed/project.config.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/proposed/architecture-contract.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/proposed/dependencies-contract.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/evidence/validation-report.md" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/evidence/drift-analysis.md"

# 4. Restart the approval gate
```

> The same `re_started` pattern applies when the flow returns to an earlier step from a later phase (for example, if the HUMAN CHECKPOINT rejects the proposal and forces `phase-1-proposal` to be redone). Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow: `phase-1-proposal` and `phase-2-validate-apply`.
> The steps `phase-0-discovery` and `phase-3-post-validation` do NOT run a gap report.

> Run this immediately after the corresponding step's approval gate passes — not batched at the end of the workflow.

**Phase A — Generate the gap report:**
```bash
pragma-ai workflow gap-report \
  --instance-id "$INSTANCE_ID" \
  --step-id <step-id>   # phase-1-proposal | phase-2-validate-apply
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
| `pragma-ai workflow create --workflow-id bootstrap-workspace --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each of the 4 steps (PHASE 0–3) begins |
| `pragma-ai workflow report ... --step-id <step> --status finished` | On completion of `phase-0-discovery` or `phase-3-post-validation` (no `--output-file`) |
| `pragma-ai workflow report ... --step-id phase-1-proposal --status finished --output-file ...` | On completion of PHASE 1, with one `--output-file` per artifact under `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}/` |
| `pragma-ai workflow report ... --step-id phase-2-validate-apply --status finished --output-file ...` | On completion of PHASE 2's Apply With Backup step, with one `--output-file` per final config file under `<APP_REPO_ROOT>/.sopp/config/` plus the `apply-report.md` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When a step ends in `blocked_input` (PHASE 0, PHASE 2's validation sub-step, PHASE 3) — the workflow stops |
| `pragma-ai workflow report ... --step-id phase-2-validate-apply --status paused` | On reaching the embedded HUMAN CHECKPOINT (Required), before yielding to the user; the step has not produced a first draft yet, so this is `paused`, not `re_started` |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id phase-1-proposal` | Gap Phase A: after PHASE 1 is approved |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id phase-2-validate-apply` | Gap Phase A: after PHASE 2 is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Gap Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
