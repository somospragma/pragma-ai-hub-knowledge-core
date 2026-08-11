# Widgetbook In Monorepos

## Detect A Monorepo

Common signals:

- a legacy `melos.yaml`, or a root `pubspec.yaml` with `workspace:` and Melos configuration
- `apps/` folder with multiple apps
- multiple `pubspec.yaml` files under the same repository
- shared packages under `packages/`, `features/`, `core/`, or `design_system/`

If none of these signals exist, use the standard setup in `references/setup.md`.

## Choose A Strategy

| Strategy | When to use it | Result |
|---|---|---|
| Single Widgetbook | One catalog should include UI from multiple packages | One `widgetbook_[appname]/` at the monorepo root |
| Per-package Widgetbook | Each package needs an independent catalog | One Widgetbook per package/app |

When unclear, ask the user. If there is no preference, prefer Single Widgetbook for simplicity.

## Dependency Rule

In a Melos workspace, prefer package dependencies that Melos can resolve. For external packages or workspaces without Melos, use explicit `path:` dependencies.

After changing dependencies, run:

```bash
melos bootstrap
cd widgetbook_[appname]
flutter pub get
dart run build_runner build --delete-conflicting-outputs
```
