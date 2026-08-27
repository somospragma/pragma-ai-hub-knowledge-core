# Widgetbook In Monorepos (Cold Init)

Use this reference when Step -1 of `SKILL.md` detects that Widgetbook is **not initialized** and the repo mode is `monorepo_melos`. For `single_repo` and `multi_repo` use `references/setup.md` instead.

## Detect a monorepo

Widgetbook must follow the monorepo path when any of these signals hold:

- `melos.yaml` exists at the monorepo root.
- The root `pubspec.yaml` declares a Dart pub workspace (Melos 7+).
- Multiple `pubspec.yaml` files exist under `apps/`, `packages/`, `features/`, `core/`, or `design_system/`.

If none of these signals exist, use `references/setup.md`.

## Choose a strategy

| Strategy | When to use it | Result |
|---|---|---|
| Single Widgetbook | One catalog documents UI from multiple packages/apps | One `apps/widgetbook_[appname]/` at the monorepo root |
| Per-package Widgetbook | Each package needs an independent catalog | One Widgetbook per package |

When unclear, ask the user. If there is no preference, prefer **Single Widgetbook** — this reference documents that path. For Per-package Widgetbook, apply the same sequence inside each target package instead of `apps/`.

## Detection (same as `references/setup.md`)

Widgetbook is considered initialized only when all four signals are true (see `references/setup.md` for the full list). The path checked is `apps/widgetbook_[appname]/` instead of a sibling directory.

## Initialization sequence (Single Widgetbook)

Working directory is the monorepo root.

### 1. Create the empty Flutter project inside `apps/`

```bash
flutter create apps/widgetbook_[appname] --empty
```

`APPNAME` is `project.package_name` from `.sopp/config/project.config.yaml`.

### 2. Install Widgetbook dependencies

```bash
cd apps/widgetbook_[appname]
flutter pub add widgetbook widgetbook_annotation \
  dev:widgetbook_generator dev:build_runner
```

### 3. Wire package dependencies

Choose **one** of the two options below based on the workspace mode.

**Option A — Melos 6 (or any Melos setup that uses explicit path deps):**

Edit `apps/widgetbook_[appname]/pubspec.yaml`. Add every package the catalog documents as a `path:` dependency:

```yaml
dependencies:
  [appname]:
    path: ../[appname]
  design_system:
    path: ../../packages/design_system
  # ...one entry per package cataloged (features/*, core, ui_kit, ...)
```

**Option B — Dart pub workspaces (Melos 7+):**

- Add `apps/widgetbook_[appname]` to the `workspace:` list in the root `pubspec.yaml`.
- Reference workspace packages as `any` inside `apps/widgetbook_[appname]/pubspec.yaml`:

```yaml
dependencies:
  [appname]: any
  design_system: any
  # workspace resolves these via the root pubspec.yaml
```

- Ensure each cataloged package declares `resolution: workspace` in its own `pubspec.yaml`.

Use Option B when the monorepo already uses `workspace:` in the root `pubspec.yaml`; use Option A otherwise. Do not mix the two styles in the same monorepo.

### 4. Scaffold the entry point

Same as `references/setup.md` step 4 (`main.dart` with `Widgetbook.material(directories: directories, ...)` and `import 'main.directories.g.dart';`). Place it at `apps/widgetbook_[appname]/lib/main.dart`.

### 5. Scaffold the folder structure

```text
apps/widgetbook_[appname]/lib/
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

For Melos 7+ pub workspaces, `dart pub get` at the monorepo root is enough when Melos is configured to defer resolution to pub workspaces; `melos bootstrap` remains the deterministic choice.

### 7. First build

```bash
cd apps/widgetbook_[appname]
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

In a Single-Widgetbook monorepo both usually resolve inside `apps/widgetbook_[appname]/lib/` (`ui_system/` for DS components, `features/` for app screens).

If either target's path in `project.config.yaml` still points at a legacy location that is not the monorepo Widgetbook root, stop and ask the user to update the config before generating use cases — do not silently write to the old path.

## Regeneration after adding use cases

```bash
melos bootstrap                    # only if pubspec dependencies changed
cd apps/widgetbook_[appname]
dart analyze lib/ui_system lib/features
dart run build_runner build --delete-conflicting-outputs
```

`dart analyze` must run **before** `build_runner`, same rule as `references/setup.md`.

## Assets

Assets used by cataloged widgets must be declared in `apps/widgetbook_[appname]/pubspec.yaml`, even when the underlying package is a workspace member. After editing assets:

```bash
cd apps/widgetbook_[appname]
flutter pub get
dart run build_runner build --delete-conflicting-outputs
```

## Bootstrap output files (for the workflow report)

When Step -1 triggers this sequence during `phase-4-3-ds-widgetbook` (new-component) or `phase-4-3-ds-widgetbook` / `phase-4-6-app-widgetbook` (new-view), include the newly created files in the phase's `--output-file` set:

- `apps/widgetbook_[appname]/pubspec.yaml`
- `apps/widgetbook_[appname]/lib/main.dart`
- `apps/widgetbook_[appname]/lib/main.directories.g.dart`
- `apps/widgetbook_[appname]/lib/ui_system/.gitkeep`
- `apps/widgetbook_[appname]/lib/features/.gitkeep`
- `apps/widgetbook_[appname]/lib/shared/.gitkeep`
- Root `pubspec.yaml` **only** when Option B was applied (workspace list edited).
- Root `melos.yaml` **only** when a Melos package list was edited.

## Source

Based on the Widgetbook Monorepo guide:
<https://docs.widgetbook.io/essentials/monorepo>
