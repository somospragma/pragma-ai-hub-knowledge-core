---
id: flutter-ds-theming-tokens
version: 1.1.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
description: >
  Design token catalog and theme access rules for Flutter Design System components.
  Use when generating widget code, resolving Figma values to Flutter tokens,
  writing tests that need theme setup, or auditing hardcoded values.
  Covers colors, spacing, radius, elevation, typography, and icon sizes.
---

# Theming Tokens

## Rule: Zero Hardcode

- If it's not in the token catalog, it MUST NOT be used.
- **FORBIDDEN**: hex values (`0xFF...`), fixed colors (`Colors.red`), magic numbers (`12.0`).

## Token Access Methods

### Option A: Context Extension (default)

Config: `project.config.yaml` → `tokens.access_method: "context_extension"`

```dart
import 'package:{{package_name}}/{{package_name}}.dart';

final tokens = context.tokens;
final color = tokens.colors.backgroundDefaultSurface;
final spacing = {{DS_PREFIX}}Spacing.m;
```

### Option B: Theme.of(context)

Config: `project.config.yaml` → `tokens.access_method: "theme_of"`

```dart
final primary = Theme.of(context).colorScheme.primary;
final success = Theme.of(context).extension<DSColors>()!.success;
final bodyLarge = Theme.of(context).textTheme.bodyLarge;
```

## Quick Reference

See [full token catalog](references/TOKEN-CATALOG.md) for complete tables.

### Spacing Tokens

| Token | Value |
|-------|-------|
| `{{DS_PREFIX}}Spacing.none` | 0px |
| `{{DS_PREFIX}}Spacing.xs` | 4px |
| `{{DS_PREFIX}}Spacing.s` | 8px |
| `{{DS_PREFIX}}Spacing.m` | 16px |
| `{{DS_PREFIX}}Spacing.l` | 24px |
| `{{DS_PREFIX}}Spacing.xl` | 32px |
| `{{DS_PREFIX}}Spacing.xxl` | 48px |
| `{{DS_PREFIX}}Spacing.xxxl` | 56px |

### Border Radius Tokens

| Token | Value |
|-------|-------|
| `{{DS_PREFIX}}BorderRadius.xs` | 4px |
| `{{DS_PREFIX}}BorderRadius.s` | 8px |
| `{{DS_PREFIX}}BorderRadius.m` | 12px |
| `{{DS_PREFIX}}BorderRadius.l` | 16px |
| `{{DS_PREFIX}}BorderRadius.xl` | 24px |
| `{{DS_PREFIX}}BorderRadius.full` | 999px |

## Forbidden Patterns

```dart
// ❌ FORBIDDEN
Container(color: Color(0xFF6200EE))
Text('Hello', style: TextStyle(fontSize: 14))
Padding(padding: EdgeInsets.all(16))

// ✅ CORRECT
Container(color: tokens.colors.brandPrimary)
Text('Hello', style: tokens.typography.bodyMedium)
Padding(padding: EdgeInsets.all({{DS_PREFIX}}Spacing.m))
```

## Test Setup

- Wrap widgets under test in `ThemeData` with light/dark extensions
- Use `pumpApp` helper for consistent theme injection
- Never use hex or `Colors.*` in assertions

## Customization

Project-specific tokens are documented in the catalog path defined in
`project.config.yaml` → `tokens.catalog_path`. Always verify token existence
before use.
