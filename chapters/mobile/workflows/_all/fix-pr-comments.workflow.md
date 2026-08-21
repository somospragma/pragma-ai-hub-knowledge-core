---
id: fix-pr-comments
version: 1.3.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: ds-orchestrator
input_contract: ../docs/templates/spec-packets/fix-pr-comments.overlay.yaml
invocation_mode: explicit_agent
description: Deterministic workflow to fix Pull Request comments in a traceable way. Use it when actionable review feedback already exists.
---
# Workflow: Fix PR Comments

## Telemetry — Workflow metadata

| Field | Value |
|---|---|
| `workflow-id` | `fix-pr-comments` |
| `user-story-id` | Value of the required `hu_id` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `phase-0-spec-packet`, `phase-1-analyze-comments`, `phase-1-1-validation-human-review`, `phase-2-apply-code-fixes`, `phase-3-audit-comment-coverage`, `phase-4-1-widget-tests`, `phase-4-2-golden-tests`, `phase-5-delivery` |

> **NON-NEGOTIABLE RULE:** Every `pragma-ai workflow ...` command in this document is **MANDATORY** to execute. The agent MUST run them — they are not suggestions or documentation.

> ⛔ **STEP-ID INTEGRITY (NON-NEGOTIABLE):** The `--step-id` and `--workflow-id` values shown in every command block below are the **ONLY** valid identifiers for this workflow. The agent MUST copy them **verbatim** from this document — never invent, abbreviate, translate, paraphrase, pluralize, capitalize differently, or otherwise modify them.
>
> - Every `--step-id` submitted to `pragma-ai workflow report` or `pragma-ai workflow gap-report` MUST match one entry in the **"Step IDs"** list above, character-for-character (kebab-case, lowercase, exact spelling).
> - Every `--workflow-id` MUST be exactly `fix-pr-comments`.
> - If a step-id you need is not in the list, STOP and ask the user — do not fabricate one.
> - The CLI rejects unknown step-ids; a wrong id silently corrupts the run's telemetry.

> Each step ends with a **human approval gate** before the gap report (see *Human approval gate* at the end of this document). PHASE 1.1 is the domain aggregate approval gate for the planning set (PHASE 0 and PHASE 1).
> **Pre-flight checks are excluded from telemetry.** The Topology gate and the "no accessible comments" precondition (see *Prerequisites*) run before the workflow instance is minted and stop the run with `blocked_input` when they fail (no telemetry emitted).
> The **gap report only runs on steps that produce output files** (`--output-file`). `phase-1-1-validation-human-review` does NOT run a gap report.
> Two phases are conditional and emit telemetry only when executed: `phase-4-1-widget-tests` (requires the plan/audit to classify fixes as having functional impact) and `phase-4-2-golden-tests` (requires visual impact).
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
  --workflow-id fix-pr-comments \
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

- URL of the PR.
- Accessible comments through conversation, exported file or integration.
  Record the source in `spec.yaml.inputs.pr_comments_source` with:
  `kind: pr_url | inline | exported_file | integration`, `value` and
  `access_status`.
- `.sopp/config/project.config.yaml` valid.
- Context resolved by the orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `ACTIVE_TARGET_ID` per affected file
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH = {targets.registry[app].root}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {targets.registry[app].root}/{pipeline.output_dir}/{pipeline.log_file}`
  - `SPEC_PACKET_PATH = {targets.registry[app].root}/{pipeline.output_dir}/specs/pr-comments-{pr_id}`

If there are no accessible comments, finish with `blocked_input`.

> ℹ️ **This precondition is not tracked by telemetry.** It runs before the workflow instance is minted; a `blocked_input` here stops the run before any `pragma-ai workflow report` call is emitted.

## User Inputs

`hu_id` is **required**: it identifies the user story this PR-fix run belongs
to and is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied,
the workflow refuses to start.

```text
@ds-orchestrator /fix-pr-comments
hu_id: <user story id, e.g. US-12345>  # required
pr_comments_source:
  kind: <pr_url|inline|exported_file|integration>
  value: <url|inline comments|path/to/comments.md|integration id>
  access_status: available
pr_id: <123>                         # optional
target_branch: <branch_name>         # optional
allow_git_commands: false            # optional, default false
allow_gh_commands: false             # optional, default false
evidence_mode: minimal                # optional, default minimal
```

## Topology Gate

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate roots (`PROJECT_ROOT` and each affected target).
3. In targets `location_strategy=melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

> ℹ️ **The Topology gate is not tracked by telemetry.** It is pure domain validation and runs before the workflow instance is minted (or before its first tracked phase, at the agent's discretion). Its success is a precondition for PHASE 0; its failure with `blocked_input` stops the run entirely — no `pragma-ai workflow report` calls are emitted for it.

## Canonical Sequence

### PHASE 0 — Mobile Spec Packet (`mini`)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
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

The spec records the PR URL/source, accessible comments, comment-to-action
matrix, success criteria, permissions per agent, and allowed categories.

> ⚡ **MANDATORY (success path)** — Report `finished` with all four packet artifacts. Substitute `${SPEC_PACKET_PATH}` with the resolved run path:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-0-spec-packet \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/review.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/validation-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.

---

### PHASE 1 — Analyze comments and build the plan

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-1-analyze-comments \
  --status started
```

**Agent**: `@component-planner`

Steps:
1. Classify comments by type: `[VISUAL]`, `[LOGIC]`, `[DOCS]`, `[TESTS]`, `[STYLE]`.
2. Map comment → file/affected area.
3. Create a prioritized plan.

Required output: update `comment_inventory`, `correction_plan`,
`artifact_plan`, and `success_criteria` in `spec.yaml`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated spec:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-1-analyze-comments \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.1.

---

### PHASE 1.1 — Validation + Human Review

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-1-1-validation-human-review \
  --status started
```

**Skill**: `mobile-sdd-spec-validation`

Validate `spec.yaml` and present `review.md` in Spanish with:

1. comments grouped by category
2. affected files
3. proposed changes
4. required tests, goldens and documentation

Wait for explicit approval before applying fixes.

> ⚡ **MANDATORY (conditional)** — If the spec fails schema/business validation and cannot continue:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-1-1-validation-human-review \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` once validation passes and the human review is presented (approval itself happens in the gate that follows):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-1-1-validation-human-review \
  --status finished
```

> **Stop here.** This is the **domain aggregate approval gate** for the planning set (PHASE 0 and PHASE 1). If the human requests changes to `comment_inventory`, `correction_plan`, `artifact_plan`, or `success_criteria`, the flow must return to the phase that owns that section: report `re_started` on `phase-1-analyze-comments`, regenerate its output, report `finished` again with `--output-file "${SPEC_PACKET_PATH}/spec.yaml"`, re-run its gap report, and re-enter PHASE 1.1 (`re_started` → `finished` on `phase-1-1-validation-human-review`). Only when the plan is explicitly approved may PHASE 2 begin. *(PHASE 1.1 produces no new output files — no gap report required.)*

---

### PHASE 2 — Apply code fixes

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-2-apply-code-fixes \
  --status started
```

**Agent**: `@widget-developer`
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: pr_comment_fixes
read_sections:
  - inputs.pr_comments_source
  - correction_plan
  - artifact_plan
  - success_criteria
```

Category coverage:
- `[VISUAL]`, `[LOGIC]`, `[STYLE]` → Phase 2
- `[TESTS]` → Phase 4.1/4.2
- `[DOCS]` → Phase 5

> ⚡ **MANDATORY (success path)** — Report `finished` with every file declared in `artifact_plan.planned[]` for the code-fix scope ([VISUAL], [LOGIC], [STYLE] categories — [TESTS] fixes go in PHASE 4.1/4.2 and [DOCS] fixes go in PHASE 5). Expand the array from the spec:

```bash
FIX_FILE_FLAGS=()
while IFS= read -r f; do
  FIX_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.category=="visual" or .category=="logic" or .category=="style") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-2-apply-code-fixes \
  --status finished \
  "${FIX_FILE_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 3.

---

### PHASE 3 — Audit comment coverage

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-3-audit-comment-coverage \
  --status started
```

**Agent**: `@code-auditor`

- Verify matrix comment-to-fix.
- If missing coverage, loop with `@widget-developer`.
- Write `evidence/audit-report.md`.

> ⚡ **MANDATORY (conditional)** — If the audit loop exceeds `pipeline.max_audit_retries` without resolving the comment-to-fix coverage matrix:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-3-audit-comment-coverage \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the audit evidence:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-3-audit-comment-coverage \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/audit-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.1 (only when the fixes have functional impact), PHASE 4.2 (only when they have visual impact), or directly to PHASE 5 when neither applies.

---

### PHASE 4.1 — Update Widget Tests (if functional impact)

> ⚡ **MANDATORY only when the fixes have functional impact** (as classified by the plan and audit). When there is no functional impact, skip this phase entirely — do not emit `started`/`finished` for it.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-4-1-widget-tests \
  --status started
```

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGET_TESTS`)

> ⚡ **MANDATORY (conditional)** — If updated widget tests cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-4-1-widget-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed without passing widget test evidence for the functional-impact fixes.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated test files and the widget-tests evidence. Expand the array from `artifact_plan.planned[group=widget_tests]`:

```bash
WIDGET_TEST_FLAGS=()
while IFS= read -r f; do
  WIDGET_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="widget_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-4-1-widget-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/widget-tests.md" \
  "${WIDGET_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.2 (only when the fixes have visual impact) or directly to PHASE 5.

---

### PHASE 4.2 — Update Golden Tests (if visual impact)

> ⚡ **MANDATORY only when the fixes have visual impact** (as classified by the plan and audit). When there is no visual impact, skip this phase entirely — do not emit `started`/`finished` for it.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-4-2-golden-tests \
  --status started
```

**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_GOLDEN_TESTS`)

> ⚡ **MANDATORY (conditional)** — If updated golden tests cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-4-2-golden-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed with a failing golden outcome for the visual-impact fixes.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated golden files and the golden-tests evidence. Expand the array from `artifact_plan.planned[group=golden_tests]`:

```bash
GOLDEN_TEST_FLAGS=()
while IFS= read -r f; do
  GOLDEN_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="golden_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-4-2-golden-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/golden-tests.md" \
  "${GOLDEN_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 5.

---

### PHASE 5 — Delivery

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-5-delivery \
  --status started
```

**Agent**: `@delivery-manager`

- Apply `[DOCS]` fixes from the plan.
- Suggest commit message text by fix type; do not run `git` or create commits.
- Coverage summary comments.
- Final Verification topology-aware.

Required output: `evidence/delivery-report.md`, human report and log.

`delivery-manager` does not run `git`, create branches, or open PRs unless
the user explicitly requests it and `agent_permissions.delivery-manager`
declares the required external tools.

> ⚡ **MANDATORY (conditional)** — If delivery preconditions are not met (missing/failing widget test evidence when functional impact was declared, inconsistent golden outcome when visual impact was declared, or unresolved comment coverage):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-5-delivery \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the delivery report and every [DOCS]-category file declared in `artifact_plan.planned[]`. Expand the array from the spec:

```bash
DOCS_FIX_FLAGS=()
while IFS= read -r f; do
  DOCS_FIX_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.category=="docs") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-5-delivery \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/delivery-report.md" \
  "${DOCS_FIX_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** — the workflow is complete.

## Rules

- Do not apply fixes before approving `review.md`.
- `spec.yaml` is the machine source of the comment-to-action matrix.
- Handoffs by reference; do not copy the entire feedback of the PR between agents.
- Validate `agent_permissions` before creating, modifying, or deleting files.

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

> **PHASE 1.1 aggregate rejection.** When PHASE 1.1 hosts the plan-approval decision, a rejection of a specific planning section (comment inventory, correction plan, artifact plan, success criteria) must first replay `phase-1-analyze-comments`: report `re_started`, regenerate its output, report `finished` again with `--output-file "${SPEC_PACKET_PATH}/spec.yaml"`, re-run its gap report, and then report `re_started` → `finished` on PHASE 1.1 itself before re-entering this gate.

> Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

> ⚡ **MANDATORY** — On rejection, example using `phase-2-apply-code-fixes`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-2-apply-code-fixes \
  --status re_started

# 2. ... regenerate the code fixes ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
FIX_FILE_FLAGS=()
while IFS= read -r f; do
  FIX_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.category=="visual" or .category=="logic" or .category=="style") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id fix-pr-comments \
  --step-id phase-2-apply-code-fixes \
  --status finished \
  "${FIX_FILE_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow:
> `phase-0-spec-packet`, `phase-1-analyze-comments`, `phase-2-apply-code-fixes`, `phase-3-audit-comment-coverage`, `phase-4-1-widget-tests` (only when executed), `phase-4-2-golden-tests` (only when executed), `phase-5-delivery`.
> `phase-1-1-validation-human-review` does NOT run a gap report. The Topology gate and the "no accessible comments" precondition are not tracked by telemetry at all.

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
| `pragma-ai workflow create --workflow-id fix-pr-comments --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each executed step begins (PHASE 0, 1, 1.1, 2, 3, 5; `phase-4-1-widget-tests` only if fixes have functional impact; `phase-4-2-golden-tests` only if fixes have visual impact) |
| `pragma-ai workflow report ... --step-id phase-1-1-validation-human-review --status finished` | On completion of the aggregate planning-approval checkpoint (no `--output-file`) |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of file-producing phases: `phase-0-spec-packet`, `phase-1-analyze-comments`, `phase-2-apply-code-fixes`, `phase-3-audit-comment-coverage`, `phase-4-1-widget-tests` (when executed), `phase-4-2-golden-tests` (when executed), `phase-5-delivery` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When `phase-1-1-validation-human-review` cannot validate, `phase-3-audit-comment-coverage` exhausts retries, widget/golden tests can't pass (`phase-4-1-widget-tests`, `phase-4-2-golden-tests`), or delivery preconditions fail (`phase-5-delivery`) — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably PHASE 1.1 aggregate rejection cascading back to PHASE 1) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding file-producing step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
