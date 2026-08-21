---
id: refactor-component
version: 1.3.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: ds-orchestrator
input_contract: ../docs/templates/spec-packets/refactor-component.overlay.yaml
invocation_mode: explicit_agent
description: >
  Deterministic workflow to refactor an existing Design System component. Use when the user requests implementation, API, visual, accessibility, or maintainability changes to an existing component with review and audit gates.
---
# Workflow: Refactor Component

## Telemetry — Workflow metadata

| Field | Value |
|---|---|
| `workflow-id` | `refactor-component` |
| `user-story-id` | Value of the required `hu_id` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `phase-0-spec-packet`, `phase-1-current-component-analysis`, `phase-2-technical-refactor-plan`, `phase-2-5-validation-human-review`, `phase-3-apply-changes`, `phase-3-5-audit`, `phase-4a-widget-tests`, `phase-4b-golden-tests`, `phase-5-delivery` |

> **NON-NEGOTIABLE RULE:** Every `pragma-ai workflow ...` command in this document is **MANDATORY** to execute. The agent MUST run them — they are not suggestions or documentation.

> ⛔ **STEP-ID INTEGRITY (NON-NEGOTIABLE):** The `--step-id` and `--workflow-id` values shown in every command block below are the **ONLY** valid identifiers for this workflow. The agent MUST copy them **verbatim** from this document — never invent, abbreviate, translate, paraphrase, pluralize, capitalize differently, or otherwise modify them.
>
> - Every `--step-id` submitted to `pragma-ai workflow report` or `pragma-ai workflow gap-report` MUST match one entry in the **"Step IDs"** list above, character-for-character (kebab-case, lowercase, exact spelling).
> - Every `--workflow-id` MUST be exactly `refactor-component`.
> - If a step-id you need is not in the list, STOP and ask the user — do not fabricate one.
> - The CLI rejects unknown step-ids; a wrong id silently corrupts the run's telemetry.

> Each step ends with a **human approval gate** before the gap report (see *Human approval gate* at the end of this document). PHASE 2.5 is the domain aggregate approval gate for the planning set (PHASE 0 through PHASE 2).
> **The Topology gate is excluded from telemetry.** It runs before the workflow instance is minted and stops the run with `blocked_input` when it fails (no telemetry emitted).
> The **gap report only runs on steps that produce output files** (`--output-file`). `phase-2-5-validation-human-review` does NOT run a gap report.
> `phase-4b-golden-tests` is conditional: emit telemetry only when the plan/audit classifies the refactor as having visual impact. Otherwise skip the phase entirely.
> Commands assume the shell's cwd is already the project root — no `cd` prefix is needed, and `--project-dir` only matters when running from elsewhere.

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
  --workflow-id refactor-component \
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

- Path for the component to refactor.
- Description of the refactor: what to change and why.
- `.sopp/config/project.config.yaml` valid.
- Context resolved by the orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `ACTIVE_TARGET_ID = active_target_defaults.design_system`
  - `ACTIVE_TARGET_ROOT = targets.registry[ACTIVE_TARGET_ID].root`
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`
  - `SPEC_PACKET_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/specs/{component_slug}-refactor`

## Topology Gate

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate `PROJECT_ROOT` and `ACTIVE_TARGET_ROOT`.
3. Validate that `ACTIVE_TARGET_ID` exists in `targets.registry` and its `kind` is
   `design_system`.
4. In `location_strategy=melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

If it fails, finish with `blocked_input`.

> ℹ️ **The Topology gate is not tracked by telemetry.** It is pure domain validation and runs before the workflow instance is minted (or before its first tracked phase, at the agent's discretion). Its success is a precondition for PHASE 0; its failure with `blocked_input` stops the run entirely — no `pragma-ai workflow report` calls are emitted for it.

## User Inputs

`hu_id` is **required**: it identifies the user story this refactor belongs to
and is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied, the
workflow refuses to start.

```text
@ds-orchestrator /refactor-component
hu_id: US-12345
component_path: lib/src/organisms/cards/product_card.dart
refactor_goal: Extract the header into a separate molecule and add support for the compact variant.
compatibility_policy: no_public_api_change
evidence_mode: minimal
```

## Execution Sequence

### PHASE 0 — Mobile Spec Packet (`mini`)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
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

The spec records target component, refactor intent, compatibility constraints
in `constraints.compatibility`, success criteria,
expected tests/goldens, permissions per agent and sections that each agent must
read.

> ⚡ **MANDATORY (success path)** — Report `finished` with all four packet artifacts. Substitute `${SPEC_PACKET_PATH}` with the resolved run path:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-0-spec-packet \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/review.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/validation-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.

---

### PHASE 1 — Current Component Analysis

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-1-current-component-analysis \
  --status started
```

**Agent**: `@component-planner`

Required output: update in `spec.yaml` `current_state`,
`impact_analysis`, `inventory` and `artifact_plan`.

> ⚡ **MANDATORY (success path)** — Report `finished`. This phase updates `spec.yaml` in place — declare it as the output file so the gap report can diff this phase's contribution:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-1-current-component-analysis \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.

---

### PHASE 2 — Technical Refactor Plan

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-2-technical-refactor-plan \
  --status started
```

**Agent**: `@component-architect`

Required output: update in `spec.yaml` `technical_plan`,
`success_criteria` and `handoffs`.

> ⚡ **MANDATORY (success path)** — Report `finished`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-2-technical-refactor-plan \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.5.

---

### PHASE 2.1 — Validation + Human Review

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-2-1-validation-human-review \
  --status started
```

**Skill**: `mobile-sdd-spec-validation`

Present:
1. impact analysis
2. change plan
3. breaking changes, if any
4. success criteria from `review.md`

Wait for explicit approval. Do not apply changes until `context.json`
marks the spec as approved.

> ⚡ **MANDATORY (conditional)** — If the spec fails schema/business validation and cannot continue:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-2-1-validation-human-review \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` once validation passes and the human review is presented (approval itself happens in the gate that follows):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-2-1-validation-human-review \
  --status finished
```

> **Stop here.** This is the **domain aggregate approval gate** for the planning set (PHASE 0 through PHASE 2). If the human requests changes to `current_state`, `impact_analysis`, `inventory`, `artifact_plan`, `technical_plan`, `success_criteria` or `handoffs`, the flow must return to the phase that owns that section: report `re_started` on the affected earlier phase, apply changes, report `finished` again for that phase, re-run its gap report, and re-enter PHASE 2.1 (`re_started` → `finished` on `phase-2-1-validation-human-review`). Only when `context.json` marks the spec as approved may PHASE 3 begin. *(PHASE 2.1 produces no new output files — no gap report required.)*

---

### PHASE 3 — Apply Changes

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-3-apply-changes \
  --status started
```

**Agent**: `@widget-developer`
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: refactor_component
read_sections:
  - technical_plan
  - artifact_plan
  - constraints.compatibility
  - success_criteria
```

Rules:
- Preserve backward compatibility when viable.
- If there are transition APIs, use `@Deprecated`.
- Restrict changes to the resolved root for `artifact_plan.planned[].target_id`.

> ⚡ **MANDATORY (success path)** — Report `finished` with one `--output-file` per file declared in `artifact_plan.planned[]`. Paths must be relative to `--project-dir` (project root). Expand the array from the spec:

```bash
# Build --output-file flags from the artifact plan
REFACTOR_FILE_FLAGS=()
while IFS= read -r f; do
  REFACTOR_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[].file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-3-apply-changes \
  --status finished \
  "${REFACTOR_FILE_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 3.5.

---

### PHASE 3.1 — Audit

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-3-1-audit \
  --status started
```

**Agent**: `@code-auditor`

Required output: `evidence/audit-report.md` and a summary in the human report.

> ⚡ **MANDATORY (conditional)** — If the audit surfaces blockers that cannot be resolved (compatibility break with `no_public_api_change`, technical vector violation, or any other audit rule that cannot be corrected by looping with `@widget-developer`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-3-1-audit \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the audit evidence:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-3-1-audit \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/audit-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4a.

---

### PHASE 4.1 — Update Widget Tests

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-4-1-widget-tests \
  --status started
```

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGET_TESTS`)

> ⚡ **MANDATORY (conditional)** — If updated widget tests cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-4-1-widget-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed without passing widget test evidence.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated test files and the widget-tests evidence. Expand the array from `artifact_plan.planned[group=ds_widget_tests]`:

```bash
DS_TEST_FLAGS=()
while IFS= read -r f; do
  DS_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_widget_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-4a-widget-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/widget-tests.md" \
  "${DS_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4b (only when the refactor has visual impact) or directly to PHASE 5.

---

### PHASE 4.2 — Update Golden Tests (if visual impact)

> ⚡ **MANDATORY only when the refactor has visual impact** (as classified by the plan and audit). When the change has no visual impact, skip this phase entirely — do not emit `started`/`finished` for it.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-4-2-golden-tests \
  --status started
```

**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_GOLDEN_TESTS`)

> ⚡ **MANDATORY (conditional)** — If golden tests were required (visual impact) but cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-4-2-golden-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed with a failing golden outcome when visual impact is declared.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated golden files and the golden-tests evidence:

```bash
DS_GOLDEN_FLAGS=()
while IFS= read -r f; do
  DS_GOLDEN_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_golden_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-4b-golden-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/golden-tests.md" \
  "${DS_GOLDEN_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 5.

---

### PHASE 5 — Delivery

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-5-delivery \
  --status started
```

**Agent**: `@delivery-manager`

Required output: `evidence/delivery-report.md` and a summary in the human report.

> ⚡ **MANDATORY (conditional)** — If delivery preconditions are not met (missing/failing widget test evidence, inconsistent golden outcome, or compatibility policy violation):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-5-delivery \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the delivery report:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-5-delivery \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/delivery-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** — the workflow is complete.

## Verification (topology-aware)

- `single_repo` or `multi_repo`:
  - `flutter analyze`
  - `flutter test`
  - `flutter test --tags golden`
- `monorepo_melos`:
  - `melos exec --scope={monorepo.target_scope} -- flutter analyze`
  - `melos exec --scope={monorepo.target_scope} -- flutter test`
  - `melos exec --scope={monorepo.target_scope} -- flutter test --tags golden`

## Rules

- Do not apply changes before approving `review.md`.
- `spec.yaml` is the machine source; `PIPELINE_SPEC_PATH` remains a readable
  cumulative report.
- Handoffs by reference; do not copy full analysis between agents.
- Validate `agent_permissions` before create, modify or delete files.

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

> **PHASE 2.5 aggregate rejection.** When PHASE 2.5 hosts the plan-approval decision, a rejection of a specific planning section (current state, impact analysis, inventory, artifact plan, technical plan, success criteria, handoffs) must first replay the phase that owns that section: report `re_started` on the affected earlier phase (PHASE 1 or PHASE 2), regenerate its output, report `finished` again with the same `--output-file` set, re-run that phase's gap report, and then report `re_started` → `finished` on PHASE 2.5 itself before re-entering this gate. Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

> ⚡ **MANDATORY** — On rejection, example using `phase-3-apply-changes`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-3-apply-changes \
  --status re_started

# 2. ... regenerate the artifacts ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
REFACTOR_FILE_FLAGS=()
while IFS= read -r f; do
  REFACTOR_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[].file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-component \
  --step-id phase-3-apply-changes \
  --status finished \
  "${REFACTOR_FILE_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow:
> `phase-0-spec-packet`, `phase-1-current-component-analysis`, `phase-2-technical-refactor-plan`, `phase-3-apply-changes`, `phase-3-5-audit`, `phase-4a-widget-tests`, `phase-4b-golden-tests` (only when executed), `phase-5-delivery`.
> `phase-2-5-validation-human-review` does NOT run a gap report. The Topology gate is not tracked by telemetry at all.

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
| `pragma-ai workflow create --workflow-id refactor-component --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each executed phase begins (PHASE 0–5; `phase-4b-golden-tests` only when the refactor has visual impact) |
| `pragma-ai workflow report ... --step-id phase-2-5-validation-human-review --status finished` | On completion of the validation + human review phase (no `--output-file`) |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of file-producing phases: `phase-0-spec-packet`, `phase-1-current-component-analysis`, `phase-2-technical-refactor-plan`, `phase-3-apply-changes`, `phase-3-5-audit`, `phase-4a-widget-tests`, `phase-4b-golden-tests` (when executed), `phase-5-delivery` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When `phase-2-5-validation-human-review` cannot validate, `phase-3-5-audit` hits an unresolvable blocker, widget/golden tests can't pass (`phase-4a-widget-tests`, `phase-4b-golden-tests`), or delivery preconditions fail (`phase-5-delivery`) — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably PHASE 2.5 aggregate rejection) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding file-producing step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
