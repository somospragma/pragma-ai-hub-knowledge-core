---
id: flutter-ds-figma-mcp
version: 1.3.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-ds-figma-mcp
description: >
  Figma MCP (Model Context Protocol) integration for accessing design data
  programmatically. Use when extracting component properties, navigating
  Figma file trees, reading styles/tokens, analyzing full screens or pages,
  and comparing implementation against design specs. Always activate when
  working with Figma URLs, extracting design tokens, or handling MCP unavailability.
---
# Figma MCP Integration

## Critical Protocol: `blocked_input`

When `get_design_context` is unavailable or returns no data, you **must** mark as `blocked_input` and return control to the orchestrator. Do NOT proceed with implementation.

Development annotations may contain state rules, interaction behaviors, and copy overrides that are invisible in the static design tree. Proceeding without them risks an incomplete or incorrect implementation.

```
# When get_design_context is unavailable:
Status: blocked_input
Tool: figma/get_design_context
Impact: Development annotations missing — implementation cannot be certified as behavior-complete.
Required to unblock: MCP restored, get_design_context returning valid data.
Do NOT: proceed with get_node or code generation until unblocked.

# Exception — when tool responds but returns empty annotations:
Status: Continue
Note: "Development annotations: none"
```

> `blocked_input` ≠ "no annotations found". If the tool returns a result (even empty), continue and mark `Development annotations: none`. Only block when the **tool itself** is unavailable or errors.

## Overview

Figma MCP provides programmatic access to Figma files via Model Context Protocol.
This enables agents to read design data directly instead of relying on manual
descriptions or screenshots.

## Available MCP Tools

### `get_file`
Retrieves the full Figma file structure (pages, frames, components).

```
Tool: figma/get_file
Input: { "fileKey": "abc123" }
Output: Document tree with pages → frames → nodes
```

**Use when:** Starting analysis of a new file, discovering available pages/screens.

### `get_node`
Retrieves a specific node by ID with all its properties and children.

```
Tool: figma/get_node
Input: { "fileKey": "abc123", "nodeId": "1234:5678" }
Output: Node with properties, children, layout, fills, strokes, effects
```

**Use when:** Analandzing a specific component, frame, or screen.

### `get_node_children`
Retrieves only the direct children of a node.

```
Tool: figma/get_node_children
Input: { "fileKey": "abc123", "nodeId": "1234:5678" }
Output: Array of child nodes with basic properties
```

**Use when:** Navigating large trees incrementally, exploring screen sections.

### `get_styles`
Retrieves all published styles (colors, text, effects, grids) in the file.

```
Tool: figma/get_styles
Input: { "fileKey": "abc123" }
Output: Array of style definitions with properties
```

**Use when:** Mapping Figma styles to DS tokens, verifying token coverage.

### `get_components`
Retrieves all published components and component sets in the file.

```
Tool: figma/get_components
Input: { "fileKey": "abc123" }
Output: Array of component definitions with variant properties
```

**Use when:** Inventorying available components, checking for existing DS atoms.

### `get_images`
Exports node(s) as images (PNG, SVG, PDF).

```
Tool: figma/get_images
Input: { "fileKey": "abc123", "nodeIds": ["1234:5678"], "format": "svg" }
Output: URLs to exported images
```

**Use when:** Downloading assets, generating reference screenshots for golden tests.

### `get_design_context`
Retrieves Figma-guided development context for a target node.

```
Tool: figma/get_design_context
Input: { "fileKey": "abc123", "nodeId": "1234:5678" }
Output: Context with guided changes, development annotations, and node-level notes
```

**Use when:** Starting any implementation-oriented analysis where annotations,
state rules, or special behaviors may exist.

### `get_screenshot`
Captures screenshot evidence for a specific guided change or relevant node.

```
Tool: figma/get_screenshot
Input: { "fileKey": "abc123", "nodeId": "1234:5678" }
Output: Screenshot URL/reference for visual verification
```

**Use when:** Capturing visual proof for each guided change from
`get_design_context`.

## Navigation Strategy

### For a Single Component
```
1. get_design_context(fileKey, nodeId) → guided changes + development annotations
2. For each guided change: get_screenshot(change/node)
3. get_node(nodeId) → full component tree
4. Parse children recursively → build layer hierarchy
5. For each child: extract type, properties, fills, strokes, effects, text, constraints
6. Register literal visible text from TEXT nodes without rewriting
7. Register layout constraints and overflow risks
8. Map each property → DS token
```

### For a Full Screen/Page
```
1. get_file(fileKey) → discover pages
2. get_design_context(fileKey, pageNodeId) → development annotations + guided changes
3. For each guided change: get_screenshot(change/node)
4. get_node(pageNodeId) → get screen frame
5. get_node_children(frameId) → top-level sections
6. For each section:
   a. Classify: header, body, footer, navigation, etc.
   b. get_node(sectionId) → full section tree
   c. Decompose into organisms → molecules → atoms
   d. Extract literal texts and constraints per section
7. Build complete screen composition map + behavior map from annotations
8. Build text contract and overflow-risk matrix
```

### For a Component Set (Variants)
```
1. get_node(componentSetId) → all variants
2. Extract variant properties (Type, Size, State, etc.)
3. For each variant: document visual differences
4. Map to Flutter enums
```

## Extracting Properties from Nodes

### Layout Properties
| Figma Property | MCP Path | Flutter Mapping |
|---------------|----------|-----------------|
| `layoutMode` | `node.layoutMode` | `Row` (HORIZONTAL) / `Column` (VERTICAL) |
| `primaryAxisSizingMode` | `node.primaryAxisSizingMode` | `MainAxisSize.min` (HUG) / `.max` (FILL) |
| `counterAxisSizingMode` | `node.counterAxisSizingMode` | `CrossAxisAlignment` |
| `itemSpacing` | `node.itemSpacing` | `SizedBox(width/height:)` → SpacingToken |
| `paddingTop/Right/Bottom/Left` | `node.padding*` | `EdgeInsets` → SpacingTokens |
| `primaryAxisAlignItems` | `node.primaryAxisAlignItems` | `MainAxisAlignment.*` |
| `counterAxisAlignItems` | `node.counterAxisAlignItems` | `CrossAxisAlignment.*` |

### Visual Properties
| Figma Property | MCP Path | Flutter Mapping |
|---------------|----------|-----------------|
| `fills[0].color` | `node.fills[0].color` | Color → token lookup |
| `strokes[0].color` | `node.strokes[0].color` | Border color → token |
| `strokeWeight` | `node.strokeWeight` | Border width |
| `cornerRadius` | `node.cornerRadius` | `BorderRadius` → RadiusToken |
| `effects[type=DROP_SHADOW]` | `node.effects` | `elevation` → ElevationToken |
| `opacity` | `node.opacity` | `Opacity` widget |
| `clipsContent` | `node.clipsContent` | `clipBehavior: Clip.antiAlias` |

### Text Properties
| Figma Property | MCP Path | Flutter Mapping |
|---------------|----------|-----------------|
| visible text | `node.characters` | Literal `String` contract |
| `style.fontFamily` | `node.style.fontFamily` | Typography token family |
| `style.fontSize` | `node.style.fontSize` | Typography token size |
| `style.fontWeight` | `node.style.fontWeight` | Typography token weight |
| `style.lineHeightPx` | `node.style.lineHeightPx` | `height` in TextStyle |
| `style.textAlignHorizontal` | `node.style.textAlignHorizontal` | `TextAlign.*` |

### Text Fidelity Rules

- Use `characters` exactly as Figma returns it for visible UI text.
- Preserve casing, accents, punctuation, line breaks that are visible in design,
  and intentional spacing.
- Do not translate, correct, summarize, expand, or invent copy.
- Layer names are not copy unless metadata/anotations explicitly say so.
- If a required state has no visible text in Figma, report a gap instead of
  inventing final copy.

### Overflow Risk Extraction

For every text-heavy or horizontal container, capture:

| Risk Signal | MCP Source | Flutter Mitigation |
|-------------|------------|--------------------|
| Horizontal auto-layout with text + trailing item | `layoutMode`, children | `Flexible`/`Expanded` |
| Fixed width text container | bounds/sizing mode | Preserve only if parent can adapt; otherwise warning |
| Long copy without truncation metadata | `characters`, text style | Allow wrap, no ellipsis |
| Screen content taller than viewport | frame bounds + sections | Scrollable body |
| Edge-to-edge full screen | frame bounds | `SafeArea` unless Figma says otherwise |

If constraints are missing, continue with conservative mitigation and document
the inference as a warning, not an automatic blocker.

## Screen-Level Analysis

When analyzing a full screen (not just a component):

1. **Identify the scaffold structure**:
   - AppBar / top navigation
   - Body content (scrollable or fixed)
   - Bottom navigation / FAB
   - Drawers / sidebars

2. **Map each section to organisms**:
   - Each major section = 1 organism
   - Within organism: molecules and atoms

3. **Identify shared patterns**:
   - Are any organisms reused across screens?
   - Do sections share molecules?

4. **Document navigation context**:
   - What routes lead to this screen?
   - What actions navigate away?
   - Modal/dialog triggers

5. **Document scroll behavior**:
   - Fixed vs scrollable areas
   - SliverAppBar collapse behavior
   - Infinite scroll / pagination

6. **Document development annotations**:
   - Conditional alerts and messages
   - Special state rules
   - Non-obvious UI interactions and callbacks

## Figma URL Parsing

```
https://www.figma.com/file/{fileKey}/{fileName}?node-id={nodeId}
https://www.figma.com/design/{fileKey}/{fileName}?node-id={nodeId}
```

- `fileKey`: Unique file identifier
- `nodeId`: URL-encoded node ID (e.g., `1234-5678` → decode to `1234:5678`)

## Error Handling

| Error | Action |
|-------|--------|
| Node not found | Verify nodeId, try parent node |
| Rate limit | Wait and retry (max 3 attempts) |
| Large file timeout | Use `get_node_children` incrementally |
| Missing properties | Mark as `unavailable` in the spec |
| No MCP access | Mark `blocked_input`, record the missing access, and return control to the workflow controller |
| `get_design_context` unavailable | Mark `blocked_input` to avoid omitting Development annotations |
| No Development annotations returned | Continue, mark `Development annotations: none` |
| `get_screenshot` unavailable for guided changes | Mark `blocked_input` to preserve evidence for guided changes |

## Checklist

- [ ] Figma MCP server configured in agent environment
- [ ] File key extracted from Figma URL
- [ ] Node ID decoded (URL format `1234-5678` → API format `1234:5678`)
- [ ] Full node tree retrieved for target component/screen
- [ ] `get_design_context` executed before code-oriented analysis
- [ ] `get_screenshot` captured for each guided change
- [ ] All visual properties extracted and mapped to tokens
- [ ] Variants discovered (if Component Set)
- [ ] States identified from variant properties or layer names
- [ ] Development annotations translated to explicit states/behaviors in spec
- [ ] Assets identified for export (icons, illustrations)
- [ ] Literal text contract extracted from all visible TEXT nodes
- [ ] Layout constraints and overflow risks documented
- [ ] Missing constraints reported as warnings when mitigable
