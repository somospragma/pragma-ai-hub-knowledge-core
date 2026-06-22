---
id: flutter-ds-widgetbook
version: 2.5.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-widgetbook
description: >
  Widgetbook patterns for interactive documentation of Design System components
  and app screens in canonical `/new-view`. Use when creating or updating
  use cases, knobs, code preview, and build_runner generation with deterministic
  scope selection.
---

# Widgetbook Patterns (Deterministic Scope)

## Step 0 — Define the scope first

Before generating any code, identify which scope applies:

| Scope | When to use | File goes in |
|---|---|---|
| `DS_COMPONENTS` | DS atoms, molecules, organisms | `{WIDGETBOOK_COMPONENTS_ROOT}/atoms\|molecules\|organisms/[name]/` |
| `APP_SCREENS` | App screens/views (`/new-view` pipeline) | `{WIDGETBOOK_SCREENS_ROOT}/features/[feature]/[screen]/` |

If `WIDGETBOOK_SCOPE` is not provided explicitly:
- In DS flow (`MODE=DS_WIDGETBOOK`) → default to `DS_COMPONENTS`
- In screen flow (`MODE=APP_WIDGETBOOK_SCREENS`) → default to `APP_SCREENS`

Read paths from `project.config.yaml`:
- Components: `structure.widgetbook_components_path` (fallback: `structure.widgetbook_path`)
- Screens: `structure.widgetbook_screens_path` (fallback: `structure.widgetbook_path`)

## Required Use Cases per scope

### DS_COMPONENTS
File: `[component]_use_case.dart`

1. `Overview` (optional for simple components)
2. `Playground` (**mandatory**)
3. State variants: `loading`, `disabled`, `error` — as knobs or fixed use cases
4. `All Variants` (**mandatory** when a variant enum exists)

### APP_SCREENS
File: `[screen]_use_case.dart`

1. `Default` (**mandatory**)
2. `Loading` (**mandatory**)
3. `Empty` (if the screen has an empty state)
4. `Error` (if the screen handles errors)
5. Domain-specific variants as needed

For screen use cases, always use wrappers/mocks. Never use real navigation — replace all navigation callbacks with `developer.log(...)`.

## Knobs

| Dart Type | Knob | Rule |
|---|---|---|
| `String` | `context.knobs.string()` | Use real domain values |
| `bool` | `context.knobs.boolean()` | |
| `enum` | `context.knobs.list()` | **Always** include `labelBuilder` |
| `double` | `context.knobs.double.slider()` | Set reasonable min/max |
| `int` | `context.knobs.int.slider()` | Set reasonable min/max |
| `Color` | ❌ no knob | Colors come from theme/tokens only |
| `VoidCallback?` | boolean + ternary | `enabled ? () => developer.log('...') : null` |

Import `developer` explicitly: `import 'dart:developer' as developer;`

## Code Preview

Every use case must include `context.setCodePreview(...)`. This is not optional.

## Commands — run in this exact order

```bash
# 1. Analyze first — catch errors before generating
dart analyze {WIDGETBOOK_COMPONENTS_ROOT}/atoms {WIDGETBOOK_COMPONENTS_ROOT}/molecules {WIDGETBOOK_COMPONENTS_ROOT}/organisms

# For APP_SCREENS:
# dart analyze {WIDGETBOOK_SCREENS_ROOT}/features

# 2. Generate only after analyze is clean
dart run build_runner build --delete-conflicting-outputs
```

`dart analyze` must run **before** `build_runner`. Running build_runner on code with errors produces broken generated files that are harder to debug than the original error.

## Critical rules

- `labelBuilder` is **mandatory** on every `knobs.list()` / enum knob
- **Never** add a knob for `Color` — colors come from the theme
- **Never** use `print` in callbacks — use `developer.log(...)`
- **Never** add `part '*.g.dart'` inside `*.use_case.dart` files — this breaks code generation
- For `APP_SCREENS`: always use test mocks/providers, never real navigation

## Checklist

- [ ] `WIDGETBOOK_SCOPE` defined (`DS_COMPONENTS` or `APP_SCREENS`)
- [ ] File `*_use_case.dart` at the correct path for the scope
- [ ] Required use cases covered for the scope
- [ ] `context.setCodePreview(...)` present in every use case
- [ ] `labelBuilder` on all enum/list knobs
- [ ] No `print` — uses `developer.log`
- [ ] No `part '*.g.dart'` in use case files
- [ ] `dart analyze` ran clean
- [ ] `dart run build_runner build --delete-conflicting-outputs` ran

## Reference files

| Topic | File |
|---|---|
| Setup | `references/setup.md` |
| Project structure | `references/project_structure.md` |
| Features guide | `references/features_guide.md` |
| Variants guide | `references/variants_guide.md` |
| Mocks | `references/mocks.md` |
| Knobs reference | `assets/knobs_reference.md` |
| Coverage audit | `references/coverage_audit.md` |
