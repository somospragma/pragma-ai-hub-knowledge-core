# Mobile Spec Packet

The Mobile Spec Packet is the executable source of truth for SDD workflows. It
keeps agent execution deterministic without asking developers to author YAML
from scratch.

## Functional Packet Location

Functional workflows resolve a packet owner before Phase 0. The owner stays
immutable for the run; it is distinct from the active target used to create a
particular artifact.

```text
{SPEC_PACKET_OWNER_ROOT}/{pipeline.output_dir}/specs/{workflow_slug}/
├── spec.yaml
├── context.json
├── review.md
├── evidence/
├── source-assets/
│   └── figma/
└── snapshots/
```

With the default config this resolves under:

```text
.sopp/flow_result/specs/{workflow_slug}/
```

For `/new-view`, the owner is the resolved app target: use `target_id` when it
is supplied, otherwise `active_target_defaults.app_target_id`, falling back to
`active_target_defaults.app`. DS phases may set `ACTIVE_TARGET_ID` to the
Design System target for their artifacts, but they must not move packet state,
evidence or pipeline reports out of the app-owned root.

## Initial Files

| File | Purpose | Audience |
|---|---|---|
| `spec.yaml` | Machine-readable requirements, permissions, planned artifacts, external access and success criteria. | Agents |
| `context.json` | Resume state: run id, current phase, approvals, completed phases, blockers and evidence references. | Agents |
| `review.md` | Compact Spanish review for human approval. | Human |
| `evidence/` | Validation reports, preflight results, audits, command summaries and checkpoint decisions. | Human and agents |
| `source-assets/figma/` | Immutable Figma exports for each visible icon, image, illustration and logo. | Agents and audit |

`context.json` is validated by `mobile-context.schema.json`. Its
`workflow_controller` is the workflow `entry_agent`, not the optional
`mobile-orchestrator` router. The controller is the only agent that may request
human approval; specialized agents return a compact handoff instead.
`packet_owner_target_id` and `packet_root` make the packet location explicit
without conflating it with the active artifact target.

The approval state is intentionally singular:

1. Before a required review, set `status: pending_human_review` and set the
   relevant `checkpoints.<name>.status: pending`.
2. After approval, set `status: approved_for_execution`, set that checkpoint to
   `approved`, and remove or replace `pending_human_review`.
3. Before the next required review, return to `pending_human_review` and record
   the next checkpoint. A `blocked_input` status stops execution.

`checkpoints` is an object keyed by checkpoint name, not a list. This lets a
controller resume a specific gate without rereading the complete conversation.

## Spec Levels

| Level | Workflows | Checkpoints |
|---|---|---|
| `mini` | `/new-component`, `/refactor-component`, `/fix-pr-comments` | Initial approval; later checkpoints only when required by the workflow. |
| `standard` | `/new-view` | Initial approval plus DS/app phase checkpoints. |
| `full` | `/new-feature`, `/refactor-feature`, `/test-plan` | Initial approval and required layer/stage checkpoints. For `/new-feature`, unit, widget and integration evidence is mandatory; golden tests and documentation are explicit opt-ins. |

## Optional Golden Tests

`/new-component`, `/new-view` and `/new-feature` accept
`golden_tests: true|false`. The default is `false`, which avoids generating
golden files and snapshots. The controller normalizes an omitted value to
`false` in `spec.yaml.inputs` and records `golden_tests: skipped_by_input` in
the packet. When enabled, every applicable golden stage must pass and persist
`evidence/golden-tests.md` before delivery. Widget tests remain mandatory.

## Shared Figma UI Fidelity Contract

`/new-view` and `/new-feature` with `figma_scope: view` add
`visual_manifest` and `layout_manifest` to the packet. They are compact,
machine-readable reconciliations of visible Figma content, not verbose
handoffs. The initial plan cannot be approved until it contains:

- `reference_screenshot`: the Figma MCP screenshot reference for the requested
  main node;
- `assets`: an immutable Figma MCP export for every visible icon, image,
  illustration and logo, identified by source node, format, packet archive path
  and SHA-256; rendered non-icon assets also record their visible container,
  clip/mask chain, bounds, scale, translation, alignment and strategy;
- `icons`: an archived Figma export plus either a declared exact DS catalog
  match (`ds_icon_exact`) or that archived Figma SVG (`figma_svg_asset`);
- `typography`: family, size, weight, line height, alignment, Figma style id
  (or `inline:<node-id>`), exact project-font resolution and the resolved
  typography token for every visible text node;
- `screen_chrome.bottom_navigation`: whether it is visible in Figma and whether
  the result is owned by `existing_app_shell`, `view_scaffold`, or
  `not_present`; and
- `reconciliation`: counts, unresolved ids, completion status, and whether a
  visual-verification checkpoint is required.

`layout_manifest` is the structural counterpart. It records the requested
Figma root and capture viewport, then every visible structural node and leaf
with its parent id, child index, bounds, layout direction/alignment/padding/gap,
clip behavior, four independent corner radii and border width. This makes the
top-to-bottom/left-to-right order and rounded shapes auditable rather than
implicit in generated widget code.

For cropped, masked, or transformed assets, the reusable source asset is
exported and Flutter recreates the visible crop with
`explicit_clip_transform`. Exporting an enclosing Figma frame is not allowed:
it loses reuse and makes the result dependent on a single screen context.

The archive is mandatory for every Figma-driven `/new-component`, `/new-view`,
or `/new-feature` with `figma_url`: `download_assets(...)` must download the
source file into `source-assets/figma/` before the initial review. A legacy
`get_images(...)` adapter is acceptable only when the active MCP exposes no
equivalent current capability. An image URL,
screenshot, existing local asset, or visually similar system/DS icon is not
evidence of provenance. The code-generation phase copies image, illustration,
logo and Figma-SVG sources without modifying them; an exact declared DS icon
may use its catalog entry while retaining the Figma export as proof. The audit
verifies the final file checksum or exact DS identity. If an asset cannot be
exported or downloaded, the workflow stops with
`FIGMA_ASSET_DOWNLOAD_UNAVAILABLE`.

Typography has a distinct constraint: Figma supplies the design metadata but
normally not a redistributable font file. The analyzer records the exact Figma
family, weight and style reference, then verifies an exact registered project
font. It must block with `FIGMA_TYPOGRAPHY_UNAVAILABLE` rather than substitute
a close family or weight.

The controller always requires the screen-level fidelity gate for this scope.
It compares the canonical Figma screenshot reference with a deterministic
Flutter capture at `layout_manifest.viewport` and writes
`evidence/figma-fidelity-report.json`. Hierarchy/child order, literal text,
asset identity, typography resolution, and declared radii/border values are
exact invariants. Measured differences allow at most `1 dp` per geometry value,
`2%` global pixel difference, and `4%` regional pixel difference. A missing
comparison or a result above those limits blocks the pipeline; the human
checkpoint reviews the compact report and render references. This fidelity gate
does not replace optional golden regression tests.

`/new-feature` uses `figma_scope: view` by default when `figma_url` is set.
Set `figma_scope: component_inventory` only when the link supplies a DS
inventory rather than a screen the feature must reproduce. That lighter scope
still verifies Figma access and component provenance, but deliberately skips
the screen layout manifest and pixel-comparison gate.

## Evidence Modes

Every packet declares `evidence_mode: minimal | standard`. The default is
`minimal`, and users can override it in a workflow invocation with
`evidence_mode: standard`.

`minimal` keeps the evidence that controls deterministic execution: validation,
Figma preflight when required, human decisions, audit, executed tests, enabled
optional stages and delivery. Other phase outcomes are compact structured
entries in `context.json.phase_results`, so later agents can resume without
re-reading prose reports. `standard` additionally writes detailed analysis,
inventory, planning, code-generation, Widgetbook and checkpoint reports.

## Portable Role Execution

`/new-feature` packets require `execution_capabilities`:

```yaml
execution_capabilities:
  subagent_delegation: available | unavailable
  fallback_policy: delegate_or_controller_executes
```

The entry controller owns every required result. A named agent such as
`test-engineer` is the preferred specialist role, not a reason to omit work on
tool surfaces that cannot delegate. When delegation is unavailable,
`feature-builder` executes the role contract itself using the same planned
artifacts, commands, evidence and blockers. This is mandatory for unit, widget
and integration tests; unavailable delegation is never `skipped_by_input`.

## Required `spec.yaml` Concepts

Every generated spec must include:

- `schema_ref`
- `workflow`
- `spec_level`
- `execution_mode`
- `inputs`
- `evidence_mode`
- `human_review`
- `agent_permissions`
- `external_access`
- `artifact_plan`
- `success_criteria`
- `handoffs`

Artifacts must declare a `target_id`; paths are resolved against:

```text
.sopp/config/project.config.yaml -> targets.registry[target_id].root
```

## Bootstrap Packet

Bootstrap uses a separate packet because target roots are still being resolved:

```text
<APP_REPO_ROOT>/.sopp/bootstrap/{run_id}/
├── bootstrap-spec.yaml
├── context.json
├── review.md
├── proposed/
│   ├── project.config.yaml
│   ├── architecture-contract.yaml
│   └── dependencies-contract.yaml
└── evidence/
```

After approval, the proposed files are applied to:

```text
<APP_REPO_ROOT>/.sopp/config/
```

Bootstrap is idempotent by default. Before discovery, it validates an existing
final `.sopp/config` triplet for the resolved app repository. A valid triplet
is returned as `reused_existing_config` without creating a new bootstrap run.
A partial or invalid triplet is `blocked_input`; it is never silently replaced.
`FORCE_RECONFIGURE: true` is required for an intentional repair or migration
proposal, which still requires human approval before applying changes.

`.copilot/` and `.kiro/` can host exported agent resources, but neither folder
owns project configuration. Their `config/` contents are legacy state and must
not be read, merged, or written by functional workflows.

## Initial Configuration Files

| File | Owns | Must Not Own |
|---|---|---|
| `project.config.yaml` | Workspace roots, topology, targets, target structure, pipeline paths, naming, tokens and testing helpers. | Layer rules, dependency catalog, package imports or generation policies. |
| `architecture-contract.yaml` | Layers, generation policies, architecture constraints and domain/data contracts. | Physical workspace topology. |
| `dependencies-contract.yaml` | Internal/external dependencies and allowed dependency matrix. | Pipeline paths or repo mode. |

These files are generated from templates, reviewed, then applied by
`/bootstrap-workspace`.

## Templates

Templates live under this documentation folder:

```text
./templates/
├── project.config.yaml
├── architecture-contract.yaml
├── dependencies-contract.yaml
├── bootstrap/
├── spec-packets/
└── schemas/
```

Workflow overlays live in:

```text
./templates/spec-packets/overlays/
```

Each overlay declares its `entry_agent` and required inputs. Invoke that agent
with the workflow command as documented in [Workflows](workflows.md). The
`bootstrap-workspace` overlay defines its input contract but uses the separate
Bootstrap Spec Packet schema.

## Schemas

Schemas live in `./templates/schemas/`:

| Schema | Validates |
|---|---|
| `mobile-spec.schema.yaml` | Functional Mobile Spec Packets. |
| `mobile-context.schema.json` | Functional `context.json` state and checkpoint records. |
| `bootstrap-spec.schema.yaml` | Bootstrap proposal/apply state. |
| `project-config.schema.yaml` | `.sopp/config/project.config.yaml`. |
| `architecture-contract.schema.yaml` | `.sopp/config/architecture-contract.yaml`. |
| `dependencies-contract.schema.yaml` | `.sopp/config/dependencies-contract.yaml`. |

Generated files must set `schema_ref` to the matching schema path.

## Validation

Use the shared skill conceptually inside workflows and the local validator when
editing the KB. From the exported chapter root, run:

```bash
ruby scripts/validate_mobile_kb.rb
ruby scripts/validate_mobile_kb.rb --strict-language
```

The validator checks parseability, references, workflow/steering sync,
permissions, Figma MCP rules, schema expectations, language policy and
anti-drift rules.
