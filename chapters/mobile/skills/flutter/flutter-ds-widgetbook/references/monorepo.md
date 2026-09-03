# Widgetbook In Monorepos (Cold Init)

Use this reference when Step -1 of `SKILL.md` detects that Widgetbook is **not initialized** and the repo mode is `monorepo_melos`. For `single_repo` and `multi_repo` use `references/setup.md` instead.

As in the single-repo flow, Widgetbook is created as a **nested** `widgetbook/` Flutter project inside its host — the app package (or the documented package), created with `flutter create`. Do not create a sibling directory and do not hand-create a plain folder named `widgetbook`.

## Detect a monorepo

Widgetbook must follow the monorepo path when any of these signals hold:

- `melos.yaml` exists at the monorepo root.
- The root `pubspec.yaml` declares a Dart pub workspace (Melos 7+).
- Multiple `pubspec.yaml` files exist under `apps/`, `packages/`, `features/`, `core/`, or `design_system/`.

If none of these signals exist, use `references/setup.md`.

## Choose a strategy

| Strategy | When to use it | Result |
|---|---|---|
| Single Widgetbook | One catalog documents UI from multiple packages/apps | One `widgetbook/` nested inside the host app package |
| Per-package Widgetbook | Each package needs an independent catalog | One nested `widgetbook/` per package |

When unclear, ask the user. If there is no preference, prefer **Single Widgetbook** — this reference documents that path. For Per-package Widgetbook, apply the same sequence inside each target package instead of the host app.

## Naming and location

- `APPNAME` is `project.package_name` from `.sopp/config/project.config.yaml`. It names the app package `path:` dependency, not the Widgetbook directory.
- The Widgetbook project directory is literally named `widgetbook`.
- `WIDGETBOOK_ROOT` resolves to `<host-package-root>/widgetbook/`. For Single Widgetbook the host is the app package (e.g. `apps/[appname]/widgetbook/` or `[appname]/widgetbook/`, depending on the monorepo layout). For Per-package Widgetbook the host is the package being cataloged.

## Detection (same as `references/setup.md`)

Widgetbook is considered initialized only when all four signals are true (see `references/setup.md` for the full list). The path checked is `<host-package-root>/widgetbook/` (nested inside the host package), not a sibling or a top-level `apps/` entry.

## Initialization sequence (Single Widgetbook)

Working directory for **step 1** is the **host app package root** (the directory that owns the app `pubspec.yaml`).

### 1. Create the empty Flutter project inside the host package

```bash
flutter create widgetbook --empty --platforms=android,ios,web
```

Run this command literally, from the host package root, so `widgetbook/` is created as a real nested Flutter project. Never hand-create a plain folder named `widgetbook`.

### 2. Install Widgetbook dependencies

```bash
cd widgetbook
flutter pub add widgetbook widgetbook_annotation \
  dev:widgetbook_generator dev:build_runner
```

### 3. Wire package dependencies

Choose **one** of the two options below based on the workspace mode.

**Option A — Melos 6 (or any Melos setup that uses explicit path deps):**

Edit `widgetbook/pubspec.yaml`. Add the host app as `path: ../` and every additional package the catalog documents as a `path:` dependency relative to `widgetbook/`:

```yaml
dependencies:
  [appname]:
    path: ../
  design_system:
    path: ../../../packages/design_system
  # ...one entry per package cataloged (features/*, core, ui_kit, ...)
```

Adjust the relative depth of each extra `path:` to match where `widgetbook/` sits inside the monorepo.

**Option B — Dart pub workspaces (Melos 7+):**

- Add the nested `widgetbook` path (relative to the monorepo root, e.g. `apps/[appname]/widgetbook`) to the `workspace:` list in the root `pubspec.yaml`.
- Reference workspace packages as `any` inside `widgetbook/pubspec.yaml`:

```yaml
dependencies:
  [appname]: any
  design_system: any
  # workspace resolves these via the root pubspec.yaml
```

- Ensure each cataloged package declares `resolution: workspace` in its own `pubspec.yaml`.

Use Option B when the monorepo already uses `workspace:` in the root `pubspec.yaml`; use Option A otherwise. Do not mix the two styles in the same monorepo.

### 4. Scaffold the entry point

Same as `references/setup.md` step 4 (`main.dart` with `Widgetbook.material(directories: directories, ...)` and `import 'main.directories.g.dart';`). Place it at `<host-package-root>/widgetbook/lib/main.dart`.

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

For Melos 7+ pub workspaces, `dart pub get` at the monorepo root is enough when Melos is configured to defer resolution to pub workspaces; `melos bootstrap` remains the deterministic choice.

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

In a Single-Widgetbook monorepo both usually resolve inside `<host-package-root>/widgetbook/lib/` (`ui_system/` for DS components, `features/` for app screens).

If either target's path in `project.config.yaml` still points at a legacy location that is not the nested Widgetbook root, stop and ask the user to update the config before generating use cases — do not silently write to the old path.

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

When Step -1 triggers this sequence during `phase-4-3-ds-widgetbook` (new-component) or `phase-4-3-ds-widgetbook` / `phase-4-6-app-widgetbook` (new-view), include the newly created files in the phase's `--output-file` set. Paths are relative to the monorepo root — prefix `widgetbook/` with the host package path (e.g. `apps/[appname]/`):

- `<host-package-path>/widgetbook/pubspec.yaml`
- `<host-package-path>/widgetbook/lib/main.dart`
- `<host-package-path>/widgetbook/lib/main.directories.g.dart`
- `<host-package-path>/widgetbook/lib/ui_system/.gitkeep`
- `<host-package-path>/widgetbook/lib/features/.gitkeep`
- `<host-package-path>/widgetbook/lib/shared/.gitkeep`
- Root `pubspec.yaml` **only** when Option B was applied (workspace list edited).
- Root `melos.yaml` **only** when a Melos package list was edited.

## Source

Based on the Widgetbook Monorepo guide:
<https://docs.widgetbook.io/essentials/monorepo>
