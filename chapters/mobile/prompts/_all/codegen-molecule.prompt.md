---
id: codegen-molecule
version: 1.0.0
scope: chapter
type: prompt
chapter: mobile
description: >
  Prompt for generating Flutter code for a molecule-level Design System component. Use when the component composes multiple atoms and must propagate state, layout, tokens, and callbacks through child components.
---
# Generation of Molecule Flutter

## Reference Skills

- flutter-ds-theming-tokens
- flutter-ds-component-template
- flutter-ds-naming-conventions
- flutter-ds-lint-rules
- flutter-ds-folder-structure
- flutter-ds-widget-anatomy

## Instruction

Generate the complete Flutter code for a molecule in the Design System,
composing existing and/or newly created atoms.

## SDD Contract

When `spec_context` exists, read `spec_ref` and `context_ref` as machine
sources. Use only `read_sections`, implement the artifacts declared in
`artifact_plan`, record evidence in
`{SPEC_PACKET_PATH}/evidence/codegen-report.md`, and treat `PIPELINE_SPEC_PATH`
as the human report.

## Inputs You Will Receive

1. Name of the molecule to create
2. Visual specifications from `design_source` and `canonical_spec`
3. List of atoms it composes (with paths and interfaces)
4. Required states
5. Destination path
6. Interface designed from `technical_plan`
7. Text and overflow contract (`contracts.text_overflow`), required in `/new-component` and
   `/new-view`; can declare "without texts/risks" if it does not apply to the molecule
8. In SDD mode, the same inputs come from `canonical_spec`,
   `technical_plan`, `contracts` and `artifact_plan`

## Differences From Atom

A molecule:
- **IMPORTS and USES** atoms in the DS (no recreate functionality)
- **DELEGATES** visual properties to child atoms
- **PROPAGATES** states to child atoms when appropriate
- **COMPOSES** layout (Row, Column, Stack) to organize atoms
- **ADDS** coordination logic between atoms

## Specific Rules

### Comments in Code

- Comments are prohibited inline, block and Dartdoc by default.
- Only allow a fundamental comment when the code cannot make the reason clear
  (e.g. temporary workaround, regulatory restriction or critical decision of interoperability).

### Correct Composition

> Comments in this snippet are instructional and must not be copied into generated code.

```dart
// CORRECT - Use existing atoms in the DS
import 'package:{{package_name}}/atoms/text/{{ds_prefix_snake}}_text.dart';
import 'package:{{package_name}}/atoms/indicators/{{ds_prefix_snake}}_badge.dart';

// In build:
{{DS_PREFIX}}Text(text: title, variant: {{DS_PREFIX}}TextVariant.titleMedium)
{{DS_PREFIX}}Badge(label: badgeLabel, variant: {{DS_PREFIX}}BadgeVariant.info)

// INCORRECT - Recreates atom functionality
Text(title, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500))
Container(
  padding: EdgeInsets.all(4),
  decoration: BoxDecoration(color: Colors.blue),
  child: Text(badgeLabel),
)
```

### State Propagation

```dart
// When the molecule is loading, child atoms are loading too:
Widget _buildLoading(BuildContext context) {
  return Column(
    children: [
      {{DS_PREFIX}}Text(text: '', state: {{DS_PREFIX}}TextState.loading),
      {{DS_PREFIX}}Badge(label: '', state: {{DS_PREFIX}}BadgeState.loading),
    ],
  );
}
```

### Parameters

```dart
// CORRECT - Data parameters
const {{DS_PREFIX}}CardHeader({
  required this.title,
  required this.subtitle,
  this.badgeLabel,     // nullable = hidden
  this.imageUrl,       // nullable = hidden
});

// INCORRECT - Passing direct widgets
const {{DS_PREFIX}}CardHeader({
  required this.titleWidget,
  required this.badgeWidget,
});
```

### Spacing Between Atoms

```dart
// ✅ Spacing with tokens
Column(
  crossAxisAlignment: CrossAxisAlignment.start,
  children: [
    {{DS_PREFIX}}Text(text: title),
    SizedBox(height: {{DS_PREFIX}}Spacing.xs),  // Spacing token
    {{DS_PREFIX}}Text(text: subtitle),
  ],
)
```

### Text And Overflow

- Propagate literal text to child atoms without changing copy.
- Do not create labels, helper text, placeholders, or CTAs that are not present in Figma.
- In `Row`, wrap textual children with `Flexible`/`Expanded` when they share
  space with icons, badges, buttons, or dynamic values.
- Use `Wrap` only when the contract allows that the horizontal group wraps of
  line.
- If detailed constraints are missing, apply the defined mitigation in
  `contracts.text_overflow` and
  record an alert; no block for that reason alone.

## Pre-Delivery Checklist

Everything from the atom, plus:
- [ ] Imports and uses atoms in the DS (no recreate functionality)?
- [ ] Imports use the correct package imports?
- [ ] Propagates states to child atoms?
- [ ] Parameters are data values, not widgets?
- [ ] Layout respects the Figma design (Row/Column/Stack)?
- [ ] Spacing between atoms uses tokens?
- [ ] Optional elements are nullable and hidden when null?
- [ ] Visible text matches Figma literally with Figma?
- [ ] Rows and long text have anti-overflow mitigation?
