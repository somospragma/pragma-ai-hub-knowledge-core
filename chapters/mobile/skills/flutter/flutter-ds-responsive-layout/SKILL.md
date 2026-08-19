---
id: flutter-ds-responsive-layout
version: 1.2.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-responsive-layout
description: >
  Responsive layout patterns for Design System components.
  Use when implementing organisms that adapt to different screen sizes,
  deciding between compact and default layouts, or handling platform
  differences (mobile vs desktop).
---
# Responsive Layout

## When to Apply

| Level | Responsive? | Reasoning |
|-------|-------------|-----------|
| **Atom** | Generally NO | Adapt by flex; no layout switching needed |
| **Molecule** | Rarely | Only if horizontal layout may collapse |
| **Organism** | **Always — no exceptions** | Organisms own their layout; must handle all screen sizes |

Every organism must explicitly decide how it handles narrow screens. This is not optional.

## Primary Pattern: LayoutBuilder

```dart
@override
Widget build(BuildContext context) {
  return LayoutBuilder(
    builder: (context, constraints) {
      if (constraints.maxWidth < 360) {
        return _buildCompact(context);
      }
      return _buildDefault(context);
    },
  );
}
```

Use `LayoutBuilder` over `MediaQuery` for component-level breakpoints. `LayoutBuilder` reacts to the **container's** available width, which is correct when the component lives inside grids, sidebars, or multi-column layouts where available width ≠ screen width.

## Breakpoints

| Breakpoint | Width | Usage |
|-----------|-------|-------|
| Compact | < 360px | Very small devices — use compact/vertical layout |
| Mobile | 360–599px | Phones (default layout) |
| Tablet | 600–1023px | Tablets |
| Desktop | ≥ 1024px | Desktop/Web |

## Platform Max Widths

DS components have fixed max widths per platform. Apply these via `ConstrainedBox`, **never** as a `SizedBox` with a fixed width in production code.

| Platform | Max Width | Applies to |
|---------|-----------|------------|
| **Mobile** (Android / iOS) | **327 px** | Default for phones |
| **Desktop** (macOS / Windows / Linux) | **610 px** | Wider layout on desktop |

```dart
class ProductCard extends StatelessWidget {
  const ProductCard({super.key, this.platform = TargetPlatform.android});
  final TargetPlatform platform;

  bool get _isDesktop =>
      platform == TargetPlatform.macOS ||
      platform == TargetPlatform.windows ||
      platform == TargetPlatform.linux;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: BoxConstraints(maxWidth: _isDesktop ? 610 : 327),
      child: _isDesktop ? _buildDesktop(context) : _buildMobile(context),
    );
  }
}
```

> `SizedBox(width: 327)` is **only** acceptable in golden tests. In production widgets, always use `ConstrainedBox` so the component can still shrink when placed in a narrower container.

## Sizing Patterns

```dart
// ✅ Flexible — adapts to container
MainAxisSize.min  // Only what it needs
Expanded          // Fills available space

// ✅ Constrained — with limits
ConstrainedBox(constraints: BoxConstraints(minWidth: 200, maxWidth: 400))

// ❌ AVOID — Fixed width hardcoded (only in golden tests)
SizedBox(width: 327)
```

## Overflow Prevention

### Figma text fidelity rule

The Figma copy is the source of truth. **Never shorten, translate, or rewrite the text from Figma to avoid overflow.** The layout adapts — the text does not change.

- Add `TextOverflow.ellipsis` **only** when Figma or the technical contract explicitly specifies truncation.
- If Figma is silent about overflow: allow wrapping (default behavior), warn in the PR, and don't block delivery.

### Text in Rows

Put text inside `Flexible` or `Expanded` when it shares horizontal space with icons, badges, buttons, prices, counters, or trailing actions:

```dart
Row(
  children: [
    Icon(icon),
    SizedBox(width: spacing),
    Expanded(
      child: Text(
        title,
        maxLines: maxLinesFromFigma,   // ← from Figma spec, not defaulted
        overflow: overflowFromFigma,   // ← from Figma spec, not defaulted
      ),
    ),
  ],
)
```

### Horizontal Groups

- Use `Wrap` for chips, tags, secondary actions, filters, or badges only when wrapping does not contradict the Figma composition.
- Use `SingleChildScrollView(scrollDirection: Axis.horizontal)` only when Figma clearly indicates horizontal scrolling.
- Avoid fixed widths unless Figma marks the node as FIXED and the parent layout can still adapt safely.

### Full Views

- Use `SafeArea` for full-screen app views unless Figma explicitly models edge-to-edge content.
- Use `SingleChildScrollView`, `CustomScrollView`, or `ListView` when vertical content can exceed the viewport.
- Keep fixed headers/footers outside the scroll body only when the design indicates fixed positioning.

### Missing Figma Constraints

Missing constraints are not a blocker. Apply conservative mitigation and report the inference:

| Missing Data | Conservative Mitigation | Report |
|--------------|-------------------------|--------|
| Text width unclear | `Flexible`/`Expanded` in horizontal layouts | ⚠️ Warning |
| Vertical content height unclear | Scrollable body | ⚠️ Warning |
| Safe area unclear | Apply `SafeArea` | ⚠️ Warning |
| Truncation unclear | Allow wrapping; no ellipsis | ⚠️ Warning |

## Rules Summary

- **NEVER** hardcode widths in production widgets (yes in golden tests)
- **ALWAYS** use `MainAxisSize.min` by default in Column/Row
- **PREFER** `Expanded`/`Flexible` over `SizedBox` with fixed width
- **CONSIDER** `LayoutBuilder` for organisms — it's the DS primary pattern
- **NEVER** shorten, translate, or rewrite Figma text to avoid overflow
- **ALWAYS** mitigate known or inferred overflow risk
- **WARN, do not block**, when Figma constraints are incomplete but mitigation is possible
- **TEST** with golden tests at multiple widths if component is responsive
