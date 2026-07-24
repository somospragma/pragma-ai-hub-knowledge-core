# Widgetbook Project Structure

Before generating a use case, detect the structure already used by the Widgetbook project.

## Required Roots

```text
widgetbook_[appname]/lib/
├── ui_system/
├── features/
└── shared/
```

UI System components belong under `ui_system/`. Feature screens belong under `features/`. Shared catalog helpers belong under `shared/`.

## Legacy Migration

If `atoms/`, `molecules/`, `organisms/`, `components/`, or `widgets/` are directly under `widgetbook_[appname]/lib/`, create `ui_system/` and move those folders inside it.

## Classification

| Item | Location |
|---|---|
| Atom/molecule/organism/component | `lib/ui_system/...` |
| Feature screen/page/view | `lib/features/...` |
| Catalog helper | `lib/shared/...` |

Use Atomic Design classification only for UI System components. Screens always stay under `features/`.

## Regeneration

After adding use cases, run:

```bash
cd widgetbook_[appname]
dart run build_runner build --delete-conflicting-outputs
```
