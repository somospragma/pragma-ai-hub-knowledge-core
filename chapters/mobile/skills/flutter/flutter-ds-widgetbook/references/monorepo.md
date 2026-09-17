# Widgetbook In Monorepos (Cold Init)

Use this reference when Step -1 of `SKILL.md` detects that Widgetbook is **not initialized** and the repo mode is `monorepo_melos`. For `single_repo` and `multi_repo` use `references/setup.md` instead.

Unlike the single-repo flow, Widgetbook is created as a **sibling** top-level Flutter project at the monorepo root, created with `flutter create` — not nested inside the app package or any other package. This is the official Widgetbook Single Widgetbook layout:

```
monorepo/
├── my_app/
├── packages/
│   └── my_design_system/
└── widgetbook/
```

Do not hand-create a plain folder named `widgetbook`; it must be a real Flutter project produced by `flutter create`.

## Detect a monorepo

Widgetbook must follow the monorepo path when any of these signals hold:

- `melos.yaml` exists at the monorepo root.
- The root `pubspec.yaml` declares a Dart pub workspace (Melos 7+).
- Multiple `pubspec.yaml` files exist under `apps/`, `packages/`, `features/`, `core/`, or `design_system/`.

If none of these signals exist, use `references/setup.md`.

## Default strategy: Single Widgetbook

**Single Widgetbook is the default and is applied automatically — do not ask the user to choose a strategy.** One catalog, created as a sibling `widgetbook/` directory at the monorepo root, documents UI from every cataloged package (host app, design system, and any other package in scope). This reference documents that path exclusively.

Only depart from Single Widgetbook when the user has explicitly requested independent per-package catalogs (one nested `widgetbook/` inside each package instead of a single sibling one). In that case, apply the equivalent sequence from `references/setup.md` inside each target package instead of following this reference.

## Naming and location

- `APPNAME` is `project.package_name` from `.sopp/config/project.config.yaml`. It names the app package `path:`/version dependency, not the Widgetbook directory.
- The Widgetbook project directory is literally named `widgetbook`.
- `WIDGETBOOK_ROOT` resolves to `<monorepo-root>/widgetbook/` — a sibling of the host app package and of `packages/`/`apps/`, never nested inside any of them.

## Detection (same as `references/setup.md`)

Widgetbook is considered initialized only when all four signals are true (see `references/setup.md` for the full list). The path checked is `<monorepo-root>/widgetbook/` (a sibling at the monorepo root), not a location nested inside the host app package or any other package.

## Initialization sequence (Single Widgetbook)

Working directory for **step 1** is the **monorepo root**.

### 1. Create the empty Flutter project at the monorepo root

```bash
flutter create widgetbook --empty --platforms=android,ios,web
```

Run this command literally, from the monorepo root, so `widgetbook/` is created as a real Flutter project sibling to `packages/`/`apps/` and the host app package. Never hand-create a plain folder named `widgetbook`.

### 2. Install Widgetbook dependencies

```bash
cd widgetbook
flutter pub add widgetbook widgetbook_annotation \
  dev:widgetbook_generator dev:build_runner
```

### 3. Wire package dependencies

Choose **one** of the two options below. Option A is the default; only switch to Option B if Melos bootstrap fails to resolve the packages under Option A.

**Option A — Path dependencies (default):**

Edit `widgetbook/pubspec.yaml`, adding the host app and every additional cataloged package as a `path:` dependency relative to the sibling `widgetbook/` directory:

```yaml
name: widgetbook_workspace

dependencies:
  widgetbook_annotation: ^3.11.0
  widgetbook: ^3.25.0
  [design_system_package]:
    path: ../packages/[design_system_package]
  [appname]:
    path: ../[appname]
  # ...one path: entry per additional package cataloged (features/*, core, ui_kit, ...)

dev_dependencies:
  build_runner:
  widgetbook_generator: ^3.24.0
```

Adjust each `path:` to the package's actual location relative to `widgetbook/` (e.g. `../apps/[appname]` or `../packages/[package]`, depending on the monorepo layout).

**Option B — Version dependencies + Melos registration (only if Melos dependency issues arise):**

> If you run into dependency issues when using [Melos](https://melos.invertase.dev/) you might need to change how you bootstrap the dependencies.

Change `widgetbook/pubspec.yaml` to reference each local package by version instead of `path:`:

```yaml
name: widgetbook_workspace

dependencies:
  widgetbook_annotation: ^3.11.0
  widgetbook: ^3.25.0
  [design_system_package]: ^1.0.0
  [appname]: ^1.0.0

dev_dependencies:
  build_runner:
  widgetbook_generator: ^3.24.0
```

Then register the sibling `widgetbook/` directory in the root `melos.yaml`'s `packages:` list so Melos resolves the local versions to local paths:

```yaml
name: my_project

packages:
  - apps/**
  - packages/**
  - widgetbook/
```

Run `melos bootstrap` to configure the dependencies. Do not mix the two styles (`path:` and version) for the same package in `widgetbook/pubspec.yaml`.

### 4. Scaffold the entry point

Same as `references/setup.md` step 4 (`main.dart` with `Widgetbook.material(directories: directories, ...)` and `import 'main.directories.g.dart';`). Place it at `<monorepo-root>/widgetbook/lib/main.dart`.

### 5. Scaffold the folder structure

```text
widgetbook/lib/
├── main.dart
├── ui_system/    # DS_COMPONENTS use cases
├── features/     # APP_SCREENS use cases
└── shared/       # catalog helpers, mocks, wrappers
```

Create the three folders with a `.gitkeep` each before any use case exists.

### 6. Bootstrap the workspace

```bash
melos bootstrap
```

### 7. First build

```bash
cd widgetbook
dart run build_runner build --delete-conflicting-outputs
```

This must generate `main.directories.g.dart` with an initially empty `directories` list.

### 8. Smoke run

```bash
flutter run -d chrome
```

The catalog must open with no use cases and no runtime errors. Only after this succeeds may Step 0 of `SKILL.md` start generating `*_use_case.dart` files.

## Path resolution for use cases

Use case output paths still come from `project.config.yaml`:

- `targets.registry[DESIGN_SYSTEM_TARGET_ID].structure.widgetbook_components_path`
- `targets.registry[APP_TARGET_ID].structure.widgetbook_screens_path`

In a Single-Widgetbook monorepo both usually resolve inside `<monorepo-root>/widgetbook/lib/` (`ui_system/` for DS components, `features/` for app screens).

If either target's path in `project.config.yaml` still points at a legacy location nested inside a package (pre-dating the sibling Single Widgetbook default), stop and ask the user to update the config before generating use cases — do not silently write to the old path.

## Regeneration after adding use cases

```bash
melos bootstrap                    # only if pubspec dependencies changed
cd widgetbook
dart analyze lib/ui_system lib/features
dart run build_runner build --delete-conflicting-outputs
```

`dart analyze` must run **before** `build_runner`, same rule as `references/setup.md`.

## Assets

Assets used by cataloged widgets must be declared in `widgetbook/pubspec.yaml`, even when the underlying package is a workspace member. After editing assets:

```bash
cd widgetbook
flutter pub get
dart run build_runner build --delete-conflicting-outputs
```

## Bootstrap output files (for the workflow report)

When Step -1 triggers this sequence during `phase-5-ds-widgetbook` (new-component) or `phase-5-ds-widgetbook` / `phase-6-ds-widgetbook` (new-view) or `phase-8-view-widgetbook`, include the newly created files in the phase's `--output-file` set. Paths are relative to the monorepo root — `widgetbook/` is already a top-level sibling, no host package prefix is needed:

- `widgetbook/pubspec.yaml`
- `widgetbook/lib/main.dart`
- `widgetbook/lib/main.directories.g.dart`
- `widgetbook/lib/ui_system/.gitkeep`
- `widgetbook/lib/features/.gitkeep`
- `widgetbook/lib/shared/.gitkeep`
- Root `melos.yaml` **only** when Option B was applied (`packages:` list edited to add `widgetbook/`).

## Source

Based on the Widgetbook Monorepo guide:
<https://docs.widgetbook.io/essentials/monorepo>
