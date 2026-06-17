---
id: flutter-ds-component-template
version: 1.3.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-component-template
description: >
  Base templates for creating Flutter Design System components by atomic level.
  Use when generating new atom, molecule, or organism widget code.
  Provides starter code structure with proper anatomy, tokens, and patterns.
  Always activate when writing a new DS widget to ensure correct _build*/_resolve* structure and token-based spacing.
---

# Component Templates

## When to Use

- **Atom**: Use [atom template](assets/atom_template.dart.txt) for indivisible components
- **Molecule**: Use [molecule template](assets/molecule_template.dart.txt) for 2+ atom compositions
- **Organism**: Use [organism template](assets/organism_template.dart.txt) for complete UI sections

## Atom Rules

- No DS widget dependencies — purely standalone
- Resolves its own colors/tokens per state and variant
- Prefix: `{{DS_PREFIX}}` + name
- Constructor: `const`, `super.key`, required params first, callbacks last
- **`build()` must delegate to `_build*` methods** — one per state (`_buildDefault`, `_buildLoading`, etc.). Never put rendering logic directly in `build()`.
- **`_resolve*` methods** handle token lookup per variant/state (e.g., `_resolveBackgroundColor`, `_resolvePadding`). Never hardcode tokens inline.

```dart
// ✅ Correct structure
@override
Widget build(BuildContext context) {
  return switch (state) {
    DSButtonState.loading  => _buildLoading(context),
    DSButtonState.disabled => Opacity(opacity: 0.5, child: IgnorePointer(child: _buildDefault(context))),
    _                      => _buildDefault(context),
  };
}

Widget _buildDefault(BuildContext context) { ... }
Widget _buildLoading(BuildContext context) { ... }
Color _resolveBackgroundColor() => switch (variant) { ... };
EdgeInsets _resolvePadding() => switch (size) { ... };

// ❌ Wrong — separate widget classes per variant instead of _build*/_resolve*
class _PrimaryButton extends StatelessWidget { ... }
class _SecondaryButton extends StatelessWidget { ... }
```

## Molecule Rules

- **IMPORT and USE** atoms from DS — never recreate functionality
- **DELEGATE** visual properties to child atoms
- **PROPAGATE** states to child atoms
- **PARAMETERS** are data (`String title`), NOT widgets (`Widget header`)
- **SPACINGS** between children use tokens — never hardcoded pixel values like `SizedBox(width: 8)` or `EdgeInsets.only(top: 4)`; use `SizedBox(height: DSSpacing.xs)` or `SizedBox(width: DSSpacing.sm)`
- **TEXT** values come from the Figma literal text contract; do not rewrite copy
- **OVERFLOW** in horizontal layouts is mitigated with `Flexible`/`Expanded` or
  `Wrap` when allowed by the contract

```dart
// ✅ Token-based spacing in a molecule
Column(
  children: [
    DSText(text: currentPrice, variant: DSTextVariant.priceCurrent),
    SizedBox(height: DSSpacing.xxs),  // ✅ token
    DSBadge(label: discountLabel!, variant: DSBadgeVariant.discount),
  ],
)

// ❌ Hardcoded spacing — not allowed
Column(
  children: [
    DSText(text: currentPrice, ...),
    SizedBox(height: 4),   // ❌ magic number
    DSBadge(label: discountLabel!, ...),
  ],
)
```

## Organism Rules

- Compose **molecules + atoms** into complete sections
- Use **Material** for elevation and surface
- **Multiple callbacks** (one per user action)
- Implement **responsiveness** with `LayoutBuilder`
- **Complete skeleton** in loading (not just parts)
- Directly fulfills **HU acceptance criteria**
- Preserve Figma literal texts and do not add extra UX/copy
- Use scroll/SafeArea/flexible constraints to avoid overflow in full sections

## Template Structure

Every template follows this internal order:

1. Imports (package imports, grouped)
2. Widget class
   - 2a. Const constructor
   - 2b. Final properties with explicit names
   - 2c. Computed getters
   - 2d. `build()` → switch by state
   - 2e. `_build*` private methods
   - 2f. `_resolve*` private methods
3. Enums (State, Variant, Size)
4. Private helper classes (if needed)
5. Comments only in fundamental exceptions (non-obvious rationale)
