# Widgetbook Variants Guide

More variants are not always better. Each variant must demonstrate a meaningful visual or behavioral difference.

## General Rule

Prefer a single `@UseCase(name: 'default')` with knobs for states and visual variants. Create additional use cases only when the widget renders a fundamentally different structure that cannot be controlled with knobs.

## Component Guidance

| Component type | Recommended coverage |
|---|---|
| Simple atom | 2-4 meaningful options through knobs |
| Molecule | default + important state/variant knobs |
| Organism | default, loading, empty, error when applicable |
| Screen | use `features_guide.md` |

## Use Knobs For

- loading/disabled/enabled flags
- enum variants such as primary/secondary/ghost
- icon visibility or position
- item count for lists
- read-only mode

## Use Separate Use Cases For

- radically different layouts
- upload button default vs uploading progress bar
- error state with retry UI when the structure changes

## Domain Data

Use literal Figma text when available. When it is not available, infer the product domain from package names, models, and API fields, then use coherent example data. Never invent interface copy.
