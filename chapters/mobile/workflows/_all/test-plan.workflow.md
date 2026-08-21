---
id: test-plan
version: 1.1.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: test-coverage-engineer
input_contract: ../docs/templates/spec-packets/test-plan.overlay.yaml
invocation_mode: explicit_agent
description: >
  Workflow for analyzing, planning, and generating complete test coverage for an existing feature. Use when the user provides a feature path and needs coverage inventory, test strategy, generated tests, execution evidence, and a testing report.
---
# Workflow: Test Plan (Full Coverage for Existing Feature)

## Telemetry — Workflow metadata

| Field | Value |
|---|---|
| `workflow-id` | `test-plan` |
| `user-story-id` | Value of the required `hu_id` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `phase-0-spec-packet`, `phase-1-feature-analysis`, `phase-2-test-plan`, `phase-2-1-validation-human-review`, `phase-3-test-generation`, `phase-4-execution-and-validation`, `phase-5-testing-report` |

> **NON-NEGOTIABLE RULE:** Every `pragma-ai workflow ...` command in this document is **MANDATORY** to execute. The agent MUST run them — they are not suggestions or documentation.

> ⛔ **STEP-ID INTEGRITY (NON-NEGOTIABLE):** The `--step-id` and `--workflow-id` values shown in every command block below are the **ONLY** valid identifiers for this workflow. The agent MUST copy them **verbatim** from this document — never invent, abbreviate, translate, paraphrase, pluralize, capitalize differently, or otherwise modify them.
>
> - Every `--step-id` submitted to `pragma-ai workflow report` or `pragma-ai workflow gap-report` MUST match one entry in the **"Step IDs"** list above, character-for-character (kebab-case, lowercase, exact spelling).
> - Every `--workflow-id` MUST be exactly `test-plan`.
> - If a step-id you need is not in the list, STOP and ask the user — do not fabricate one.
> - The CLI rejects unknown step-ids; a wrong id silently corrupts the run's telemetry.

> Each step ends with a **human approval gate** before the gap report (see *Human approval gate* at the end of this document). PHASE 2.1 is the domain aggregate approval gate for the planning set (PHASE 0 through PHASE 2).
> The **gap report only runs on steps that produce output files** (`--output-file`). `phase-2-1-validation-human-review` does NOT run a gap report.
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
  --workflow-id test-plan \
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

- A feature exists and either has no tests or has incomplete test coverage
- The user asks to "add tests", "improve coverage", "test the checkout feature"
- After a `/new-feature` workflow completes (tests are a separate step)
- After a `/refactor-feature` workflow if coverage is still below targets
- The user wants a coverage report for a specific feature

Do NOT use for:
- Testing DS components (use `@test-engineer` via DS pipeline)
- Golden tests (use `@golden-test-engineer`)
- Integration/E2E tests (separate workflow — future)
- Creating a new feature (use `/new-feature`)

---

## Prerequisites

- Feature must already exist at the given path with source code
- `.sopp/config/project.config.yaml` valid (or run `/bootstrap-workspace` first)
- Context resolved:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `ACTIVE_TARGET_ID` resolved from `feature_path`
  - `ACTIVE_TARGET_ROOT = targets.registry[ACTIVE_TARGET_ID].root`
  - `TOPOLOGY_REPO_MODE`
  - `SPEC_PACKET_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/specs/{feature_name}-test-plan`

---

## Inputs

`hu_id` is **required**: it identifies the user story this test plan belongs to
and is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied, the
workflow refuses to start.

```text
@test-coverage-engineer /test-plan
hu_id: US-12345
feature_name: product_catalog
feature_path: lib/src/features/product_catalog/
evidence_mode: minimal
```

### Input variations

> Note: every variation below still requires `hu_id` as its first line, just like the main example above.

```text
# Full coverage (default — all layers)
@test-coverage-engineer /test-plan
hu_id: US-12345
feature_name: product_catalog
feature_path: lib/src/features/product_catalog/

# Single layer focus
@test-coverage-engineer /test-plan
hu_id: US-12345
feature_name: checkout
feature_path: lib/src/features/checkout/
scope: presentation

# Specific files focus
@test-coverage-engineer /test-plan
hu_id: US-12345
feature_name: auth
feature_path: lib/src/features/auth/
focus: login_bloc.dart, token_repository_impl.dart

# Monorepo package
@test-coverage-engineer /test-plan
hu_id: US-12345
feature_name: payments
feature_path: packages/payments/lib/
topology: monorepo_melos
target_root: packages/payments/
```

---

## Execution Sequence

### PHASE 0 — Mobile Spec Packet (`full`)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-0-spec-packet \
  --status started
```

**Agent:** `@test-coverage-engineer`
**Skill:** `mobile-sdd-spec-validation`

Create `SPEC_PACKET_PATH` with:

1. `spec.yaml` (`schema_ref: ../docs/templates/schemas/mobile-spec.schema.yaml`,
   `spec_level: full`, `execution_mode: propose_then_apply`)
2. `context.json`
3. `review.md` in Spanish
4. `evidence/validation-report.md`

The spec records feature path, requested scope/focus, coverage targets by layer,
integration-test expectations, report path, commands to run,
`stage_checkpoints: required` and `agent_permissions`.

> ⚡ **MANDATORY (success path)** — Report `finished` with all four packet artifacts. Substitute `${SPEC_PACKET_PATH}` with the resolved run path:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-0-spec-packet \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/review.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/validation-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.

---

### PHASE 1 — Feature Analysis

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-1-feature-analysis \
  --status started
```

**Agent:** `@test-coverage-engineer`

Steps:
1. Read all source files in `feature_path` recursively
2. Classify each file by layer (domain / data / presentation)
3. For each source file identify:
   - Public classes and methods
   - Dependencies (imports, injected services)
   - Complexity (branches, async, Either paths)
4. Locate existing test directory and map coverage:
   - Which source files have test files
   - Which test files are incomplete (not all paths tested)
   - Which source files have zero tests
5. Produce coverage inventory table

Output: `evidence/coverage-inventory.md`.
Update `spec.yaml` sections `coverage_inventory`, `source_inventory` and
`risk_map`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the coverage inventory evidence and the updated spec:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-1-feature-analysis \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/coverage-inventory.md" \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.

---

### PHASE 2 — Test Plan

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-2-test-plan \
  --status started
```

**Agent:** `@test-coverage-engineer`

Steps:
1. For each missing/incomplete test, define:
   - Test file path (mirroring source structure)
   - Test cases (descriptive names following `should [verb] when [condition]`)
   - Mocks needed (one level deep)
   - Fixtures needed (JSON responses, entity instances)
2. Prioritize: domain → data → BLoC → pages
3. Estimate total test cases to generate
4. Add the mandatory testing report to `artifact_plan.planned`:
   - `target_id: project_docs` or the configured docs target
   - `path: docs/testing/{feature_name}-testing-report-{YYYY-MM-DD}.md`
   - `action: create`
   - `owner: test-coverage-engineer`
   - `group: docs`

Output: Test plan summary.
Update `spec.yaml` sections `test_plan`, `artifact_plan`, `success_criteria`
and `handoffs`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated spec:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-2-test-plan \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.1.

---

### PHASE 2.1 — Validation + Human Review

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-2-1-validation-human-review \
  --status started
```

**Skill:** `mobile-sdd-spec-validation`

Validate `spec.yaml` and present `review.md` in Spanish with:

1. coverage gaps by layer
2. test files to create/modify
3. expected commands
4. report path
5. risks or manual validations

Wait for explicit approval before generating tests.

> ⚡ **MANDATORY (conditional)** — If the spec fails schema/business validation and cannot continue:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-2-1-validation-human-review \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` once validation passes and the human review is presented (approval itself happens in the gate that follows):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-2-1-validation-human-review \
  --status finished
```

> **Stop here.** This is the **domain aggregate approval gate** for the planning set (PHASE 0 through PHASE 2). If the human requests changes to `coverage_inventory`, `source_inventory`, `risk_map`, `test_plan`, `artifact_plan`, `success_criteria`, or `handoffs`, the flow must return to the phase that owns that section: report `re_started` on the affected earlier phase (PHASE 1 or PHASE 2), regenerate its output, report `finished` again with the same `--output-file` set, re-run that phase's gap report, and re-enter PHASE 2.1 (`re_started` → `finished` on `phase-2-1-validation-human-review`). Only when the plan is explicitly approved may PHASE 3 begin. *(PHASE 2.1 produces no new output files — no gap report required.)*

---

### PHASE 3 — Test Generation

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-3-test-generation \
  --status started
```

**Agent:** `@test-coverage-engineer`
Mandatory compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: test_generation
read_sections:
  - test_plan
  - artifact_plan
  - success_criteria
  - coverage_targets
  - stage_checkpoints
```

Steps:
1. Create test directory structure (mirror source)
2. For **missing** tests (🆕): generate complete test files
3. For **incomplete** tests (⚠️): add missing test cases to existing files
4. For **outdated** tests (🔄): update mocks, patterns, assertions to match current source
5. Track every modification to existing tests with a reason (for the report)
6. Each test file follows:
   - `mocktail 1.0.5` for mocking
   - `bloc_test 9.1.7` for BLoC
   - AAA pattern
   - `group()` for organization
   - One test file per source file

Test generation per layer:
- **Domain**: use case tests (success + failure + edge cases)
- **Data**: repository tests (remote success, remote failure, cache), mapper tests, data source tests
- **Presentation BLoC**: `blocTest()` for every event → state transition
- **Presentation Pages**: widget tests (render per state, interactions, navigation)
- **Integration**: full user flow tests (navigation, data loading, user actions)
  - Location: `integration_test/features/{feature_name}/`
  - Uses `IntegrationTestWidgetsFlutterBinding`
  - One test per main user flow
  - CANNOT be executed by the agent — marked as "pending manual validation"

Output: Test files created/modified on disk (unit + widget + integration).

> ⚡ **MANDATORY (success path)** — Report `finished` with every test file declared in `artifact_plan.planned[]` (unit, widget, integration) and the updated context. Expand the array from the spec:

```bash
TEST_FILE_FLAGS=()
while IFS= read -r f; do
  TEST_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="unit_tests" or .group=="widget_tests" or .group=="integration_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-3-test-generation \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${TEST_FILE_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.

---

### PHASE 4 — Execution & Validation

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-4-execution-and-validation \
  --status started
```

**Agent:** `@test-coverage-engineer`

Steps:
1. Run all tests:
   - `flutter test test/features/{feature_name}/`
   - Monorepo: `melos exec --scope={target_scope} -- "flutter test"`
2. Fix any failing tests immediately
3. Run coverage check:
   - `flutter test --coverage test/features/{feature_name}/`
4. Validate per-layer targets:
   - Domain: 95%+
   - Data: 85%+
   - Presentation BLoC: 85%+
   - Presentation Pages: 70%+
5. If below target: generate additional tests for uncovered branches
6. Re-run until all targets met

Output: All tests passing, coverage validated.
Persist command output and coverage summary under `SPEC_PACKET_PATH/evidence/`.

> ⚡ **MANDATORY (conditional)** — If unit/widget tests cannot be made to pass, or the non-negotiable coverage targets (domain 95%, data 85%, BLoC 85%, pages 70%) cannot be met after generating additional tests:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-4-execution-and-validation \
  --status failed
```
> ❌ The workflow stops here — the test plan is incomplete without passing tests at the required coverage.

> ⚡ **MANDATORY (success path)** — Report `finished` with the test-execution and coverage evidence:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-4-execution-and-validation \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/test-execution.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/coverage-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 5.

---

### PHASE 5 — Testing Report (mandatory — FILE CREATION action)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-5-testing-report \
  --status started
```

**Agent:** `@test-coverage-engineer`

> **CRITICAL: This is a FILE CREATION action. The agent MUST create this file
> on disk. The workflow is NOT complete until this file exists.**

**Action:** Create a NEW file at this EXACT path:
`{PROJECT_ROOT}/docs/testing/{feature_name}-testing-report-{YYYY-MM-DD}.md`

This file must already be declared in `artifact_plan.planned[]` with
`target_id=project_docs` or the configured docs target, `owner:
test-coverage-engineer` and `group: docs`.

**Steps:**
1. If `docs/testing/` directory does not exist → CREATE IT
2. Create the file with:
   - Summary metrics (files analyzed, tests created, tests modified, tests passing)
   - Coverage by layer table (files, tests, coverage %, target, status)
   - Test inventory per layer (source file → test file → test cases → status)
   - **Changes to existing tests** table (file, action, reason for each modification)
   - Mocks created table
   - Gaps & recommendations
   - Run commands
3. VERIFY the file exists on disk after creation

**Example path:** `docs/testing/product_catalog-testing-report-2026-05-11.md`

Output: Testing report file created at `docs/testing/`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the testing report file. Substitute `${TESTING_REPORT_PATH}` with the actual file created (relative to `--project-dir`, e.g. `docs/testing/product_catalog-testing-report-2026-05-11.md`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-5-testing-report \
  --status finished \
  --output-file "${TESTING_REPORT_PATH}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** — the workflow is complete.

---

## Mandatory Post-Execution Checklist

> **The agent MUST complete ALL items below before reporting to the user.
> If any item missing, the test plan is INCOMPLETE.**

| # | Action | Verification |
|---|---|---|
| A | Generate test files for all untested source files | Files exist on disk |
| B | Run tests — all pass | `flutter test` exits with 0 |
| C | Validate coverage targets met | Domain 95%+, Data 85%+, BLoC 85%+, Pages 70%+ |
| D | Create `docs/testing/{feature_name}-testing-report-{date}.md` | File exists on disk (read it back) |
| E | Report final summary to user | Only after A–D are done |

---

## Verification (topology-aware)

After all phases:

- `single_repo`:
  ```bash
  flutter test test/features/{feature_name}/
  flutter test --coverage test/features/{feature_name}/
  ```
- `monorepo_melos`:
  ```bash
  melos exec --scope={target_scope} -- "flutter test"
  melos exec --scope={target_scope} -- "flutter test --coverage"
  ```

---

## Rules

### Completion criteria (ALL must be true)
- [ ] All source files have corresponding test files (unit + widget)
- [ ] All unit + widget tests pass (zero failures)
- [ ] Coverage targets met per layer
- [ ] Integration test files generated for main user flows
- [ ] Testing report file EXISTS at `docs/testing/{feature_name}-testing-report-{date}.md`

### Prohibitions
- NEVER use mockito — always mocktail
- NEVER test generated code (*.g.dart, *.freezed.dart)
- NEVER write tests that depend on other tests
- NEVER skip a layer — test domain, data, AND presentation
- NEVER end without creating the testing report file in `docs/testing/`
- NEVER leave failing tests

### Obligations
- ALWAYS mirror source directory structure in test directory
- ALWAYS use AAA pattern
- ALWAYS test both success AND failure paths
- ALWAYS test all BLoC events and state transitions
- ALWAYS use `blocTest()` for BLoC tests
- ALWAYS track every modification to existing tests with a reason (for the report)
- ALWAYS include "Changes to Existing Tests" section in the report (even if empty)
- ALWAYS generate integration tests for main user flows (in `integration_test/features/{feature_name}/`)
- ALWAYS mark integration tests as "pending manual validation" in the report
- ALWAYS create `docs/testing/` directory if it doesn't exist
- ALWAYS create the testing report file as the LAST action before reporting
- ALWAYS verify the report file exists on disk after creating it
- ALWAYS run `flutter test` to confirm all unit + widget tests pass before finishing
- NEVER attempt to run integration tests — they require a device/emulator
- NEVER generate tests before `review.md` is approved.
- ALWAYS validate generated/modified tests against `SPEC_PACKET_PATH/spec.yaml`.
- ALWAYS use compact handoffs by `spec_ref` and `context_ref`.

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

> **PHASE 2.1 aggregate rejection.** When PHASE 2.1 hosts the plan-approval decision, a rejection of a specific planning section (coverage inventory, source inventory, risk map, test plan, artifact plan, success criteria, handoffs) must first replay the phase that owns that section: report `re_started` on the affected earlier phase (PHASE 1 or PHASE 2), regenerate its output, report `finished` again with the same `--output-file` set, re-run that phase's gap report, and then report `re_started` → `finished` on PHASE 2.1 itself before re-entering this gate.

> Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

> ⚡ **MANDATORY** — On rejection, example using `phase-3-test-generation`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-3-test-generation \
  --status re_started

# 2. ... regenerate the test files ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
TEST_FILE_FLAGS=()
while IFS= read -r f; do
  TEST_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="unit_tests" or .group=="widget_tests" or .group=="integration_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id test-plan \
  --step-id phase-3-test-generation \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${TEST_FILE_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow:
> `phase-0-spec-packet`, `phase-1-feature-analysis`, `phase-2-test-plan`, `phase-3-test-generation`, `phase-4-execution-and-validation`, `phase-5-testing-report`.
> `phase-2-1-validation-human-review` does NOT run a gap report.

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
| `pragma-ai workflow create --workflow-id test-plan --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each phase begins (PHASE 0, 1, 2, 2.1, 3, 4, 5) |
| `pragma-ai workflow report ... --step-id phase-2-1-validation-human-review --status finished` | On completion of the aggregate planning-approval checkpoint (no `--output-file`) |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of every file-producing phase: `phase-0-spec-packet`, `phase-1-feature-analysis`, `phase-2-test-plan`, `phase-3-test-generation`, `phase-4-execution-and-validation`, `phase-5-testing-report` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When `phase-2-1-validation-human-review` cannot validate, or `phase-4-execution-and-validation` cannot pass tests or meet coverage targets — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably PHASE 2.1 aggregate rejection cascading back to PHASE 1 or PHASE 2) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding file-producing step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
