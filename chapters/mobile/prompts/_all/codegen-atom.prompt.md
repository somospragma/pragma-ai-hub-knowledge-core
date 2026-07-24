---
id: codegen-atom
version: 1.0.1
scope: chapter
type: prompt
chapter: mobile
description: >
  Prompt for generating Flutter code for an atom-level Design System component. Use when the component is classified as an atom and its technical plan, tokens, states, and artifact path are approved.
---
# Generation of Atom Flutter

## Reference Skills

- flutter-ds-theming-tokens
- flutter-ds-component-template
- flutter-ds-naming-conventions
- flutter-ds-lint-rules
- flutter-ds-widget-anatomy
- flutter-ds-a11y-semantics

## Instruction

Generate the complete Flutter code for an atom-level component in the Design System.

## SDD Contract

When `spec_context` exists, read `spec_ref` and `context_ref` as machine
sources. Use only `read_sections`, implement the artifacts declared in
`artifact_plan`, record evidence in
`{SPEC_PACKET_PATH}/evidence/codegen-report.md`, and treat `PIPELINE_SPEC_PATH`
as the human report.

## Inputs You Will Receive

1. Name of the atom to create
2. Visual specifications from `design_source` and `canonical_spec`
3. Required states
4. Required variants
5. Destination path from `artifact_plan`
6. Interface designed from `technical_plan`
7. Text and overflow contract (`contracts.text_overflow`), required in `/new-component` and
   `/new-view`; can declare "without texts/risks" if it does not apply to the atom
8. In SDD mode, the same inputs come from `canonical_spec`,
   `technical_plan`, `contracts` and `artifact_plan`

## Absolute Rules

### Tokens
- Every color → token semantic (according to `project.config.yaml` → `tokens.access_method`)
- Every typography value → token of text/typography
- Every spacing value → spacing token
- Every radius value → radius token
- Every elevation value → token elevation
- **ZERO magic values**. If there is no token → generate ⚠️ ALERT

### Template
- Use ALWAYS the template of Atom of the skill `flutter-ds-component-template`
- Follow the anatomy from the `flutter-ds-widget-anatomy` skill

### Naming
- Clase: `{{DS_PREFIX}}[Name]` in PascalCase
- File: `{{ds_prefix_snake}}_[name].dart` in snake_case
- Enum state: `{{DS_PREFIX}}[Name]State`
- Enum of variante: `{{DS_PREFIX}}[Name]Variant`
- Enum of size: `{{DS_PREFIX}}[Name]Size`

### Clean Code
- Code self-explanatory through names and structure
- Inline, block, and Dartdoc comments are prohibited by default
- Only allow a fundamental comment when the code cannot make the reason clear
- Constructor `const` whenever possible
- Named parameters always
- 1 public widget per file
- Private `_build*` methods for state-specific UI
- Private `_resolve*` methods to resolve tokens per variant/state

### Accessibility
- Consult `flutter-ds-a11y-semantics`
- `Semantics` labels on interactive elements
- Minimum touch targets of 48x48

### Text And Overflow
- Use visible text only from `literal_texts`, `contracts.literal_texts` and
  `contracts.text_overflow`.
- Do not invent, translate, fix, or rewrite labels.
- If the atom renders text inside a constrained container, respect
  `maxLines`/`overflow` only if Figma or `contracts.text_overflow` indicates it.
- Do not force width/height to resolve overflow unless Figma marks the node as FIXED.

## File Structure

```dart
import 'package:flutter/material.dart';
import 'package:{{package_name}}/tokens/...';

class {{DS_PREFIX}}[Name] extends StatelessWidget {
  const {{DS_PREFIX}}[Name]({super.key, required this.param, ...});

  final Type param;

  bool get _isInteractive => ...;

  @override
  Widget build(BuildContext context) {
    return switch (state) {
      ...State.loading => _buildLoading(context),
      ...State.disabled => Opacity(opacity: 0.5, child: IgnorePointer(child: _buildDefault(context))),
      _ => _buildDefault(context),
    };
  }

  Widget _buildDefault(BuildContext context) { ... }
  Widget _buildLoading(BuildContext context) { ... }

  Color _resolveBackgroundColor(BuildContext context) { ... }
  EdgeInsets _resolvePadding() { ... }
}

enum {{DS_PREFIX}}[Name]State { default_, disabled, loading, focused, error }
enum {{DS_PREFIX}}[Name]Variant { primary, secondary }
enum {{DS_PREFIX}}[Name]Size { sm, md, lg }
```

## Pre-Delivery Checklist

- [ ] Uses only DS tokens for visual values?
- [ ] Contains no inline, block, or Dartdoc comments unless there is a fundamental exception?
- [ ] Constructor is `const`?
- [ ] All parameters are named?
- [ ] Implements all required states?
- [ ] Implements all required variants?
- [ ] `build()` delegates to private methods?
- [ ] Disabled uses `Opacity` + `IgnorePointer`?
- [ ] Loading shows skeleton/shimmer with tokens?
- [ ] Callbacks are null-safe?
- [ ] Compiles with correct imports and types?
- [ ] Accessibility: Semantics labels?
- [ ] 1 public widget per file?
- [ ] Package imports (no relativos)?
- [ ] Is visible text literal from the Figma contract?
- [ ] Overflow is mitigated without changing copy or the base layout?
