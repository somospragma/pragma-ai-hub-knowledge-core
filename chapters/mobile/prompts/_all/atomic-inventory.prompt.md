---
id: atomic-inventory
version: 1.0.0
scope: chapter
type: prompt
chapter: mobile
description: >
  Prompt to inventory existing components, classify reuse, and build the bottom-up creation DAG. Use when Figma analysis must become a canonical component inventory and generation order.
---
# Atomic Inventory, Canonical Spec, And DAG

## Reference Skills

- flutter-ds-folder-structure
- flutter-ds-naming-conventions
- flutter-ds-atomic-hierarchy
- flutter-ds-theming-tokens
- flutter-ds-asset-management
- flutter-ds-responsive-layout

## Instruction

From the structured Figma analysis, generate the canonical component
specification, inventory the repository, and create the generation plan. If
`spec_context` is provided, read `spec_ref` first; `PIPELINE_SPEC_PATH` remains
the human report.

## SDD Contract

When `spec_context` exists:

- Read only `read_sections`.
- Update `canonical_spec`, `inventory`, `dag`, `artifact_plan`, and `contracts`.
- Record evidence in `{SPEC_PACKET_PATH}/evidence/planning-report.md`.
- Do not copy the full analysis into handoffs.

## Process

### Phase A: Canonical Specification

1. **Normalize** each value of `visual_analysis` to its exact token in the DS.
   - Consult `flutter-ds-theming-tokens` and the project catalog.
   - If there is no token, generate a clear alert and do not invent tokens.

2. **Define props** for the component:
   - Name: `{{DS_PREFIX}}[Name]` or a descriptive name according to level.
   - Typed parameters with required, optional, and default values.
   - Enums: State, Variant, Size.
   - Typed callbacks.
   - Special behaviors from `design_source.annotations`.
   - Vector contract from `assets`.
   - Literal text contract from `literal_texts`.
   - Safe layout contract from `layout_constraints`.
   - Do not invent copy or extra UX if Figma/metadata does not support it.

3. **Write** `canonical_spec` in `spec.yaml`.

### Phase B: Repository Inventory

For each sub-component in the atomic decomposition:

**Search in 4 steps:**

1. **Exact name**: `symbol:[NameComponent]` in the repo.
2. **Expected file**: path according to `flutter-ds-folder-structure`.
3. **Functionality**: semantic search if steps 1-2 find nothing.
4. **Folder**: list files in `lib/[level]/[subfolder]/`.

**For each match:**

- Read the full file.
- Extract constructor, parameters, states, and variants.
- Classify:
  - Compatible: reuse.
  - Partial: document what is missing.
  - Incompatible: create new.

**For each missing component:**

- Mark as "To create".
- Assign atomic level.
- Propose path and name.

### Phase C: Dependency DAG

1. Infer dependencies between sub-components.
2. Classify:
   - `reuse`: existing component.
   - `separate`: new independent widget.
   - `inline`: private widget inside the parent.
3. Generate a strict bottom-up order.

### Phase D: Text And Overflow

1. Propagate `literal_texts` without translating, fixing, summarizing, or improving them.
2. If a required state has no text from Figma, record a scope/debt alert; do not
   turn technical placeholders into final copy. For views, keep `loading`,
   `empty`, `error`, and `populated` using the project standard fallback when
   Figma does not define the state.
3. Propagate `layout_constraints` risks and define mitigation per component/view.
4. If detailed constraints are missing, do not block for that reason alone:
   infer conservative anti-overflow mitigation and mark the inference.

## Required Output

```markdown
## Canonical Specification: [NameComponent]

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

### Special Behaviors
| Rule/Annotation | UI Impact | Required Prop/State/Callback | Priority |
|------------------|------------|-------------------------------|----------|

### View States And Fallbacks (only `/new-view`)
| State | Source | Component/Widget | Copy | Standard Fallback | Alert |
|-------|--------|------------------|------|-------------------|-------|

### Vector Contract
| Vector/Asset | UI Use | Strategy | Owner (DS/APP) | Path/Constant | State |
|--------------|--------|----------|----------------|---------------|-------|

### Literal Text Contract
| Prop/Element | Exact Figma Text | Node ID | Scope/State | Editable By Agent |
|--------------|------------------|---------|-------------|-------------------|

### Safe Layout Contract
| Element | Overflow Risk | Required Mitigation | Inferred From Missing Constraints | Severity |
|---------|---------------|---------------------|-----------------------------------|----------|

## Inventory And DAG

### Existing - Reuse
| Component | Level | Path | API |
|-----------|-------|------|-----|

### Existing - Requires Extension
| Component | Level | Path | Missing Capability | Proposed Change |
|-----------|-------|------|--------------------|-----------------|

### Missing - Create
| Component | Level | Proposed Path | Strategy | Specs |
|-----------|-------|---------------|----------|-------|

### Vector/Asset Inventory
| Vector/Asset | Final Strategy | Reuses DS Icon | Asset To Create/Register | Location |
|--------------|----------------|----------------|--------------------------|----------|

### Text And Overflow Inventory
| Component/Widget | Literal Text Used | Overflow Mitigation | Alerts |
|------------------|-------------------|---------------------|--------|

### DAG
[Dependency diagram]

### Creation Order (bottom-up)
1. [Atom 1] - no dependencies
2. [Atom 2] - depends on Atom 1
3. [Molecule 1] - depends on Atom 1, Atom 2
4. [Organism] - depends on Molecule 1

### Alerts
- [ambiguities, conflicts, or pending decisions]
```

## Golden Rule

NEVER propose creating a component that already exists and is compatible.
If compatibility is uncertain, mark it as Partial with details.
NEVER ignore `Development` annotations reported in `design_source.annotations`.
NEVER ignore vectors reported in `assets`.
NEVER invent, translate, correct, or rewrite visible text from Figma.
NEVER block only because constraints are incomplete if overflow can be mitigated
conservatively and the alert can be reported.
