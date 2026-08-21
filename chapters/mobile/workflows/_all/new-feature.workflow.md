---
id: new-feature
version: 1.1.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: feature-builder
input_contract: ../docs/templates/spec-packets/new-feature.overlay.yaml
invocation_mode: explicit_agent
description: >
  Workflow for building a complete Clean Architecture feature with domain, data, and presentation layers. Use when the user requests a new feature, module, flow, or Melos feature package, optionally coordinating missing DS components.
---
# Workflow: New Feature (Full Clean Architecture)

## Telemetry — Workflow metadata

| Field | Value |
|---|---|
| `workflow-id` | `new-feature` |
| `user-story-id` | Value of the required `hu_id` invocation input (e.g. `US-12345`, `HU-678`) |
| Step IDs | `phase-0-spec-packet`, `phase-0-1-figma-fidelity-planning`, `phase-0-2-ui-component-inventory`, `phase-1-scaffold`, `phase-1-1-api-contract-analysis`, `phase-2-domain-layer`, `phase-3-data-layer`, `phase-4-presentation-layer`, `phase-5-wiring`, `phase-6-1-unit-tests`, `phase-6-2-widget-tests`, `phase-6-3-integration-tests`, `phase-6-4-golden-tests`, `phase-7-audit`, `checkpoint-final-build-review`, `phase-8-documentation`, `phase-9-delivery` |

> **NON-NEGOTIABLE RULE:** Every `pragma-ai workflow ...` command in this document is **MANDATORY** to execute. The agent MUST run them — they are not suggestions or documentation.

> ⛔ **STEP-ID INTEGRITY (NON-NEGOTIABLE):** The `--step-id` and `--workflow-id` values shown in every command block below are the **ONLY** valid identifiers for this workflow. The agent MUST copy them **verbatim** from this document — never invent, abbreviate, translate, paraphrase, pluralize, capitalize differently, or otherwise modify them.
>
> - Every `--step-id` submitted to `pragma-ai workflow report` or `pragma-ai workflow gap-report` MUST match one entry in the **"Step IDs"** list above, character-for-character (kebab-case, lowercase, exact spelling).
> - Every `--workflow-id` MUST be exactly `new-feature`.
> - If a step-id you need is not in the list, STOP and ask the user — do not fabricate one.
> - The CLI rejects unknown step-ids; a wrong id silently corrupts the run's telemetry.

> Each step ends with a **human approval gate** before the gap report (see *Human approval gate* at the end of this document). The workflow keeps its domain-specific layer checkpoints (`sopp_gate.rb` Executable Phase Gate for PHASE 2 / 3 / 4) and the final `HUMAN CHECKPOINT — Final Build Review` on top of the generic per-step gate.
> **Pre-flight Gates are excluded from telemetry.** The topology gate runs before the workflow instance is minted and stops the run with `blocked_input` when it fails (no telemetry emitted).
> The **gap report only runs on steps that produce output files** (`--output-file`). `checkpoint-final-build-review` does NOT run a gap report.
> Five phases are conditional and emit telemetry only when executed: `phase-0-1-figma-fidelity-planning` (requires `figma_url` + `figma_scope=view`), `phase-0-2-ui-component-inventory` (requires `figma_url` or `ui_components`), `phase-1-1-api-contract-analysis` (requires `api_contract`), `phase-6-4-golden-tests` (requires `golden_tests=true`), `phase-8-documentation` (requires `documentation=true`).
> Commands assume the shell's cwd is already the project root — no `cd` prefix is needed, and `--project-dir` only matters when running from elsewhere.

---

## Setup — Mint the workflow instance

> ⚡ **MANDATORY** — Always run this at the start, before any step.

### Resolve user-story-id (mandatory)

`hu_id` is a **required** invocation input for this workflow (see *Inputs*), so the agent already has the user story identifier at the start. The agent MUST map it to `user-story-id` before running `workflow create`:

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
  --workflow-id new-feature \
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

## When to Use

Use this workflow when:

- The user asks to "create a feature", "implement the product catalog", "build the checkout flow"
- The feature requires domain logic (entities, use cases, repositories)
- The feature connects to a REST API or local database
- The feature needs a BLoC with state management
- The feature may need new DS components (detected in Phase 0.2)

Do NOT use for:
- DS component only (use `/new-component`)
- View/screen without backend logic (use `/new-view`)
- Refactoring existing code (use `/refactor-component`)

---

## Prerequisites

- Feature name and description provided by the user
- API contract **or** manual entity_name + fields provided:
  - If `api_contract` is given → `entity_name` is inferred from the schema (the primary schema referenced by the endpoints, or the user can hint which schema to use)
  - Without an `api_contract` → `entity_name` and `fields` are required
- `.sopp/config/project.config.yaml` valid (or run `/bootstrap-workspace` first)
- Context resolved:
  - `PROJECT_ROOT`
  - `TARGET_REGISTRY`
  - `ACTIVE_TARGET_ID` (`app` or the feature target specified by the input)
  - `ACTIVE_TARGET_ROOT = targets.registry[ACTIVE_TARGET_ID].root`
  - `ALLOWED_ARTIFACT_ROOTS = targets.registry.*.root`
  - `TOPOLOGY_REPO_MODE`
  - `PIPELINE_SPEC_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/{pipeline.spec_file}`
  - `PIPELINE_LOG_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/{pipeline.log_file}`
  - `SPEC_PACKET_PATH = {ACTIVE_TARGET_ROOT}/{pipeline.output_dir}/specs/{feature_name}`

---

## Gate — Topology (mandatory)

1. Validate `TOPOLOGY_REPO_MODE` (`single_repo | monorepo_melos | multi_repo`).
2. Validate `PROJECT_ROOT` and `ACTIVE_TARGET_ROOT` are accessible.
3. Validate `ACTIVE_TARGET_ID` exists in `targets.registry`.
4. If `location_strategy = melos_package`, resolve `repo_root` and
   `package_path` with `docs/scripts/melos_workspace.rb`; require `ok=true`.

If any validation fails, terminate with `blocked_input`.

> ℹ️ **The Topology gate is not tracked by telemetry.** It is pure domain validation and runs before the workflow instance is minted (or before its first tracked phase, at the agent's discretion). Its success is a precondition for PHASE 0; its failure with `blocked_input` stops the run entirely — no `pragma-ai workflow report` calls are emitted for it.

---

## Inputs

`hu_id` is **required**: it identifies the user story this feature belongs to
and is mapped 1:1 to `user-story-id` for telemetry. If it is not supplied, the
workflow refuses to start.

```text
@feature-builder /new-feature
hu_id: US-12345                                              [Required]
feature_name: product_catalog
description: Browse and search products by category with detail view
api_contract: <see below — accepts any format>
user_story: docs/hus/user story-045.md  (optional — contains acceptance criteria + DoD)
figma_url: https://www.figma.com/file/xxx/ProductList?node-id=123  (optional)
figma_scope: view | component_inventory  (optional; default view when figma_url is supplied)
target_location: app_folder | melos_package
sequence_diagram: docs/diagrams/product_catalog_flow.mmd  (optional)
golden_tests: false  (optional; default false)
documentation: false  (optional; default false)
evidence_mode: minimal  (optional; default minimal)
```

### `api_contract` — Single field, any format

The `api_contract` field accepts whatever the developer has available.
The agent auto-detects the format and extracts entities, endpoints, and schemas.

| What you have | What to put in `api_contract` |
|---|---|
| OpenAPI/Swagger file | `docs/api/openapi.yaml` or `https://api.example.com/docs/openapi.json` |
| GraphQL schema | `docs/api/schema.graphql` |
| Postman collection | `docs/api/collection.json` |
| Protobuf | `protos/product_service.proto` |
| JSON example response | `docs/api/product_response.json` |
| Markdown spec | `docs/api/product-api.md` |
| Inline cURL + response | Paste directly (see example below) |
| Manual endpoints + fields | Write them directly (see example below) |

**Examples:**

```text
# File path
api_contract: docs/api/openapi.yaml

# URL
api_contract: https://api.example.com/docs/openapi.json

# Inline JSON response (fastest)
api_contract: |
  GET /products
  Response:
  {
    "data": [{"product_id": "1", "name": "Widget", "price": 9.99, "category_id": "c1"}],
    "meta": {"page": 1, "total": 100, "has_more": true}
  }

  GET /products/:id
  Response:
  {"product_id": "1", "name": "Widget", "price": 9.99, "category_id": "c1", "image_url": "https://..."}

# Inline cURL
api_contract: |
  curl -X GET https://api.example.com/v1/products -H "Authorization: Bearer {token}"
  Response: {"data": [{"product_id": "1", "name": "Widget", "price": 9.99}], "meta": {"has_more": true}}

  curl -X GET https://api.example.com/v1/products/{id}
  Response: {"product_id": "1", "name": "Widget", "price": 9.99, "category_id": "c1"}

# Manual (simplest fallback — no file needed)
api_contract: |
  GET /products -> List<Product>
  GET /products/:id -> Product
  POST /products (body: CreateProductRequest) -> Product

  Product:
    id: String
    name: String
    price: double
    categoryId: String
    isAvailable: bool
    imageUrl: String?

  CreateProductRequest:
    name: String
    price: double
    categoryId: String
```

---

## Execution Sequence

### PHASE 0 — Mobile Spec Packet (`full`)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-0-spec-packet \
  --status started
```

**Agent:** `@feature-builder`
**Skill:** `mobile-sdd-spec-validation`

Create `SPEC_PACKET_PATH` with:

1. `spec.yaml` (`schema_ref: ../docs/templates/schemas/mobile-spec.schema.yaml`,
   `spec_level: full`, `execution_mode: propose_then_apply`)
2. `context.json`
3. `review.md` in Spanish
4. `evidence/validation-report.md`

The agent drafts the spec from `feature_name`, description, API contract,
optional user story, Figma URL and sequence diagram. The developer reviews `review.md`
instead of writing YAML manually.

Normalize omitted `golden_tests` and `documentation` inputs to `false` and
persist both resolved booleans in `spec.yaml.inputs` before validation. An
omitted option must never be interpreted as an unrecorded skip later.
When `figma_url` is supplied, normalize an omitted `figma_scope` to `view`.
Use `component_inventory` only when the Figma link is intentionally not a
screen the feature will implement.

The full spec must include:

- requirements and success criteria
- API/entity/domain analysis inputs
- layer plan: domain, data, presentation, wiring and mandatory tests
- expected artifacts per layer
- mandatory artifacts under `artifact_plan.planned[group=unit_tests]`,
  `artifact_plan.planned[group=widget_tests]` and
  `artifact_plan.planned[group=integration_tests]`
- success criteria with evidence for each mandatory test stage
- golden artifacts under `artifact_plan.planned[group=golden_tests]` only when
  `golden_tests=true`; otherwise record `skipped_by_input`
- documentation artifacts under `artifact_plan.planned[group=docs]` using
  `target_id=project_docs` or the configured docs target only when
  `documentation=true`; otherwise record `skipped_by_input`
- required layer checkpoints
- `stage_checkpoints: required`
- `agent_permissions` for feature, DS, audit, test and delivery agents; include
  `golden-test-engineer` only when `golden_tests=true`
- `external_access.figma_mcp.required=true` only when `figma_url` is provided
  and `agent_permissions.figma-analyzer.can_call_external_tools` includes
  `figma_mcp`
- `visual_manifest`, `layout_manifest`, a Figma fidelity report artifact, and
  presentation/widget-test criteria when `figma_scope=view`
- commands and evidence expected
- `execution_capabilities.subagent_delegation` and
  `fallback_policy=delegate_or_controller_executes`

When `figma_scope=view`, execute PHASE 0.1 before validating the initial
review. Validate the completed spec and wait for explicit approval before
scaffold or code generation.

> ⚡ **MANDATORY (success path)** — Report `finished` with all four packet artifacts. Substitute `${SPEC_PACKET_PATH}` with the resolved run path:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-0-spec-packet \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  --output-file "${SPEC_PACKET_PATH}/review.md" \
  --output-file "${SPEC_PACKET_PATH}/evidence/validation-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 0.1 (only when `figma_url` + `figma_scope=view`), PHASE 0.2 (only when `figma_url` or `ui_components`), or directly to PHASE 1.

---

### PHASE 0.1 — Shared Figma UI Fidelity Planning (conditional)

> ⚡ **MANDATORY only when `figma_url` is supplied AND `figma_scope=view`.** When the condition does not hold, skip this phase entirely — do not emit `started`/`finished` for it.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-0-1-figma-fidelity-planning \
  --status started
```

**Condition:** `figma_url` is supplied and `figma_scope=view`.
**Preferred specialist role:** `@figma-analyzer`.
**Execution owner:** `@feature-builder` when native delegation is unavailable
and the packet grants Figma MCP plus packet-write permissions.

Before the initial review, execute the same Figma analysis contract as
`/new-view`: capture metadata hierarchy, design context, variables, screenshot,
assets, `visual_manifest`, and `layout_manifest`. The plan must resolve every
visible node's parent-child order, bounds, layout, corner radii, border width,
literal text and fixed tolerances (`1 dp`, `2%` global, `4%` regional). Missing
or unresolved geometry blocks with `FIGMA_LAYOUT_MANIFEST_INCOMPLETE`.

> ⚡ **MANDATORY (conditional)** — If Figma geometry cannot be resolved and the phase ends with `FIGMA_LAYOUT_MANIFEST_INCOMPLETE`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-0-1-figma-fidelity-planning \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated spec and every source asset archived under `source-assets/figma/`. Expand `${FIGMA_ASSET_FLAGS[@]}` from `spec.yaml.assets[].archive_path`:

```bash
FIGMA_ASSET_FLAGS=()
while IFS= read -r asset; do
  FIGMA_ASSET_FLAGS+=(--output-file "$asset")
done < <(yq -r '.assets[].archive_path' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-0-1-figma-fidelity-planning \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  "${FIGMA_ASSET_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 0.2 (only when `figma_url` or `ui_components`) or directly to PHASE 1.

---

---

### PHASE 0.2 — UI Component Inventory (conditional)

> ⚡ **MANDATORY only when `figma_url` OR `ui_components` is provided.** When neither is supplied, skip this phase entirely — do not emit `started`/`finished` for it.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-0-2-ui-component-inventory \
  --status started
```

**Condition:** `figma_url` or `ui_components` is provided.
**Agent:** `@feature-builder`

Steps:
1. If `figma_url` is provided, reuse PHASE 0.1 analysis when
   `figma_scope=view`; do not re-query or reinterpret Figma. For
   `component_inventory`, `@feature-builder` prefers Figma MCP preflight
   and screen analysis through `@figma-analyzer`. When native subagent
   delegation is unavailable, it executes the `figma-analyzer` role contract
   itself only if the packet grants `figma_mcp`; otherwise it blocks:
   - parse `fileKey` and `nodeId`
   - verify Figma MCP is configured in the active tool
   - verify `get_design_context(fileKey, nodeId)` succeeds
   - verify a screenshot can be obtained for the target node
   - download every visible Figma icon, image, illustration, logo, and
     image-fill source into `{SPEC_PACKET_PATH}/source-assets/figma/`, with
     node id, format and SHA-256 recorded in `spec.yaml.assets`
   - persist `evidence/figma-mcp-preflight.md`
   - if any required check or source download fails, set
     `spec.yaml.external_access.figma_mcp.status=blocked_input` and stop
2. Identify required DS components from Figma or description
3. Search the repository for each component
4. Classify: ✅ exists | ⚠️ partial | 🆕 missing
5. For each 🆕 or ⚠️ component:
   - Delegate to `@ds-orchestrator /new-component` or `/refactor-component`
   - Wait for DS pipeline completion
6. If DS pipeline returns `blocked_input`, present options to user

Output: `evidence/ui-component-inventory.md`.
Update `spec.yaml` sections `ui_inventory`, `artifact_plan.planned[group=ds_components]` and
`dependencies.ds_pipeline`.

**Skip condition:** No `figma_url` and no `ui_components` provided.

> ⚡ **MANDATORY (conditional)** — If Figma MCP preflight fails (sets `spec.yaml.external_access.figma_mcp.status=blocked_input`) or a delegated DS pipeline returns `blocked_input` that cannot be resolved:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-0-2-ui-component-inventory \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the inventory evidence, the updated spec, and (when Figma preflight ran) the preflight evidence plus any archived source assets. Expand `${FIGMA_ASSET_FLAGS[@]}` and `${FIGMA_PREFLIGHT_FLAGS[@]}` only when `figma_url` was supplied:

```bash
# Only when Figma preflight ran
FIGMA_ASSET_FLAGS=()
FIGMA_PREFLIGHT_FLAGS=()
if [ -n "$figma_url" ]; then
  while IFS= read -r asset; do
    FIGMA_ASSET_FLAGS+=(--output-file "$asset")
  done < <(yq -r '.assets[].archive_path' "${SPEC_PACKET_PATH}/spec.yaml")
  FIGMA_PREFLIGHT_FLAGS+=(--output-file "${SPEC_PACKET_PATH}/evidence/figma-mcp-preflight.md")
fi

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-0-2-ui-component-inventory \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/ui-component-inventory.md" \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  "${FIGMA_PREFLIGHT_FLAGS[@]}" \
  "${FIGMA_ASSET_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.

---

### PHASE 1 — Scaffold

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-1-scaffold \
  --status started
```

**Agent:** `@feature-builder`
Mandatory compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: scaffold
read_sections:
  - topology
  - artifact_plan.planned[group=scaffold]
  - technical_plan.layers
  - architecture_contract_refs
```

Steps:
1. Determine target location (app folder vs Melos package)
2. If Melos package:
   - Create `pubspec.yaml` with `resolution: workspace`
   - Create barrel export `lib/{package_name}.dart`
   - Update root `pubspec.yaml` workspace list
   - Run `dart pub get`
3. Create all directories per the architecture map

Output: Directory structure created, registered in `PIPELINE_LOG_PATH`.
Persist scaffold evidence under `SPEC_PACKET_PATH/evidence/`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the updated spec and every file declared in `artifact_plan.planned[group=scaffold]` (pubspec.yaml, barrel exports, workspace registrations, etc.):

```bash
SCAFFOLD_FLAGS=()
while IFS= read -r f; do
  SCAFFOLD_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="scaffold") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-1-scaffold \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml" \
  "${SCAFFOLD_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 1.1 (only when `api_contract` is provided) or directly to PHASE 2.

---

### PHASE 1.1 — API Contract Analysis (conditional)

> ⚡ **MANDATORY only when `api_contract` is provided** (file, URL, or inline cURL). When it is not supplied, skip this phase entirely — do not emit `started`/`finished` for it.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-1-1-api-contract-analysis \
  --status started
```

**Condition:** `api_contract` is provided (file, URL, or inline cURL in the prompt).
**Agent:** `@feature-builder`

Steps:
1. Detect format (OpenAPI, GraphQL, Postman, Protobuf, JSON example, Markdown, cURL)
2. Read and parse the contract
3. Locate schemas and paths relevant to `entity_name`
4. Extract:
   - Endpoints with methods, path params, query params
   - Request/response schemas (field names, types, required/optional, nullability)
   - Pagination pattern (offset/limit, cursor, page/pageSize)
   - Error response structure (status codes, error body)
   - Enum definitions → Dart enums
   - Nested object schemas → separate DTOs
5. Produce an internal **API Analysis** that feeds Phase 2 and Phase 3:
   - Domain model fields (from response schema, cleaned of API naming)
   - DTO fields (exact API field names with `@JsonKey` mappings)
   - Data source method signatures (one per endpoint)
   - Use case list (inferred from endpoints: GET list → GetAll, GET by id → GetById, POST → Create, etc.)

Output: `evidence/api-contract-analysis.md`.
Update `spec.yaml` sections `contracts.api`, `domain_model_plan`,
`data_model_plan` and `use_case_plan`.

**Skip condition:** No `api_contract` provided and no inline cURL — use `fields` and `api_endpoints` directly.

> ⚡ **MANDATORY (success path)** — Report `finished` with the analysis evidence and the updated spec:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-1-1-api-contract-analysis \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/api-contract-analysis.md" \
  --output-file "${SPEC_PACKET_PATH}/spec.yaml"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 2.

---

### PHASE 2 — Domain Layer

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-2-domain-layer \
  --status started
```

#### Executable Phase Gate (mandatory)

Before presenting the initial review, run `docs/scripts/sopp_gate.rb open-initial`,
show its spec hash and approval challenge, and end the response. Before every
code-producing phase, run `docs/scripts/sopp_gate.rb can-enter` for the
target phase. After Domain, Data or Presentation generation and evidence, run
`open-checkpoint` and end the response. The controller must never write an
approval state directly or infer approval from the initial plan approval.

If the human requests changes, remain in the current layer:

1. Record the verbatim request with `request-changes`.
2. Write a bounded proposal at
   `revisions/<layer>/<revision>/proposal.md`, including files, criteria and
   earliest affected layer.
3. Run `propose-adjustment` and stop for a later human authorization.
4. After `authorize-adjustment`, apply only the proposed scope, regenerate
   evidence and run `open-checkpoint` again.
5. Require a fresh approval of the new artifact hash. Revision authorization
   is never layer approval.

If a revision affects an earlier layer, invalidate that layer and every
dependent checkpoint as `stale`, then resume from the earliest affected layer.
Questions or ambiguous feedback do not change state. A missing executable gate,
evidence file, schema target, approval record or matching hash is blocking.

**Agent:** `@feature-builder`
Mandatory compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: domain_layer
read_sections:
  - requirements
  - domain_model_plan
  - use_case_plan
  - success_criteria.domain
```

Generate:
1. Domain model (`@freezed abstract class`, no JSON, with business logic getters)
2. Repository interface (`abstract interface class`, `Either<Failure, T>` returns)
3. Use case(s) (`@injectable`, implements `UseCase<T, Params>`)

Output: `context.json.artifacts.domain` and `evidence/domain-checkpoint.md`.

#### REQUIRED CHECKPOINT — Domain Layer

Present a compact Spanish review:

1. files created/modified
2. entities/use cases/repositories produced
3. criteria covered
4. self-verification result

Wait for explicit approval before PHASE 3.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated domain files, the domain checkpoint evidence, and the updated context. Expand the array from `artifact_plan.planned[group=domain]`:

```bash
DOMAIN_FILE_FLAGS=()
while IFS= read -r f; do
  DOMAIN_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="domain") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-2-domain-layer \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/domain-checkpoint.md" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${DOMAIN_FILE_FLAGS[@]}"
```

> **Stop here.** This step is gated by the **Executable Phase Gate + REQUIRED CHECKPOINT — Domain Layer** (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 3.

---

### PHASE 3 — Data Layer

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-3-data-layer \
  --status started
```

**Agent:** `@feature-builder`
Mandatory compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: data_layer
read_sections:
  - contracts.api
  - data_model_plan
  - artifact_plan.planned[group=data]
  - success_criteria.data
```

Generate:
1. DTO (`@freezed abstract class` + `fromJson`, `@JsonKey` for API field names)
2. Mapper (`abstract final class` with `fromModel` / `toModel`)
3. Remote data source (interface + `@LazySingleton` implementation)
4. Local data source (interface only — implementation noted as optional)
5. Repository implementation (`@LazySingleton(as:)`, cache-first, error mapping)

Output: `context.json.artifacts.data` and `evidence/data-checkpoint.md`.

#### REQUIRED CHECKPOINT — Data Layer

Present a compact Spanish review:

1. DTOs, mappers, data sources and repository implementation
2. API mappings and error handling
3. criteria covered
4. self-verification result

Wait for explicit approval before PHASE 4.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated data files, the data checkpoint evidence, and the updated context. Expand the array from `artifact_plan.planned[group=data]`:

```bash
DATA_FILE_FLAGS=()
while IFS= read -r f; do
  DATA_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="data") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-3-data-layer \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/data-checkpoint.md" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${DATA_FILE_FLAGS[@]}"
```

> **Stop here.** This step is gated by the **Executable Phase Gate + REQUIRED CHECKPOINT — Data Layer** (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 4.

---

### PHASE 4 — Presentation Layer

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-4-presentation-layer \
  --status started
```

**Agent:** `@feature-builder`
Mandatory compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: presentation_layer
read_sections:
  - requirements
  - artifact_plan.planned[group=presentation]
  - navigation
  - literal_texts
  - visual_manifest
  - layout_manifest
  - success_criteria.presentation
```

Generate:
1. Event (`@freezed sealed class`, one factory per user action)
2. State (`@freezed sealed class`: initial, loading, success, error)
3. BLoC (`@injectable`, explicit `transformer:` on every `on<>`, `result.match()`)
4. UIModel (`@freezed abstract class` + `fromDomain` factory)
5. Page (`BlocProvider` + `getIt<Bloc>()` + `BlocBuilder` with exhaustive switch)
6. When `figma_scope=view`, apply the shared `codegen-view` fidelity contract:
   exact literal text, hierarchy/order, geometry, four-corner radii, borders,
   assets, and capture plan at `layout_manifest.viewport`.

Output: `context.json.artifacts.presentation` and
`evidence/presentation-checkpoint.md`.

When `figma_scope=view`, run the shared app-view audit before the Presentation
checkpoint. Persist `evidence/figma-fidelity-report.json`; it must pass `1 dp`
geometry, `2%` global pixel difference, and `4%` regional pixel difference.
Otherwise stop with `FIGMA_FIDELITY_TOLERANCE_EXCEEDED`.

#### REQUIRED CHECKPOINT — Presentation Layer

Present a compact Spanish review:

1. events/states/BLoC/UIModel/page
2. state coverage and navigation status
3. Figma fidelity report and any blocked visual criteria when applicable
4. criteria covered
5. self-verification result

Wait for explicit approval before PHASE 5.

> ⚡ **MANDATORY (conditional)** — When `figma_scope=view`, if the fidelity report exceeds tolerances and the phase stops with `FIGMA_FIDELITY_TOLERANCE_EXCEEDED`:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-4-presentation-layer \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated presentation files, the presentation checkpoint evidence, the updated context, and (when `figma_scope=view`) the Figma fidelity report. Expand the array from `artifact_plan.planned[group=presentation]`:

```bash
PRESENTATION_FILE_FLAGS=()
while IFS= read -r f; do
  PRESENTATION_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="presentation") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

# Only when figma_scope=view
FIDELITY_FLAGS=()
if [ "$figma_scope" = "view" ]; then
  FIDELITY_FLAGS+=(--output-file "${SPEC_PACKET_PATH}/evidence/figma-fidelity-report.json")
fi

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-4-presentation-layer \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/presentation-checkpoint.md" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${PRESENTATION_FILE_FLAGS[@]}" \
  "${FIDELITY_FLAGS[@]}"
```

> **Stop here.** This step is gated by the **Executable Phase Gate + REQUIRED CHECKPOINT — Presentation Layer** (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 5.

---

### PHASE 5 — Wiring

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-5-wiring \
  --status started
```

**Agent:** `@feature-builder`

Steps:
1. Run `dart run build_runner build --delete-conflicting-outputs`
   - Monorepo: `melos exec --scope={package} -- "dart run build_runner build --delete-conflicting-outputs"`
2. Verify DI registration: `grep "{Entity}Repository\|{Feature}Bloc" injection.config.dart`
3. Register route in GoRouter (if router file is accessible)
   - If not accessible, note as manual step
4. If Melos package: register `ExternalModule` in app's injection container

Output: `evidence/wiring-validation.md`.
Persist build_runner, DI and route evidence under `SPEC_PACKET_PATH/evidence/`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the wiring evidence:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-5-wiring \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/wiring-validation.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 6.1.

---

### PHASE 6.1 — Unit Tests (required)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-1-unit-tests \
  --status started
```

**Preferred specialist role:** `@test-engineer`
**Mode:** `FEATURE_UNIT_TESTS`

**Execution owner:** `@feature-builder`. Delegate only when
`execution_capabilities.subagent_delegation=available`; otherwise the controller
executes the `test-engineer` contract and writes the same planned artifacts and
evidence.

Mandatory compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: feature_unit_tests
read_sections:
  - artifact_plan.planned[group=domain]
  - artifact_plan.planned[group=data]
  - artifact_plan.planned[group=unit_tests]
  - contracts
  - success_criteria
```

Generate and run unit tests for domain models, use cases, repositories, mappers,
data sources and BLoC behavior where applicable. Persist
`evidence/unit-tests.md`, test paths, command and result in `context.json`.
This phase is complete only when its declared tests pass. If tests cannot run or
fail, record `blocked_input` or `failed` with command output and stop.

> ⚡ **MANDATORY (conditional)** — If unit tests cannot run or cannot be made to pass (records `blocked_input` or `failed`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-1-unit-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed without a passing `evidence/unit-tests.md`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated test files and the unit-tests evidence. Expand the array from `artifact_plan.planned[group=unit_tests]`:

```bash
UNIT_TEST_FLAGS=()
while IFS= read -r f; do
  UNIT_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="unit_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-1-unit-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/unit-tests.md" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${UNIT_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 6.2.

---

### PHASE 6.2 — Widget Tests (required)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-2-widget-tests \
  --status started
```

**Preferred specialist role:** `@test-engineer`
**Mode:** `FEATURE_WIDGET_TESTS`

**Execution owner:** `@feature-builder`; use the same delegate-or-controller
rule as Phase 6.1.

Mandatory compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: feature_widget_tests
read_sections:
  - artifact_plan.planned[group=presentation]
  - artifact_plan.planned[group=widget_tests]
  - contracts.literal_texts
  - visual_manifest
  - layout_manifest
  - success_criteria
```

Generate and run widget tests for the feature page and interactive states,
including loading, empty, error, populated, critical actions and navigation.
Persist `evidence/widget-tests.md`, test paths, command and result in
`context.json`. A missing or failing result stops the pipeline.

> ⚡ **MANDATORY (conditional)** — If widget tests cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-2-widget-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed without a passing `evidence/widget-tests.md`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated widget tests and the widget-tests evidence. Expand the array from `artifact_plan.planned[group=widget_tests]`:

```bash
WIDGET_TEST_FLAGS=()
while IFS= read -r f; do
  WIDGET_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="widget_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-2-widget-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/widget-tests.md" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${WIDGET_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 6.3.

---

### PHASE 6.3 — Integration Tests (required)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-3-integration-tests \
  --status started
```

**Preferred specialist role:** `@test-engineer`
**Mode:** `FEATURE_INTEGRATION_TESTS`

**Execution owner:** `@feature-builder`; use the same delegate-or-controller
rule as Phase 6.1.

Mandatory compact handoff:

```yaml
spec_ref: {SPEC_PACKET_PATH}/spec.yaml
context_ref: {SPEC_PACKET_PATH}/context.json
phase: feature_integration_tests
read_sections:
  - requirements
  - navigation
  - artifact_plan.planned[group=integration_tests]
  - success_criteria
```

Generate and run at least one feature journey through the app entry point using
the configured integration-test harness. Cover the primary success path and a
relevant failure or empty state when the feature exposes one. Persist
`evidence/integration-tests.md`, test path, command and result in
`context.json`.

An unavailable integration environment is `blocked_input`, not a skipped test.
Do not audit or deliver a feature without passed integration-test evidence.

> ⚡ **MANDATORY (conditional)** — If integration tests fail or the environment is unavailable (`blocked_input`):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-3-integration-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed without a passing `evidence/integration-tests.md`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated integration tests and the integration-tests evidence. Expand the array from `artifact_plan.planned[group=integration_tests]`:

```bash
INTEGRATION_TEST_FLAGS=()
while IFS= read -r f; do
  INTEGRATION_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="integration_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-3-integration-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/integration-tests.md" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${INTEGRATION_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 6.4 (only when `golden_tests=true`) or directly to PHASE 7.

---

### PHASE 6.4 — Golden Tests (conditional)

> ⚡ **MANDATORY only when `golden_tests=true`.** When `golden_tests=false`, skip this phase entirely — do not emit `started`/`finished` for it. The workflow's own `skipped_by_input` record in `context.json`, `spec.yaml` and `PIPELINE_LOG_PATH` covers the skip.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-4-golden-tests \
  --status started
```

**Condition:** `golden_tests=true`.
**Agent:** `@golden-test-engineer`
**Mode:** `FEATURE_GOLDEN_TESTS`

When enabled, create and run complete feature-view goldens for relevant stable
states and persist `evidence/golden-tests.md`. When disabled, record
`golden_tests: skipped_by_input` with `reason: golden_tests=false` in
`context.json`, `spec.yaml` and `PIPELINE_LOG_PATH`; do not create golden files
or invoke `@golden-test-engineer`.

> ⚡ **MANDATORY (conditional)** — If golden tests were requested but cannot be made to pass:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-4-golden-tests \
  --status failed
```
> ❌ The workflow stops here — delivery cannot proceed with a failing golden outcome when `golden_tests=true`.

> ⚡ **MANDATORY (success path)** — Report `finished` with the generated golden files and the golden-tests evidence. Expand the array from `artifact_plan.planned[group=golden_tests]`:

```bash
GOLDEN_TEST_FLAGS=()
while IFS= read -r f; do
  GOLDEN_TEST_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="golden_tests") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-6-4-golden-tests \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/golden-tests.md" \
  "${GOLDEN_TEST_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 7.

---

### PHASE 7 — Audit

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-7-audit \
  --status started
```

**Agent:** `@code-auditor`

Steps:
1. Review all generated implementation and test files against:
   - SOLID principles
   - Clean Architecture dependency rules
   - Dart coding standard
   - Naming conventions
   - DI correctness (no DataSource in BLoC, no domain importing Flutter)
   - When `figma_scope=view`: `visual_manifest` and `layout_manifest`, including
     exact literal text, hierarchy/child order, geometry, four-corner radii,
     borders, source assets, typography and screen-chrome ownership. Require
     `evidence/figma-fidelity-report.json` to pass `1 dp` geometry, `2%`
     global pixel difference and `4%` regional pixel difference.
2. If issues found:
   - Report in `evidence/audit-report.md`
   - Return to `@feature-builder` for corrections
   - Max retries: `pipeline.max_audit_retries` (default: 3)
3. If approved: mark complete

For `figma_scope=view`, a missing, unresolved or failed layout/fidelity result
is a blocker (`FIGMA_LAYOUT_MANIFEST_INCOMPLETE` or
`FIGMA_FIDELITY_TOLERANCE_EXCEEDED`), not an audit warning.

Output: `evidence/audit-report.md` and a summary in the human report.

> ⚡ **MANDATORY (conditional)** — If the audit loop exceeds `pipeline.max_audit_retries` without passing, or hits a fidelity blocker (`FIGMA_LAYOUT_MANIFEST_INCOMPLETE` or `FIGMA_FIDELITY_TOLERANCE_EXCEEDED`) that cannot be resolved:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-7-audit \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the audit evidence:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-7-audit \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/audit-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to the `HUMAN CHECKPOINT — Final Build Review`.

---

### HUMAN CHECKPOINT — Final Build Review (required)

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id checkpoint-final-build-review \
  --status started
```

Present to the developer:
1. Feature build report (all files created)
2. DI registration status
3. Route registration status
4. Any manual steps needed
5. spec criteria covered and evidence paths

Wait for explicit approval.

> ⚡ **MANDATORY (success path)** — Report `finished` once the review has been presented (approval itself happens in the gate that follows):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id checkpoint-final-build-review \
  --status finished
```

> **Stop here.** This is the **domain aggregate approval gate** for the full build (PHASE 0 through PHASE 7). On rejection of a specific artifact or layer, follow the `sopp_gate.rb` revision protocol (see *Human approval gate*): report `re_started` on the affected earlier phase, apply the bounded revision, re-report `finished` with the same `--output-file` set, re-run that phase's gap report, and then re-enter this checkpoint (`re_started` → `finished` on `checkpoint-final-build-review`). Only when the checkpoint is approved may PHASE 8 begin (when `documentation=true`) or PHASE 9 (when `documentation=false`). *(This step produces no output files — no gap report required.)*

---

### PHASE 8 — Documentation (conditional)

> ⚡ **MANDATORY only when `documentation=true`.** When `documentation=false`, skip this phase entirely — do not emit `started`/`finished` for it. The workflow's own `skipped_by_input` record in `context.json`, `spec.yaml` and `PIPELINE_LOG_PATH` covers the skip.

> ⚡ **MANDATORY (when executed)** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-8-documentation \
  --status started
```

**Agent:** `@feature-builder` using shared skill `documentation-projects`

**Condition:** `documentation=true`.

Steps:
1. Resolve documentation directory:
   - If `docs/` exists at `PROJECT_ROOT` → use it
   - If `documentation/` or similar exists → use the existing one
   - Otherwise → create `docs/` at `PROJECT_ROOT`
2. Before invoking the shared skill, update `spec.yaml.artifact_plan.planned`
   with every document that may be created or modified:
   - `target_id: project_docs` or the configured docs target
   - `path: docs/<document>.md` relative to that target
   - `action: create | modify`
   - `owner: feature-builder`
   - `group: docs`
3. Check which of the 7 documents exist:
   - `index.md`, `project-overview.md`, `requirements.md`, `project-structure.md`,
     `tech-stack.md`, `features.md`, `implementation.md`, `user-flow.md`
4. For **missing documents** → generate from templates using shared skill `documentation-projects`
5. For **existing documents** → update with the new feature information:
   - `features.md` → add feature entry (name, description, status, layer files)
   - `project-structure.md` → update folder tree if new directories were created
   - `implementation.md` → update if new patterns, DI modules, or routes were added
   - `tech-stack.md` → update if new dependencies were introduced
   - `user-flow.md` → add user flow if the feature introduces a new user journey
   - `requirements.md` → add functional requirements if `acceptance_criteria` or `functional_requirements` were provided as input
   - `project-overview.md` → update current state table if feature changes project scope
6. Propose documentation commit message:
   `docs({feature}): update project documentation`

Output: `evidence/documentation-report.md` and a list of created/updated
documents in `PIPELINE_LOG_PATH`.

**Skill invocation:** `documentation-projects action=update target={docs_path} documents=all`

The shared skill internally orchestrates `doc-auditor`, `doc-interviewer`,
`doc-generator` and `doc-validator`; the mobile workflow must not reference
legacy generate-docs aliases.

When `documentation=false`, record `documentation: skipped_by_input` with
`reason: documentation=false` in `context.json`, `spec.yaml` and
`PIPELINE_LOG_PATH`. Do not modify project documentation or invoke the shared
skill.

> ⚡ **MANDATORY (success path)** — Report `finished` with the documentation-report evidence and every generated/updated document. Expand the array from `artifact_plan.planned[group=docs]`:

```bash
DOCS_FILE_FLAGS=()
while IFS= read -r f; do
  DOCS_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="docs") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-8-documentation \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/documentation-report.md" \
  "${DOCS_FILE_FLAGS[@]}"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** and then continue to PHASE 9.

---

### PHASE 9 — Delivery

> ⚡ **MANDATORY** — Report `started` when the step begins.

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-9-delivery \
  --status started
```

**Preferred specialist role:** `@delivery-manager`

**Execution owner:** `@feature-builder`. When native delegation is unavailable,
the controller executes the delivery-manager validation contract and writes the
same delivery evidence.

Steps:
1. Validate all files resolve within
   `targets.registry[artifact_plan.planned[].target_id].root`.
2. Validate topology constraints (monorepo: no changes outside `target_scope`).
3. Require passing evidence for `unit-tests.md`, `widget-tests.md` and
   `integration-tests.md`; reject delivery when any is absent, failed or
   blocked.
4. When `figma_scope=view`, require a passing
   `evidence/figma-fidelity-report.json` with the manifest viewport, complete
   node/order reconciliation, and the declared `1 dp` / `2%` / `4%` results.
   Reject delivery when it is absent, unresolved or failed.
5. Require exactly one recorded optional outcome:
   - `golden-tests.md` passed when `golden_tests=true`, or
     `golden_tests: skipped_by_input` when false.
   - `documentation-report.md` passed when `documentation=true`, or
     `documentation: skipped_by_input` when false.
6. Validate `spec.yaml` parses and validates against its schema before marking
   completion.
7. Propose a branch name and Conventional Commit messages
   (`feat({feature}): implement {feature} feature`).
8. Draft a PR description with the feature, test evidence, optional-stage
   outcomes, DI and route status.

Output: `evidence/delivery-report.md` and a summary in the human report.

The delivery manager does not run `git`, create branches or open PRs unless the
user explicitly asks for it and the spec grants external tool permissions.

> ⚡ **MANDATORY (conditional)** — If any delivery precondition is not met (missing/failing unit/widget/integration test evidence, inconsistent golden or documentation outcome, unresolved Figma fidelity report when `figma_scope=view`, schema-invalid `spec.yaml`, or artifacts outside their target root):

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-9-delivery \
  --status failed
```
> ❌ The workflow stops here.

> ⚡ **MANDATORY (success path)** — Report `finished` with the delivery report:

```bash
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-9-delivery \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/delivery-report.md"
```

> **Stop here.** Get human approval (see *Human approval gate*). Once approved, run this step's **gap report** — the workflow is complete.

---

## Verification (topology-aware)

After all phases:

- `single_repo` or `multi_repo`:
  ```bash
  flutter analyze --fatal-infos
  dart run build_runner build --delete-conflicting-outputs
  flutter test
  ```
- `monorepo_melos`:
  ```bash
  melos exec --scope={target_scope} -- "flutter analyze --fatal-infos"
  melos exec --scope={target_scope} -- "dart run build_runner build --delete-conflicting-outputs"
  melos exec --scope={target_scope} -- "flutter test"
  ```

---

## Output Report

```markdown
## Feature Build Report: {feature_name}

### Summary
- **Entity**: {EntityName}
- **Location**: {path}
- **Target**: {app_folder | melos_package}
- **Files created**: {count}
- **DI registered**: ✅ | ❌
- **Route registered**: ✅ | ❌ | ⚠️ manual
- **build_runner**: ✅ | ❌
- **Audit**: ✅ approved | ❌ rejected (attempt {N})
- **Unit tests**: ✅ passed | ❌ failed | ⛔ blocked
- **Widget tests**: ✅ passed | ❌ failed | ⛔ blocked
- **Integration tests**: ✅ passed | ❌ failed | ⛔ blocked
- **Golden tests**: ✅ passed | ⏭ skipped_by_input
- **Documentation**: ✅ updated | 🆕 created | ⏭ skipped_by_input

### Phase 0.2 — DS Components (if applicable)
| Component | Status | Action |
|---|---|---|

### Files Created
| # | Layer | File | Status |
|---|---|---|---|

### Manual Follow-up
- [ ] Register route in GoRouter (only if explicitly reported as manual)
```

---

## Rules

- NEVER skip domain or data layers — always generate the full stack
- NEVER proceed to scaffold/code generation before `review.md` is approved
- NEVER proceed to Phase 1 if Phase 0.2 has unresolved `blocked_input`
- NEVER generate files outside the root resolved by
  `artifact_plan.planned[].target_id`
- NEVER call Figma MCP outside the Figma preflight role contract and its
  explicit packet permission.
- NEVER replace a visible Figma asset with a similar local, platform, or DS
  resource. The Figma source archive is mandatory; only a declared
  `ds_icon_exact` may reuse its exact catalog id while retaining the archive.
- NEVER generate a Figma-backed feature view without a complete
  `layout_manifest`, exact literal text/order checks, and a passing Figma
  fidelity report. `figma_scope=component_inventory` is the only exception.
- NEVER skip or downgrade a mandatory phase because a specialist cannot be
  delegated. `@feature-builder` owns required unit, widget and integration
  tests and executes the `test-engineer` role contract when needed.
- NEVER mark the feature complete without passing unit, widget and integration
  evidence
- NEVER invoke `@golden-test-engineer` unless `golden_tests=true`
- NEVER invoke `documentation-projects` unless `documentation=true`
- ALWAYS run topology gate before any file generation
- ALWAYS run `build_runner` in Phase 5 before audit
- ALWAYS delegate DS component creation to `@ds-orchestrator` (never build DS components directly)
- ALWAYS enforce `agent_permissions` from `spec.yaml` before file creation,
  modification, command execution or external tool access
- ALWAYS register each phase in `PIPELINE_LOG_PATH`
- ALWAYS update `SPEC_PACKET_PATH/context.json` after every layer checkpoint
- ALWAYS use compact handoffs by `spec_ref`, `context_ref`, `phase` and
  `read_sections`
- ALWAYS record golden and documentation stages as executed or `skipped_by_input`
- If a phase fails or returns `blocked_input`, stop and report to user

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

> **Domain aggregate approval gates**, which layer on top of the per-step gate:
>
> - **PHASE 2 / PHASE 3 / PHASE 4 layer checkpoints** — Each layer runs the `docs/scripts/sopp_gate.rb` Executable Phase Gate (`open-initial`, `can-enter`, `open-checkpoint`) plus the embedded **REQUIRED CHECKPOINT** in the same phase. Rejection triggers the revision protocol: `request-changes` → write a bounded proposal at `revisions/<layer>/<revision>/proposal.md` → `propose-adjustment` → stop for authorization. After `authorize-adjustment`, apply only the proposed scope, regenerate evidence, and run `open-checkpoint` again. If a revision affects an earlier layer, invalidate that layer and every dependent checkpoint as `stale`, then replay from the earliest affected layer.
>
> - **`checkpoint-final-build-review` (post-PHASE 7)** — Approves the full build (PHASE 0 through PHASE 7). Rejection replays the affected earlier phase (`re_started` → `finished` → gap report) and then re-enters this checkpoint (`re_started` → `finished` on `checkpoint-final-build-review`). Only when the checkpoint is approved may PHASE 8 (when `documentation=true`) or PHASE 9 begin.

> Use `re_started` — never `paused` — to signal the re-execution of a step that already reported `finished`. `sopp_gate.rb` revision authorization is never step approval; it authorizes bounded regeneration, and the fresh `finished` still requires explicit human approval at the gate.

> ⚡ **MANDATORY** — On rejection, example using `phase-4-presentation-layer`:

```bash
# 1. Report re_started
pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-4-presentation-layer \
  --status re_started

# 2. ... regenerate the artifacts under the sopp_gate.rb revision protocol ...

# 3. Report finished again (recaptures baseline; rebuild the same --output-file set as the original attempt)
PRESENTATION_FILE_FLAGS=()
while IFS= read -r f; do
  PRESENTATION_FILE_FLAGS+=(--output-file "$f")
done < <(yq -r '.artifact_plan.planned[] | select(.group=="presentation") | .file' "${SPEC_PACKET_PATH}/spec.yaml")

FIDELITY_FLAGS=()
if [ "$figma_scope" = "view" ]; then
  FIDELITY_FLAGS+=(--output-file "${SPEC_PACKET_PATH}/evidence/figma-fidelity-report.json")
fi

pragma-ai workflow report \
  --instance-id "$INSTANCE_ID" \
  --workflow-id new-feature \
  --step-id phase-4-presentation-layer \
  --status finished \
  --output-file "${SPEC_PACKET_PATH}/evidence/presentation-checkpoint.md" \
  --output-file "${SPEC_PACKET_PATH}/context.json" \
  "${PRESENTATION_FILE_FLAGS[@]}" \
  "${FIDELITY_FLAGS[@]}"

# 4. Restart the approval gate
```

---

## Gap calculation & reporting (per step)

> ⚡ **MANDATORY only for steps with output files.** In this workflow:
> `phase-0-spec-packet`, `phase-0-1-figma-fidelity-planning` (only when executed), `phase-0-2-ui-component-inventory` (only when executed), `phase-1-scaffold`, `phase-1-1-api-contract-analysis` (only when executed), `phase-2-domain-layer`, `phase-3-data-layer`, `phase-4-presentation-layer`, `phase-5-wiring`, `phase-6-1-unit-tests`, `phase-6-2-widget-tests`, `phase-6-3-integration-tests`, `phase-6-4-golden-tests` (only when executed), `phase-7-audit`, `phase-8-documentation` (only when executed), `phase-9-delivery`.
> `checkpoint-final-build-review` does NOT run a gap report. The Topology Gate is not tracked by telemetry at all.

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
| `pragma-ai workflow create --workflow-id new-feature --user-story-id <id>` | At the start, once (Setup) |
| `pragma-ai workflow report ... --step-id <step> --status started` | When each executed step begins (PHASE 0–9 + `checkpoint-final-build-review`; conditional phases only when their condition holds) |
| `pragma-ai workflow report ... --step-id checkpoint-final-build-review --status finished` | On completion of the final build review (no `--output-file`) |
| `pragma-ai workflow report ... --step-id <step> --status finished --output-file ...` | On completion of every file-producing phase (see *Gap calculation* section for the full list) |
| `pragma-ai workflow report ... --step-id <step> --status failed` | When PHASE 0.1 hits `FIGMA_LAYOUT_MANIFEST_INCOMPLETE`, PHASE 0.2 hits Figma-preflight or DS-pipeline block, PHASE 4 hits `FIGMA_FIDELITY_TOLERANCE_EXCEEDED`, PHASE 6.1 / 6.2 / 6.3 / 6.4 tests fail or block, PHASE 7 exhausts audit retries or hits a fidelity blocker, or PHASE 9 preconditions fail — the workflow stops |
| `pragma-ai workflow report ... --step-id <step> --status re_started` | When the human rejects the result at the approval gate, or the flow returns to a step that was already `finished` (notably PHASE 2 / 3 / 4 layer checkpoints via `sopp_gate.rb` revision protocol, or `checkpoint-final-build-review` aggregate rejection) |
| `pragma-ai workflow gap-report --instance-id "$INSTANCE_ID" --step-id <step>` | Phase A: after the corresponding file-producing step is approved |
| `pragma-ai workflow gap-report ... --submit --report-id <id> --summary "<text>"` | Phase B: immediately after Phase A, for the same step |
| `pragma-ai workflow list --user-story-id "$USER_STORY_ID"` | Check overall progress (any time) |
| `pragma-ai workflow status "$INSTANCE_ID"` | Check instance detail (any time) |
