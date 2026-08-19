---
id: new-component
version: 1.3.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: ds-orchestrator
input_contract: ../docs/templates/spec-packets/new-component.overlay.yaml
invocation_mode: explicit_agent
description: >
  Deterministic workflow to create a new Design System component from Figma. Use when the user requests a reusable atom, molecule, or organism with spec packet validation, Figma MCP preflight, human review, code generation, tests, Widgetbook, and audit gates.
---
# Workflow: New Component from Figma

## Telemetry — Workflow metadata

| Field | Value |
|---|---|
| `workflow-id` | `new-component` |
| `user-story-id` | Value of the required `hu_id` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `topology-gate`, `app-repo-ownership-gate`, `figma-mcp-gate`, `phase-0-spec-packet`, `phase-1-design-analysis`, `phase-2-spec-inventory-dag`, `phase-2-5-architecture-technical`, `phase-2-7-validation-human-review`, `phase-3-ds-code-generation`, `phase-3-5-quality-audit`, `phase-4a-widget-tests-ds`, `phase-4b-golden-tests-ds`, `phase-4c-widgetbook-ds`, `phase-5-delivery` |

> **NON-NEGOTIABLE RULE:** Every `pragma-ai workflow ...` command in this document is **MANDATORY** to execute. The agent MUST run them — they are not suggestions or documentation.

> Each step ends with a **human approval gate** before the gap report (see *Human approval gate* at the end of this document).
> The **gap report only runs on steps that produce output files** (`--output-file`). In this workflow, the three pre-flight gates and `phase-2-7-validation-human-review` do not run a gap report.
> `phase-4b-golden-tests-ds` is conditional on `golden_tests=true`; when `false`, the step is skipped and emits no telemetry (the workflow records `skipped_by_input` in its own artifacts).
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
  --workflow-id new-component \
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

## Prerequisites

- URL for the component in Figma with `node-id`.
- User Story (user story) with acceptance criteria (inline text or
  reference to a Markdown file).
- `.sopp/config/project.config.yaml` valid.
- If missing reliable path/topology configuration, run first
  `@workspace-discovery /bootstrap-workspace`.
- Context resolved by the orchestrator:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `ACTIVE_TARGET_ID = active_target_defaults.design_system`
  - `ACTIVE_TARGET_ROOT = targets.registry[ACTIVE_TARGET_ID].root`
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`
  - `SPEC_PACKET_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/specs/{component_slug}`

## Topology Gate (required)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id topology-gate \
  --status started
```

1. `TOPOLOGY_REPO_MODE` valid (`single_repo | monorepo_melos | multi_repo`).
2. `PROJECT_ROOT` and `ACTIVE_TARGET_ROOT` accessible.
3. `ACTIVE_TARGET_ID` exists in `targets.registry` and its `kind` is
   `design_system`.
4. If `location_strategy=melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

If any validation fails, finish with `blocked_input`.

> ⚡ **MANDATORY (conditional)** — If any check fails and the step ends with `blocked_input`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id topology-gate \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id topology-gate \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, continue to the App Repo Ownership Gate. *(This step produces no output files — no gap report required.)*

## App Repo Ownership Gate (required)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id app-repo-ownership-gate \
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
  --workflow-id new-component \
  --step-id app-repo-ownership-gate \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id app-repo-ownership-gate \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, continue to the Figma MCP Gate. *(This step produces no output files — no gap report required.)*

## Figma MCP Gate (required)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id figma-mcp-gate \
  --status started
```

Before PHASE 1, `@ds-orchestrator` must delegate Figma MCP preflight to
`@figma-analyzer`. The analyzer verifies that Figma MCP is available and that
the user/agent has access to the file and `node-id`.

Minimum checklist:

1. URL parseable with `fileKey` and `nodeId`.
2. Figma MCP is configured in the active tool.
3. `get_design_context(fileKey, nodeId)` returns context for the node.
4. `get_screenshot(...)` returns a screenshot for the main node.
5. Sufficient permissions to read components, styles, variables and assets.
6. The active agent can write the packet-only Figma source archive at
   `{SPEC_PACKET_PATH}/source-assets/figma/`.
7. `get_images(...)` exports can be persisted by the active tool surface; a
   screenshot or temporary URL alone does not satisfy source-asset access.

If it fails, update `spec.yaml.external_access.figma_mcp.status=blocked_input`,
persist `evidence/figma-mcp-preflight.md` and finish with `blocked_input`.

> ⚡ **MANDATORY (conditional)** — If preflight fails (persists `evidence/figma-mcp-preflight.md` and ends with `blocked_input`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id figma-mcp-gate \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` on completion (successful preflight produces no artifact — the diagnostic file is only written on failure, and the failure branch already reported `failed`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id figma-mcp-gate \
  --status finished
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, continue to PHASE 0. *(On the success path this step produces no output files — no gap report required.)*

## User Inputs

`hu_id` is **required**: it identifies the user story this component belongs to
and is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied, the
workflow refuses to start.

```text
@ds-orchestrator /new-component
hu_id: US-12345                                              [Required]
component_name: ds_status_badge
figma_url: https://www.figma.com/file/xxx/Component?node-id=123
user_story: [Optional acceptance context]
user_story_path: [Optional Markdown path; e.g. docs/user-stories/story-123.md]
atomic_hint: [Optional atom|molecule|organism]
golden_tests: false  [Optional; default false]
evidence_mode: minimal  [Optional; default minimal]
```

## Execution Sequence

### PHASE 0 — Mobile Spec Packet (`mini`)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-0-spec-packet \
  --status started
```

**Agent**: `@ds-orchestrator`
**Skill**: `mobile-sdd-spec-validation`

Create `SPEC_PACKET_PATH` with:

1. `spec.yaml` (`schema_ref: ../docs/templates/schemas/mobile-spec.schema.yaml`,
   `spec_level: mini`, `execution_mode: propose_then_apply`)
2. `context.json`
3. `review.md` in Spanish
4. `evidence/validation-report.md`

The initial spec records inputs, acceptance criteria, Figma URL, user story,
expected success criteria (`widget_tests`, optional `goldens`, `widgetbook`,
`audit`), `external_access.figma_mcp.required=true`, permissions per agent and
sections that each agent must read. Normalize an omitted `golden_tests` input to
`false` and persist the resolved boolean in `spec.yaml.inputs` before
validation. Plan golden artifacts and golden success criteria only when it is
`true`.

Minimum packet permissions:

- `figma-analyzer`: can call `figma_mcp` and write only analysis of design
  in `spec.yaml` + evidence.
- `component-planner` and `component-architect`: cannot call Figma MCP; only
  enrich the spec and evidence.
- `widget-developer`: can create/modify files declared in
  `artifact_plan.planned[]` for `target_id=design_system`; cannot delete
  files.
- test agents: can create/modify tests and evidence for the scope.
- `code-auditor` and `delivery-manager`: verify and report; do not generate UI.

> ⚡ **MANDATORY (success path)** — Report `finished` with all four packet artifacts. Substitute `${SPEC_PACKET_PATH}` with the resolved run path:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-0-spec-packet \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/review.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/validation-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.

---

### PHASE 1 — Design Analysis

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-1-design-analysis \
  --status started
```

**Agent**: `@figma-analyzer`
**Prompt**: `figma-analysis.prompt.md`

Required output: update in `spec.yaml` only `design_source`,
`literal_texts`, `layout_constraints`, `assets` and `success_criteria.visual`.
Download every visible Figma icon, image, illustration, logo, and image-fill
source into `{SPEC_PACKET_PATH}/source-assets/figma/`, recording node id,
format, archive path and SHA-256 in `assets`. A screenshot, temporary export
URL, existing local asset, or similar icon is not a substitute.
Persist evidence in `evidence/figma-analysis.md`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated spec, the analysis evidence, and every source asset archived under `source-assets/figma/`. Expand `${FIGMA_SOURCE_ASSETS[@]}` from the paths recorded in `spec.yaml.assets[].archive_path`:

```bash
# Build --output-file flags for every archived Figma source asset
FIGMA_ASSET_FLAGS=()
while IFS= read -r asset; do
  FIGMA_ASSET_FLAGS+=(--output-file "$asset")
done < <(yq -r '.assets[].archive_path' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-1-design-analysis \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/evidence/figma-analysis.md" \
  "${FIGMA_ASSET_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.

---

### PHASE 2 — Spec + Inventory + DAG

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-spec-inventory-dag \
  --status started
```

**Agent**: `@component-planner`
**Prompt**: `atomic-inventory.prompt.md`

Update in `spec.yaml` only `canonical_spec`, `inventory`, `dag` and
`artifact_plan.planned[group=ds_components]`.

> ⚡ **MANDATORY (success path)** — Report `finished`. This phase updates `spec.yaml` in place — declare it as the output file so the gap report can diff this phase's contribution:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-spec-inventory-dag \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.5.

---

### PHASE 2.5 — Architecture Technical

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-5-architecture-technical \
  --status started
```

**Agent**: `@component-architect`

Update in `spec.yaml` only `technical_plan`, `artifact_plan`,
`contracts.text_overflow`, `success_criteria` and `handoffs`.

> ⚡ **MANDATORY (success path)** — Report `finished`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-5-architecture-technical \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.7.

---

### PHASE 2.7 — Validation + Human Review

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-7-validation-human-review \
  --status started
```

**Skill**: `mobile-sdd-spec-validation`

Validate `spec.yaml` and present `review.md`.

Present to the developer:
1. visual analysis, literal text, and the Figma source archive for every visible asset.
2. inventory, DAG and planned artifacts.
3. technical plan.
4. success criteria from `review.md`.

Wait for explicit approval to continue.
If the human requests adjustments, update only `spec.yaml`, `review.md` and the
affected sections. Do not generate code until `context.json` marks the spec
as approved.

> ⚡ **MANDATORY (conditional)** — If the spec fails schema/business validation and cannot continue:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-7-validation-human-review \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` once validation passes and the human review is presented (approval itself happens in the gate that follows):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-2-7-validation-human-review \
  --status finished
```

> **Stop here.** This is the **domain aggregate approval gate** for the whole planning set (PHASE 0 through PHASE 2.5). If the human requests changes to `design_source`, `literal_texts`, `assets`, `inventory`, `dag`, `technical_plan`, or `artifact_plan`, the flow must return to the phase that owns that section: report `re_started` on the affected earlier phase, apply changes, report `finished` again for that phase, re-run its gap report, and re-enter PHASE 2.7 (which itself gets `re_started` → `finished` again). Only when `context.json` marks the spec as approved may PHASE 3 begin. *(PHASE 2.7 produces no new output files — no gap report required.)*

---

### PHASE 3 — DS Code Generation

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-ds-code-generation \
  --status started
```

**Agent**: `@widget-developer`
**Prompts**: `codegen-atom.prompt.md`, `codegen-molecule.prompt.md`, `codegen-organism.prompt.md`

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
  - success_criteria
```

Output: files `.dart` bajo
`targets.registry[artifact_plan.planned[].target_id].root`.

> ⚡ **MANDATORY (success path)** — Report `finished` with one `--output-file` per `.dart` file declared in `artifact_plan.planned[group=ds_components]`. Paths must be relative to `--project-dir` (project root). Expand the array from the spec:

```bash
# Build --output-file flags from the artifact plan
DS_FILE_FLAGS=()
while IFS= read -r f; do
  DS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_components") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-ds-code-generation \
  --status finished \
  "${DS_FILE_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 3.5.

---

### PHASE 3.5 — Quality Audit

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-5-quality-audit \
  --status started
```

**Agent**: `@code-auditor`

Loop with `@widget-developer` up to `pipeline.max_audit_retries`.

Required output: `evidence/audit-report.md` and a summary in the human report.
The audit must block a missing Figma source archive, a checksum mismatch for a
runtime asset, an undeclared DS exact-icon mapping, or a substituted font.

> ⚡ **MANDATORY (conditional)** — If the audit loop exceeds `pipeline.max_audit_retries` without passing, or hits an audit-blocker (missing archive, checksum mismatch, undeclared DS icon mapping, substituted font) that cannot be resolved:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-5-quality-audit \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the audit evidence:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-5-quality-audit \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/audit-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4a.

---

### PHASE 4a — Widget Tests DS

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-4a-widget-tests-ds \
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
  - literal_texts
  - contracts.text_overflow
  - success_criteria
```

> ⚡ **MANDATORY (conditional)** — Widget tests are required. If they cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-4a-widget-tests-ds \
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
  --workflow-id new-component \
  --step-id phase-4a-widget-tests-ds \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/widget-tests.md" \
  "${DS_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4b (only when `golden_tests=true`) or directly to PHASE 4c.

---

### PHASE 4b — Golden Tests DS (conditional)

> ⚡ **MANDATORY only when `golden_tests=true`.** When `golden_tests=false`, skip this phase entirely — do not emit `started`/`finished` for it. The workflow's own `skipped_by_input` record in `context.json`, `spec.yaml` and `PIPELINE_LOG_PATH` covers the skip.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-4b-golden-tests-ds \
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

When `golden_tests=false`, do not invoke `@golden-test-engineer` or create
golden artifacts. Record `golden_tests: skipped_by_input` with
`reason: golden_tests=false` in `context.json`, `spec.yaml` and
`PIPELINE_LOG_PATH`.

> ⚡ **MANDATORY (conditional)** — If golden tests were requested but cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-4b-golden-tests-ds \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed with a failing golden outcome when `golden_tests=true`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated golden test files and the golden-tests evidence:

```bash
DS_GOLDEN_FLAGS=()
while IFS= read -r f; do
  DS_GOLDEN_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_golden_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-4b-golden-tests-ds \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/golden-tests.md" \
  "${DS_GOLDEN_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4c.

---

### PHASE 4c — Widgetbook DS

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-4c-widgetbook-ds \
  --status started
```

**Agent**: `@widgetbook-developer`
**Prompt**: `test-generation.prompt.md` (`MODE=DS_WIDGETBOOK`)
Required compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: ds_widgetbook
read_sections:
  - artifact_plan.planned[group=ds_components]
  - technical_plan
  - literal_texts
  - contracts.text_overflow
  - success_criteria
```

> ⚡ **MANDATORY (success path)** — Report `finished` with the Widgetbook use-case files. Expand the file array from `artifact_plan.planned[group=ds_widgetbook]`:

```bash
DS_WIDGETBOOK_FLAGS=()
while IFS= read -r f; do
  DS_WIDGETBOOK_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_widgetbook") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-4c-widgetbook-ds \
  --status finished \
  "${DS_WIDGETBOOK_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 5.

---

### PHASE 5 — Delivery

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-5-delivery \
  --status started
```

**Agent**: `@delivery-manager`
**Prompt**: `delivery-review.prompt.md`

Required output: `evidence/delivery-report.md` and a summary in the human report.

Delivery requires passing `evidence/widget-tests.md` and exactly one golden
outcome: passing `evidence/golden-tests.md` when `golden_tests=true`, or the
recorded `golden_tests: skipped_by_input` outcome when false.

> ⚡ **MANDATORY (conditional)** — If delivery preconditions are not met (missing/failing `evidence/widget-tests.md`, or an inconsistent golden outcome):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-5-delivery \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the delivery report:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-5-delivery \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/delivery-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** — the workflow is complete.

## Rules

- Do not generate code before approving `review.md`.
- `spec.yaml` is the machine source; `PIPELINE_SPEC_PATH` remains a readable
  cumulative report.
- Handoffs by reference; do not copy full human reports between agents.
- Do not generate artifacts outside the resolved root for
  `artifact_plan.planned[].target_id`.
- Widget tests are required. Golden tests are conditional and must be recorded
  as executed or `skipped_by_input`.
- Record each phase in `PIPELINE_LOG_PATH`.
- If a phase does not apply, use `skipped` with an explicit reason.

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

> **PHASE 2.7 aggregate rejection.** When PHASE 2.7 hosts the plan-approval decision, a rejection of a specific planning section (design analysis, inventory/DAG, technical plan) must first replay the phase that owns that section: report `re_started` on the affected earlier phase (PHASE 1, PHASE 2, or PHASE 2.5), regenerate its output, report `finished` again with the same `--output-file` set, re-run that phase's gap report, and then report `re_started` → `finished` on PHASE 2.7 itself before re-entering this gate. Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`.

> ⚡ **MANDATORY** — On rejection, example using `phase-3-ds-code-generation`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-ds-code-generation \
  --status re_started

# 2. ... regenerate the artifacts ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
DS_FILE_FLAGS=()
while IFS= read -r f; do
  DS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="ds_components") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-component \
  --step-id phase-3-ds-code-generation \
  --status finished \
  "${DS_FILE_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow:
> `phase-0-spec-packet`, `phase-1-design-analysis`, `phase-2-spec-inventory-dag`, `phase-2-5-architecture-technical`, `phase-3-ds-code-generation`, `phase-3-5-quality-audit`, `phase-4a-widget-tests-ds`, `phase-4b-golden-tests-ds` (only when executed), `phase-4c-widgetbook-ds`, `phase-5-delivery`.
> The three pre-flight gates (`topology-gate`, `app-repo-ownership-gate`, `figma-mcp-gate`) and `phase-2-7-validation-human-review` do NOT run a gap report.

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
| `pragma-ai workflow create --workflow-id new-component --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each step begins (gates, PHASE 0–5; PHASE 4b only if `golden_tests=true`) |
| `pragma-ai workflow report ... --step-id <step> --status finished` | On completion of `topology-gate`, `app-repo-ownership-gate`, `figma-mcp-gate`, `phase-2-7-validation-human-review` (no `--output-file`) |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of file-producing phases: `phase-0-spec-packet`, `phase-1-design-analysis`, `phase-2-spec-inventory-dag`, `phase-2-5-architecture-technical`, `phase-3-ds-code-generation`, `phase-3-5-quality-audit`, `phase-4a-widget-tests-ds`, `phase-4b-golden-tests-ds` (when executed), `phase-4c-widgetbook-ds`, `phase-5-delivery` |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When a gate blocks (`topology-gate`, `app-repo-ownership-gate`, `figma-mcp-gate`), validation fails (`phase-2-7-validation-human-review`), the audit loop exhausts retries (`phase-3-5-quality-audit`), tests can't pass (`phase-4a-widget-tests-ds`, `phase-4b-golden-tests-ds`), or delivery preconditions fail (`phase-5-delivery`) — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably PHASE 2.7 aggregate rejection) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding file-producing step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
