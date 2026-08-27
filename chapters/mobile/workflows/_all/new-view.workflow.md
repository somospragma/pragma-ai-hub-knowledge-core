---
id: new-view
version: 1.5.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: ds-orchestrator
input_contract: ../docs/templates/spec-packets/new-view.overlay.yaml
invocation_mode: explicit_agent
description: >
  Deterministic workflow to create a Flutter view or screen from Figma using DS components and the app presentation layer. Use when the user requests a Figma-driven app screen with view states, tests, Widgetbook, and audit gates.
---
# Workflow: New View/Screen from Figma

## Telemetry — Workflow metadata

| Field | Value |
|---|---|
| `workflow-id` | `new-view` |
| `user-story-id` | Value of the required `hu_id` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `gate-0-canonical-configuration`, `gate-0-1-topology`, `gate-0-2-spec-packet-ownership`, `gate-0-5-ownership-repo-app`, `gate-1-architecture`, `gate-2-contracts-policy`, `gate-3-figma-mcp`, `phase-0-spec-packet`, `phase-1-analysis-of-screen`, `phase-2-inventory-dag`, `phase-2-1-architecture-technical`, `phase-2-2-contracts-minimum`, `phase-2-3-validation-human-review`, `phase-3-1-codegen-ds`, `phase-3-2-audit-ds`, `phase-3-3-checkpoint-ds`, `phase-3-4-codegen-view`, `phase-3-5-audit-view`, `phase-3-6-checkpoint-view`, `phase-4-1-ds-widget-tests`, `phase-4-2-ds-golden-tests`, `phase-4-3-ds-widgetbook`, `phase-4-4-view-widget-tests`, `phase-4-5-view-golden-tests`, `phase-4-6-app-widgetbook`, `phase-5-delivery` |

> **NON-NEGOTIABLE RULE:** Every `pragma-ai workflow ...` command in this document is **MANDATORY** to execute. The agent MUST run them — they are not suggestions or documentation.

> ⛔ **STEP-ID INTEGRITY (NON-NEGOTIABLE):** The `--step-id` and `--workflow-id` values shown in every command block below are the **ONLY** valid identifiers for this workflow. The agent MUST copy them **verbatim** from this document — never invent, abbreviate, translate, paraphrase, pluralize, capitalize differently, or otherwise modify them.
>
> - Every `--step-id` submitted to `pragma-ai workflow report` or `pragma-ai workflow gap-report` MUST match one entry in the **"Step IDs"** list above, character-for-character (kebab-case, lowercase, exact spelling).
> - Every `--workflow-id` MUST be exactly `new-view`.
> - If a step-id you need is not in the list, STOP and ask the user — do not fabricate one.
> - The CLI rejects unknown step-ids; a wrong id silently corrupts the run's telemetry.

> Each step ends with a **human approval gate** before the gap report (see *Human approval gate* at the end of this document). The workflow keeps three domain-specific aggregate approval gates on top of the generic per-step gate: PHASE 2.3 (initial spec plan), PHASE 3.3 (DS layer checkpoint), PHASE 3.6 (app view layer checkpoint).
> The **gap report only runs on steps that produce output files** (`--output-file`). In this workflow the seven pre-flight gates, `phase-2-3-validation-human-review`, `phase-3-3-checkpoint-ds` and `phase-3-6-checkpoint-view` do NOT run a gap report.
> Two phases are conditional and emit telemetry only when executed: `phase-2-2-contracts-minimum` requires `CONTRACTS_POLICY=generate`; `phase-4-2-ds-golden-tests` and `phase-4-5-view-golden-tests` require `golden_tests=true`.
> Commands assume the shell's cwd is already the project root — no `cd` prefix is needed, and `--project-dir` only matters when running from elsewhere.

---

## Setup — Mint the workflow instance

> ⚡ **MANDATORY** — Always run this at the start, before any step.

### Resolve user-story-id (mandatory)

`hu_id` is a **required** invocation input for this workflow (see *User Inputs*), so the agent already has the user story identifier at the start. The agent MUST map it to `user-story-id` before running `workflow create`:

1. **Invocation input (canonical):** Use the `hu_id` value provided in the invocation. This is the required path.
2. **Fallback — Session context:** If `hu_id` was not supplied but a `user-story-id` is already available from a parent flow or another sub-workflow in this session, reuse it silently.
3. **Fallback — Project file:** If neither of the above is available, read the ID from `output/.active-user-story` when it exists.
4. **Last resort — Ask the user:** If no source yields an ID, ask explicitly and refuse to proceed without a value:

```
Kratos: To track progress I need the user-story-id.
  What is the active user story? (e.g. US-12345, HU-678)
```

> Once resolved, the agent MUST persist the value to `output/.active-user-story` so downstream workflows inherit it automatically.

```bash
# 1. Take the required hu_id from the invocation and use it as user-story-id
USER_STORY_ID="$hu_id"

# 2. Persist for other workflows so they don't have to ask again
echo "$USER_STORY_ID" > output/.active-user-story

# 3. Mint the instance
INSTANCE_ID=$(pragma-ai workflow create \
  --workflow-id new-view \
  --user-story-id "$USER_STORY_ID")
```

---

## Evidence Mode

Accept `evidence_mode: minimal | standard`; default to `minimal` and persist it
as `spec.yaml.evidence_mode` before validation. In `minimal`, retain gate
evidence and record every other phase as a compact
`context.json.phase_results` entry. `standard` additionally writes detailed
phase reports. Neither mode may omit a gate, approval, test result, blocker or
delivery result.

## Initial Invocation Is Plan-Only

The initial `/new-view` response may write only the Mobile Spec Packet and its
evidence. It must complete analysis, DS/App inventory, DAG, and technical plan
inside `spec.yaml`, then present `review.md` in Spanish and end the response.
It must not generate Flutter code, tests, assets, routes, Widgetbook files, or
project configuration in that response.

Only a later human turn that explicitly approves the pending packet may change
`context.json` to `approved_for_execution` and unlock Phase 3.1. Approval is
invalid when the packet lacks the required plan or when
`checkpoints.initial_spec.status` is not `pending`.

Invoke this workflow through `@ds-orchestrator`. A bare workflow name or a
request that lacks the controller must not authorize implementation; respond
with the canonical invocation instead of generating code.

## Prerequisites

- URL from Figma with `node-id`.
- user story with acceptance criteria (inline text or reference to a Markdown file).
- A valid final configuration triplet in the app repository:
  `.sopp/config/project.config.yaml`, `architecture-contract.yaml`, and
  `dependencies-contract.yaml`.
- This workflow never starts bootstrap automatically. If configuration is
  missing, partial, invalid, ambiguous, or legacy-only, finish with
  `blocked_input` and the relevant configuration code. The human must invoke
  `@workspace-discovery /bootstrap-workspace` explicitly.
- Context resolved by the orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `APP_TARGET_ID = target_id` when supplied; otherwise
    `active_target_defaults.app_target_id`, falling back to
    `active_target_defaults.app`
  - `DESIGN_SYSTEM_TARGET_ID = active_target_defaults.design_system_target_id`,
    falling back to `active_target_defaults.design_system`
  - `SPEC_PACKET_OWNER_TARGET_ID = APP_TARGET_ID` (immutable for the run)
  - `SPEC_PACKET_OWNER_ROOT = targets.registry[SPEC_PACKET_OWNER_TARGET_ID].root`
  - `ACTIVE_TARGET_ID` per implementation phase (`DESIGN_SYSTEM_TARGET_ID` for
    DS, `APP_TARGET_ID` for the view)
  - `ACTIVE_TARGET_ROOT`
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `GENERATION_SCOPE`
  - `CONTRACTS_POLICY`
  - `ARCHITECTURE_CONTRACT_PATH`
  - `PIPELINE_SPEC_PATH = {SPEC_PACKET_OWNER_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {SPEC_PACKET_OWNER_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`
  - `SPEC_PACKET_PATH = {SPEC_PACKET_OWNER_ROOT}/{pipeline.output_dir}/specs/{view_slug}`

## Gates required

### Gate 0 - Canonical Configuration

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-canonical-configuration \
  --status started
```

Before any packet, log, Figma request, or code generation:

1. Resolve `PROJECT_ROOT` from optional `project_root`, then the IDE workspace
   root, then the current repository root.
2. Inspect only `<candidate>/.sopp/config/` for the three final configuration
   files.
3. Require one valid configuration triplet whose
   `project.repository_local_path` matches the resolved app repository.
4. Ignore runtime-looking files under any tool-specific KB folder; only
   `<APP_REPO_ROOT>/.sopp/` may contain project runtime state.
5. If the triplet is missing, partial, invalid, or ambiguous, finish with
   `blocked_input`. Do not create a bootstrap proposal or write any YAML.

> ⚡ **MANDATORY (conditional)** — If the triplet is missing, partial, invalid, or ambiguous:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-canonical-configuration \
  --status failed
```

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-canonical-configuration \
  --status finished
```

### Gate 0.1 - Topology

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-1-topology \
  --status started
```

1. Validate `TOPOLOGY_REPO_MODE`.
2. Validate roots (`PROJECT_ROOT`, `APP_TARGET_ID` and
   `DESIGN_SYSTEM_TARGET_ID` if DS components will be created).
3. In targets `location_strategy=melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

> ⚡ **MANDATORY (conditional)** — If any validation fails and the gate ends with `blocked_input`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-1-topology \
  --status failed
```

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-1-topology \
  --status finished
```

### Gate 0.2 - Spec Packet Ownership

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-2-spec-packet-ownership \
  --status started
```

Before writing any packet, log, report or Figma evidence:

1. Resolve `APP_TARGET_ID` from `target_id` or the app default. It must exist
   in `targets.registry` and have `kind: app`.
2. Set `SPEC_PACKET_OWNER_TARGET_ID = APP_TARGET_ID` and
   `SPEC_PACKET_OWNER_ROOT = targets.registry[APP_TARGET_ID].root`.
3. Compute every packet-state path from `SPEC_PACKET_OWNER_ROOT` only.
   `ACTIVE_TARGET_ID` may change for DS and app implementation phases, but it
   must never change `SPEC_PACKET_PATH`, `PIPELINE_LOG_PATH` or
   `PIPELINE_SPEC_PATH`.
4. If the resolved packet root differs from `SPEC_PACKET_OWNER_ROOT`, stop with
   `CONFIG_SPEC_PACKET_ROOT_MISMATCH`. If the target is missing or is not an
   app, stop with `CONFIG_SPEC_PACKET_OWNER_INVALID`.

> ⚡ **MANDATORY (conditional)** — If `CONFIG_SPEC_PACKET_ROOT_MISMATCH` or `CONFIG_SPEC_PACKET_OWNER_INVALID` triggers:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-2-spec-packet-ownership \
  --status failed
```

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-2-spec-packet-ownership \
  --status finished
```

### Gate 0.5 — Ownership of the Repo App

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-5-ownership-repo-app \
  --status started
```

1. `project.config.yaml` must be the canonical config for the app repo:
   `{PROJECT_ROOT}/.sopp/config/project.config.yaml`.
2. `PROJECT_ROOT` cannot be a library DS/shared/core.
3. Minimum app signals:
   - `single_repo | multi_repo`: exists `lib/main.dart` or `lib/main_*.dart`
     or folder `android/` or `ios/`.
   - `monorepo_melos`: Melos resolver passes, package target is valid and the
     target is not classified as DS/shared/core.
4. If it fails, block with:
   - `CONFIG_PROJECT_CONFIG_OUTSIDE_APP_REPO`
   - `CONFIG_PROJECT_ROOT_POINTS_TO_LIBRARY`
   - `CONFIG_APP_EXECUTABLE_SIGNAL_MISSING`

> ⚡ **MANDATORY (conditional)** — If any of the above blocking codes triggers:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-5-ownership-repo-app \
  --status failed
```

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-0-5-ownership-repo-app \
  --status finished
```

### Gate 1 — Architecture

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-1-architecture \
  --status started
```

1. If `architecture_contract.generation_policies.view_generation.require_architecture_contract=true`, require
   `ARCHITECTURE_CONTRACT_PATH`.
2. `architecture.md` is optional visual support.

> ⚡ **MANDATORY (conditional)** — If the required `ARCHITECTURE_CONTRACT_PATH` is missing:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-1-architecture \
  --status failed
```

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-1-architecture \
  --status finished
```

### Gate 2 — Policy of contracts

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-2-contracts-policy \
  --status started
```

1. `optional`: continue.
2. `generate`: generate contracts minimum in
   `spec.yaml.contracts.minimal_domain_data` before Phase 3.4.
3. `required`: block if referenced domain/data contracts are missing.

If it fails a gate, finish with `blocked_input`.

> ⚡ **MANDATORY (conditional)** — If `CONTRACTS_POLICY=required` and referenced domain/data contracts are missing:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-2-contracts-policy \
  --status failed
```

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-2-contracts-policy \
  --status finished
```

### Gate 3 — Figma MCP

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-3-figma-mcp \
  --status started
```

Before PHASE 1, `@ds-orchestrator` prefers `@figma-analyzer` for Figma MCP
preflight. When the active surface cannot delegate natively, it executes the
figma-analyzer role contract itself only when the packet grants Figma MCP,
packet-write and source-archive permissions. The preflight verifies that Figma
MCP is configured and has permissions for the file/screen; otherwise stop with
`PLATFORM_CONTROLLER_ROLE_CAPABILITY_MISSING`.

Minimum checklist:

1. URL parseable with `fileKey` and `nodeId`.
2. Figma MCP is available in the active tool.
3. `get_design_context(fileKey, nodeId)` responds.
4. `get_screenshot(...)` responds for the main frame.
5. Access is confirmed for required components, styles, variables and assets.
6. The active agent can write the packet-only Figma source archive at
   `{SPEC_PACKET_PATH}/source-assets/figma/`.
7. `get_images(...)` exports can be persisted by the active tool surface; a
   screenshot or temporary URL alone does not satisfy source-asset access.

If it fails, update `spec.yaml.external_access.figma_mcp.status=blocked_input`,
persist `evidence/figma-mcp-preflight.md` and finish with `blocked_input`.

> ⚡ **MANDATORY (conditional)** — If preflight fails (persists `evidence/figma-mcp-preflight.md` and ends with `blocked_input` or `PLATFORM_CONTROLLER_ROLE_CAPABILITY_MISSING`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-3-figma-mcp \
  --status failed
```

> ⚡ **MANDATORY (success path)** — Report `finished` on completion (successful preflight produces no artifact — the diagnostic file is only written on failure, and the failure branch already reported `failed`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id gate-3-figma-mcp \
  --status finished
```

## User Inputs

`hu_id` is **required**: it identifies the user story this view belongs to and
is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied, the
workflow refuses to start.

```text
@ds-orchestrator /new-view
hu_id: US-12345                                             [Required]
view_name: product_catalog_view
figma_url: https://www.figma.com/file/xxx/Screen?node-id=456
user_story: [User story or acceptance criteria]
user_story_path: [Optional Markdown path; e.g. docs/user-stories/story-123.md]
route_name: [Optional route name or path]
target_id: [Optional app target id]
project_root: [Optional absolute app repository root when the IDE opens a multi-root workspace]
golden_tests: false  [Optional; default false]
evidence_mode: minimal  [Optional; default minimal]
```

## Canonical Sequence

### PHASE 0 — Mobile Spec Packet (`standard`)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-0-spec-packet \
  --status started
```

**Agent**: `@ds-orchestrator`
**Skill**: `mobile-sdd-spec-validation`

Create `SPEC_PACKET_PATH` with:

1. `spec.yaml` (`schema_ref: ../docs/templates/schemas/mobile-spec.schema.yaml`,
   `spec_level: standard`, `execution_mode: propose_then_apply`)
2. `context.json`
3. `review.md` in Spanish
4. `evidence/validation-report.md`

Record `packet_owner_target_id: APP_TARGET_ID` and
`packet_root: SPEC_PACKET_PATH` in `context.json`. Verify that the packet path
is inside `SPEC_PACKET_OWNER_ROOT` before the first write. DS phases may write
only their planned artifacts under `DESIGN_SYSTEM_TARGET_ID`; they must keep
all packet state and evidence under this app-owned packet.

The initial spec records inputs, Figma URL, user story, contracts policy,
architecture required, success criteria for DS + view and checkpoints
required. Must include `external_access.figma_mcp.required=true` and
`agent_permissions` per agent. Normalize an omitted `golden_tests` input to
`false` and persist the resolved boolean in `spec.yaml.inputs`. Plan golden
artifacts and golden success criteria only when it is `true`. Do not generate
code in this phase.

> ⚡ **MANDATORY (success path)** — Report `finished` with all four packet artifacts. Substitute `${SPEC_PACKET_PATH}` with the resolved run path:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-0-spec-packet \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/review.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/validation-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.

---

### PHASE 1 — Analysis of Screen

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-1-analysis-of-screen \
  --status started
```

**Preferred specialist role**: `@figma-analyzer`
**Execution owner**: `@ds-orchestrator` when native delegation is unavailable
and the approved packet grants the figma-analyzer role permissions.
**Prompt**: `figma-analysis.prompt.md`

Update in `spec.yaml` only `design_source`, `literal_texts`,
`layout_constraints`, `view_states`, `navigation`, `assets`, and
`visual_manifest`, and `layout_manifest`. Download every visible Figma icon, image, illustration,
logo, and image-fill source into `{SPEC_PACKET_PATH}/source-assets/figma/` and
record its node id, format, archive path and SHA-256 in `assets`. Do not accept
a screenshot, URL, existing local asset, or similar icon as a substitute.
Persist evidence in `evidence/figma-analysis.md` and record phase in
`PIPELINE_LOG_PATH`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated spec, the analysis evidence, and every source asset archived under `source-assets/figma/`. Expand `${FIGMA_SOURCE_ASSETS[@]}` from the paths recorded in `spec.yaml.assets[].archive_path`:

```bash
# Build --output-file flags for every archived Figma source asset
FIGMA_ASSET_FLAGS=()
while IFS= read -r asset; do
  FIGMA_ASSET_FLAGS+=(--output-file "$asset")
done < <(yq -r '.assets[].archive_path' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-1-analysis-of-screen \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/evidence/figma-analysis.md" \
  "${FIGMA_ASSET_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.

---

### PHASE 2 — Extended Inventory + DAG

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-inventory-dag \
  --status started
```

**Agent**: `@component-planner`
**Prompt**: `atomic-inventory.prompt.md`

Update in `spec.yaml` only `canonical_spec`, `inventory`, `dag`,
`artifact_plan.planned[group=ds_components]` and `artifact_plan.planned[group=app_view]`.
The DS vs App separation must remain explicit in `inventory` and `artifact_plan`.

> ⚡ **MANDATORY (success path)** — Report `finished`. This phase updates `spec.yaml` in place — declare it as the output file so the gap report can diff this phase's contribution:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-inventory-dag \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.1.

---

### PHASE 2.1 — Architecture Technical

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-1-architecture-technical \
  --status started
```

**Agent**: `@component-architect`

Update in `spec.yaml` only `technical_plan`, `artifact_plan`,
`contracts.text_overflow`, `contracts.asset_rendering`,
`contracts.icon_mapping`, `contracts.typography_mapping`,
`contracts.screen_chrome`, `visual_manifest`, `success_criteria`, `handoffs`
and `checkpoints`.

> ⚡ **MANDATORY (success path)** — Report `finished`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-1-architecture-technical \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.2 (only when `CONTRACTS_POLICY=generate`) or directly to PHASE 2.3.

---

### PHASE 2.2 — Contracts Minimum (only `CONTRACTS_POLICY=generate`)

> ⚡ **MANDATORY only when `CONTRACTS_POLICY=generate`.** When the policy is `optional` or `required`, skip this phase entirely — do not emit `started`/`finished` for it.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-2-contracts-minimum \
  --status started
```

**Agent**: `@component-architect`

Update in `spec.yaml` only `contracts.minimal_domain_data`.

> ⚡ **MANDATORY (success path)** — Report `finished`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-2-contracts-minimum \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.3.

---

### PHASE 2.3 — Validation + Human Review

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-3-validation-human-review \
  --status started
```

**Skill**: `mobile-sdd-spec-validation`

The orchestrator validates the `/new-view` plan gate in
`mobile-sdd-spec-validation`, presents `review.md` and waits for explicit
approval.

Present:

1. visual analysis, texts, constraints and states view.
2. visual manifest reconciliation: cropped assets, exact icon mappings,
   typography mappings, and bottom-navigation ownership.
3. layout manifest reconciliation: viewport, parent-child order, bounds,
   direction, padding, gap, clipping, four-corner radii, border width, and
   fixed fidelity tolerances.
4. inventory + DAG with DS/App separation.
5. technical plan.
6. success criteria of DS, view, tests, goldens and Widgetbook.

If the human requests adjustments, update only `spec.yaml`, `review.md` and the
affected sections. Do not generate code until `context.json` marks the spec as
approved.

The response that presents this review must end here. Code generation begins
only in a later human turn with explicit approval of this pending packet.

> ⚡ **MANDATORY (conditional)** — If the plan gate cannot be validated (schema/business failure that cannot be repaired in-review):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-3-validation-human-review \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` once validation passes and the human review is presented (approval itself happens in the gate that follows):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-2-3-validation-human-review \
  --status finished
```

> **Stop here.** This is the **domain aggregate approval gate** for the initial spec plan (PHASE 0 through PHASE 2.2). If the human requests changes to `design_source`, `literal_texts`, `assets`, `view_states`, `navigation`, `visual_manifest`, `layout_manifest`, `inventory`, `dag`, `technical_plan`, `contracts.minimal_domain_data`, or `artifact_plan`, the flow must return to the phase that owns that section: report `re_started` on the affected earlier phase, apply changes, report `finished` again for that phase, re-run its gap report, and re-enter PHASE 2.3 (which itself gets `re_started` → `finished` again). Only when `context.json.status=approved_for_execution` and `checkpoints.initial_spec.status=approved` may PHASE 3.1 begin. *(PHASE 2.3 produces no new output files — no gap report required.)*

---

### PHASE 3.1 — Codegen of Components DS

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-1-codegen-ds \
  --status started
```

**Agent**: `@widget-developer`

Required order: atoms → molecules → organisms.
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_codegen
read_sections:
  - technical_plan
  - artifact_plan.planned[group=ds_components]
  - literal_texts
  - layout_constraints
  - assets
  - source-assets/figma
  - contracts.text_overflow
  - contracts.technical_vectors
  - contracts.asset_rendering
  - contracts.icon_mapping
  - contracts.typography_mapping
  - visual_manifest
  - layout_manifest
  - success_criteria
```

> ⚡ **MANDATORY (success path)** — Report `finished` with one `--output-file` per `.dart` file declared in `artifact_plan.planned[group=ds_components]`. Paths must be relative to `--project-dir` (project root). Expand the array from the spec:

```bash
# Build --output-file flags from the artifact plan
DS_FILE_FLAGS=()
while IFS= read -r f; do
  DS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_components") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-1-codegen-ds \
  --status finished \
  "${DS_FILE_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 3.2.

---

### PHASE 3.2 — Audit of Components DS

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-2-audit-ds \
  --status started
```

**Agent**: `@code-auditor`

Loop with `@widget-developer` up to `pipeline.max_audit_retries`.

Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_component_audit
read_sections:
  - artifact_plan.planned[group=ds_components]
  - technical_plan
  - contracts.technical_vectors
  - contracts.asset_rendering
  - contracts.icon_mapping
  - contracts.typography_mapping
  - visual_manifest
  - layout_manifest
  - success_criteria
```

> ⚡ **MANDATORY (conditional)** — If the audit loop exceeds `pipeline.max_audit_retries` without passing:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-2-audit-ds \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the DS audit evidence:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-2-audit-ds \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/ds-component-audit.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 3.3.

---

### PHASE 3.3 — Checkpoint Human of Layer DS

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-3-checkpoint-ds \
  --status started
```

**Agent**: `@ds-orchestrator`

Present a compact review in Spanish before generating the app view:

1. DS components created/modified
2. audit result DS
3. covered visual criteria
4. risks or fallbacks pending

Wait for explicit approval. If the human requests adjustments, return to
PHASE 3.1 or PHASE 3.2 as applicable. Do not continue to PHASE 3.4 until
`context.json.checkpoints.ds_layer.status=approved` and
`context.json.status=approved_for_execution`.

> ⚡ **MANDATORY (success path)** — Report `finished` once the DS-layer review has been presented (approval itself happens in the gate that follows):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-3-checkpoint-ds \
  --status finished
```

> **Stop here.** This is the **domain aggregate approval gate** for the DS layer (PHASE 3.1 and PHASE 3.2). On rejection of the DS layer, report `re_started` on the affected earlier phase (`phase-3-1-codegen-ds` or `phase-3-2-audit-ds`), regenerate, re-report `finished`, re-run that phase's gap report, and then report `re_started` → `finished` on `phase-3-3-checkpoint-ds` before re-entering this gate. Only when `context.json.checkpoints.ds_layer.status=approved` and `context.json.status=approved_for_execution` may PHASE 3.4 begin. *(PHASE 3.3 produces no new output files — no gap report required.)*

---

### PHASE 3.4 — Codegen of View App

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-4-codegen-view \
  --status started
```

**Agent**: `@widget-developer`
**Prompt**: `codegen-view.prompt.md`
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: app_view_codegen
read_sections:
  - technical_plan.view
  - artifact_plan.planned[group=app_view]
  - contracts
  - view_states
  - navigation
  - literal_texts
  - layout_constraints
  - contracts.text_overflow
  - contracts.technical_vectors
  - contracts.asset_rendering
  - contracts.icon_mapping
  - contracts.typography_mapping
  - contracts.screen_chrome
  - source-assets/figma
  - visual_manifest
  - layout_manifest
  - success_criteria
```

Output:
- View in `targets.registry[APP_TARGET_ID].structure.views_path`.
- Private widgets in `targets.registry[APP_TARGET_ID].structure.view_widgets_path`.

> ⚡ **MANDATORY (success path)** — Report `finished` with one `--output-file` per file declared in `artifact_plan.planned[group=app_view]`. Expand the array from the spec:

```bash
APP_VIEW_FLAGS=()
while IFS= read -r f; do
  APP_VIEW_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="app_view") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-4-codegen-view \
  --status finished \
  "${APP_VIEW_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 3.5.

---

### PHASE 3.5 — Audit of App View

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-5-audit-view \
  --status started
```

**Agent**: `@code-auditor`

Loop with `@widget-developer` up to `pipeline.max_audit_retries`.
The audit must reconcile every `visual_manifest` entry. A missing downloaded
Figma source archive, checksum mismatch, missing exact icon, unrecreated
`explicit_clip_transform` crop, unresolved typography, or incorrect
bottom-navigation ownership is a blocker.
It must also reject a missing/changed `layout_manifest` child order, geometry
outside `1 dp`, incorrect corner radii or border width, or a fidelity report
over `2%` global / `4%` regional pixel difference.

Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: app_view_audit
read_sections:
  - artifact_plan.planned[group=app_view]
  - technical_plan.view
  - literal_texts
  - assets
  - source-assets/figma
  - visual_manifest
  - layout_manifest
  - contracts.asset_rendering
  - contracts.icon_mapping
  - contracts.typography_mapping
  - contracts.screen_chrome
  - success_criteria
```

> ⚡ **MANDATORY (conditional)** — If the audit loop exceeds `pipeline.max_audit_retries` without passing, or an audit blocker (missing Figma archive, checksum mismatch, missing exact icon, unrecreated crop, unresolved typography, incorrect bottom-navigation ownership, `layout_manifest` geometry outside `1 dp`, incorrect corner radii/border width, or fidelity report over `2%` global / `4%` regional pixel difference) cannot be resolved:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-5-audit-view \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the app-view audit evidence and the Figma fidelity report:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-5-audit-view \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/app-view-audit.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/figma-fidelity-report.json"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 3.6.

---

### PHASE 3.6 — Human Checkpoint of App View

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-6-checkpoint-view \
  --status started
```

**Agent**: `@ds-orchestrator`

Present the app-view audit and wait for explicit approval before tests. Include
the resolved bottom-navigation ownership, every Figma source archive result,
any crop/icon/typography mapping, and `evidence/figma-fidelity-report.json`.
The fidelity report is required for every view and compares the canonical Figma
screenshot with Flutter at `layout_manifest.viewport`. It must pass `1 dp`
geometry, `2%` global pixel difference, and `4%` regional pixel difference. If
capture or comparison cannot be completed, stop with
`FIGMA_FIDELITY_COMPARISON_UNAVAILABLE`.

Do not continue until `context.json.checkpoints.app_view_layer.status=approved`
and `context.json.status=approved_for_execution`.

> ⚡ **MANDATORY (conditional)** — If capture or comparison cannot be completed (`FIGMA_FIDELITY_COMPARISON_UNAVAILABLE`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-6-checkpoint-view \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` once the app-view checkpoint review has been presented (approval itself happens in the gate that follows):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-6-checkpoint-view \
  --status finished
```

> **Stop here.** This is the **domain aggregate approval gate** for the app view layer (PHASE 3.4 and PHASE 3.5). On rejection of the app view layer, report `re_started` on the affected earlier phase (`phase-3-4-codegen-view` or `phase-3-5-audit-view`), regenerate, re-report `finished`, re-run that phase's gap report, and then report `re_started` → `finished` on `phase-3-6-checkpoint-view` before re-entering this gate. Only when `context.json.checkpoints.app_view_layer.status=approved` and `context.json.status=approved_for_execution` may PHASE 4.1 begin. *(PHASE 3.6 produces no new output files — no gap report required.)*

---

### PHASE 4.1 — Tests of Components DS

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-1-ds-widget-tests \
  --status started
```

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGET_TESTS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_widget_tests
read_sections:
  - artifact_plan.planned[group=ds_components]
  - technical_plan
  - contracts.text_overflow
  - success_criteria
```

> ⚡ **MANDATORY (conditional)** — Widget tests are required for delivery. If they cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-1-ds-widget-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed without a passing `evidence/widget-tests.md`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated test files and the widget-tests evidence. Expand the file array from `artifact_plan.planned[group=ds_widget_tests]`:

```bash
DS_TEST_FLAGS=()
while IFS= read -r f; do
  DS_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_widget_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-1-ds-widget-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/widget-tests.md" \
  "${DS_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.2 (only when `golden_tests=true`) or directly to PHASE 4.3.

---

### PHASE 4.2 — Golden of Components DS (conditional)

> ⚡ **MANDATORY only when `golden_tests=true`.** When `golden_tests=false`, skip this phase entirely — do not emit `started`/`finished` for it. The workflow's own `skipped_by_input` record in `context.json`, `spec.yaml` and `PIPELINE_LOG_PATH` covers the skip.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-2-ds-golden-tests \
  --status started
```

**Condition**: `golden_tests=true`.
**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_GOLDEN_TESTS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_golden_tests
read_sections:
  - artifact_plan.planned[group=ds_components]
  - technical_plan
  - layout_constraints
  - contracts.text_overflow
  - success_criteria
```

When `golden_tests=false`, do not invoke `@golden-test-engineer` or create DS
golden artifacts. Record the single run outcome `golden_tests: skipped_by_input`
with `reason: golden_tests=false` in `context.json`, `spec.yaml` and
`PIPELINE_LOG_PATH`.

> ⚡ **MANDATORY (conditional)** — If DS golden tests were requested but cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-2-ds-golden-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed with a failing golden outcome when `golden_tests=true`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated DS golden files and the golden-tests evidence:

```bash
DS_GOLDEN_FLAGS=()
while IFS= read -r f; do
  DS_GOLDEN_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_golden_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-2-ds-golden-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/golden-tests.md" \
  "${DS_GOLDEN_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.3.

---

### PHASE 4.3 — Widgetbook of Components DS

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-3-ds-widgetbook \
  --status started
```

**Agent**: `@widgetbook-developer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGETBOOK`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_widgetbook
preflight:
  - ensure_widgetbook_initialized  # Step -1 of flutter-ds-widgetbook
read_sections:
  - artifact_plan.planned[group=ds_components]
  - technical_plan
  - literal_texts
  - contracts.text_overflow
  - success_criteria
```

> **Preflight bootstrap.** Before generating any use case, `@widgetbook-developer`
> runs Step -1 of the `flutter-ds-widgetbook` skill. When the Widgetbook host
> project is not initialized, it executes the cold-init sequence from
> `references/setup.md` (single/multi-repo) or `references/monorepo.md`
> (`monorepo_melos`) and appends every bootstrapped file to the phase's
> `--output-file` set. Typical bootstrap files (paths depend on repo mode; see
> the "Bootstrap output files" section in each reference):
>
> - `widgetbook_[appname]/pubspec.yaml` (or `apps/widgetbook_[appname]/pubspec.yaml`)
> - `widgetbook_[appname]/lib/main.dart`
> - `widgetbook_[appname]/lib/main.directories.g.dart`
> - `widgetbook_[appname]/lib/ui_system/.gitkeep`
> - `widgetbook_[appname]/lib/features/.gitkeep`
> - `widgetbook_[appname]/lib/shared/.gitkeep`
> - Root `pubspec.yaml` and/or `melos.yaml` only when a monorepo workspace list was edited.
>
> If any initialization command fails, report `phase-4-3-ds-widgetbook` as
> `failed` with the captured error and stop the workflow — do not fall back
> to writing use cases against an uninitialized project.
> The DS phase owns the first Widgetbook bootstrap; PHASE 4.6 must find the
> project already initialized and only add screen use cases.

> ⚡ **MANDATORY (success path)** — Report `finished` with the DS Widgetbook use-case files **plus** any bootstrap files produced by Step -1. Expand the use-case array from `artifact_plan.planned[group=ds_widgetbook]` and, when Step -1 bootstrapped Widgetbook, append the bootstrap files reported by `@widgetbook-developer`:

```bash
DS_WIDGETBOOK_FLAGS=()
while IFS= read -r f; do
  DS_WIDGETBOOK_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_widgetbook") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

# Optional: append bootstrap files when Step -1 initialized Widgetbook.
# The agent lists them in evidence/widgetbook.md under a "bootstrap_files" block.
if [ -f "${SPEC_PACKET_PATH}/evidence/widgetbook.bootstrap-files.txt" ]; then
  while IFS= read -r f; do
    DS_WIDGETBOOK_FLAGS+=(--output-file "$f")
  done < "${SPEC_PACKET_PATH}/evidence/widgetbook.bootstrap-files.txt"
fi

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-3-ds-widgetbook \
  --status finished \
  "${DS_WIDGETBOOK_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.4.

---

### PHASE 4.4 — Tests of View

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-4-view-widget-tests \
  --status started
```

**Agent**: `@test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=VIEW_WIDGET_TESTS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: view_widget_tests
read_sections:
  - artifact_plan.planned[group=app_view]
  - technical_plan.view
  - view_states
  - navigation
  - visual_manifest
  - layout_manifest
  - contracts.text_overflow
  - contracts.screen_chrome
  - success_criteria
```

Minimum coverage:
1. `loading`
2. `empty`
3. `error`
4. `populated`
5. critical navigation
6. bottom-navigation ownership when applicable
7. literal text and mitigation of overflow when applicable

> ⚡ **MANDATORY (conditional)** — View widget tests are required for delivery. If they cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-4-view-widget-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed without a passing `evidence/view-widget-tests.md`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated view test files and the view-widget-tests evidence. Expand the file array from `artifact_plan.planned[group=view_widget_tests]`:

```bash
VIEW_TEST_FLAGS=()
while IFS= read -r f; do
  VIEW_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="view_widget_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-4-view-widget-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/view-widget-tests.md" \
  "${VIEW_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.5 (only when `golden_tests=true`) or directly to PHASE 4.6.

---

### PHASE 4.5 — Golden Tests of Complete View (conditional)

> ⚡ **MANDATORY only when `golden_tests=true`.** When `golden_tests=false`, skip this phase entirely — do not emit `started`/`finished` for it. The single `golden_tests: skipped_by_input` outcome recorded in Phase 4.2 already represents this decision.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-5-view-golden-tests \
  --status started
```

**Condition**: `golden_tests=true`.
**Agent**: `@golden-test-engineer`
**Prompt**: `test-generation.prompt.md` (`MODE=VIEW_GOLDEN_TESTS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: view_golden_tests
read_sections:
  - artifact_plan.planned[group=app_view]
  - technical_plan.view
  - view_states
  - layout_constraints
  - assets
  - source-assets/figma
  - visual_manifest
  - layout_manifest
  - contracts.asset_rendering
  - contracts.icon_mapping
  - contracts.typography_mapping
  - contracts.screen_chrome
  - contracts.text_overflow
  - success_criteria
```

When `golden_tests=false`, this phase is already represented by the single
`golden_tests: skipped_by_input` outcome recorded in Phase 4.2. Do not invoke
the agent or create view golden artifacts.

Minimum coverage:
1. `loading`
2. `empty`
3. `error`
4. `populated`
5. `light/dark`
6. compact viewport if overflow risk exists

> ⚡ **MANDATORY (conditional)** — If view golden tests were requested but cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-5-view-golden-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed with a failing view-golden outcome when `golden_tests=true`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated view golden files and the view-golden-tests evidence:

```bash
VIEW_GOLDEN_FLAGS=()
while IFS= read -r f; do
  VIEW_GOLDEN_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="view_golden_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-5-view-golden-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/view-golden-tests.md" \
  "${VIEW_GOLDEN_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.6.

---

### PHASE 4.6 — Widgetbook of Screen App

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-6-app-widgetbook \
  --status started
```

**Agent**: `@widgetbook-developer`
**Prompt**: `test-generation.prompt.md` (`MODE=APP_WIDGETBOOK_SCREENS`, `WIDGETBOOK_SCOPE=APP_SCREENS`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: app_widgetbook
preflight:
  - ensure_widgetbook_initialized  # Step -1 of flutter-ds-widgetbook
read_sections:
  - artifact_plan.planned[group=app_view]
  - technical_plan.view
  - view_states
  - literal_texts
  - visual_manifest
  - layout_manifest
  - contracts.screen_chrome
  - contracts.text_overflow
  - success_criteria
```

Minimum coverage:
1. `Default`
2. `Loading`
3. `Empty` (if applicable)
4. `Error` (if applicable)
5. `Populated`

> **Preflight bootstrap.** `@widgetbook-developer` re-runs Step -1 of the
> `flutter-ds-widgetbook` skill as a defensive check. In the normal flow the
> DS phase (PHASE 4.3) already initialized Widgetbook, so this check must be a
> no-op that only verifies the four signals. When PHASE 4.6 is entered in
> isolation (rerun, `re_started`, or a workflow that skipped PHASE 4.3), the
> bootstrap runs here and appends the bootstrap files reported by the agent to
> the phase's `--output-file` set. A failing initialization reports
> `phase-4-6-app-widgetbook` as `failed`; do not fall back to writing screen
> use cases against an uninitialized project.

> ⚡ **MANDATORY (success path)** — Report `finished` with the app-screen Widgetbook use-case files **plus** any bootstrap files produced by Step -1 (usually empty here because PHASE 4.3 already initialized Widgetbook). Expand the file array from `artifact_plan.planned[group=app_widgetbook]`:

```bash
APP_WIDGETBOOK_FLAGS=()
while IFS= read -r f; do
  APP_WIDGETBOOK_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="app_widgetbook") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

# Optional: append bootstrap files when Step -1 initialized Widgetbook in
# this phase (normally empty because PHASE 4.3 already handled it).
if [ -f "${SPEC_PACKET_PATH}/evidence/widgetbook.bootstrap-files.txt" ]; then
  while IFS= read -r f; do
    APP_WIDGETBOOK_FLAGS+=(--output-file "$f")
  done < "${SPEC_PACKET_PATH}/evidence/widgetbook.bootstrap-files.txt"
fi

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-4-6-app-widgetbook \
  --status finished \
  "${APP_WIDGETBOOK_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 5.

---

### PHASE 5 — Delivery

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-5-delivery \
  --status started
```

**Agent**: `@delivery-manager`
**Prompt**: `delivery-review.prompt.md`

Must:
1. validate the DS/App structure against `targets.registry` and
   `artifact_plan.planned[].target_id`
2. update the DS barrel only for components DS
3. use branch prefix:
   - `naming.view_branch_prefix` if it exists
   - fallback `naming.branch_prefix`
4. generate `evidence/delivery-report.md` and a summary in the human report
5. validate that the delivery satisfies `SPEC_PACKET_PATH/spec.yaml`
6. require passing `evidence/widget-tests.md` and
   `evidence/view-widget-tests.md`
7. require passing `evidence/golden-tests.md` when `golden_tests=true`, or the
   recorded `golden_tests: skipped_by_input` outcome when false
8. require completed visual-manifest and layout-manifest reconciliation plus a
   passing `evidence/figma-fidelity-report.json` at the manifest viewport:
   exact text/hierarchy/assets/typography/shape values, at most `1 dp`
   geometry delta, `2%` global pixel difference and `4%` regional pixel
   difference

> ⚡ **MANDATORY (conditional)** — If any delivery precondition is not met (missing/failing DS or view widget tests, inconsistent golden outcome, incomplete visual/layout reconciliation, or failing fidelity report):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-5-delivery \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the delivery report:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-5-delivery \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/delivery-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** — the workflow is complete.

---

## Human approval gate

> ⚡ **MANDATORY** — Always runs after each `finished`. It cannot be skipped, and approval cannot be inferred from silence.

At the end of each step, present the result and request **explicit** approval:

```
Agent: I've completed [step name]. Do you approve the result?
  1. ✅ Approved — continue
  2. ✏️ Edits — tell me what to change
  3. ❌ Rejected — redo from scratch
```

- **If approved:** If the step produces files, proceed to the gap report and then to the next step. If it produces no files, proceed directly to the next step.
- **If edits are requested:** Apply the changes in place on the artifact, keep `finished` (the baseline is already captured), and re-present for approval. The gap report will capture those edits as the diff against the agent's first draft.
- **If rejected:** Report `re_started`, regenerate the artifact from scratch, report `finished` again (recapturing the baseline), and restart the gate. Repeat until approved.

> **Three domain aggregate approval gates**, which layer on top of the per-step gate:
> - **PHASE 2.3 (initial spec plan)** — approves the aggregate of PHASE 0, PHASE 1, PHASE 2, PHASE 2.1, and PHASE 2.2. On rejection of a specific section (design analysis, inventory/DAG, technical plan, minimal contracts), replay the owning phase (`re_started` → `finished` → gap report) and then re-report `re_started` → `finished` on PHASE 2.3 before re-entering this gate. Only when `checkpoints.initial_spec.status=approved` and `context.json.status=approved_for_execution` may PHASE 3.1 begin.
> - **PHASE 3.3 (DS layer checkpoint)** — approves the aggregate of PHASE 3.1 and PHASE 3.2. Rejection replays `phase-3-1-codegen-ds` or `phase-3-2-audit-ds` and then PHASE 3.3 itself. Only when `checkpoints.ds_layer.status=approved` and `context.json.status=approved_for_execution` may PHASE 3.4 begin.
> - **PHASE 3.6 (app view layer checkpoint)** — approves the aggregate of PHASE 3.4 and PHASE 3.5. Rejection replays `phase-3-4-codegen-view` or `phase-3-5-audit-view` and then PHASE 3.6 itself. Only when `checkpoints.app_view_layer.status=approved` and `context.json.status=approved_for_execution` may PHASE 4.1 begin.

> Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

> ⚡ **MANDATORY** — On rejection, example using `phase-3-4-codegen-view`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-4-codegen-view \
  --status re_started

# 2. ... regenerate the artifacts ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
APP_VIEW_FLAGS=()
while IFS= read -r f; do
  APP_VIEW_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="app_view") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-view \
  --step-id phase-3-4-codegen-view \
  --status finished \
  "${APP_VIEW_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow:
> `phase-0-spec-packet`, `phase-1-analysis-of-screen`, `phase-2-inventory-dag`, `phase-2-1-architecture-technical`, `phase-2-2-contracts-minimum` (only when executed), `phase-3-1-codegen-ds`, `phase-3-2-audit-ds`, `phase-3-4-codegen-view`, `phase-3-5-audit-view`, `phase-4-1-ds-widget-tests`, `phase-4-2-ds-golden-tests` (only when executed), `phase-4-3-ds-widgetbook`, `phase-4-4-view-widget-tests`, `phase-4-5-view-golden-tests` (only when executed), `phase-4-6-app-widgetbook`, `phase-5-delivery`.
> The seven pre-flight gates (`gate-0-canonical-configuration`, `gate-0-1-topology`, `gate-0-2-spec-packet-ownership`, `gate-0-5-ownership-repo-app`, `gate-1-architecture`, `gate-2-contracts-policy`, `gate-3-figma-mcp`) and the three human-review phases (`phase-2-3-validation-human-review`, `phase-3-3-checkpoint-ds`, `phase-3-6-checkpoint-view`) do NOT run a gap report.

> Run this immediately after the corresponding step's approval gate passes — not batched at the end of the workflow.

**Phase A — Generate the gap report:**
```bash
pragma-ai workflow gap-report \
  --instance-id "$INSTANCE_ID" \
  --step-id <step-id>
```

**Phase B — Submit the gap report interpretation:**
```bash
pragma-ai workflow gap-report \
  --instance-id "$INSTANCE_ID" \
  --step-id <step-id> \
  --submit \
  --report-id <report-id> \
  --summary "<summary of the detected gap or 'no changes'>"
```

---

## Progress reporting (instance-level)

Use at any point to check overall state:

```bash
pragma-ai workflow list --user-story-id "$USER_STORY_ID"
pragma-ai workflow status "$INSTANCE_ID"
```

---

## Summary of commands for this workflow

| Command | When |
|---|---|
| `pragma-ai workflow create --workflow-id new-view --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each executed step begins (7 gates + PHASE 0–5; `phase-2-2-contracts-minimum` only if `CONTRACTS_POLICY=generate`; `phase-4-2-ds-golden-tests` and `phase-4-5-view-golden-tests` only if `golden_tests=true`) |
| `pragma-ai workflow report ... --step-id <step> --status finished` | On completion of steps without output files: the seven gates and `phase-2-3-validation-human-review`, `phase-3-3-checkpoint-ds`, `phase-3-6-checkpoint-view` |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of file-producing phases: `phase-0-spec-packet`, `phase-1-analysis-of-screen`, `phase-2-inventory-dag`, `phase-2-1-architecture-technical`, `phase-2-2-contracts-minimum` (when executed), `phase-3-1-codegen-ds`, `phase-3-2-audit-ds`, `phase-3-4-codegen-view`, `phase-3-5-audit-view`, `phase-4-1-ds-widget-tests`, `phase-4-2-ds-golden-tests` (when executed), `phase-4-3-ds-widgetbook`, `phase-4-4-view-widget-tests`, `phase-4-5-view-golden-tests` (when executed), `phase-4-6-app-widgetbook`, `phase-5-delivery` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When a gate blocks with `blocked_input`, `phase-2-3-validation-human-review` cannot validate, an audit exhausts `pipeline.max_audit_retries` or hits an unresolvable blocker (`phase-3-2-audit-ds`, `phase-3-5-audit-view`), fidelity capture is unavailable (`phase-3-6-checkpoint-view`), tests can't pass (`phase-4-1-*`, `phase-4-2-*`, `phase-4-4-*`, `phase-4-5-*`), or delivery preconditions fail (`phase-5-delivery`) — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably at PHASE 2.3, PHASE 3.3, or PHASE 3.6 aggregate rejections) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding file-producing step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
