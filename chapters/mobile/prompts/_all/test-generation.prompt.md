---
id: test-generation
version: 1.0.0
scope: chapter
type: prompt
chapter: mobile
description: >
  Shared prompt for generating test, golden, and Widgetbook validation artifacts for DS components or app views. Use when the orchestrator provides an explicit validation MODE.
---
# Test Generation (Deterministic By Mode)

## Reference Skills

- flutter-ds-testing-patterns
- flutter-ds-golden-testing
- flutter-ds-widgetbook
- flutter-ds-theming-tokens
- flutter-ds-folder-structure

## Required Mode

Before execution, the orchestrator must define `MODE` and the agent must honor it.

| Agent | Allowed MODE | Deliverables |
|---|---|---|
| `@test-engineer` | `DS_WIDGET_TESTS` | Only DS component `*_test.dart` files |
| `@test-engineer` | `VIEW_WIDGET_TESTS` | Only app view tests (`loading/empty/error/populated` + navigation) |
| `@golden-test-engineer` | `DS_GOLDEN_TESTS` | Only DS component `*_golden_test.dart` files |
| `@golden-test-engineer` | `VIEW_GOLDEN_TESTS` | Only complete view `*_view_golden_test.dart` files |
| `@widgetbook-developer` | `DS_WIDGETBOOK` | Only DS component `*_use_case.dart` files |
| `@widgetbook-developer` | `APP_WIDGETBOOK_SCREENS` | Only app screen `*_use_case.dart` files |

If `MODE` is not defined or does not match the current agent, stop with `blocked_input`.

For `FEATURE_*` modes, `@feature-builder` may be the execution owner when
`execution_capabilities.subagent_delegation=unavailable`. It adopts the
`test-engineer` role contract without changing test scope, execution order,
planned artifacts, commands, or evidence requirements. Its fallback policy is
`delegate_or_controller_executes`.

## SDD Contract

When `spec_context` exists, read `spec_ref` and `context_ref` as machine
sources. Use only `read_sections`, generate tests/interactive documentation
for artifacts declared in `artifact_plan`, record evidence under
`{SPEC_PACKET_PATH}/evidence/`, and treat `PIPELINE_SPEC_PATH` as a human report.

## Required Topology Context

The handoff must include:

- `topology.repo_mode`
- `target.target_root`
- `execution_context.melos_enabled`
- `execution_context.melos_root`
- `execution_context.target_scope`

If any item is missing, stop with `blocked_input`.

## Command Resolver (required)

### `single_repo`

- Execute commands in `target.target_root`.
- Commands:
  - `flutter test`
  - `flutter test {declared_test_path}`
  - `flutter test {declared_integration_test_path}`
  - `flutter test --update-goldens --tags golden`
  - `dart run build_runner build --delete-conflicting-outputs`

### `monorepo_melos`

- Execute commands from `execution_context.melos_root`.
- Require `execution_context.melos_enabled=true`.
- Require non-empty `execution_context.target_scope`.
- Commands:
  - `melos exec --scope={target_scope} -- flutter test`
  - `melos exec --scope={target_scope} -- flutter test {declared_test_path}`
  - `melos exec --scope={target_scope} -- flutter test {declared_integration_test_path}`
  - `melos exec --scope={target_scope} -- flutter test --update-goldens --tags golden`
  - `melos exec --scope={target_scope} -- dart run build_runner build --delete-conflicting-outputs`

### `multi_repo`

- Execute commands in `target.target_root` of the active feature repo.
- Commands are the same as `single_repo`.

## Critical Scope Rule

- Generate only artifacts for the received `MODE`.
- Do not create files for other modes.
- Report only the subsection for the executed mode.
- Do not add inline, block, or Dartdoc comments in generated files unless the
  reason is fundamental and cannot be inferred from the code.

## Inputs You Will Receive

1. `MODE`.
2. Component/view source code.
3. Supported states.
4. Supported variants, if applicable.
5. `design_source`, `literal_texts`, `layout_constraints`, and `assets`, if applicable.
6. Topology context.
7. `contracts.text_overflow`, required for artifacts generated from
   `/new-component` or `/new-view`.

## MODE: `DS_WIDGET_TESTS` (only `@test-engineer`)

### Minimum Coverage

1. Basic rendering.
2. States.
3. Variants.
4. Interactions.
5. Defaults.
6. Accessibility.
7. Literal text and anti-overflow mitigation when applicable.

### Output

1. `[component]_test.dart`.
2. Evidence with executed command and result.

## MODE: `VIEW_WIDGET_TESTS` (only `@test-engineer`)

### Minimum Coverage

1. `loading`
2. `empty`
3. `error`
4. `populated`
5. critical navigation, including the declared bottom-navigation ownership
6. absence of overflow in main and compact constraints when applicable

### Rules

- Do not generate golden tests in this mode.
- Do not generate Widgetbook files in this mode.
- File: `[view]_view_test.dart`.

### Output

1. `test/presentation/views/[view]/[view]_view_test.dart`.
2. Evidence of the executed mode.

## MODE: `FEATURE_UNIT_TESTS` (only `@test-engineer`)

### Minimum Coverage

1. Domain entities, value behavior and use cases.
2. Repository implementation success and mapped failure paths.
3. DTO and mapper conversions, including nullable and malformed API values.
4. Data-source success and failure mapping with mocks or fakes.
5. BLoC events, emitted states and use-case interaction where the feature has a BLoC.

### Rules

- Generate only tests planned under `artifact_plan.planned[group=unit_tests]`.
- Keep production code unchanged. Return implementation defects to the feature
  builder and stop the phase until they are corrected.
- Execute the declared test paths, or the feature unit-test directory when the
  packet declares it, and persist the exact command and result.

### Output

1. Planned `test/...` unit-test files for the feature.
2. `evidence/unit-tests.md` with files, command, passed/failed totals and result.

## MODE: `FEATURE_WIDGET_TESTS` (only `@test-engineer`)

### Minimum Coverage

1. Page rendering in loading, empty, error and populated states when applicable.
2. Primary user actions and callback dispatch.
3. Critical navigation from and back to the feature flow.
4. Visible literal text and compact constraints when overflow risk is declared.

### Rules

- Generate only tests planned under `artifact_plan.planned[group=widget_tests]`.
- Use deterministic dependencies, state fixtures and routing fakes.
- Execute the declared feature widget-test paths and persist the exact command
  and result.

### Output

1. Planned feature widget-test files.
2. `evidence/widget-tests.md` with files, command, passed/failed totals and result.

## MODE: `FEATURE_INTEGRATION_TESTS` (only `@test-engineer`)

### Minimum Coverage

1. One end-to-end primary journey through the app entry point.
2. A relevant empty or failure outcome when the feature exposes one.
3. Navigation into and out of the feature when it belongs to an app flow.

### Rules

- Generate only tests planned under `artifact_plan.planned[group=integration_tests]`.
- Use the configured integration-test harness and stable fake or test backend
  where the project provides one.
- Execute the declared integration-test path. If the required device, emulator
  or harness is unavailable, return `blocked_input`; never record this mode as
  skipped.

### Output

1. Planned `integration_test/...` feature journey file(s).
2. `evidence/integration-tests.md` with files, command, environment and result.

## MODE: `DS_GOLDEN_TESTS` (only `@golden-test-engineer`)

### Required Goldens

1. Variant grid in light mode.
2. State grid.
3. Dark mode.
4. Variant x state combinations.
5. Sizes, if applicable.
6. Compact width if `contracts.text_overflow` reports overflow risk.

### Output

1. `[component]_golden_test.dart`.
2. Evidence with command and result.

## MODE: `VIEW_GOLDEN_TESTS` (only `@golden-test-engineer`)

### Required Complete View Goldens

1. `loading`
2. `empty`
3. `error`
4. `populated`
5. `light` and `dark` themes
6. compact viewport if `contracts.text_overflow` reports overflow risk

### Rules

- File: `[view]_view_golden_test.dart`.
- Capture the complete screen (Scaffold + main sections), not isolated private widgets.
- Use state wrappers/mocks to stabilize results.
- Align constraints with the main design target, for example mobile portrait.
- If overflow risks exist, include an additional compact scenario and report
  whether mitigation depends on inferred constraints.

### Output

1. `test/presentation/views/[view]/[view]_view_golden_test.dart`.
2. Evidence with command and result.

## MODE: `FEATURE_GOLDEN_TESTS` (only `@golden-test-engineer`)

### Required Complete Feature Goldens

1. Stable primary page state.
2. Relevant loading, empty or error state when implemented.
3. Light and dark theme when the application supports both.
4. Compact viewport when `contracts.text_overflow` reports overflow risk.

### Rules

- Execute this mode only when the approved input `golden_tests=true` and the
  packet plans `artifact_plan.planned[group=golden_tests]`.
- Capture complete feature pages, not isolated private widgets.
- Use deterministic state wrappers and mocks.

### Output

1. Planned feature golden test files and snapshots.
2. `evidence/golden-tests.md` with the command and result.

## MODE: `DS_WIDGETBOOK` (only `@widgetbook-developer`)

### Required Stories

1. Overview, if applicable.
2. Playground.
3. States.
4. All variants, if applicable.

### Rules

- Define `WIDGETBOOK_SCOPE=DS_COMPONENTS`.
- Resolve `WIDGETBOOK_COMPONENTS_ROOT`.

### Output

1. `[component]_use_case.dart`.
2. Evidence of the executed mode.

## MODE: `APP_WIDGETBOOK_SCREENS` (only `@widgetbook-developer`)

### Minimum Coverage

1. `Default`
2. `Loading`
3. `Empty`, if applicable
4. `Error`, if applicable
5. `Populated`

### Rules

- Define `WIDGETBOOK_SCOPE=APP_SCREENS`.
- Resolve `WIDGETBOOK_SCREENS_ROOT`.
- Do not create DS component Widgetbook files in this mode.
- Use literal text from Figma as the initial values for knobs/mocks; do not
  invent copy to make the example seem more realistic.

### Output

1. `[screen]_use_case.dart`.
2. Evidence of the executed mode.

## Human Testing Report Format

```markdown
## Testing Report

### [Executed MODE]
- **File(s)**: ...
- **Command**: ...
- **Passed**: ...
- **Failed**: ...
- **Result**: ...
```
