---
id: flutter-ds-widgetbook
version: 3.0.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-widgetbook
description: >
  Widgetbook patterns for interactive documentation of Design System components
  and app screens in canonical `/new-view`. Use when creating or updating
  use cases, knobs, code preview, and build_runner generation with deterministic
  scope selection. Includes cold-init detection and bootstrap when the
  Widgetbook host project is not yet configured.
---
# Widgetbook Patterns (Deterministic Scope)

## Step -1 — Ensure Widgetbook is initialized (Preflight)

Before choosing scope or generating any use case, verify that the Widgetbook host project exists and is wired up. Generating use cases against an uninitialized Widgetbook project produces files that will not compile or run.

Widgetbook is a **nested** Flutter project created with `flutter create widgetbook --empty --platforms=android,ios,web` from the app root, exactly as the official Widgetbook Quick Start prescribes. The result is `<app-root>/widgetbook/` — a subfolder inside the app project, **not** a sibling directory and **not** a hand-created plain folder.

Widgetbook is considered initialized only when **all four** signals are true:

1. `{WIDGETBOOK_ROOT}/pubspec.yaml` exists.
2. It declares `widgetbook` and `widgetbook_annotation` as dependencies, plus `widgetbook_generator` and `build_runner` as dev dependencies.
3. It declares the host app package as a `path:` dependency (`path: ../`, or Melos workspace equivalent).
4. `{WIDGETBOOK_ROOT}/lib/main.dart` (or its equivalent entry file) references `directories` produced by `widgetbook_generator` (an `import` or `part` of `main.directories.g.dart` or `widgetbook.directories.g.dart`).

Resolve `WIDGETBOOK_ROOT` from `topology.repo_mode`:

| `repo_mode` | `WIDGETBOOK_ROOT` |
|---|---|
| `single_repo` / `multi_repo` | Nested inside the app repo root: `<app-root>/widgetbook/` |
| `monorepo_melos` | Nested inside the host package: `<host-package-root>/widgetbook/` (Single Widgetbook), or nested inside each cataloged package (Per-package Widgetbook) |

The Widgetbook directory is literally named `widgetbook`. `APPNAME` is `project.package_name` from `.sopp/config/project.config.yaml` — it names the app `path:` dependency, not the Widgetbook directory.

**If any signal is missing:** the project must be bootstrapped. The very first command is always, run literally from the app root (or the host package root in a monorepo):

```bash
flutter create widgetbook --empty --platforms=android,ios,web
```

Never satisfy the "missing project" case by hand-creating an empty folder named `widgetbook` or by writing files into a non-Flutter directory — the directory must be a real Flutter project produced by `flutter create`. Then continue with the full initialization sequence:

- For `single_repo` / `multi_repo`: run the full initialization sequence in `references/setup.md`.
- For `monorepo_melos`: run the full initialization sequence in `references/monorepo.md`.

Include every bootstrap-produced file in the phase's `--output-file` set so the workflow's gap report can diff it (see the "Bootstrap output files" section in each reference).

If the initialization command itself fails, stop with `blocked_input` and surface the captured error. Do not proceed to Step 0.

**If all four signals are present:** continue directly to Step 0.

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
| Theme and color tokens | ❌ not a knob | Come from the configured theme and token system |
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
- **Never** add knobs for theme or color tokens; they come from the configured theme
- **Never** use `print` in callbacks — use `developer.log(...)`
- **Never** add `part '*.g.dart'` inside `*.use_case.dart` files — this breaks code generation
- For `APP_SCREENS`: always use test mocks/providers, never real navigation

## Checklist

- [ ] Step -1 preflight passed (Widgetbook initialized or just bootstrapped)
- [ ] `WIDGETBOOK_SCOPE` defined (`DS_COMPONENTS` or `APP_SCREENS`)
- [ ] File `*_use_case.dart` at the correct path for the scope
- [ ] Required use cases covered for the scope
- [ ] `context.setCodePreview(...)` present in every use case
- [ ] `labelBuilder` on all enum/list knobs
- [ ] Not `print` — uses `developer.log`
- [ ] Not `part '*.g.dart'` in use case files
- [ ] `dart analyze` ran clean
- [ ] `dart run build_runner build --delete-conflicting-outputs` ran

## Reference files

| Topic | File |
|---|---|
| Setup (cold init for `single_repo` / `multi_repo`) | `references/setup.md` |
| Setup (cold init for `monorepo_melos`) | `references/monorepo.md` |
| Project structure | `references/project_structure.md` |
| Features guide | `references/features_guide.md` |
| Variants guide | `references/variants_guide.md` |
| Mocks | `references/mocks.md` |
| Knobs reference | `assets/knobs_reference.md` |
| Coverage audit | `references/coverage_audit.md` |
