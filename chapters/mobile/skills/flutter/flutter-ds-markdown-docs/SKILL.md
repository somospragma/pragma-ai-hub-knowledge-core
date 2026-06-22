---
id: flutter-ds-markdown-docs
version: 1.2.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-markdown-docs
description: >
  Markdown documentation standard for Design System components.
  Use when generating README files for organisms, documenting component
  APIs, writing usage examples, or creating component catalogs.
---

# Markdown Documentation

## When to Generate

The decision follows the atomic level of the component:

| Level | README required? | Why |
|-------|-----------------|-----|
| **Atom** | No (default) | Small API, self-evident from code. Inline `///` doc comments are enough. |
| **Molecule** | Only if composition logic is non-obvious | If two developers could read the code and disagree on how sub-components interact, document it. |
| **Organism** | Always, no exceptions | Organisms integrate multiple pieces, own their states, tokens, and Figma counterpart. Without a README, onboarding and reuse break. |

**What counts as "non-obvious" for molecules?** Conditional sub-component rendering, state propagation across children, layout rules that depend on data combinations — anything where the *why* of the composition isn't clear from the code structure alone. A straightforward `Label + Input + ErrorText` molecule is obvious; a `SearchBar` that swaps content based on mode is not.

## README Template

The full starter template is at [assets/COMPONENT-README-TEMPLATE.md](assets/COMPONENT-README-TEMPLATE.md). Use it as your scaffold.

## Required Sections

These 9 sections are mandatory for every README. Don't add, remove, or rename them — consistency across components lets developers navigate any README without relearning the structure.

1. **Title** — Component name (`DSComponentName`) + one-sentence description
2. **Usage** — A Dart code example that **actually compiles**. No pseudo-code. Copy-paste must work.
3. **API** — Table of all constructor parameters: name, type, required ✅/❌, default, description
4. **Enums** — One table per enum (`Variant`, `State`, `Size`…) with value descriptions
5. **Tokens** — Table of DS tokens consumed, grouped by category (Color, Spacing, Radius, Elevation)
6. **Composition** — ASCII tree of sub-components showing hierarchy and atomic level of each
7. **States** — Table of visual/interaction behavior per state
8. **Figma** — URL to the design file + atomic level declaration
9. **Anti-patterns** — Explicit ❌ list of misuse to prevent

> The template also includes a **Preview** section (screenshot table) — fill it when images are available, but it is not one of the 9 required sections and does not block the README from being complete.

## Section Notes

**Usage** is the most-read section. A broken or pseudo-code example destroys trust in the entire README. Write it last once the widget API is stable, and verify it compiles.

**Tokens** is what separates a DS README from a generic Flutter component doc. It tells reviewers whether the component is properly wired to the token system. Every `DSSpacing.*`, `DSColors.*`, `DSBorderRadius.*`, `DSTextStyles.*` reference in the widget file should appear here.

**Composition** makes dependencies explicit. If the organism uses a `CardHeader` molecule that in turn uses `DSImage` + `DSBadge`, show both levels in the tree.

**Anti-patterns** are more valuable the more complex the component. For organisms, there are almost always at least two: one about nesting (don't put this inside itself) and one about parameter types (pass data, not widgets).

## Rules

- Inline, block, and doc comments in code are not mandatory — the README is where the contract lives
- The README is **complementary** to the code, not a replacement for it
- Always use the `DS` prefix for component names in code examples (e.g., `DSButton`, not `Button`)
- Token examples must use the actual DS token names — don't invent plausible-sounding tokens
