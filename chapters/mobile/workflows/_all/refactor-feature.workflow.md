---
id: refactor-feature
version: 2.1.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: refactoring-advisor
input_contract: ../docs/templates/spec-packets/refactor-feature.overlay.yaml
invocation_mode: explicit_agent
description: >
  Workflow for refactoring an existing feature that already follows Clean Architecture (or close to it). Analyzes code smells, architectural violations, and complexity — then executes incremental improvements that keep the app compiling at every stage. Not for DS components (use /refactor-component) or legacy rewrites from scratch.
---
# Workflow: Refactor Feature (Evolutionary Improvement)

## Telemetry — Workflow metadata

| Field | Value |
|---|---|
| `workflow-id` | `refactor-feature` |
| `user-story-id` | Value of the required `hu_id` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `phase-0-plan-review`, `phase-1-apply-verify`, `phase-2-documentation` |

## Workflow Execution Contract

**This document is not reference material — you are executing it.** Every fenced `bash` block is a real shell tool call your agent MUST issue. Do not paraphrase, summarize, describe, or narrate them; emit the exact command via your shell tool.

The following rules bind every phase in this workflow and are enforced by the Response Contract embedded at the top of each phase:

1. **Telemetry integrity.** Every executed phase emits exactly one `--status started` before its work and exactly one terminal status on completion — `--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when the human rejects and the phase must be regenerated — via `pragma-ai workflow report`. Skipping any of these is a workflow violation.
2. **Step-id and phase-name integrity.** The `--step-id` and `--workflow-id` values are the ONLY valid identifiers. Copy them **verbatim** from the `Step IDs` table above — never invent, translate, abbreviate, paraphrase, pluralize, or re-case them. `--workflow-id` MUST be exactly `refactor-feature`. The CLI silently rejects unknown step-ids. This also governs every phase name you narrate, header, or put in an approval prompt: it MUST match, verbatim, a `### PHASE` header (or its embedded `#### Step`) tied to one of the `Step IDs` above. Never execute, narrate, or present a phase that is not in that table — including a phase from a previous version of this document, from memory, or from a different workflow. If a phase you are about to run does not appear there, stop and re-read the `Step IDs` table before continuing.
3. **Human approval per phase.** After every `finished`, present the approval prompt block (Aprobado / Ediciones / Rechazado) VERBATIM as the last thing in your response and yield. Silence is not approval. `phase-0-plan-review`'s final sub-step (Checkpoint) is the human decision point for the whole merged planning phase (Spec Packet, Analysis, Impact Analysis, Refactoring Plan); `phase-1-apply-verify` additionally has an internal REQUIRED CHECKPOINT per architectural step, embedded in its Execution sub-step: report `--status paused` on reaching each such checkpoint (a real, CLI-supported status distinct from `re_started`) and only continue once the human explicitly approves. See *Human approval gate* for the rejection replay protocol.
4. **Gap report per phase.** After the human approves a phase, run the two-phase gap report against the same step-id — every step-id in this workflow produces files when executed. The Topology gate is not tracked by telemetry at all and never runs a gap report.
5. **Conditional phases.** This workflow has no fully conditional phases (every phase executes when its predecessors do). The Topology gate stops the run before minting when it fails.
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
  --workflow-id refactor-feature \
  --inputs-file "$WORKFLOW_INPUTS_FILE"

# The preflight succeeded; use the explicitly supplied hu_id for telemetry.
USER_STORY_ID="$hu_id"

# Persist only after a valid invocation has started.
echo "$USER_STORY_ID" > output/.active-user-story

# Mint the instance.
INSTANCE_ID=$(pragma-ai workflow create \
  --workflow-id refactor-feature \
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

## When to Use

Use this workflow when:

- The feature already exists and follows Clean Architecture (or partially)
- The user wants to improve structure without rewriting from scratch
- The BLoC is too large and needs splitting
- A use case is inline in the BLoC and needs extraction
- The feature needs to be moved to a Melos package
- Patterns need updating (dartz→fpdart, fold→match, Freezed 2→3)
- Layers have violations (presentation importing data, BLoC calling DataSource)
- The feature needs a new endpoint/entity added to existing structure

Do NOT use for:
- DS component refactoring (use `/refactor-component`)
- Creating a new feature from scratch (use `/new-feature`)
- Adding tests to existing code (use `/test-plan`)

---

## Prerequisites

- Feature path provided by the user (must exist and contain code)
- `.sopp/config/project.config.yaml` valid (or run `/bootstrap-workspace` first)
- Context resolved:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `ACTIVE_TARGET_ID` (`app` or feature target)
  - `ACTIVE_TARGET_ROOT = targets.registry[ACTIVE_TARGET_ID].root`
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH`
  - `PIPELINE_LOG_PATH`
  - `SPEC_PACKET_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/specs/{feature_name}-refactor`

---

## Gate — Topology (mandatory)

1. Validate `TOPOLOGY_REPO_MODE` (`single_repo | monorepo_melos | multi_repo`).
2. Validate `PROJECT_ROOT` and `ACTIVE_TARGET_ROOT` are accessible.
3. Validate `feature_path` exists and contains Dart files.
4. Validate each affected file maps to an allowed `target_id`.
5. If `location_strategy=melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

If any validation fails, terminate with `blocked_input`.

> ℹ️ **The Topology gate is not tracked by telemetry.** It is pure domain validation and runs before the workflow instance is minted (or before its first tracked phase, at the agent's discretion). Its success is a precondition for PHASE 0; its failure with `blocked_input` stops the run entirely — no `pragma-ai workflow report` calls are emitted for it.

---

## Inputs

`hu_id` is **required**: it identifies the user story this refactor belongs to
and is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied, the
workflow refuses to start.

```text
@refactoring-advisor /refactor-feature
hu_id: US-12345
feature_name: checkout
feature_path: lib/src/features/checkout/
refactor_goal: Split the CheckoutBloc into CartBloc and PaymentBloc, extract coupon validation to a use case
constraints: Don't change the API contract, keep route paths the same
user_story: docs/hus/user story-078.md  (optional — contains acceptance criteria + DoD)
target_location: same | melos_package
sequence_diagram: docs/diagrams/checkout_flow.mmd  (optional)
evidence_mode: minimal  (optional; default minimal)
```

### Input variations

> Note: every variation below still requires `hu_id` as its first line, just like the main example above.

```text
# Simple refactor (most common)
@refactoring-advisor /refactor-feature
hu_id: US-12345
feature_name: checkout
feature_path: lib/src/features/checkout/
refactor_goal: The BLoC is too large, needs splitting

# Package extraction
@refactoring-advisor /refactor-feature
hu_id: US-12345
feature_name: payments
feature_path: lib/src/features/payments/
refactor_goal: Extract to a standalone Melos package
target_location: melos_package
package_name: payments

# Pattern update
@refactoring-advisor /refactor-feature
hu_id: US-12345
feature_name: auth
feature_path: lib/src/features/auth/
refactor_goal: Replace dartz with fpdart, update Freezed to 3.x syntax

# Add endpoint to existing feature
@refactoring-advisor /refactor-feature
hu_id: US-12345
feature_name: products
feature_path: lib/src/features/products/
refactor_goal: Add DELETE /products/:id endpoint to existing feature
api_contract: |
  DELETE /products/:id -> void (204)
```

---

## Execution Sequence

### PHASE 0 — Plan + Review

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call **once**, before Step 1.
> 2. Do the work described under Steps 1–5 below, in order.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 1 until the user replies.
>
> ```
> He completado PHASE 0 — Plan + Review. ¿Apruebas el resultado?
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
  --workflow-id refactor-feature \
  --step-id phase-0-plan-review \
  --status started
```

#### Step 1 — Mobile Spec Packet (`full`)

**Agent:** `@refactoring-advisor`
**Skill:** `mobile-sdd-spec-validation`

Create `SPEC_PACKET_PATH` with:

1. `spec.yaml` (`schema_ref: ../docs/templates/schemas/mobile-spec.schema.yaml`,
   `spec_level: full`, `execution_mode: propose_then_apply`)
2. `context.json`
3. `review.md` in Spanish
4. `evidence/validation-report.md`

The initial spec records feature name, feature path, refactor goal, constraints, risk policy,
expected checkpoints, `agent_permissions` and success criteria. It is enriched
by Steps 2–4 before execution approval.

#### Step 2 — Analysis

**Agent:** `@refactoring-advisor`

Steps:
1. Read all files in `feature_path` recursively
2. Map the current architecture:
   - Layers present (domain / data / presentation)
   - State management pattern
   - Error handling approach
   - DI mechanism
   - Freezed version/syntax
3. Detect code smells and violations:
   - Layer dependency violations
   - God classes (>300 lines or >5 responsibilities)
   - Missing abstractions (concrete where interface expected)
   - Outdated patterns (dartz, fold, Freezed 2.x, Provider)
   - DI issues (manual instantiation, missing annotations)
   - Error handling gaps (raw try/catch, hardcoded messages)
   - Dead code (unused imports, commented blocks)
4. Count existing tests and map coverage
5. Map internal dependency graph (who imports whom)

Output: `evidence/refactoring-analysis.md`.
Update `spec.yaml` sections `current_state`, `issues`, `test_inventory` and
`dependency_graph`.

#### Step 3 — Impact Analysis

**Agent:** `@refactoring-advisor`

Steps:
1. List all files that will be affected
2. Identify external dependents (other features importing from this one)
3. Assess breaking changes:
   - Public API changes (exported classes/functions)
   - DI registration changes (other modules depending on these registrations)
   - Route changes (navigation from other features)
4. Identify tests that will need updates vs tests that should still pass
5. Rate overall risk: `low` | `medium` | `high`

Output: update `spec.yaml` sections `impact_analysis`, `risk`,
`breaking_changes` and `affected_artifacts`.

#### Step 4 — Refactoring Plan

**Agent:** `@refactoring-advisor`

Steps:
1. Decompose the refactoring into atomic steps
2. Each step MUST leave the app in a compilable state
3. Order band:
   - Dependencies (prerequisites first)
   - Risk (lowest first)
   - Type (additive → structural → destructive)
4. For each step specify:
   - Action (extract, split, move, rename, replace, delete)
   - Files created / modified / deleted
   - Risk level (low / medium / high)
   - Reversibility (✅ / ⚠️)
   - Verification command

Output: update `spec.yaml` sections `refactoring_plan`, `execution_steps`,
`success_criteria` and `handoffs`.

The plan must also update `spec.yaml.artifact_plan.planned` with every created,
modified, moved or deleted file. Mandatory documentation outputs must be
included with `group: docs`, including:

- `docs/refactoring/{feature_name}-refactoring-{YYYY-MM-DD}.md`
- every project documentation file that PHASE 2 may create or modify

If any planned artifact has `action: delete`, the spec must explicitly set
`agent_permissions.refactoring-advisor.can_delete_files=true` and record the
human approval that enabled the destructive action. Without that elevation,
delete actions remain blocked.

#### Step 5 — Checkpoint (Validation + Human Review)

**Agent:** `@refactoring-advisor`

Present to the user:
1. Analysis summary (current state + issues found)
2. Impact analysis (files affected, breaking changes, risk)
3. Refactoring plan (ordered steps with risk ratings)
4. `review.md` in Spanish with criteria, checkpoints and evidence expected

Question:
"I've analyzed the feature and prepared a refactoring plan with {N} atomic steps (risk: {level}). Want me to proceed with execution?"

**Do NOT proceed without explicit approval.** This step's presentation is the human decision point for the whole phase. If the user requests changes to a specific section, regenerate the sub-step that owns it (Step 1, 2, 3 or 4) in place and re-present Step 5 before continuing — see *Human approval gate*.

> ⚡ **MANDATORY (success path)** — Report `finished` with all packet artifacts, including the analysis evidence produced in Step 2. Substitute `${SPEC_PACKET_PATH}` with the resolved run path:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-0-plan-review \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/review.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/validation-report.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/refactoring-analysis.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.

---

### PHASE 1 — Apply + Verify

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call **once**, before Step 1 — not per plan step.
> 2. Do the work described under Steps 1–3 below, in order, running the embedded REQUIRED CHECKPOINT per architectural step where applicable (inside Step 1) — emit `--status paused` each time that checkpoint is reached, before yielding to the user.
> 3. Once Step 3 (Audit) has completed, emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Do not begin PHASE 2 until the user replies.
>
> ```
> He completado PHASE 1 — Apply + Verify. ¿Apruebas el resultado?
>   1. ✅ Aprobado — continuar
>   2. ✏️ Ediciones — dime qué cambiar
>   3. ❌ Rechazado — regenerar desde cero
> ```
>
> Silence is not approval. Continuing past step 5 without a user reply is a workflow violation.

> ⚡ **EXECUTE NOW** — Run the command below via your shell tool once, before Step 1 (not per plan step). Do not narrate; do not paraphrase.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-1-apply-verify \
  --status started
```

#### Step 1 — Execution (iterative)

**Agent:** `@refactoring-advisor`
Mandatory compact handoff per step:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: refactor_execution
step: <step_id>
read_sections:
  - refactoring_plan
  - execution_steps.<step_id>
  - success_criteria
  - impact_analysis
  - risk
```

For each step in the approved plan:

1. **Execute** the change
2. **Verify compilation**:
   - `single_repo`: `flutter analyze --fatal-infos`
   - `monorepo_melos`: `melos exec --scope={target_scope} -- "flutter analyze --fatal-infos"`
3. **Verify DI** (if annotations changed):
   - `dart run build_runner build --delete-conflicting-outputs`
4. **Run existing tests**:
   - `flutter test {feature_path}` (or scoped with Melos)
5. **Assess test results**:
   - All pass → continue to next step
   - Expected failures (structural change) → queue for Step 2
   - Unexpected failures (regression) → revert step, reassess plan
6. **Log** step completion
7. **Update context** in `SPEC_PACKET_PATH/context.json`

If a step fails compilation:
- Fix immediately (do not move to next step)
- If fix requires plan adjustment, re-present to user

Output: Execution log per step in `PIPELINE_LOG_PATH`.

##### REQUIRED CHECKPOINT — After Each Architectural Step

If a step changes public API, DI, route behavior, layer boundaries, package
location or data contracts, present a compact Spanish review and wait for
approval before continuing.

> ⚡ **MANDATORY** — Emit this as soon as the review above is presented, before yielding to the user:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-1-apply-verify \
  --status paused
```

Operational note: `paused` (not `re_started`) is correct here — the phase already reported `started` once before Step 1 and has not yet produced Step 1's overall output or reached `finished`. This may repeat once per qualifying architectural step; each occurrence just records another wait-for-human event against the same step-id.

> **IMPORTANT: After completing ALL refactoring steps, you are NOT done.**
> You MUST continue to Step 2 (tests) and Step 3 (audit) of this same phase, then to PHASE 2 (documentation).
> The refactoring is incomplete without tests, audit and the documentation file.

> ⚡ **MANDATORY (conditional)** — If a step causes an unrecoverable compilation failure, an unrevertible test regression, or a plan-invalidating conflict that cannot be resolved by re-presenting the plan for adjustment:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-1-apply-verify \
  --status failed
```
> ❌ The workflow stops here.

#### Step 2 — Test Analysis & Coverage (mandatory)

**Agent:** `@refactoring-advisor`

> **This step is NOT optional.** Every refactoring MUST include test analysis
> and generation. A refactoring without verified test coverage is incomplete.

Steps:
1. Locate the test directory for the feature (create if missing)
2. Inventory existing tests (unit, widget, integration)
3. If tests exist: update broken ones (imports, mocks, assertions)
4. **Generate missing tests** for EVERY file that lacks coverage:
   - Domain use cases: success path, failure path, edge cases
   - Data repositories: cache-first logic, error mapping
   - Data mappers: fromModel/toModel with JSON fixtures
   - Data sources: HTTP calls with mocked Dio
   - BLoC: every event → state transition
   - Pages/Widgets: rendering, interactions, state-driven UI
5. Coverage targets (non-negotiable):
   - Domain: 95%+
   - Data: 85%+
   - Presentation BLoC: 85%+
   - Presentation pages: 70%+
6. Test generation rules:
   - `mocktail 1.0.5` for mocking
   - `bloc_test 9.1.7` for BLoC tests
   - AAA pattern (Arrange-Act-Assert)
   - Descriptive names: `should [verb] when [condition]`
   - One test file per source file
   - ALL success AND failure paths covered
7. Run all tests and verify they pass

Output: test files, `spec.yaml.success_criteria.tests` and
`evidence/test-validation.md`.
Persist test evidence under `SPEC_PACKET_PATH/evidence/`.

> ⚡ **MANDATORY (conditional)** — If tests cannot be made to pass or the non-negotiable coverage targets (domain 95%, data 85%, BLoC 85%, pages 70%) cannot be met:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-1-apply-verify \
  --status failed
```
> ❌ The workflow stops here — the refactoring is incomplete without verified test coverage.

#### Step 3 — Audit

**Agent:** `@code-auditor`

Steps:
1. Review all modified/created files against:
   - Clean Architecture dependency rules
   - SOLID principles
   - Dart coding standard
   - Naming conventions
   - DI correctness
2. Verify no regressions introduced:
   - No new layer violations
   - No dead code left behind
   - Barrel exports updated (if package extraction)
   - No unused DI registrations
3. If issues found:
   - Return to `@refactoring-advisor` for corrections
   - Max retries: `pipeline.max_audit_retries` (default: 3)
4. If approved: mark complete

Output: `evidence/audit-report.md` and a summary in the human report.
Audit must explicitly verify modified code against `SPEC_PACKET_PATH/spec.yaml`.

> ⚡ **MANDATORY (conditional)** — If the audit loop exceeds `pipeline.max_audit_retries` without passing, or hits an unresolvable blocker (new layer violation, dead code, unused DI registration, missing barrel export):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-1-apply-verify \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Once Step 3 (Audit) approves, report `finished` with every file declared in `artifact_plan.planned[]` (created, modified, moved or deleted), plus the test and audit evidence. Expand the arrays from the spec:

```bash
# Build --output-file flags from the artifact plan (skip entries with action: delete
# since deleted paths cannot be captured as a baseline; the delete itself is recorded
# in spec.yaml + PIPELINE_LOG_PATH).
REFACTOR_FILE_FLAGS=()
while IFS= read -r f; do
  REFACTOR_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.action != "delete") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

TEST_FILE_FLAGS=()
while IFS= read -r f; do
  TEST_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="unit_tests" or .group=="widget_tests" or .group=="integration_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-1-apply-verify \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/evidence/test-validation.md" \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/evidence/audit-report.md" \
  "${REFACTOR_FILE_FLAGS[@]}" \
  "${TEST_FILE_FLAGS[@]}"
```

> **Stop here.** The embedded **REQUIRED CHECKPOINT — After Each Architectural Step** applies per step during Step 1's iteration; this outer approval gate applies once, at the end of Step 3 (Audit), covering the full executed plan, tests and audit. Once approved, run this step's **gap report** and then continue to PHASE 2.

---

### PHASE 2 — Documentation

> ### ▶ Response Contract (non-negotiable)
>
> Your response for this phase MUST, in order:
>
> 1. Emit the `--status started` command below as a real shell tool call.
> 2. Do the work described under Steps 1–2 below — this phase creates a real refactoring documentation file on disk under `docs/refactoring/`, then updates the project documentation files under `docs/`.
> 3. Emit the terminal status command (`--status finished` on success, `--status failed` on unrecoverable blocker, or `--status re_started` when replaying after rejection) via a real shell tool call, with the exact `--output-file` set below.
> 4. **File-producing phase.** After the human approves, emit the two gap-report commands (Phase A + Phase B) for this same `--step-id`.
> 5. End your response with the block below **verbatim** and yield. Do not add prose after it. Once approved, the workflow is complete.
>
> ```
> He completado PHASE 2 — Documentation. ¿Apruebas el resultado?
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
  --workflow-id refactor-feature \
  --step-id phase-2-documentation \
  --status started
```

#### Step 1 — Report & Documentation

**Agent:** `@refactoring-advisor`

Generate two outputs:

##### 1.1. Pipeline report

```markdown
## Refactoring Report: {feature_name}

### Summary
- **Scope**: refactor
- **Intent**: {user's original intent}
- **Steps executed**: {N}/{total}
- **Files created**: {count}
- **Files modified**: {count}
- **Files deleted**: {count}
- **Tests updated**: {count}
- **Compilation**: ✅
- **Tests**: ✅ all pass
- **Audit**: ✅ approved

### Changes by Step
| # | Action | Files | Status |
|---|---|---|---|
| 1 | Extract ValidateCouponUseCase | +1, ~1 | ✅ |
| 2 | Split CheckoutBloc → CartBloc + PaymentBloc | +2, ~3, -1 | ✅ |
| 3 | Replace fold() with match() | ~6 | ✅ |

### Next Steps
- [ ] Run full test suite: `flutter test`
- [ ] Consider adding tests: `@test-coverage-engineer /test-plan`
- [ ] Update feature documentation if public API changed
- [ ] Verify navigation from other features still works
```

Output: human report summary.

##### 1.2. Refactoring documentation file (mandatory — FILE CREATION action)

> **CRITICAL: This is a FILE CREATION action, not just a report to the user.**
> The agent MUST use the file creation tool to write this file to disk.
> The refactoring is NOT complete until this file exists on disk.

**Action:** Create a NEW file at this EXACT path:
`{PROJECT_ROOT}/docs/refactoring/{feature_name}-refactoring-{YYYY-MM-DD}.md`

This file must already be declared in `artifact_plan.planned[]` with
`target_id=project_docs` or the configured docs target, `owner:
refactoring-advisor` and `group: docs`.

**Steps:**
1. If `docs/refactoring/` directory does not exist → CREATE IT
2. Create the file with: Intent, Before (structure + issues), After (structure + improvements), Rationale, Files Changed table, Test Coverage table
3. VERIFY the file exists on disk after creation

**Example path:** `docs/refactoring/checkout-refactoring-2026-05-08.md`

Output: Documentation file created at `docs/refactoring/`.

#### Step 2 — Project Documentation Update (mandatory)

**Agent:** `@refactoring-advisor` using shared skill `documentation-projects`

**Condition:** Always executes — NEVER skip.

Steps:
1. Resolve documentation directory:
   - If `docs/` exists at `PROJECT_ROOT` → use it
   - If `documentation/` or similar exists → use the existing one
   - Otherwise → create `docs/` at `PROJECT_ROOT`
2. Before invoking the shared skill, update `spec.yaml.artifact_plan.planned`
   with every document that may be created or modified:
   - `target_id: project_docs` or the configured docs target
   - `path: docs/<document>.md` relative to that target
   - `action: create | modify`
   - `owner: refactoring-advisor`
   - `group: docs`
3. Check which of the 7 project documents exist:
   - `index.md`, `project-overview.md`, `requirements.md`, `project-structure.md`,
     `tech-stack.md`, `features.md`, `implementation.md`, `user-flow.md`
4. For **missing documents** → generate from templates using shared skill `documentation-projects`
5. For **existing documents** → update with the refactoring changes:
   - `project-structure.md` → update if folder structure changed (extracted classes, new packages)
   - `features.md` → update feature entry if public API or behavior changed
   - `implementation.md` → update if new patterns, DI modules, or architectural decisions were introduced
   - `tech-stack.md` → update if dependencies were added or removed
   - `user-flow.md` → update if user journeys were affected
6. Propose documentation commit message:
   `docs({feature}): update project documentation after refactoring`

Output: List of created/updated documents in `PIPELINE_LOG_PATH`.

**Skill invocation:** `documentation-projects action=update target={docs_path} documents=all`

The shared skill internally orchestrates `doc-auditor`, `doc-interviewer`,
`doc-generator` and `doc-validator`; the mobile workflow must not reference
legacy generate-docs aliases.

> ⚡ **MANDATORY (success path)** — Report `finished` with the refactoring documentation file and every project documentation file created or modified. Substitute `${REFACTORING_DOC_PATH}` with the actual file created (relative to `--project-dir`, e.g. `docs/refactoring/checkout-refactoring-2026-05-08.md`), and expand the docs array from `artifact_plan.planned[group=docs]`:

```bash
DOCS_FILE_FLAGS=()
while IFS= read -r f; do
  DOCS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="docs") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-2-documentation \
  --status finished \
  --output-file "${REFACTORING_DOC_PATH}" \
  "${DOCS_FILE_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** — the workflow is complete.

---

## Mandatory Post-Execution Checklist

> **The agent MUST complete ALL items below before reporting to the user.
> If any item missing, the refactoring is INCOMPLETE.**

| # | Action | Verification |
|---|---|---|
| A | Generate test files for all untested source files | `flutter test` passes, coverage targets met |
| B | Delegate audit to `@code-auditor` | Audit approved |
| C | Create `docs/refactoring/{feature_name}-refactoring-{date}.md` | File exists on disk (read it back) |
| D | Report final summary to user | Only after A, B, C are done |

---

## Verification (topology-aware)

After all phases:

- `single_repo`:
  ```bash
  flutter analyze --fatal-infos
  dart run build_runner build --delete-conflicting-outputs
  flutter test
  ```
- `monorepo_melos`:
  ```bash
  melos exec --scope={target_scope} -- "flutter analyze --fatal-infos"
  melos exec --scope={target_scope} -- "dart run build_runner build --delete-conflicting-outputs"
  melos exec --scope={target_scope} -- "flutter test"
  ```

---

## Rules

### Completion criteria (ALL must be true)
- [ ] All refactoring steps executed and compiling
- [ ] All tests pass (existing updated + new generated)
- [ ] Coverage targets met (domain 95%, data 85%, BLoC 85%, pages 70%)
- [ ] `@code-auditor` approved
- [ ] Documentation file EXISTS at `docs/refactoring/{feature_name}-refactoring-{date}.md`
- [ ] Project documentation (7 documents) updated via shared skill `documentation-projects`

### Prohibitions
- NEVER skip the analysis phase — always understand before changing
- NEVER make a change that leaves the app in a non-compilable state
- NEVER proceed past PHASE 0's Checkpoint (Step 5) without explicit user approval
- NEVER execute a refactor step before `review.md` is approved
- NEVER delete tests without updating them to match new structure
- NEVER change behavior during refactoring (unless explicitly requested as part of intent)
- NEVER refactor DS components — delegate to `@ds-orchestrator /refactor-component`
- NEVER end without creating the documentation file in `docs/refactoring/`
- NEVER end without generating missing tests in PHASE 1's Test Analysis & Coverage step
- NEVER skip PHASE 2's Project Documentation Update step — it is mandatory after every refactoring

### Obligations
- ALWAYS verify compilation after each atomic step
- ALWAYS run build_runner if DI annotations or Freezed classes changed
- ALWAYS preserve existing test coverage (update broken tests, never delete)
- ALWAYS generate missing tests to meet coverage targets
- ALWAYS use mocktail for mocking and bloc_test for BLoC tests
- ALWAYS delegate to `@code-auditor` for final quality review
- ALWAYS enforce `agent_permissions` from `spec.yaml` before file creation,
  modification, command execution or external tool access
- ALWAYS register each phase in `PIPELINE_LOG_PATH`
- ALWAYS update `SPEC_PACKET_PATH/context.json` after each approved checkpoint
- ALWAYS use compact handoffs by `spec_ref`, `context_ref`, `phase` and
  `read_sections`
- ALWAYS create `docs/refactoring/` directory if it doesn't exist
- ALWAYS create the documentation .md file as the LAST action before reporting completion
- ALWAYS verify the documentation file exists on disk after creating it
- ALWAYS update project documentation (7 documents) in PHASE 2's Project Documentation Update step using shared skill `documentation-projects`
- If a step causes unexpected test failures, REVERT and reassess before continuing

---

## Response Contract Violations

The following are workflow violations. If your response for a phase contains any of them, you have failed the workflow contract for that phase:

- Omitting the `--status started` tool call before starting the phase's work.
- Omitting the terminal status tool call (`--status finished`, `--status failed`, or `--status re_started`) at the end of the phase.
- Emitting `--status finished` without every declared `--output-file` flag (for `phase-0-plan-review`, `phase-1-apply-verify`, `phase-2-documentation`).
- Using a `--step-id` or `--workflow-id` value that does not appear in the `Step IDs` table above, character-for-character.
- Narrating, presenting, or executing a phase (in a header, approval prompt, or telemetry call) whose name does not correspond verbatim to an entry in the `Step IDs` table above — including a phase that existed in a previous version of this document.
- Ending a phase response without the approval prompt block, or adding prose after it.
- Starting the next phase's work before the user has explicitly answered the approval prompt.
- Running the gap report on the Topology gate — it is not a step-id and is never tracked by telemetry.
- Reporting `phase-2-documentation --status finished` without the refactoring documentation file actually created on disk under `docs/refactoring/`.
- Reaching the REQUIRED CHECKPOINT — After Each Architectural Step without emitting `--status paused` for `phase-1-apply-verify` before yielding to the user.

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

> **`phase-0-plan-review` internal rejection.** A rejection of a specific planning section (current state, issues, impact analysis, risk, breaking changes, refactoring plan, execution steps, success criteria, handoffs, artifact plan) presented at Step 5 (Checkpoint) is resolved by regenerating the sub-step that owns that section (Step 1, 2, 3 or 4) in place, within the same step-id, and re-presenting Step 5. No cross-step-id replay is needed, and `finished` is only reported once, after Step 5 is approved.

> **`phase-1-apply-verify` per-step revisions.** Inside this phase, the embedded **REQUIRED CHECKPOINT — After Each Architectural Step** (in Step 1 — Execution) may reject a specific step or require plan adjustment. Handle this in domain (adjust and re-present the plan; if it invalidates the planning phase, report `re_started` on `phase-0-plan-review`, regenerate the affected sub-step, report `finished` again, re-run its gap report, and resume `phase-1-apply-verify`). `phase-1-apply-verify`'s outer `finished` is only reported once Step 3 (Audit) has approved the full executed plan, tests and audit — not per step.

> Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

> ⚡ **MANDATORY** — On rejection, example using `phase-1-apply-verify`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-1-apply-verify \
  --status re_started

# 2. ... re-run the affected step(s) with the adjusted plan, tests and/or audit ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
REFACTOR_FILE_FLAGS=()
while IFS= read -r f; do
  REFACTOR_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.action != "delete") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

TEST_FILE_FLAGS=()
while IFS= read -r f; do
  TEST_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="unit_tests" or .group=="widget_tests" or .group=="integration_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-1-apply-verify \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/evidence/test-validation.md" \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/evidence/audit-report.md" \
  "${REFACTOR_FILE_FLAGS[@]}" \
  "${TEST_FILE_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY for every executed step.** All three step-ids in this workflow produce output files: `phase-0-plan-review`, `phase-1-apply-verify`, `phase-2-documentation`.
> The Topology gate is not tracked by telemetry at all and never runs a gap report.

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
| `pragma-ai workflow create --workflow-id refactor-feature --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each phase begins (PHASE 0, 1, 2) |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of any executed phase — all three step-ids produce output files: `phase-0-plan-review`, `phase-1-apply-verify`, `phase-2-documentation` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When `phase-1-apply-verify` cannot recover from a compilation/regression in Execution, can't pass or meet coverage targets in Tests, or exhausts retries in Audit — the workflow stops |
| `pragma-ai workflow report ... --step-id phase-1-apply-verify --status paused` | On reaching the embedded REQUIRED CHECKPOINT — After Each Architectural Step, before yielding to the user; may repeat once per qualifying step |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably `phase-0-plan-review`'s internal Step 5 rejection regenerating Step 1/2/3/4, or `phase-1-apply-verify`'s per-step revisions) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
