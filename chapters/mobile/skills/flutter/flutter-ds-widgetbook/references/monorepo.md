# Monorepo — Widgetbook Setup in a Monorepository

---

## Table of contents

1. [Detect whether it's a monorepo](#1-detect-whether-its-a-monorepo)
2. [Choose a strategy](#2-choose-a-strategy)
3. [Strategy A — Single Widgetbook](#3-strategy-a--single-widgetbook)
4. [Strategy B — Per-package Widgetbook](#4-strategy-b--per-package-widgetbook)
5. [Setup with Melos](#5-setup-with-melos)
6. [Commands in a monorepo](#6-commands-in-a-monorepo)

---

## 1. Detect whether it's a monorepo

Look for these indicators:

| Indicator | Meaning |
|---|---|
| A `melos.yaml` file at the root | Monorepo managed with Melos |
| A `packages/` folder with subfolders that have a `pubspec.yaml` | Monorepo with shared packages |
| An `apps/` folder with multiple apps | Multi-app monorepo |
| Multiple `pubspec.yaml` files in subdirectories of the same repository | Manual monorepo |

If **none** of these indicators is present → use the standard setup in `references/setup.md`.

---

## 2. Choose a strategy

| Strategy | When to use it | Result |
|---|---|---|
| **Single Widgetbook** | You want a single catalog with components from every package | One `widgetbook_[appname]/` folder at the monorepo root |
| **Per-package Widgetbook** | Each package has its own independent catalog | One `widgetbook_[appname]/` folder inside each package/app |

If it's unclear which one to choose, **ask the user**. If the user has no preference, prefer **Single Widgetbook** for simplicity.

---

## 3. Strategy A — Single Widgetbook

A single Widgetbook at the monorepo root that catalogs components from every package.

### Monorepo structure

```
monorepo/
├── my_app/
├── packages/
│   └── my_design_system/
└── widgetbook_[appname]/                  ← Single Widgetbook for the whole monorepo
    ├── pubspec.yaml
    ├── build.yaml
    └── lib/
        ├── main.dart
        ├── ui_system/
        ├── features/
        └── shared/
```

### widgetbook_[appname]/pubspec.yaml

```yaml
name: widgetbook_workspace
description: Component catalog for the monorepo

publish_to: none

environment:
  sdk: '>=3.0.0 <4.0.0'
  flutter: '>=3.19.0'

dependencies:
  flutter:
    sdk: flutter
  widgetbook: ^3.22.0
  widgetbook_annotation: ^3.22.0
  # Reference every monorepo package that contains widgets to catalog
  my_design_system:
    path: ../packages/my_design_system
  my_app:
    path: ../my_app

dev_dependencies:
  widgetbook_generator: ^3.22.0
  build_runner:
  flutter_test:
    sdk: flutter
```

> **Key point:** Every package that contains widgets to catalog must appear as a dependency
> with a `path:` relative to the `widgetbook_[appname]/` folder.

### build.yaml (same as the standard setup)

```yaml
targets:
  $default:
    builders:
      widgetbook_generator:
        options:
          root_dir: lib
```

### Imports in the use cases

Use cases import widgets using the corresponding package name:

```dart
// Design system widget (shared package)
import 'package:my_design_system/my_design_system.dart';

// Main app widget
import 'package:my_app/my_app.dart';
```

---

## 4. Strategy B — Per-package Widgetbook

Each package or app has its own independent Widgetbook. More flexible, but it requires maintaining multiple catalogs.

### Monorepo structure

```
monorepo/
├── my_app/
│   └── widgetbook_my_app/              ← App Widgetbook
│       ├── pubspec.yaml
│       └── lib/
├── packages/
│   └── my_design_system/
│       └── widgetbook_my_design_system/          ← Design system Widgetbook
│           ├── pubspec.yaml
│           └── lib/
```

### my_app/widgetbook_my_app/pubspec.yaml

```yaml
name: my_app_widgetbook_workspace
description: Component catalog for my_app

publish_to: none

environment:
  sdk: '>=3.0.0 <4.0.0'
  flutter: '>=3.19.0'

dependencies:
  flutter:
    sdk: flutter
  widgetbook: ^3.22.0
  widgetbook_annotation: ^3.11.0
  my_app:
    path: ../

dev_dependencies:
  widgetbook_generator: ^3.22.0
  build_runner:
  flutter_test:
    sdk: flutter
```

### packages/my_design_system/widgetbook_my_design_system/pubspec.yaml

```yaml
name: my_design_system_widgetbook_workspace
description: Component catalog for the Design System

publish_to: none

environment:
  sdk: '>=3.0.0 <4.0.0'
  flutter: '>=3.19.0'

dependencies:
  flutter:
    sdk: flutter
  widgetbook: ^3.22.0
  widgetbook_annotation: ^3.11.0
  my_design_system:
    path: ../

dev_dependencies:
  widgetbook_generator: ^3.22.0
  build_runner:
  flutter_test:
    sdk: flutter
```

> **Note:** Each widgetbook references **only** its parent package with `path: ../`.

---

## 5. Setup with Melos

If the monorepo uses [Melos](https://melos.invertase.dev/) to manage dependencies:

### melos.yaml

```yaml
name: my_project

packages:
  - apps/**
  - packages/**
  - widgetbook_[appname]/          # Single Widgetbook at the root
  # Or for per-package:
  # - apps/**/widgetbook_*/
  # - packages/**/widgetbook_*/
```

### Widgetbook pubspec.yaml (with Melos)

When Melos manages dependencies, use **versions** instead of `path:`:

```yaml
name: widgetbook_workspace

dependencies:
  flutter:
    sdk: flutter
  widgetbook: ^3.22.0
  widgetbook_annotation: ^3.11.0
  my_design_system: ^1.0.0       # Melos resolves the path automatically
  my_app: ^1.0.0                 # Melos resolves the path automatically

dev_dependencies:
  widgetbook_generator: ^3.22.0
  build_runner:
```

After configuring, run:

```bash
melos bootstrap
```

> **If you run into dependency issues with Melos:** switch from versions (`^1.0.0`) to explicit
> paths (`path: ../packages/my_design_system`) or vice versa, depending on which one resolves
> the conflicts.

---

## 6. Commands in a monorepo

```bash
# Single Widgetbook — from the monorepo root
cd widgetbook_[appname] && flutter pub get
cd widgetbook_[appname] && dart run build_runner build --delete-conflicting-outputs
cd widgetbook_[appname] && flutter run -d chrome

# Per-package — from each individual widgetbook
cd my_app/widgetbook_my_app && flutter pub get
cd my_app/widgetbook_my_app && dart run build_runner build --delete-conflicting-outputs

cd packages/my_design_system/widgetbook_my_design_system && flutter pub get
cd packages/my_design_system/widgetbook_my_design_system && dart run build_runner build --delete-conflicting-outputs

# With Melos — global bootstrap
melos bootstrap
```

---

## Reference

Official documentation: [docs.widgetbook.io/essentials/monorepo](https://docs.widgetbook.io/essentials/monorepo)
