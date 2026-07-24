---
id: refactor-feature
version: 1.1.0
scope: chapter
type: steering
chapter: mobile
entry_agent: refactoring-advisor
input_contract: ../docs/templates/spec-packets/overlays/refactor-feature.yaml
invocation_mode: explicit_agent
description: >
  Workflow for refactoring an existing feature that follows, or should migrate toward, Clean Architecture. Use to analyze code, plan incremental changes, apply domain/data/presentation refactors, add tests, and produce refactoring documentation.
---
# Workflow: Refactor Feature (Evolutionary Improvement)

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
5. If `location_strategy=melos_package`, validate `repo_root/melos.yaml` and
   `repo_root/package_path`.

If any validation fails, terminate with `blocked_input`.

---

## Inputs

```text
@refactoring-advisor /refactor-feature
feature_name: checkout
feature_path: lib/src/features/checkout/
refactor_goal: Split the CheckoutBloc into CartBloc and PaymentBloc, extract coupon validation to a use case
constraints: Don't change the API contract, keep route paths the same
user_story: docs/hus/user story-078.md  (optional — contains acceptance criteria + DoD)
target_location: same | melos_package
sequence_diagram: docs/diagrams/checkout_flow.mmd  (optional)
```

### Input variations

```text
# Simple refactor (most common)
@refactoring-advisor /refactor-feature
feature_name: checkout
feature_path: lib/src/features/checkout/
refactor_goal: The BLoC is too large, needs splitting

# Package extraction
@refactoring-advisor /refactor-feature
feature_name: payments
feature_path: lib/src/features/payments/
refactor_goal: Extract to a standalone Melos package
target_location: melos_package
package_name: payments

# Pattern update
@refactoring-advisor /refactor-feature
feature_name: auth
feature_path: lib/src/features/auth/
refactor_goal: Replace dartz with fpdart, update Freezed to 3.x syntax

# Add endpoint to existing feature
@refactoring-advisor /refactor-feature
feature_name: products
feature_path: lib/src/features/products/
refactor_goal: Add DELETE /products/:id endpoint to existing feature
api_contract: |
  DELETE /products/:id -> void (204)
```

---

## Execution Sequence

### PHASE S0 — Mobile Spec Packet (`full`)

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

---

### PHASE 1 — Analysis

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

---

### PHASE 2 — Impact Analysis

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

---

### PHASE 3 — Refactoring Plan

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

---

### PHASE 4 — Checkpoint (mandatory)

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

---

### PHASE 5 — Execution (iterative)

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

---

### PHASE 6 — Test Analysis & Coverage (mandatory)

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

---

### PHASE 7 — Audit

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

---

### PHASE 8 — Report & Documentation

**Agent:** `@refactoring-advisor`

Generate two outputs:

#### 8a. Pipeline report

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

#### 8b. Refactoring documentation file (mandatory — FILE CREATION action)

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

---

### PHASE 9 — Project Documentation Update (mandatory)

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
