---
id: flutter-ds-widget-anatomy
version: 1.3.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-widget-anatomy
description: >
  Standard internal structure for a Design System widget file.
  Use when writing or reviewing Flutter widget code to ensure correct
  ordering of imports, constructor, properties, build methods,
  resolvers, enums, and helper classes.
---

# Widget Anatomy

## File Structure Order

Every DS widget file follows this exact 4-section order — no exceptions:

### 1. Imports
```dart
import 'package:flutter/material.dart';
import 'package:{{package_name}}/tokens/spacing_tokens.dart';
// Package imports only — never relative (../). Grouped: flutter → DS → third-party
```

### 2. Widget Class

The class body itself has a fixed internal order:

```dart
class {{DS_PREFIX}}WidgetName extends StatelessWidget {
  // 2a. Constructor — const, super.key, required first, callbacks last
  const {{DS_PREFIX}}WidgetName({
    super.key,
    required this.label,
    this.variant = {{DS_PREFIX}}WidgetNameVariant.primary,
    this.state = {{DS_PREFIX}}WidgetNameState.default_,
    this.onPressed,
  });

  // 2b. Final fields
  final String label;
  final {{DS_PREFIX}}WidgetNameVariant variant;
  final {{DS_PREFIX}}WidgetNameState state;
  final VoidCallback? onPressed;

  // 2c. Computed getters
  bool get _isInteractive =>
      state != {{DS_PREFIX}}WidgetNameState.disabled && onPressed != null;

  // 2d. build — thin dispatcher only, never contains layout logic directly
  @override
  Widget build(BuildContext context) {
    return switch (state) {
      {{DS_PREFIX}}WidgetNameState.loading  => _buildLoading(context),
      {{DS_PREFIX}}WidgetNameState.disabled => _buildDisabled(context),
      _                                     => _buildDefault(context),
    };
  }

  // 2e. _build* helpers — one per state
  Widget _buildDefault(BuildContext context) { /* layout */ }
  Widget _buildLoading(BuildContext context) { /* skeleton/spinner */ }
  Widget _buildDisabled(BuildContext context) {
    // Disabled = Opacity(0.5) wrapping IgnorePointer wrapping _buildDefault.
    // This pattern is mandatory — do not hardcode disabled styling inline.
    return Opacity(opacity: 0.5, child: IgnorePointer(child: _buildDefault(context)));
  }

  // 2f. _resolve* methods — token logic isolated per variant/state
  Color _resolveBackgroundColor(BuildContext context) {
    return switch (variant) { /* token per variant */ };
  }
}
```

### 3. Enums

Enums go **after** the widget class, not before. This keeps the public class name at the top of the file where readers look first, while the enums serve as a supporting reference below it.

```dart
enum {{DS_PREFIX}}WidgetNameState { default_, disabled, loading, focused, error }
enum {{DS_PREFIX}}WidgetNameVariant { primary, secondary }
enum {{DS_PREFIX}}WidgetNameSize { sm, md, lg }
```

> `default` is a reserved Dart keyword — always use `default_` (with trailing underscore).

### 4. Private Helper Classes (if needed)

Only acceptable when a helper is simple (< 30 lines). If it grows beyond that, extract it to its own file.

## Rules

1. **1 public widget per file** — no exceptions
2. **Enums** go in the same file, **after** the widget class
3. **Private helpers** only if simple (< 30 lines per helper)
4. **Imports**: package imports grouped and sorted, never relative
5. **Constructor**: `const`, `super.key`, required first, callbacks last
6. **Properties**: `final`, self-explanatory names
7. **Build**: delegates to `_build*` methods — the build method itself has no layout logic
8. **Disabled state**: always `Opacity(0.5)` + `IgnorePointer` wrapping `_buildDefault` — this is the DS standard pattern
9. **Resolvers**: `_resolve*` methods isolate all token resolution per variant/state from layout code
10. **Limits**: ~200 lines per file, ~30 lines per method
11. **Comments**: avoid inline/block/doc comments by default; allow only
    fundamental, non-obvious technical notes
