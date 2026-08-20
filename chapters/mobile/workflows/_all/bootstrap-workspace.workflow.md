---
id: bootstrap-workspace
version: 1.3.0
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
| `user-story-id` | Value of the required `HU_ID` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `phase-0-reuse-or-diagnose`, `phase-1-discovery`, `phase-2-proposal`, `phase-3-pre-apply-validation`, `phase-4-apply-with-backup`, `phase-5-post-bootstrap-validation` |

> **NON-NEGOTIABLE RULE:** Every `pragma-ai workflow ...` command in this document is **MANDATORY** to execute. The agent MUST run them — they are not suggestions or documentation.

> Each step ends with a **human approval gate** before the gap report (see *Human approval gate* at the end of this document).
> The **gap report only runs on steps that produce output files** (`--output-file`). In this workflow, only `phase-2-proposal` and `phase-4-apply-with-backup` produce files.
> Commands assume the shell's cwd is already the project root — no `cd` prefix is needed, and `--project-dir` only matters when running from elsewhere.

---

## Setup — Mint the workflow instance

> ⚡ **MANDATORY** — Always run this at the start, before any step.

### Resolve user-story-id (mandatory)

`HU_ID` is a **required** invocation input for this workflow (see *User Inputs*), so the agent already has the user story identifier at the start. The agent MUST map it to `user-story-id` before running `workflow create`:

1. **Invocation input (canonical):** Use the `HU_ID` value provided in the invocation. This is the required path.
2. **Fallback — Session context:** If `HU_ID` was not supplied but a `user-story-id` is already available from a parent flow or another sub-workflow in this session, reuse it silently.
3. **Fallback — Project file:** If neither of the above is available, read the ID from `output/.active-user-story` when it exists.
4. **Last resort — Ask the user:** If no source yields an ID, ask explicitly and refuse to proceed without a value:

```
Kratos: To track progress I need the user-story-id.
  What is the active user story? (e.g. US-12345, HU-678)
```

> Once resolved, the agent MUST persist the value to `output/.active-user-story` so downstream workflows inherit it automatically.

```bash
# 1. Take the required HU_ID from the invocation and use it as user-story-id
USER_STORY_ID="$HU_ID"

# 2. Persist for other workflows so they don't have to ask again
echo "$USER_STORY_ID" > output/.active-user-story

# 3. Mint the instance
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

`HU_ID` is **required**: it identifies the user story this bootstrap belongs to
and is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied, the
workflow refuses to start.

```text
@workspace-discovery /bootstrap-workspace
HU_ID: US-12345                                             # required
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

### PHASE 0 — Reuse Or Diagnose Canonical Configuration

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-0-reuse-or-diagnose \
  --status started
```

**Agent**: `@workspace-discovery`

Run this gate immediately after the app repository is deterministically
resolved. When the app root is not supplied explicitly, complete PHASE 1 discovery
first, then return to this gate before PHASE 2 creates a proposal. Inspect only the
final canonical files in `<APP_REPO_ROOT>/.sopp/config/`.

1. If the complete triplet is valid, matches `APP_REPO_ROOT`, and resolves all
   target roots, return `reused_existing_config` and stop. Do not create a
   bootstrap packet, proposal, backup, or replacement configuration.
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

> ⚡ **MANDATORY (conditional)** — If the step ends with `blocked_input: CONFIG_BOOTSTRAP_INCOMPLETE` or `CONFIG_BOOTSTRAP_CONFIG_INVALID` and the human does NOT re-invoke with `FORCE_RECONFIGURE: true`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-0-reuse-or-diagnose \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion (applies both to `reused_existing_config` as a successful terminal outcome and to continuing on to PHASE 1):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-0-reuse-or-diagnose \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved: if the outcome was `reused_existing_config`, the workflow ends; otherwise, continue to PHASE 1. *(This step produces no output files — no gap report required.)*

---

### PHASE 1 — Discovery

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-1-discovery \
  --status started
```

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

> ⚡ **MANDATORY (conditional)** — If deterministic resolution fails and the step ends with `blocked_input`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-1-discovery \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-1-discovery \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, continue to PHASE 2. *(This step produces no output files — no gap report required.)*

---

### PHASE 2 — Bootstrap Spec Packet + Proposal

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-2-proposal \
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

- PHASE 1-3: may read the workspace and write only inside `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}`.
- PHASE 4: may write inside `<APP_REPO_ROOT>/.sopp/config/` only after the human checkpoint is approved and backups are created.
- Must never delete existing configuration files.
- Must never apply changes if the resolved root points to a Design System, shared, or core package instead of the app repository.

> ⚡ **MANDATORY (success path)** — Report `finished` with ALL generated files (add `evidence/workspace-discovery-report.md` and `evidence/candidates.json` only if `evidence_mode=standard`). Substitute `${APP_REPO_ROOT}` and `${RUN_ID}` with the run's actual values:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-2-proposal \
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

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** (this step produces output files) and then continue to PHASE 3.

---

### PHASE 3 — Pre-Apply Validation

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-3-pre-apply-validation \
  --status started
```

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

> ⚡ **MANDATORY (conditional)** — If validation fails and the step ends with `blocked_input`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-3-pre-apply-validation \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-3-pre-apply-validation \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). The generic approval gate applies to the validation itself; additionally, transitioning to PHASE 4 requires the domain-specific **HUMAN CHECKPOINT (Required)** for `propose_then_apply` defined below. Once approved, continue to PHASE 4. *(This step produces no output files — no gap report required.)*

---

### HUMAN CHECKPOINT (Required)

The orchestrator presents:

1. topology proposal
2. proposed app, Design System, and core paths
3. key differences from the current configuration, if any
4. explicit confirmation that `APP_REPO_ROOT` is not a Design System, shared, or core package
5. summary of `review.md`

Ask exactly:

"I generated the workspace configuration proposal. Do you approve applying the changes with backup?"

Without explicit approval, finish with state `proposed`. Do not write final files outside `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}`.

Operational note: this is not a second command. The same workflow remains paused in `proposed`; when the human approves, the orchestrator executes PHASE 4 atomically with backups.

> **Telemetry note:** This checkpoint is the domain-specific approval gate for the PHASE 3 → PHASE 4 transition. It follows the same rule as the generic gate (explicit approval, never inferred from silence). If the human rejects the proposal, report `re_started` on `phase-2-proposal` (see *Human approval gate*), regenerate the proposal, re-report `finished` (recapturing the baseline), and re-enter this checkpoint.

---

### PHASE 4 — Apply With Backup (If Approved)

> ⚡ **MANDATORY** — Report `started` when the step begins (only after the HUMAN CHECKPOINT has been approved).

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-4-apply-with-backup \
  --status started
```

**Agent**: `@workspace-discovery`
**Prompt**: `workspace-discovery.prompt.md` with `APPLY_MODE=apply_with_backup`

Required output:

1. `<APP_REPO_ROOT>/.sopp/config/project.config.yaml`
2. `<APP_REPO_ROOT>/.sopp/config/architecture-contract.yaml`
3. `<APP_REPO_ROOT>/.sopp/config/dependencies-contract.yaml`
4. `.bak` backups for the three files, if they existed
5. `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}/apply-report.md`

> ⚡ **MANDATORY (success path)** — Report `finished` with ALL generated files. Add one `--output-file` per `.bak` actually created (only if the originals existed). Substitute `${APP_REPO_ROOT}` and `${RUN_ID}` with the run's actual values:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-4-apply-with-backup \
  --status finished \
  --output-file "${APP_REPO_ROOT}/.sopp/config/project.config.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/config/architecture-contract.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/config/dependencies-contract.yaml" \
  --output-file "${APP_REPO_ROOT}/.sopp/bootstrap/${RUN_ID}/apply-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** (this step produces output files) and then continue to PHASE 5.

---

### PHASE 5 — Post-Bootstrap Validation

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-5-post-bootstrap-validation \
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
  --step-id phase-5-post-bootstrap-validation \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-5-post-bootstrap-validation \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, the workflow is complete. *(This step produces no output files — no gap report required.)*

## Expected Result

If PHASE 0-5 succeed:

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

## Human approval gate

> ⚡ **MANDATORY** — Always runs after each `finished`. It cannot be skipped, and approval cannot be inferred from silence.

At the end of each step, present the result and request **explicit** approval:

```
Agent: I've completed [step name]. Do you approve the result?
  1. ✅ Approved — continue
  2. ✏️ Edits — tell me what to change
  3. ❌ Rejected — redo from scratch
```

- **If approved:** If the step produces files (`phase-2-proposal`, `phase-4-apply-with-backup`), proceed to the gap report and then to the next step. If it produces no files, proceed directly to the next step.
- **If edits are requested:** Apply the changes in place on the artifact, keep `finished` (the baseline is already captured), and re-present for approval. The gap report will capture those edits as the diff against the agent's first draft.
- **If rejected:** Report `re_started`, regenerate the artifact from scratch, report `finished` again (recapturing the baseline), and restart the gate. Repeat until approved.

> For the PHASE 3 → PHASE 4 transition, the domain-specific **HUMAN CHECKPOINT (Required)** in the Canonical Sequence applies in addition to the generic approval gate (same explicit-approval rule).

> ⚡ **MANDATORY** — On rejection, example using `phase-2-proposal`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-2-proposal \
  --status re_started

# 2. ... regenerate the artifact ...

# 3. Report finished again (recaptures baseline; include the same --output-file set as the original attempt)
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id bootstrap-workspace \
  --step-id phase-2-proposal \
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

> The same `re_started` pattern applies when the flow returns to an earlier step from a later phase (for example, if the HUMAN CHECKPOINT rejects the proposal and forces PHASE 2 to be redone). Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow: `phase-2-proposal` and `phase-4-apply-with-backup`.
> The steps `phase-0-reuse-or-diagnose`, `phase-1-discovery`, `phase-3-pre-apply-validation`, and `phase-5-post-bootstrap-validation` do NOT run a gap report.

> Run this immediately after the corresponding step's approval gate passes — not batched at the end of the workflow.

**Phase A — Generate the gap report:**
```bash
pragma-ai workflow gap-report \
  --instance-id "$INSTANCE_ID" \
  --step-id <step-id>   # phase-2-proposal | phase-4-apply-with-backup
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
| `pragma-ai workflow create --workflow-id bootstrap-workspace --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each of the 6 steps (PHASE 0–5) begins |
| `pragma-ai workflow report ... --step-id <step> --status finished` | On completion of `phase-0-reuse-or-diagnose`, `phase-1-discovery`, `phase-3-pre-apply-validation`, `phase-5-post-bootstrap-validation` (no `--output-file`) |
| `pragma-ai workflow report ... --step-id phase-2-proposal --status finished --output-file ...` | On completion of PHASE 2, with one `--output-file` per artifact under `<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}/` |
| `pragma-ai workflow report ... --step-id phase-4-apply-with-backup --status finished --output-file ...` | On completion of PHASE 4, with one `--output-file` per final config file under `<APP_REPO_ROOT>/.sopp/config/` plus the `apply-report.md` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When a step ends in `blocked_input` (PHASE 0, PHASE 1, PHASE 3, PHASE 5) — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id phase-2-proposal` | Gap Phase A: after PHASE 2 is approved |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id phase-4-apply-with-backup` | Gap Phase A: after PHASE 4 is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Gap Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
