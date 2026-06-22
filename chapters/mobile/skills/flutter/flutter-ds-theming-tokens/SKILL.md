---
id: flutter-ds-theming-tokens
version: 1.2.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-theming-tokens
description: >
  Design token catalog and theme access rules for Flutter Design System components.
  Use when generating widget code, resolving Figma values to Flutter tokens,
  writing tests that need theme setup, or auditing hardcoded values.
  Covers colors, spacing, radius, elevation, typography, and icon sizes.
---

# Theming Tokens

## Rule: Zero Hardcode

Every visual value in a DS component must come from the token catalog. If a value isn't in the catalog, it does not belong in the code.

**Forbidden patterns — these are always violations:**

```dart
// ❌ FORBIDDEN
Container(color: Color(0xFF6200EE))     // hex value
Container(color: Colors.red)            // fixed Flutter color
Text('Hi', style: TextStyle(fontSize: 14)) // magic number
Padding(padding: EdgeInsets.all(16))    // magic number

// ✅ CORRECT
Container(color: tokens.colors.brandPrimary)
Text('Hi', style: tokens.typography.bodyMedium)
Padding(padding: EdgeInsets.all({{DS_PREFIX}}Spacing.m))
```

When auditing code, flag **any** raw number, hex color, or `Colors.*` reference as a blocker.

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

## Spacing Token Quick Reference

| Token | Value | Use for |
|-------|-------|---------|
| `{{DS_PREFIX}}Spacing.none` | 0px | Gaps to eliminate |
| `{{DS_PREFIX}}Spacing.xs` | 4px | Icon-to-text gap |
| `{{DS_PREFIX}}Spacing.s` | 8px | Between related items |
| `{{DS_PREFIX}}Spacing.m` | 16px | Standard internal padding |
| `{{DS_PREFIX}}Spacing.l` | 24px | Section gaps |
| `{{DS_PREFIX}}Spacing.xl` | 32px | Large section gaps |
| `{{DS_PREFIX}}Spacing.xxl` | 48px | Page-level margins |
| `{{DS_PREFIX}}Spacing.xxxl` | 56px | Hero spacing |

## Border Radius Token Quick Reference

| Token | Value |
|-------|-------|
| `{{DS_PREFIX}}BorderRadius.xs` | 4px |
| `{{DS_PREFIX}}BorderRadius.s` | 8px |
| `{{DS_PREFIX}}BorderRadius.m` | 12px |
| `{{DS_PREFIX}}BorderRadius.l` | 16px |
| `{{DS_PREFIX}}BorderRadius.xl` | 24px |
| `{{DS_PREFIX}}BorderRadius.full` | 999px |

See [full token catalog](references/TOKEN-CATALOG.md) for colors, typography, elevation, and icon sizes.

## Test Setup

- Wrap widgets under test in `ThemeData` with light/dark extensions
- Use `pumpApp` helper for consistent theme injection
- Never use hex or `Colors.*` in assertions

## Customization

Project-specific tokens are documented in the catalog path defined in
`project.config.yaml` → `tokens.catalog_path`. Always verify token existence
before use.
