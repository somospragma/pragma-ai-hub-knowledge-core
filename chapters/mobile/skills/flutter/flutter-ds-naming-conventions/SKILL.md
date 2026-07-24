---
id: flutter-ds-naming-conventions
version: 1.3.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-naming-conventions
description: >
  Official naming conventions for the Flutter Design System.
  Use when creating files, classes, enums, variables, branches, commits,
  golden test outputs, or mapping Figma names to Dart identifiers.
---
# Naming Conventions

> **Scope**: This skill covers Design System-specific naming conventions (DS prefix, Figma-to-Dart mapping, DS branches, goldens). For the general Dart/Flutter code standard (general naming, imports, style, analysis_options), see `flutter-dart-coding-standard`.

## Files

| Type | Convention | Example |
|------|-----------|---------|
| Widget | `snake_case.dart` | `ds_button.dart` |
| Widget test | `*_test.dart` | `ds_button_test.dart` |
| Golden test | `*_golden_test.dart` | `ds_button_golden_test.dart` |
| Widgetbook story | `*_use_case.dart` | `ds_button_use_case.dart` |
| Token | `*_tokens.dart` | `spacing_tokens.dart` |
| Theme | `{{ds_prefix_snake}}_*.dart` | `ds_theme.dart` |
| Private part | `_[name].dart` | `_product_card_header.dart` |

> **Widgetbook note:** The DS uses `*_use_case.dart`, not the generic community convention `*.stories.dart`. Always use `_use_case.dart` in this codebase.

## Classes

| Type | Convention | Example |
|------|-----------|---------|
| Atom | `{{DS_PREFIX}}PascalCase` | `{{DS_PREFIX}}Button` |
| Molecule | `{{DS_PREFIX}}PascalCase` | `{{DS_PREFIX}}CardHeader` |
| Organism | `{{DS_PREFIX}}PascalCase` | `{{DS_PREFIX}}ProductCard` |
| State enum | `[Widget]State` | `{{DS_PREFIX}}ButtonState` |
| Variant enum | `[Widget]Variant` | `{{DS_PREFIX}}BadgeVariant` |
| Size enum | `[Widget]Size` | `{{DS_PREFIX}}ButtonSize` |

## Variables & Parameters

| Type | Convention | Example |
|------|-----------|---------|
| Widget param | `camelCase` | `labelText`, `isEnabled` |
| Callback (no arg) | `on` + `PascalCase` | `onPressed`, `onDismiss` |
| Callback (with arg) | `on` + `PascalCase` + `Changed` | `onValueChanged` |
| Private variable | `_camelCase` | `_isHovered` |
| Token constant | static `camelCase` | `spacingMd` |

## Enum Values

| Type | Convention | Example |
|------|-----------|---------|
| State | `camelCase` | `default_`, `disabled`, `loading` |
| Variant | `camelCase` | `primary`, `secondary`, `outlined` |
| Size | **Abbreviated** camelCase | `sm`, `md`, `lg` — NOT `small`, `medium`, `large` |

> **`default` is a reserved keyword in Dart.** Always use `default_` (with trailing underscore) for the default state value in enums. Using `default` will cause a compile error.

## Branches & Commits

Branch names and commit messages follow project configuration. See [full naming reference](references/NAMING-REFERENCE.md) for the complete table.

### Branch naming

Branches are prefixed by values from `project.config.yaml`:

```
# DS component work (new components, fixes, docs)
{naming.branch_prefix}[slug]        →  feat/ds-badge

# App view / screen work
{naming.view_branch_prefix}[slug]   →  feat/app-product-detail
```

The default `naming.branch_prefix` is `feat/ds-`. The slug is the component name in kebab-case — **no additional suffixes** like `-atom`, `-component`, or `-widget`.

```
✅  feat/ds-badge
✅  feat/ds-product-card
❌  feat/ds-badge-atom       ← don't add the atomic level to the slug
❌  feat/ds-add-badge        ← don't use action verbs in the slug
```

### Commits (Conventional Commits)

Commits use **no scope** — just `type: description`:

```
feat: add {{DS_PREFIX}}Badge atom component
test: add widget and golden tests for Badge
docs: add widgetbook stories for Badge
fix: Badge color token in disabled state
refactor: extract Badge colors to resolver
```

> Use scopeless format: `feat:` not `feat(ds):`. The DS context is implicit from the branch and repo.

## Figma → Dart Mapping

The algorithm for converting a Figma path to a Dart name:

1. **Class name**: `{{DS_PREFIX}}` + PascalCase of the *meaningful component segments*, **reversed** when order matters (e.g., `Card / Product` → `ProductCard`, not `CardProduct`)
2. **Variant segment**: becomes a named parameter backed by a `[Widget]Variant` enum. **Never** a named constructor or subclass.
3. **Size segment**: becomes a `[Widget]Size` enum with **abbreviated values** (`sm`, `md`, `lg`)

| Figma Name | Dart Class | Constructor call |
|-----------|-----------|-----------------|
| `Card / Product` | `{{DS_PREFIX}}ProductCard` (organism) | `{{DS_PREFIX}}ProductCard(...)` |
| `Badge` | `{{DS_PREFIX}}Badge` (atom) | `{{DS_PREFIX}}Badge(...)` |
| `Icon / Close` | `{{DS_PREFIX}}Icon` | `{{DS_PREFIX}}Icon(Icons.close, ...)` |
| `Button / Primary / Medium` | `{{DS_PREFIX}}Button` | `{{DS_PREFIX}}Button(variant: {{DS_PREFIX}}ButtonVariant.primary, size: {{DS_PREFIX}}ButtonSize.md, ...)` |
| `Input / Text / Default` | `{{DS_PREFIX}}TextField` | `{{DS_PREFIX}}TextField(state: {{DS_PREFIX}}TextFieldState.default_, ...)` |

**Common mistakes to avoid:**

- ❌ `DSCard.product()` — named constructors for variants. Use enum params instead: `DSCard(variant: .product)`
- ❌ `DSButtonSize.medium` — full word. Use the abbreviated form: `DSButtonSize.md`
- ❌ `DSPrimaryMediumButton` — encoding variant/size in the class name. Keep the class name clean: `DSButton`
