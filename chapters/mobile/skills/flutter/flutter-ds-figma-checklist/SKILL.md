---
id: flutter-ds-figma-checklist
version: 1.3.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-figma-checklist
description: >
  Complete comparison checklist between Flutter implementation and Figma spec.
  Use when auditing visual fidelity, verifying token mapping accuracy,
  checking variant/state coverage, or validating anatomy against Figma layers.
  Always activate when fixing overflow errors, checking typography fidelity,
  reviewing color tokens, or verifying that a component matches a Figma design.
---
# Figma Comparison Checklist

## 1. Design Context
- [ ] Figma URL with correct `node-id`
- [ ] `get_design_context` executed before deep analysis
- [ ] Screenshot(s) for visual reference
- [ ] `get_screenshot` captured for each guided change
- [ ] Node metadata extracted (via Figma MCP `get_node` or manual inspection)
- [ ] `get_styles` used to verify published token mappings (if MCP available)
- [ ] MCP status documented: direct access | manual fallback
- [ ] Development annotations documented (alerts, states, special rules)
- [ ] Literal text contract extracted from visible TEXT nodes
- [ ] Layout constraints and overflow-risk matrix extracted or warning recorded

> See `flutter-ds-figma-mcp` for details about the available MCP tools.

## 2. Variants & Properties
- [ ] All Figma properties have a Flutter parameter
- [ ] All possible values mapped
- [ ] Defaults match
- [ ] Boolean properties (`show X`) modeled correctly
- [ ] Variant enums have all Figma values
- [ ] Special behaviors from Development annotations modeled explicitly

## 3. Color Tokens
- [ ] Container fill matches Figma token
- [ ] Each text uses correct color token
- [ ] Icons use correct semantic color per variant
- [ ] Borders use correct token
- [ ] Verified in both **light** and **dark** — run golden test or Widgetbook preview in both `ThemeMode.light` and `ThemeMode.dark`

## 4. Typography
- [ ] Each text uses correct typography token
- [ ] Family and weight match the Figma style source and an exact registered
      project font; no close-font fallback
- [ ] Font size matches
- [ ] Font weight matches (Regular=400, Medium=500, Bold=700)
- [ ] `textAlign` matches
- [ ] `maxLines` and `overflow` if truncation exists
- [ ] Visible text matches Figma literally: casing, accents, punctuation, and line breaks
- [ ] No copy was invented, translated, corrected, summarized, or shortened
- [ ] View states not defined by Figma use standard fallback and are reported

## 5. Spacing & Padding
- [ ] Internal padding (top, right, bottom, left) matches tokens
- [ ] Gap between each child pair matches
- [ ] Sandmmetric vs asandmmetric correct
- [ ] Desktop variant scales padding correctly (if applicable)

## 6. Sizes & Dimensions
- [ ] Icon sizes match spec
- [ ] Component flexible or fixed per Figma
- [ ] Height adapts to content (`MainAxisSize.min`) unless specified
- [ ] Sub-components use corresponding DS widget
- [ ] Horizontal text layouts use `Flexible`/`Expanded` where needed
- [ ] Scroll/SafeArea strategy prevents full-view overflow
- [ ] Missing Figma constraints are warnings when mitigated, not blockers

## 6a. Rendered Assets And Icons
- [ ] Each visible asset maps its source node to its visible container
- [ ] Every visible icon, image, illustration, logo, and image-fill source was
      downloaded from Figma into `source-assets/figma/` with format and SHA-256
- [ ] Cropped/masked/scaled assets use the source file plus explicit clip,
      transform, and alignment; no enclosing-frame export is used as a shortcut
- [ ] A DS icon is used only when its exact catalog match is declared and its
      Figma source export remains archived
- [ ] Otherwise, the archived Figma SVG is registered and rendered
- [ ] Final runtime assets have the same checksum as their archived Figma source
- [ ] The runtime result preserves source bounds versus visible bounds

## 6c. Screen Chrome
- [ ] Visible bottom navigation is classified as shared app shell, view-owned
      scaffold, or not present
- [ ] A shared shell is integrated without duplication
- [ ] A view-owned navigation bar is rendered and covered by a widget test

## 6b. Overflow Safety

> **Critical rule:** Text is a Figma contract. `TextOverflow.ellipsis` or `maxLines` truncation is ONLY acceptable when Figma explicitly defines truncation for that text node (fixed-size container with truncate behavior, or Development annotation). If Figma is silent on truncation, preserve the full text and adapt the layout instead.

- [ ] No `RenderFlex overflow` risk in known compact widths
- [ ] No fixed width/height added without Figma backing
- [ ] `Wrap` or scroll used for groups that can exceed available space
- [ ] `TextOverflow.ellipsis` only when Figma or contract **explicitly** defines truncation — document the Figma backing
- [ ] Long literal text is preserved; `Flexible`/`Expanded` adapts the layout, not the text
- [ ] When overflow mitigation uses inference (Figma silent), record a warning in the spec

**Pattern — overflow-safe horizontal layout without truncating text:**
```dart
Row(
  children: [
    Flexible(           // title shrinks, text preserved intact
      child: Text(productTitle),
    ),
    const SizedBox(width: 8),
    PriceBadge(price: price), // badge keeps its natural width
  ],
)
// ❌ WRONG without Figma contract:
// Text(productTitle, overflow: TextOverflow.ellipsis, maxLines: 1)
```

## 7. Border Radius
- [ ] Main container radius matches token
- [ ] Internal elements' radius (chips, badges) correct

## 8. Desktop vs Mobile
- [ ] Widget accepts platform parameter (if applicable)
- [ ] Typography scales correctly
- [ ] Padding/spacing scales if Figma indicates
- [ ] Width adapts
- [ ] Tests for both variants
- [ ] Desktop golden tests

See [extended checklist](references/EXTENDED-CHECKLIST.md) for anatomy, states, interaction, modularity, and assets verification.

## Verification Commands

Always run these commands before closing any audit. They are non-optional.

| Check | Commy |
|-------|---------|
| Lint | `flutter analyze lib/src/{level}/{component}/` |
| Tests | `flutter test test/{level}/{component}/` |
| Goldens | `flutter test --update-goldens --tags golden` |
| Widgetbook | `dart run build_runner build` |
