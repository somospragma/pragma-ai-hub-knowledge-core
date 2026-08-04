---
id: new-feature
version: 1.1.0
scope: chapter
type: workflow
chapter: mobile
entry_agent: feature-builder
input_contract: ../docs/templates/spec-packets/overlays/new-feature.yaml
invocation_mode: explicit_agent
description: >
  Workflow for building a complete Clean Architecture feature with domain, data, and presentation layers. Use when the user requests a new feature, module, flow, or Melos feature package, optionally coordinating missing DS components.
---
# Workflow: New Feature (Full Clean Architecture)

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
- The feature may need new DS components (detected in Phase 0)

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
4. If `location_strategy = melos_package`, validate `repo_root/melos.yaml` and
   `repo_root/package_path`.

If any validation fails, terminate with `blocked_input`.

---

## Inputs

```text
@feature-builder /new-feature
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

### PHASE S0 — Mobile Spec Packet (`full`)

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

When `figma_scope=view`, execute PHASE S0.5 before validating the initial
review. Validate the completed spec and wait for explicit approval before
scaffold or code generation.

---

### PHASE S0.5 — Shared Figma UI Fidelity Planning (conditional)

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

---

---

### PHASE 0 — UI Component Inventory (conditional)

**Condition:** `figma_url` or `ui_components` is provided.
**Agent:** `@feature-builder`

Steps:
1. If `figma_url` is provided, reuse PHASE S0.5 analysis when
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

---

### PHASE 1 — Scaffold

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

---

### PHASE 1.5 — API Contract Analysis (conditional)

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

---

### PHASE 2 — Domain Layer

#### Executable Phase Gate (mandatory)

Before presenting the initial review, run `scripts/sopp_gate.rb open-initial`,
show its spec hash and approval challenge, and end the response. Before every
code-producing phase, run `scripts/sopp_gate.rb can-enter` for the
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

---

### PHASE 3 — Data Layer

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

---

### PHASE 4 — Presentation Layer

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

---

### PHASE 5 — Wiring

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

---

### PHASE 6a — Unit Tests (required)

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

---

### PHASE 6b — Widget Tests (required)

**Preferred specialist role:** `@test-engineer`
**Mode:** `FEATURE_WIDGET_TESTS`

**Execution owner:** `@feature-builder`; use the same delegate-or-controller
rule as Phase 6a.

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

---

### PHASE 6c — Integration Tests (required)

**Preferred specialist role:** `@test-engineer`
**Mode:** `FEATURE_INTEGRATION_TESTS`

**Execution owner:** `@feature-builder`; use the same delegate-or-controller
rule as Phase 6a.

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

---

### PHASE 6d — Golden Tests (conditional)

**Condition:** `golden_tests=true`.
**Agent:** `@golden-test-engineer`
**Mode:** `FEATURE_GOLDEN_TESTS`

When enabled, create and run complete feature-view goldens for relevant stable
states and persist `evidence/golden-tests.md`. When disabled, record
`golden_tests: skipped_by_input` with `reason: golden_tests=false` in
`context.json`, `spec.yaml` and `PIPELINE_LOG_PATH`; do not create golden files
or invoke `@golden-test-engineer`.

---

### PHASE 7 — Audit

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

---

### HUMAN CHECKPOINT — Final Build Review (required)

Present to the developer:
1. Feature build report (all files created)
2. DI registration status
3. Route registration status
4. Any manual steps needed
5. spec criteria covered and evidence paths

Wait for explicit approval.

---

### PHASE 8 — Documentation (conditional)

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

---

### PHASE 9 — Delivery

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

### Phase 0 — DS Components (if applicable)
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
- NEVER proceed to Phase 1 if Phase 0 has unresolved `blocked_input`
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
