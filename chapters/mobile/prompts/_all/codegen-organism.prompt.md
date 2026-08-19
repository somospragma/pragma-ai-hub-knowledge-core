---
id: codegen-organism
version: 1.0.0
scope: chapter
type: prompt
chapter: mobile
description: >
  Prompt for generating Flutter code for an organism-level Design System component. Use when building a complete UI section that composes atoms and molecules and must satisfy user-story acceptance criteria.
---
# Generation of Organism Flutter

## Reference Skills

- flutter-ds-theming-tokens
- flutter-ds-component-template
- flutter-ds-naming-conventions
- flutter-ds-lint-rules
- flutter-ds-folder-structure
- flutter-ds-widget-anatomy
- flutter-ds-responsive-layout
- flutter-ds-a11y-semantics

## Instruction

Generate the complete Flutter code for an organism in the Design System,
composing existing and/or newly created molecules and atoms.

## SDD Contract

When `spec_context` exists, read `spec_ref` and `context_ref` as machine
sources. Use only `read_sections`, implement the artifacts declared in
`artifact_plan`, record evidence in
`{SPEC_PACKET_PATH}/evidence/codegen-report.md`, and treat `PIPELINE_SPEC_PATH`
as the human report.

## Inputs You Will Receive

1. Name of the organism to create
2. Complete visual specifications from `design_source` and `canonical_spec`
3. List of molecules and atoms it composes (with paths and interfaces)
4. Required states
5. Functional acceptance criteria from the user story
6. Destination path
7. Interface designed from `technical_plan`
8. Text and overflow contract (`contracts.text_overflow`), required in `/new-component` and
   `/new-view`; can declare "without texts/risks" if it does not apply to the organism
9. In SDD mode, the same inputs come from `canonical_spec`,
   `technical_plan`, `contracts` and `artifact_plan`

## Differences From Molecule

An organism:
- Composes **molecules + atoms** with higher complexity
- Typically, it is a **complete UI section** (card, form, navigation bar)
- Can contain **coordination logic** between molecules
- Usually uses **Material** for elevation and surface
- Is the most **parameterized** level, with many callbacks and data inputs
- Responds most directly to the business user story

## Specific Rules

### Comments in Code

- Comments are prohibited inline, block and Dartdoc by default.
- Only allow a fundamental comment when the code cannot make the reason clear
  (e.g. temporary workaround, regulatory restriction or critical decision of interoperability).

### Composition With Material

> Comments in this snippet are instructional and must not be copied into generated code.

```dart
@override
Widget build(BuildContext context) {
  return Material(
    elevation: 0, // ElevationTokens.level1
    borderRadius: BorderRadius.circular(0), // {{DS_PREFIX}}BorderRadius.l
    color: /* token of surface */,
    clipBehavior: Clip.antiAlias,
    child: switch (state) {
      ...State.loading => _buildLoading(context),
      ...State.disabled => Opacity(
        opacity: 0.5,
        child: IgnorePointer(child: _buildContent(context)),
      ),
      _ => InkWell(
        onTap: onTap,
        child: _buildContent(context),
      ),
    },
  );
}
```

### Callbacks Multiple

```dart
const {{DS_PREFIX}}ProductCard({
  // Data
  required this.productName,
  required this.productPrice,
  this.productImageUrl,
  this.badgeLabel,
  // State
  this.state = {{DS_PREFIX}}ProductCardState.default_,
  // Callbacks - one per user action
  this.onTap,
  this.onAddToCart,
  this.onToggleFavorite,
  this.onShare,
});
```

### Acceptance Criteria

The organism is where the user story criteria are fulfilled.
For each criterion, verify that the code implements it:

```dart
// user story: "Must show image, name, price, and action button"
// Verify that the build includes all these elements

// user story: "The button favorite must be toggleable"
// Verify that parameter isFavorite and callback onToggleFavorite exist

// user story: "In loading state, show skeleton"
// Verify that _buildLoading() implements the full skeleton
```

### Responsiveness

```dart
Widget _buildContent(BuildContext context) {
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

### Text And Overflow

- Use only literal text from `literal_texts`,
  `contracts.literal_texts` and `contracts.text_overflow`.
- Do not invent empty states, error messages, badges, CTAs or microcopy if they are not
  in Figma/metadata/annotations.
- Design defensive composition against overflow:
  - `Flexible`/`Expanded` for text in rows
  - `Wrap` for horizontal groups that can wrap
  - vertical scroll when the organism can grow inside a view
  - flexible constraints instead of fixed sizes
- If Figma does not provide constraints sufficient, apply the defined mitigation in
  `contracts.text_overflow`, continue and record an alert.

### Full Skeleton

```dart
Widget _buildLoading(BuildContext context) {
  // The skeleton must cover the entire card, not only parts
  return Column(
    children: [
      // Header skeleton
      MoleculeHeader(state: MoleculeHeaderState.loading),
      SizedBox(height: /* spacing token */),
      // Body skeleton
      MoleculeBody(state: MoleculeBodyState.loading),
      SizedBox(height: /* spacing token */),
      // Actions skeleton
      MoleculeActions(state: MoleculeActionsState.loading),
    ],
  );
}
```

## Pre-Delivery Checklist

Everything from atom and molecule, plus:
- [ ] Imports and uses molecules + atoms in the DS?
- [ ] Uses Material for elevation/surface?
- [ ] Each user-story acceptance criterion is implemented?
- [ ] All interaction callbacks are exposed?
- [ ] Considers responsiveness with LayoutBuilder?
- [ ] Loading shows a full skeleton, not only partial placeholders?
- [ ] Error state shows clear indicators?
- [ ] Uses InkWell/GestureDetector for the main interaction?
- [ ] Accessibility: Semantics label includes state?
- [ ] If >200 lines, split into private files?
- [ ] Visible text matches Figma literally with Figma?
- [ ] Overflow risks are mitigated or flagged?
