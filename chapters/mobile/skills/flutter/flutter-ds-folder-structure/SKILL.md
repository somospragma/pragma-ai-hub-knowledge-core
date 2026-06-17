---
id: flutter-ds-folder-structure
version: 1.4.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-folder-structure
description: >
  Official folder structure for the Flutter Design System package.
  Use when creating new files, locating existing components, setting up
  test paths, or verifying file placement during code audit.
  Covers lib/, test/, widgetbook/, and pipeline output directories.
  Always activate when adding new screens/views (go in lib/src/presentation/views/
  with private widgets using _ prefix), new DS atoms/molecules/organisms (go in
  lib/src/{level}/), or when a legacy path like lib/atoms/ is detected (register
  alert, keep new code in lib/src/).
---

# Folder Structure

## Directory Tree

See [full tree reference](references/TREE.md) for the complete expanded structure.

```
{{package_name}}/
├── lib/
│   ├── {{package_name}}.dart  ← Public barrel file
│   └── src/            ← Internal implementation
│       ├── atoms/      ← Level 1: Indivisible components
│       │   ├── buttons/
│       │   ├── inputs/
│       │   ├── text/
│       │   ├── images/
│       │   ├── indicators/
│       │   ├── feedback/
│       │   └── dividers/
│       ├── molecules/  ← Level 2: Atom compositions
│       │   ├── cards/
│       │   ├── list_items/
│       │   ├── search/
│       │   ├── forms/
│       │   ├── navigation/
│       │   └── feedback/
│       ├── organisms/  ← Level 3: Complex compositions
│       │   ├── cards/
│       │   ├── navigation/
│       │   ├── forms/
│       │   ├── lists/
│       │   └── feedback/
│       ├── tokens/     ← Design tokens
│       └── theme/      ← DS theme
├── test/               ← Mirrors lib/ structure
├── widgetbook/         ← Mirrors lib/ structure
├── [pipeline.output_dir]/
│   ├── [pipeline.log_file]
│   └── [pipeline.spec_file]
│
│  ── APP-LEVEL (fuera del paquete DS) ──
│
├── lib/src/presentation/ ← Vistas/pantallas de la app
│   ├── views/            ← Pantallas completas (Scaffold)
│   │   ├── home/
│   │   │   ├── home_view.dart
│   │   │   ├── _home_hero_section.dart
│   │   │   └── _home_content_list.dart
│   │   ├── detail/
│   │   │   └── detail_view.dart
│   │   └── ...
│   └── widgets/          ← Widgets privados de vistas
│       ├── empty_state_widget.dart
│       └── error_retry_widget.dart
└── test/presentation/  ← Tests de vistas
```

## Folder Rules

### Design System (paquete DS)
1. **Atoms**: Components with no DS widget dependencies
2. **Molecules**: Compose 2+ atoms
3. **Organisms**: Compose molecules + atoms into complete sections
4. **Subfolders** group by function: `buttons/`, `cards/`, `forms/`, etc.
5. **Implementation source** always lives under `lib/src`. The public
   `lib/{{package_name}}.dart` barrel exports only approved public APIs using
   `export 'src/...';`.
6. **Agents must search/propose implementation changes in `lib/src` first**.
   If a legacy layout exists (`lib/atoms`, `lib/presentation`, `lib/features`),
   register an alert and keep new code in the configured `lib/src` path unless
   project configuration explicitly overrides it.
7. **Large components** (>200 lines) get their own subfolder:
   ```
   lib/src/organisms/cards/product_card/
   ├── product_card.dart          # Public widget
   ├── _product_card_header.dart  # Private widget
   └── _product_card_body.dart    # Private widget
   ```
8. **Tests** cover the `lib/src` implementation from `test/`
9. **Widgetbook stories** replicate the public component taxonomy

### Vistas/Pantallas (app-level, fuera del DS)
10. **Views** live in `structure.views_path` (default: `lib/src/presentation/views/`)
11. **Each view** with private section widgets gets its own subfolder, and those private widgets use the **underscore prefix** (`_`) in their filename:
    ```
    lib/src/presentation/views/product_detail/
    ├── product_detail_view.dart          ← main view (no DS prefix)
    ├── _product_detail_hero_section.dart ← private widget (underscore prefix)
    └── _product_detail_content_list.dart ← private widget (underscore prefix)
    ```
12. **View widgets** shared across multiple views go to `structure.view_widgets_path` (e.g., `lib/src/presentation/widgets/`)
13. Views **do NOT** carry the DS prefix — they belong to the app, not the DS package
14. Views **do NOT** get exported in the DS barrel file (`lib/{{package_name}}.dart`)
15. En flujo canónico `/new-view`, la vista completa **sí** genera:
   - `test/presentation/views/[view]/[view]_view_golden_test.dart`
   - `{structure.widgetbook_screens_path}/features/[feature]/[view]/[view]_use_case.dart`
16. Los widgets privados de vista (`structure.view_widgets_path`) **no** generan
    golden/widgetbook dedicados.

### Artefactos de Pipeline (determinista)
17. Nunca hardcodear rutas de pipeline en prompts/agentes
18. Resolver siempre desde `project.config.yaml`:
   - `pipeline.output_dir`
   - `pipeline.log_file`
   - `pipeline.spec_file`
   - `structure.widgetbook_components_path` (fallback `structure.widgetbook_path`)
   - `structure.widgetbook_screens_path` (fallback `structure.widgetbook_path`)

## Path Mapping

### Componentes DS
| Level | Lib | Test | Widgetbook |
|-------|-----|------|------------|
| Atom | `lib/src/atoms/[sub]/` | `test/atoms/[sub]/` | `{structure.widgetbook_components_path}/atoms/[sub]/` |
| Molecule | `lib/src/molecules/[sub]/` | `test/molecules/[sub]/` | `{structure.widgetbook_components_path}/molecules/[sub]/` |
| Organism | `lib/src/organisms/[sub]/` | `test/organisms/[sub]/` | `{structure.widgetbook_components_path}/organisms/[sub]/` |

### Vistas (app-level)
| Tipo | Path | Test | Widgetbook |
|------|------|------|------------|
| View | `lib/src/presentation/views/[name]/` | `test/presentation/views/[name]/` | `{structure.widgetbook_screens_path}/features/[feature]/[name]/` |
| View Widget | `lib/src/presentation/widgets/` | `test/presentation/widgets/` | N/A (privado) |

> En flujo canónico `/new-view`, además de widget tests de vista también se genera:
> `test/presentation/views/[name]/[name]_view_golden_test.dart`.
