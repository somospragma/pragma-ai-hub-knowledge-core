---
id: figma-analysis
version: 1.0.0
scope: chapter
type: prompt
chapter: mobile
description: >
  Specialized prompt to analyze Figma components or screens and convert them into an actionable Flutter specification. Use when a workflow has a Figma URL and needs design extraction through Figma MCP.
---
# Figma Analysis For Flutter DS

## Reference Skills

- flutter-ds-figma-mcp
- flutter-ds-theming-tokens
- flutter-ds-figma-checklist
- flutter-ds-atomic-hierarchy
- flutter-ds-asset-management

## Instruction

Given a Figma link and a user story, generate the design analysis. If `spec_context` is provided, update `spec_ref` first; `PIPELINE_SPEC_PATH` remains a human report and must not become an executable or machine source.

## SDD Contract

When `spec_context` exists:

- Read `spec_ref`, `context_ref`, `phase`, and `read_sections`.
- Write to `spec.yaml`: `design_source`, `visual_analysis`, `literal_texts`, `layout_constraints`, `assets`, `visual_manifest`, `layout_manifest`, and `acceptance_criteria`.
- Record evidence in `{SPEC_PACKET_PATH}/evidence/figma-analysis.md`.
- Do not use `PIPELINE_SPEC_PATH` as the machine source.

## Process

### 1. MCP Access

1. Parse the URL (`fileKey`, `nodeId`).
2. Execute the required preflight:
   - Figma MCP is configured in the active tool surface.
   - File access is confirmed.
   - Read permissions exist for the node, components, styles, variables, and assets.
   - A screenshot is available for the main node.
   - Evidence is written to `{SPEC_PACKET_PATH}/evidence/figma-mcp-preflight.md`.
   - `spec.yaml.external_access.figma_mcp.status=verified`.
3. Discover capabilities and prefer `get_metadata`, `get_design_context`,
   `get_variable_defs`, and `download_assets`. Use legacy tool names only when
   they provide equivalent output.
4. Execute `get_metadata(fileKey, nodeId)` to capture ids, hierarchy, order,
   positions, and sizes for all visible nodes.
5. Execute `get_design_context(fileKey, nodeId)` as the first styling step.
6. Extract from `get_design_context`:
   - `Development` annotations
   - Figma-guided states/behaviors
   - nodes critical for visual evidence
7. Execute `get_screenshot(...)` for the requested main node and each relevant change/annotation. Record the main screenshot reference in `visual_manifest.reference_screenshot`.
8. Execute `get_variable_defs(...)` to resolve radius, spacing, and typography variables.
9. Extract every visible `TEXT` node with exact literal text, node id, parent id, child index, layer, scope/state, style, alignment, and truncation rules when available.
8. Extract relevant constraints/layout: auto-layout, HUG/FILL/FIXED sizing, padding, spacing, alignment, bounds, scroll/clip, and overflow-risk zones.
10. Detect every visible icon, image, illustration, logo, image-fill source, and vector asset.
11. Execute `download_assets(...)` for every detected source asset, download the returned Figma export into `{SPEC_PACKET_PATH}/source-assets/figma/`, and record its format, archive path, and SHA-256 in `spec.yaml.assets`. Use `get_images(...)` only as a compatible fallback. Prefer `svg` for vectors and use raster output only when required. Do not export an enclosing frame to simulate a crop.
11. If the node is a screen, use `get_node_children` for sections.
12. Use `get_styles(fileKey)` and `get_components(fileKey)` for global context.

### 1b. Missing MCP Access Or Critical Data

- Do not request direct input from the user.
- Write a partial section with `MCP status: not available`.
- Update `spec.yaml.external_access.figma_mcp.status=blocked_input`.
- Add `### 1.7 Input Blockers` with exact missing items.
- Record `blocked_input` in the log and return control to the orchestrator.

If MCP responds but `get_design_context` fails, also block with `blocked_input`; do not omit critical states or behaviors.
If `get_design_context` responds correctly but there are no `Development` annotations, do not block. Record `Development annotations: none` and continue.
If `get_screenshot` fails for any guided change, also block to avoid losing required visual evidence.
If any visible icon, image, illustration, logo, or image-fill source cannot be exported and downloaded from Figma, block with `FIGMA_ASSET_DOWNLOAD_UNAVAILABLE`. A screenshot, an expiring export URL, a similar local resource, or a platform icon is not a fallback.
If detailed constraints are missing from Figma, do not block automatically. Record an alert, infer conservative anti-overflow mitigation, and continue if the layout can be implemented reasonably.

### 2. Visual Extraction And Token Mapping

For each element, document layout, visuals, text, icons, and vectors.
If a value has no token, mark `ALERT`.

For visible text:

- Copy `characters` exactly as they come from Figma.
- Preserve uppercase/lowercase, accents, punctuation, and visible line breaks.
- Do not translate, fix, summarize, expand, or invent copy.
- Separate visible text from technical layer names.

Additionally, document a vector matrix with:

- functional use in screen/component
- consumption strategy (`DS_ICON`, `SVG_ASSET`, `PNG_ASSET`)

For `/new-view`, also build `visual_manifest`:

- every visible non-icon asset maps source node to visible container, clip/mask
  chain, bounds, transform and `direct_asset` or `explicit_clip_transform`;
- `explicit_clip_transform` is mandatory for an image shown through a crop,
  mask, or non-default scale; reuse the source asset rather than exporting the
  frame;
- every icon has an archived Figma export and maps either to a proven exact DS icon or to that exported Figma SVG;
- every text node maps Figma style id (or `inline:<node-id>`), family, size, weight, line height, alignment, token, and exact project-font resolution; do not approximate a font;
- screen chrome records whether bottom navigation is visible in Figma;
- reconciliation records all unresolved visible elements and requires visual
  verification for crops, exported icons, or visible bottom navigation.
- path/constant proposal
- rendering rules (size token, color token/original, semantics)

For `/new-view` and `/new-feature` with `figma_scope=view`, also build a
complete `layout_manifest`: exact root viewport, visible-node hierarchy,
parent-child index, bounds, direction, alignment, padding, gap, clip, four
corner radii, border width, and reconciliation. Use fixed tolerances of `1 dp`
for geometry, `2%` global pixel difference, and `4%` regional pixel difference.
Missing structural nodes, a changed child order, or unresolved shape geometry
must block with `FIGMA_LAYOUT_MANIFEST_INCOMPLETE`.

### 3. Variants, States, And Hierarchy

- Figma variants -> Flutter enums.
- Component states: default, hover, pressed, disabled, loading, focused, error.
- Include special states/behaviors defined in `Development` annotations (alerts, conditional rules, transitions, callbacks).
- For views, always record `loading`, `empty`, `error`, and `populated`.
- If Figma does not define visual/copy for any required state, mark it as `fallback_required` and flag that it must resolve through the project's standard fallback.
- Include atomic decomposition.
- If it is a complete view, include `view_states`, `navigation`, and screen structure in `spec.yaml`.

### 4. Acceptance Criteria

Extract a functional checklist from the user story.
If the user story requests text, states, or UX that are not present in Figma/metadata, report a scope alert and do not generate additional copy or UI.

## Required Output

Write first to `spec.yaml`. Optional human report format:

```markdown
## Analysis from Figma: [NameComponent/NameView]

### 1.0 MCP Metadata
- **File key**: [fileKey]
- **Node ID**: [nodeId]
- **Type**: [Component | Component Set | Frame/Screen]
- **MCP status**: [direct access | not available]
- **Design context status**: [obtained | not available]
- **Screenshots per change**: [N screenshots]

### 1.1 Visual Properties
| Element | Property | Figma Value | Flutter Token | Status |
|---------|----------|-------------|---------------|--------|

### 1.1b Literal Text
| Node ID | Scope/State | Layer | Exact Figma Text | Flutter Use | Editable By Agent |
|---------|-------------|-------|------------------|-------------|-------------------|

### 1.1c Layout, Constraints And Overflow Risk
| Element | Node ID | Figma Constraints | Risk | Recommended Mitigation | Status |
|---------|---------|-------------------|------|------------------------|--------|

### 1.2 Variants
| Figma Variant | Flutter Enum | Visual Differences |
|---------------|--------------|--------------------|

### 1.3 States
| State | Source (Figma/Fallback) | Visual Changes | Copy | Flutter Implementation | Alert |
|-------|--------------------------|----------------|------|------------------------|-------|

### 1.3b Development Annotations (required when they exist)
| Annotation | Node/Scope | Type (state/behavior/rule) | Flutter Impact | Required |
|------------|------------|-----------------------------|----------------|----------|

### 1.3c Vectors And Assets (required when they exist)
| Vector/Asset | Node ID | UI Use | Strategy (DS_ICON\|SVG_ASSET\|PNG_ASSET) | Path/Constant Proposal | Render (size/color/semantics) | State |
|--------------|---------|--------|--------------------------------------------|------------------------|-------------------------------|-------|

### 1.4 Atomic Decomposition
[proposed tree]

### 1.4b View Structure (only if applicable)
- **Scaffold**: [...]
- **Scroll**: [...]
- **Identified organisms**: [...]
- **Navigation**: [...]
- **View states**: [...]

### 1.5 Acceptance Criteria
- [ ] CA-1 ...
- [ ] CA-2 ...

### 1.6 Alerts
- ...
- If `get_design_context` fails, mark an explicit block.
- If there are no `Development` annotations, record `none` and continue.
- If vectors critical to the target UI are missing, mark an explicit block.
- If a visible icon lacks an exact DS mapping or exported Figma SVG, mark an explicit block.
- If Figma constraints are missing, continue with anti-overflow mitigation and record the risk; do not block unless implementation is impossible.
- If the user story requests text/UX not present in Figma, report it as not covered by design, without inventing copy.

### 1.7 Input Blockers (only if applicable)
- ...
```
