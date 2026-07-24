# Widgetbook Coverage Audit

Use this reference to find components and screens that exist in the main project but are not represented in Widgetbook.

## When To Run

| Situation | Action |
|---|---|
| Widgetbook was added to a project with existing UI | Audit the full UI System |
| New screens were added | Audit Features |
| The user asks what is missing from Widgetbook | Run a full audit |
| Delivery needs a coverage snapshot | Run a full audit |

## Process

1. Scan UI System widgets in the main project.
2. Scan screens/pages/views in the main project.
3. Scan existing `*.use_case.dart` files in `widgetbook_[appname]/lib/ui_system` and `widgetbook_[appname]/lib/features`.
4. Cross-check source widgets/screens against use cases.
5. Present a coverage report before generating anything.
6. Generate approved missing use cases.
7. Run `dart run build_runner build --delete-conflicting-outputs` inside the Widgetbook package.
8. Repeat the scan and report the updated coverage.

## Useful Commands

```bash
find lib -name "*.dart" -path "*/widgets/*" -or          -name "*_widget.dart" -or          -name "*_button.dart" -or          -name "*_card.dart" -or          -name "*_field.dart" | sort

find lib -name "*_screen.dart" -or          -name "*_page.dart" -or          -name "*_view.dart" | grep -v widgetbook | sort

find widgetbook_[appname]/lib -name "*.use_case.dart" | sort
```

## Exclusions

Do not catalog mixins, extensions, themes, models, entities, providers, blocs, cubits, services, repositories, barrels, private widgets, or generic layout wrappers without meaningful public props.

## Report Template

```markdown
## Widgetbook Audit - [project name]

**UI System** - X/Y cataloged (Z%)
- [x] ComponentA -> already has a use case
- [ ] ComponentB -> missing use case -> lib/path/component_b.dart

**Features** - X/Y cataloged (Z%)
- [x] ScreenA -> already has a use case
- [ ] ScreenB -> missing use case -> lib/features/feature/screen_b.dart

**Action proposal:** create the N missing use cases. Should I proceed with all, or prioritize some first?
```
