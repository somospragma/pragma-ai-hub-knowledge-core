---
id: refactor-feature
version: 1.1.0
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
| Step IDs | `phase-0-spec-packet`, `phase-1-analysis`, `phase-2-impact-analysis`, `phase-3-refactoring-plan`, `phase-4-checkpoint`, `phase-5-execution`, `phase-6-tests`, `phase-7-audit`, `phase-8-report-and-documentation`, `phase-9-project-documentation-update` |

> **NON-NEGOTIABLE RULE:** Every `pragma-ai workflow ...` command in this document is **MANDATORY** to execute. The agent MUST run them — they are not suggestions or documentation.

> ⛔ **STEP-ID INTEGRITY (NON-NEGOTIABLE):** The `--step-id` and `--workflow-id` values shown in every command block below are the **ONLY** valid identifiers for this workflow. The agent MUST copy them **verbatim** from this document — never invent, abbreviate, translate, paraphrase, pluralize, capitalize differently, or otherwise modify them.
>
> - Every `--step-id` submitted to `pragma-ai workflow report` or `pragma-ai workflow gap-report` MUST match one entry in the **"Step IDs"** list above, character-for-character (kebab-case, lowercase, exact spelling).
> - Every `--workflow-id` MUST be exactly `refactor-feature`.
> - If a step-id you need is not in the list, STOP and ask the user — do not fabricate one.
> - The CLI rejects unknown step-ids; a wrong id silently corrupts the run's telemetry.

> Each step ends with a **human approval gate** before the gap report (see *Human approval gate* at the end of this document). PHASE 4 is the domain aggregate approval gate for the planning set (PHASE 0 through PHASE 3); PHASE 5 also has its own REQUIRED CHECKPOINT per architectural step, described in the phase body.
> **The Topology gate is excluded from telemetry.** It runs before the workflow instance is minted and stops the run with `blocked_input` when it fails (no telemetry emitted).
> The **gap report only runs on steps that produce output files** (`--output-file`). `phase-4-checkpoint` does NOT run a gap report.
> Commands assume the shell's cwd is already the project root — no `cd` prefix is needed, and `--project-dir` only matters when running from elsewhere.

---

## Setup — Mint the workflow instance

> ⚡ **MANDATORY** — Always run this at the start, before any step.

### Resolve user-story-id (mandatory)

`hu_id` is a **required** invocation input for this workflow (see *Inputs*), so the agent already has the user story identifier at the start. The agent MUST map it to `user-story-id` before running `workflow create`:

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

### PHASE 0 — Mobile Spec Packet (`full`)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-0-spec-packet \
  --status started
```

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
by PHASE 1-3 before execution approval.

> ⚡ **MANDATORY (success path)** — Report `finished` with all four packet artifacts. Substitute `${SPEC_PACKET_PATH}` with the resolved run path:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-0-spec-packet \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/review.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/validation-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.

---

### PHASE 1 — Analysis

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-1-analysis \
  --status started
```

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

> ⚡ **MANDATORY (success path)** — Report `finished` with the analysis evidence and the updated spec:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-1-analysis \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/refactoring-analysis.md" \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.

---

### PHASE 2 — Impact Analysis

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-2-impact-analysis \
  --status started
```

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

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated spec:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-2-impact-analysis \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 3.

---

### PHASE 3 — Refactoring Plan

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-3-refactoring-plan \
  --status started
```

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
- every project documentation file that Phase 9 may create or modify

If any planned artifact has `action: delete`, the spec must explicitly set
`agent_permissions.refactoring-advisor.can_delete_files=true` and record the
human approval that enabled the destructive action. Without that elevation,
delete actions remain blocked.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated spec:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-3-refactoring-plan \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.

---

### PHASE 4 — Checkpoint (mandatory)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-4-checkpoint \
  --status started
```

**Agent:** `@refactoring-advisor`

Present to the user:
1. Analysis summary (current state + issues found)
2. Impact analysis (files affected, breaking changes, risk)
3. Refactoring plan (ordered steps with risk ratings)
4. `review.md` in Spanish with criteria, checkpoints and evidence expected

Question:
"I've analyzed the feature and prepared a refactoring plan with {N} atomic steps (risk: {level}). Want me to proceed with execution?"

**Do NOT proceed without explicit approval.**

If the user requests changes to the plan, adjust and re-present.

> ⚡ **MANDATORY (success path)** — Report `finished` once the review has been presented (approval itself happens in the gate that follows):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-4-checkpoint \
  --status finished
```

> **Stop here.** This is the **domain aggregate approval gate** for the planning set (PHASE 0 through PHASE 3). If the human requests changes to `current_state`, `issues`, `impact_analysis`, `risk`, `breaking_changes`, `refactoring_plan`, `execution_steps`, `success_criteria`, `handoffs`, or `artifact_plan`, the flow must return to the phase that owns that section: report `re_started` on the affected earlier phase (PHASE 1, PHASE 2, or PHASE 3), regenerate its output, report `finished` again with the same `--output-file` set, re-run that phase's gap report, and re-enter PHASE 4 (`re_started` → `finished` on `phase-4-checkpoint`). Only when the plan is explicitly approved may PHASE 5 begin. *(PHASE 4 produces no new output files — no gap report required.)*

---

### PHASE 5 — Execution (iterative)

> ⚡ **MANDATORY** — Report `started` when the step begins (once, at the start of the iterative execution — not per plan step).

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-5-execution \
  --status started
```

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
   - Expected failures (structural change) → queue for Phase 6
   - Unexpected failures (regression) → revert step, reassess plan
6. **Log** step completion
7. **Update context** in `SPEC_PACKET_PATH/context.json`

If a step fails compilation:
- Fix immediately (do not move to next step)
- If fix requires plan adjustment, re-present to user

Output: Execution log per step in `PIPELINE_LOG_PATH`.

#### REQUIRED CHECKPOINT — After Each Architectural Step

If a step changes public API, DI, route behavior, layer boundaries, package
location or data contracts, present a compact Spanish review and wait for
approval before continuing.

> **IMPORTANT: After completing ALL refactoring steps, you are NOT done.**
> You MUST continue to Phase 6 (tests), Phase 7 (audit), and Phase 8 (documentation).
> The refactoring is incomplete without tests and the documentation file.

> ⚡ **MANDATORY (conditional)** — If a step causes an unrecoverable compilation failure, an unrevertible test regression, or a plan-invalidating conflict that cannot be resolved by re-presenting the plan for adjustment:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-5-execution \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Once every step in the approved plan has completed, report `finished` with every file declared in `artifact_plan.planned[]` (created, modified, moved or deleted). Expand the array from the spec:

```bash
# Build --output-file flags from the artifact plan (skip entries with action: delete
# since deleted paths cannot be captured as a baseline; the delete itself is recorded
# in spec.yaml + PIPELINE_LOG_PATH).
REFACTOR_FILE_FLAGS=()
while IFS= read -r f; do
  REFACTOR_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.action != "delete") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-5-execution \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${REFACTOR_FILE_FLAGS[@]}"
```

> **Stop here.** The embedded **REQUIRED CHECKPOINT — After Each Architectural Step** applies per step during iteration; this outer approval gate applies once, at the end of PHASE 5, covering the full executed plan. Once approved, run this step's **gap report** and then continue to PHASE 6.

---

### PHASE 6 — Test Analysis & Coverage (mandatory)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-6-tests \
  --status started
```

**Agent:** `@refactoring-advisor`

> **This phase is NOT optional.** Every refactoring MUST include test analysis
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
  --step-id phase-6-tests \
  --status failed
```
> ❌ The workflow stops here — the refactoring is incomplete without verified test coverage.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated/updated test files, the test-validation evidence, and the updated spec. Expand the test files from `artifact_plan.planned[group=unit_tests|widget_tests|integration_tests]`:

```bash
TEST_FILE_FLAGS=()
while IFS= read -r f; do
  TEST_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="unit_tests" or .group=="widget_tests" or .group=="integration_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-6-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/test-validation.md" \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  "${TEST_FILE_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 7.

---

### PHASE 7 — Audit

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-7-audit \
  --status started
```

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
  --step-id phase-7-audit \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the audit evidence:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-7-audit \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/audit-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 8.

---

### PHASE 8 — Report & Documentation

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-8-report-and-documentation \
  --status started
```

**Agent:** `@refactoring-advisor`

Generate two outputs:

#### 8.1. Pipeline report

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

#### 8.2. Refactoring documentation file (mandatory — FILE CREATION action)

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

> ⚡ **MANDATORY (success path)** — Report `finished` with the refactoring documentation file. Substitute `${REFACTORING_DOC_PATH}` with the actual file created (relative to `--project-dir`, e.g. `docs/refactoring/checkout-refactoring-2026-05-08.md`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-8-report-and-documentation \
  --status finished \
  --output-file "${REFACTORING_DOC_PATH}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 9.

---

### PHASE 9 — Project Documentation Update (mandatory)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-9-project-documentation-update \
  --status started
```

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

> ⚡ **MANDATORY (success path)** — Report `finished` with every project documentation file created or modified. Expand the array from `artifact_plan.planned[group=docs]`:

```bash
DOCS_FILE_FLAGS=()
while IFS= read -r f; do
  DOCS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="docs") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-9-project-documentation-update \
  --status finished \
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
- NEVER proceed past Phase 4 without explicit user approval
- NEVER execute a refactor step before `review.md` is approved
- NEVER delete tests without updating them to match new structure
- NEVER change behavior during refactoring (unless explicitly requested as part of intent)
- NEVER refactor DS components — delegate to `@ds-orchestrator /refactor-component`
- NEVER end without creating the documentation file in `docs/refactoring/`
- NEVER end without generating missing tests in Phase 6
- NEVER skip Phase 9 (Project Documentation Update) — it is mandatory after every refactoring

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
- ALWAYS update project documentation (7 documents) in Phase 9 using shared skill `documentation-projects`
- If a step causes unexpected test failures, REVERT and reassess before continuing

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

> **PHASE 4 aggregate rejection.** When PHASE 4 hosts the plan-approval decision, a rejection of a specific planning section (current state, issues, impact analysis, risk, breaking changes, refactoring plan, execution steps, success criteria, handoffs, artifact plan) must first replay the phase that owns that section: report `re_started` on the affected earlier phase (PHASE 1, PHASE 2, or PHASE 3), regenerate its output, report `finished` again with the same `--output-file` set, re-run that phase's gap report, and then report `re_started` → `finished` on PHASE 4 itself before re-entering this gate.

> **PHASE 5 per-step revisions.** Inside PHASE 5, the embedded **REQUIRED CHECKPOINT — After Each Architectural Step** may reject a specific step or require plan adjustment. Handle this in domain (adjust and re-present the plan; if it invalidates earlier planning phases, cascade back to PHASE 1/2/3 via `re_started`). PHASE 5's outer `finished` is only reported once every step in the approved plan has executed successfully — not per step.

> Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

> ⚡ **MANDATORY** — On rejection, example using `phase-5-execution`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-5-execution \
  --status re_started

# 2. ... re-run the affected step(s) with the adjusted plan ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
REFACTOR_FILE_FLAGS=()
while IFS= read -r f; do
  REFACTOR_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.action != "delete") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id refactor-feature \
  --step-id phase-5-execution \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${REFACTOR_FILE_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow:
> `phase-0-spec-packet`, `phase-1-analysis`, `phase-2-impact-analysis`, `phase-3-refactoring-plan`, `phase-5-execution`, `phase-6-tests`, `phase-7-audit`, `phase-8-report-and-documentation`, `phase-9-project-documentation-update`.
> `phase-4-checkpoint` does NOT run a gap report. The Topology gate is not tracked by telemetry at all.

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
| `pragma-ai workflow create --workflow-id refactor-feature --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each phase begins (PHASE 0–9) |
| `pragma-ai workflow report ... --step-id phase-4-checkpoint --status finished` | On completion of the aggregate planning-approval checkpoint (no `--output-file`) |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of every file-producing phase: `phase-0-spec-packet`, `phase-1-analysis`, `phase-2-impact-analysis`, `phase-3-refactoring-plan`, `phase-5-execution`, `phase-6-tests`, `phase-7-audit`, `phase-8-report-and-documentation`, `phase-9-project-documentation-update` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When `phase-5-execution` cannot recover from a compilation/regression, `phase-6-tests` can't pass or can't meet coverage targets, or `phase-7-audit` exhausts retries — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably PHASE 4 aggregate rejection cascading back to PHASE 1/2/3, or PHASE 5 per-step revisions) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding file-producing step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
