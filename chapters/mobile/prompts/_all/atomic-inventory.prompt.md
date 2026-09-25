---
id: atomic-inventory
version: 1.0.0
scope: chapter
type: prompt
chapter: mobile
description: Prompt to inventory existing components, classify reuse, and build the bottom-up creation DAG. Use it when the Figma analysis (§1) already exists and you need to decide what to reuse, what to extend, and what to create with `@component-planner`. Do not use it as the entrypoint of a complete task.
---

# Atomic Inventory, Canonical Spec, and DAG

## Reference skills

- flutter-ds-folder-structure
- flutter-ds-naming-conventions
- flutter-ds-atomic-hierarchy
- flutter-ds-theming-tokens
- flutter-ds-asset-management
- flutter-ds-responsive-layout

## INSTRUCTION

From the Figma analysis (§1), generate the canonical specification of the
component, inventory the repository, and create the creation plan.

## PROCESS

### Phase A: Canonical Specification

1. **Normalize** every value in §1 to its exact DS token
   - Check `flutter-ds-theming-tokens` and the project catalog
   - If no token exists → ⚠️ ALERT (do not invent tokens)

2. **Define props** of the component:
   - Name: `{{DS_PREFIX}}[Name]` or descriptive per level
   - Typed parameters with required/optional/defaults
   - Enums: State, Variant, Size
   - Typed callbacks
   - Special behaviors from `§1.3b Development Annotations`
   - Vectors contract from `§1.3c Vectors and Assets`
   - Literal texts contract from `§1.1b Literal Texts`
   - Safe layout contract from `§1.1c Layout, Constraints, and Overflow Risk`
   - Do not invent additional copy or UX if not backed by Figma/metadata

3. **Write** §2 in `PIPELINE_SPEC_PATH`

### Phase B: Repository Inventory

For EACH sub-component in the atomic decomposition:

**4-step search:**

1. **Exact name**: `symbol:[ComponentName]` in the repo
2. **Expected file**: path per `flutter-ds-folder-structure`
3. **Functionality**: semantic search if steps 1-2 do not find it
4. **Folder**: list files under `lib/[level]/[subfolder]/`

**For each found:**
- Read the full file
- Extract: constructor, parameters, states, variants
- Classify:
  - ✅ Compatible → reuse
  - ⚠️ Partial → document what is missing
  - ❌ Incompatible → create new

**For each NOT found:**
- 🆕 Mark as "To be created"
- Assign atomic level
- Propose path and name

### Phase C: Dependency DAG

1. Infer dependencies between sub-components
2. Classify:
   - `reuse` → existing component
   - `separate` → new independent widget
   - `inline` → private widget of the parent
3. Generate strict bottom-up order

### Phase D: Texts and Overflow

1. Propagate the texts from `§1.1b` without translating, correcting,
   summarizing, or improving them.
2. If a required state has no text from Figma, log a scope alert and debt;
   do not turn a technical placeholder into final copy. For views, keep
   `loading`, `empty`, `error`, and `populated` using the project's
   standard fallback when Figma does not define them.
3. Propagate risks from `§1.1c` and define mitigation per component/view.
4. If detailed constraints are missing, do not block solely for that:
   infer a conservative anti-overflow mitigation and flag the inference.

## MANDATORY OUTPUT

```markdown
## §2 Canonical Specification: [ComponentName]

### Props
| Parameter | Type | Required | Default | Token/Ref |
|-----------|------|----------|---------|-----------|

### Enums
- {{DS_PREFIX}}[Name]State: default_, disabled, loading, focused, error
- {{DS_PREFIX}}[Name]Variant: primary, secondary, ...
- {{DS_PREFIX}}[Name]Size: sm, md, lg (if applicable)

### Callbacks
| Callback | Type | Description |
|----------|------|-------------|

### Special Behaviors (from §1.3b)
| Rule/Annotation | UI Impact | Required Prop/State/Callback | Priority |
|-----------------|-----------|------------------------------|----------|

### View States and Fallbacks (only `/new-view`)
| State | Source | Component/Widget | Copy | Standard fallback | Alert |
|-------|--------|------------------|------|-------------------|-------|

### Vectors Contract (from §1.3c)
| Vector/Asset | UI Use | Strategy | Owner (DS/APP) | Path/Constant | Status |
|--------------|--------|----------|----------------|---------------|--------|

### Literal Texts Contract (from §1.1b)
| Prop/Element | Exact Figma text | Node ID | Scope/State | Editable by agent |
|--------------|------------------|---------|-------------|-------------------|

### Safe Layout Contract (from §1.1c)
| Element | Overflow risk | Required mitigation | Inferred due to missing constraints | Severity |
|---------|---------------|---------------------|-------------------------------------|----------|

## §3 Inventory and DAG

### ✅ Existing — Reuse
| Component | Level | Path | API |
|-----------|-------|------|-----|

### ⚠️ Existing — Need Extension
| Component | Level | Path | What is missing | Proposed change |
|-----------|-------|------|-----------------|-----------------|

### 🆕 Missing — Create
| Component | Level | Proposed path | Strategy | Specs |
|-----------|-------|---------------|----------|-------|

### 🎯 Vectors/Assets Inventory
| Vector/Asset | Final strategy | Reuses DS Icon | Asset to create/register | Location |
|--------------|----------------|----------------|--------------------------|----------|

### 🧩 Texts and Overflow Inventory
| Component/Widget | Literal texts used | Overflow mitigation | Alerts |
|------------------|--------------------|---------------------|--------|

### DAG
[Dependency diagram]

### 📋 Creation Order (bottom-up)
1. [Atom 1] — no dependencies
2. [Atom 2] — depends on Atom 1
3. [Molecule 1] — depends on Atom 1, Atom 2
4. [Organism] — depends on Molecule 1

### ⚠️ Alerts
- [ambiguities, conflicts, pending decisions]
```

## GOLDEN RULE

NEVER propose creating a component that already exists and is compatible.
If there is doubt about compatibility, mark as ⚠️ Partial with detail.
NEVER ignore `Development` annotations reported in `§1.3b`.
NEVER ignore vectors reported in `§1.3c`.
NEVER invent, translate, correct, or rewrite visible Figma texts.
NEVER block solely due to incomplete constraints if you can mitigate
overflow conservatively and report the alert.
