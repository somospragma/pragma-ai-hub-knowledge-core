---
id: flutter-ds-responsive-layout
version: 1.1.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
description: >
  Responsive layout patterns for Design System components.
  Use when implementing organisms that adapt to different screen sizes,
  deciding between compact and default layouts, or handling platform
  differences (mobile vs desktop).
---

# Responsive Layout

## When to Apply

- **Atoms**: Generally NO — adapt by flex
- **Molecules**: Rarely — only if horizontal layout may collapse
- **Organisms**: ALWAYS consider responsiveness

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

## Suggested Breakpoints

| Breakpoint | Width | Usage |
|-----------|-------|-------|
| Compact | < 360px | Very small devices |
| Mobile | 360–599px | Phones (default) |
| Tablet | 600–1023px | Tablets |
| Desktop | ≥ 1024px | Desktop/Web |

## Platform Pattern

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

Use these rules whenever implementing components or full views from Figma:

### Text in Rows

```dart
Row(
  children: [
    Icon(icon),
    SizedBox(width: spacing),
    Expanded(
      child: Text(
        title,
        maxLines: maxLinesFromFigma,
        overflow: overflowFromFigma,
      ),
    ),
  ],
)
```

- Put text inside `Flexible` or `Expanded` when it shares horizontal space with
  icons, badges, buttons, prices, counters, or trailing actions.
- Do not add `ellipsis` by default. Use `TextOverflow.ellipsis` only when Figma
  or the technical contract explicitly defines truncation.
- Preserve the literal text from Figma; never shorten copy to avoid overflow.

### Horizontal Groups

- Use `Wrap` for chips, tags, secondary actions, filters, or badges only when
  wrapping does not contradict the Figma composition.
- Use `SingleChildScrollView(scrollDirection: Axis.horizontal)` only when Figma
  clearly indicates horizontal scrolling.
- Avoid fixed widths unless Figma marks the node as FIXED and the parent layout
  can still adapt safely.

### Full Views

- Use `SafeArea` for full-screen app views unless Figma explicitly models
  edge-to-edge content.
- Use `SingleChildScrollView`, `CustomScrollView`, or `ListView` when vertical
  content can exceed the viewport.
- Keep fixed headers/footers outside the scroll body only when the design
  indicates fixed positioning.

### Missing Figma Constraints

Missing constraints are not an automatic blocker. Continue with conservative
mitigation and report the inference:

| Missing Data | Conservative Mitigation | Report |
|--------------|-------------------------|--------|
| Text width unclear | `Flexible`/`Expanded` in horizontal layouts | Warning |
| Vertical content height unclear | Scrollable body | Warning |
| Safe area unclear | Apply `SafeArea` | Warning |
| Truncation unclear | Allow wrapping; no ellipsis | Warning |

## Rules

- **NEVER** hardcode widths in production widgets (yes in golden tests)
- **ALWAYS** use `MainAxisSize.min` by default in Column/Row
- **PREFER** `Expanded`/`Flexible` over `SizedBox` with fixed width
- **CONSIDER** `LayoutBuilder` for organisms
- **NEVER** shorten, translate, or rewrite Figma text to avoid overflow
- **ALWAYS** mitigate known or inferred overflow risk
- **WARN, do not block**, when Figma constraints are incomplete but mitigation
  is possible
- **TEST** with golden tests at multiple widths if component is responsive
